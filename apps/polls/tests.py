from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Choice, Poll, Vote

User = get_user_model()


class PollTestMixin:
    def make_user(self, username="voter", **kwargs):
        return User.objects.create_user(
            username=username, email=f"{username}@example.com", password="testpass123", **kwargs
        )

    def make_poll(self, *, status=Poll.STATUS_OPEN, choice_type=Poll.CHOICE_SINGLE, **kwargs):
        author = kwargs.pop("created_by", None)
        if author is None:
            author = User.objects.filter(username="vixi").first()
            if author is None:
                author = self.make_user("vixi", is_staff=True)
        poll = Poll.objects.create(
            title=kwargs.pop("title", "Pizza toppings"),
            slug=kwargs.pop("slug", "pizza-toppings"),
            description=kwargs.pop("description", "Pick your **favorite**."),
            flair=kwargs.pop("flair", "Community"),
            choice_type=choice_type,
            status=status,
            created_by=author,
            **kwargs,
        )
        if not poll.choices.exists():
            Choice.objects.create(poll=poll, text="Pineapple", order=0)
            Choice.objects.create(poll=poll, text="No pineapple", order=1)
        return Poll.objects.get(pk=poll.pk)


class PollModelTests(PollTestMixin, TestCase):
    def test_markdown_description(self):
        poll = self.make_poll()
        self.assertIn("<strong>favorite</strong>", poll.description_html)

    def test_open_poll_creates_blog_post(self):
        poll = self.make_poll()
        self.assertIsNotNone(poll.blog_post)
        self.assertEqual(poll.blog_post.status, "published")
        self.assertEqual(poll.blog_post.title, poll.title)
        tag_names = set(poll.blog_post.tags.values_list("name", flat=True))
        self.assertIn("poll", tag_names)
        self.assertIn("Community", tag_names)

    def test_draft_poll_skips_blog_post(self):
        poll = self.make_poll(status=Poll.STATUS_DRAFT, slug="draft-poll", title="Draft")
        self.assertIsNone(poll.blog_post)

    def test_closes_at_ends_voting(self):
        poll = self.make_poll(closes_at=timezone.now() - timedelta(minutes=1))
        self.assertFalse(poll.is_open)
        self.assertTrue(poll.has_ended)

    def test_discord_votes_by_label_and_id(self):
        poll = self.make_poll(status=Poll.STATUS_CLOSED)
        pineapple = poll.choices.get(text="Pineapple")
        other = poll.choices.get(text="No pineapple")

        poll.discord_votes = {"Pineapple": 10, str(other.pk): 3}
        poll.save()

        rows = {row["choice"].text: row for row in poll.results()}
        self.assertEqual(rows["Pineapple"]["discord_votes"], 10)
        self.assertEqual(rows["No pineapple"]["discord_votes"], 3)
        self.assertEqual(rows["Pineapple"]["total"], 10)

    def test_discord_votes_ignored_while_open(self):
        poll = self.make_poll(discord_votes={"Pineapple": 99})
        rows = {row["choice"].text: row for row in poll.results()}
        self.assertEqual(rows["Pineapple"]["discord_votes"], 0)
        self.assertEqual(rows["Pineapple"]["total"], 0)

    def test_invalid_discord_votes_json(self):
        poll = self.make_poll()
        poll.discord_votes = ["not", "an", "object"]
        with self.assertRaises(ValidationError):
            poll.full_clean()


class PollVoteTests(PollTestMixin, TestCase):
    def setUp(self):
        self.user = self.make_user()
        self.poll = self.make_poll()
        self.pineapple = self.poll.choices.get(text="Pineapple")
        self.other = self.poll.choices.get(text="No pineapple")

    def test_login_required_to_vote(self):
        url = reverse("polls:vote", kwargs={"slug": self.poll.slug})
        response = self.client.post(url, {"choice": self.pineapple.pk})
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)
        self.assertEqual(Vote.objects.count(), 0)

    def test_single_choice_vote(self):
        self.client.login(username="voter", password="testpass123")
        url = reverse("polls:vote", kwargs={"slug": self.poll.slug})
        response = self.client.post(url, {"choice": self.pineapple.pk})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Vote.objects.filter(user=self.user).count(), 1)
        self.assertEqual(Vote.objects.get().choice, self.pineapple)

    def test_changing_single_vote(self):
        self.client.login(username="voter", password="testpass123")
        url = reverse("polls:vote", kwargs={"slug": self.poll.slug})
        self.client.post(url, {"choice": self.pineapple.pk})
        self.client.post(url, {"choice": self.other.pk})
        self.assertEqual(Vote.objects.filter(user=self.user).count(), 1)
        self.assertEqual(Vote.objects.get().choice, self.other)

    def test_multi_choice_vote(self):
        poll = self.make_poll(
            title="Snacks",
            slug="snacks",
            choice_type=Poll.CHOICE_MULTI,
        )
        a, b = poll.choices.all()
        self.client.login(username="voter", password="testpass123")
        url = reverse("polls:vote", kwargs={"slug": poll.slug})
        self.client.post(url, {"choices": [a.pk, b.pk]})
        self.assertEqual(Vote.objects.filter(user=self.user, poll=poll).count(), 2)

    def test_multi_choice_respects_max(self):
        poll = self.make_poll(
            title="Pick one snack",
            slug="one-snack",
            choice_type=Poll.CHOICE_MULTI,
            max_choices=1,
        )
        a, b = poll.choices.all()
        self.client.login(username="voter", password="testpass123")
        url = reverse("polls:vote", kwargs={"slug": poll.slug})
        self.client.post(url, {"choices": [a.pk, b.pk]})
        self.assertEqual(Vote.objects.filter(poll=poll).count(), 0)

    def test_cannot_vote_when_closed(self):
        self.poll.status = Poll.STATUS_CLOSED
        self.poll.save()
        self.client.login(username="voter", password="testpass123")
        url = reverse("polls:vote", kwargs={"slug": self.poll.slug})
        self.client.post(url, {"choice": self.pineapple.pk})
        self.assertEqual(Vote.objects.count(), 0)


class PollViewTests(PollTestMixin, TestCase):
    def test_open_list_and_archive(self):
        open_poll = self.make_poll()
        closed = self.make_poll(
            title="Old poll",
            slug="old-poll",
            status=Poll.STATUS_CLOSED,
        )

        open_page = self.client.get(reverse("polls:list"))
        self.assertContains(open_page, open_poll.title)
        self.assertNotContains(open_page, closed.title)

        archive = self.client.get(reverse("polls:archive"))
        self.assertContains(archive, closed.title)
        self.assertNotContains(archive, open_poll.title)

    def test_draft_hidden_from_detail(self):
        poll = self.make_poll(status=Poll.STATUS_DRAFT, slug="secret", title="Secret")
        response = self.client.get(reverse("polls:detail", kwargs={"slug": poll.slug}))
        self.assertEqual(response.status_code, 404)

    def test_blog_detail_embeds_poll(self):
        poll = self.make_poll()
        response = self.client.get(poll.blog_post.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pineapple")
        self.assertContains(response, "Log in")

        self.make_user("voter")
        self.client.login(username="voter", password="testpass123")
        response = self.client.get(poll.blog_post.get_absolute_url())
        self.assertContains(response, "Cast your vote")

    def test_home_page_shows_poll_blog_post(self):
        poll = self.make_poll()
        response = self.client.get(reverse("home"))
        self.assertContains(response, poll.title)
        self.assertContains(response, "Community")
