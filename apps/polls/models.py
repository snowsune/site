from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
import markdown

from apps.blog.models import BlogPost, Tag


class PollQuerySet(models.QuerySet):
    def visible(self):
        return self.exclude(status=Poll.STATUS_DRAFT)

    def currently_open(self):
        now = timezone.now()
        return self.filter(status=Poll.STATUS_OPEN).filter(
            Q(opens_at__isnull=True) | Q(opens_at__lte=now),
            Q(closes_at__isnull=True) | Q(closes_at__gt=now),
        )

    def ended(self):
        now = timezone.now()
        return self.visible().filter(
            Q(status=Poll.STATUS_CLOSED)
            | Q(status=Poll.STATUS_OPEN, closes_at__isnull=False, closes_at__lte=now)
        )


class Poll(models.Model):
    """A site poll, optionally mirrored as a blog post on the front page."""

    STATUS_DRAFT = "draft"
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_OPEN, "Open"),
        (STATUS_CLOSED, "Closed"),
    ]

    CHOICE_SINGLE = "single"
    CHOICE_MULTI = "multi"
    CHOICE_TYPE_CHOICES = [
        (CHOICE_SINGLE, "Single choice"),
        (CHOICE_MULTI, "Multi choice"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(
        blank=True, help_text="Markdown description shown with the poll."
    )
    description_html = models.TextField(blank=True)
    flair = models.CharField(
        max_length=40,
        blank=True,
        help_text="Short badge on the poll and blog preview (e.g. Community, Site, Comics).",
    )

    choice_type = models.CharField(
        max_length=10,
        choices=CHOICE_TYPE_CHOICES,
        default=CHOICE_SINGLE,
        help_text="Single choice = pick one. Multi choice = pick several.",
    )
    max_choices = models.PositiveIntegerField(
        default=0,
        help_text="For multi choice: max options a voter can pick. 0 = no limit.",
    )

    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_DRAFT
    )
    opens_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Optional. If set, voting starts at this time.",
    )
    closes_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Optional. If set, voting ends at this time even if status is still Open.",
    )

    discord_votes = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "After the poll closes, paste Discord vote counts keyed by choice id "
            'or label. Example: {"Pineapple": 14, "No pineapple": 31} or {"1": 14, "2": 31}'
        ),
    )

    blog_post = models.OneToOneField(
        BlogPost,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="poll",
        help_text="Linked blog post so this poll shows up in the blog / homepage feed.",
    )
    publish_to_blog = models.BooleanField(
        default=True,
        help_text="Create/update a blog post when this poll is opened.",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="polls_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PollQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "closes_at"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        if self.description:
            self.description_html = markdown.markdown(
                self.description, extensions=["extra", "codehilite", "toc"]
            )
        else:
            self.description_html = ""

        super().save(*args, **kwargs)

        if self.publish_to_blog and self.status != self.STATUS_DRAFT:
            self.sync_blog_post()

    def clean(self):
        super().clean()
        if self.max_choices and self.choice_type != self.CHOICE_MULTI:
            raise ValidationError(
                {"max_choices": "Max choices only applies to multi choice polls."}
            )
        self._validate_discord_votes(self.discord_votes)

    def _validate_discord_votes(self, value):
        if not value:
            return {}
        if not isinstance(value, dict):
            raise ValidationError(
                {
                    "discord_votes": "Discord votes must be a JSON object of label/id → count."
                }
            )
        cleaned = {}
        for key, raw in value.items():
            try:
                count = int(raw)
            except (TypeError, ValueError):
                raise ValidationError(
                    {"discord_votes": f'Count for "{key}" must be a whole number.'}
                )
            if count < 0:
                raise ValidationError(
                    {"discord_votes": f'Count for "{key}" cannot be negative.'}
                )
            cleaned[str(key)] = count
        return cleaned

    def get_absolute_url(self):
        return reverse("polls:detail", kwargs={"slug": self.slug})

    @property
    def is_open(self):
        if self.status != self.STATUS_OPEN:
            return False
        now = timezone.now()
        if self.opens_at and now < self.opens_at:
            return False
        if self.closes_at and now >= self.closes_at:
            return False
        return True

    @property
    def has_ended(self):
        if self.status == self.STATUS_CLOSED:
            return True
        if self.status == self.STATUS_OPEN and self.closes_at:
            return timezone.now() >= self.closes_at
        return False

    @property
    def is_visible(self):
        return self.status != self.STATUS_DRAFT

    def discord_votes_for(self, choice):
        """Resolve Discord votes for a choice by id or label (case-insensitive)."""
        data = self.discord_votes or {}
        if not data:
            return 0

        pk_key = str(choice.pk)
        if pk_key in data:
            try:
                return int(data[pk_key] or 0)
            except (TypeError, ValueError):
                return 0
        if choice.pk in data:
            try:
                return int(data[choice.pk] or 0)
            except (TypeError, ValueError):
                return 0

        target = choice.text.strip().lower()
        for key, raw in data.items():
            if str(key).strip().lower() == target:
                try:
                    return int(raw or 0)
                except (TypeError, ValueError):
                    return 0
        return 0

    def results(self):
        """Site votes + Discord votes (Discord only counted once the poll has ended)."""
        include_discord = self.has_ended
        choices = list(
            self.choices.annotate(site_count=Count("votes")).order_by("order", "pk")
        )
        rows = []
        for choice in choices:
            site_votes = choice.site_count
            discord = self.discord_votes_for(choice) if include_discord else 0
            rows.append(
                {
                    "choice": choice,
                    "site_votes": site_votes,
                    "discord_votes": discord,
                    "total": site_votes + discord,
                }
            )
        grand_total = sum(row["total"] for row in rows)
        divisor = grand_total or 1
        for row in rows:
            row["percent"] = round(100.0 * row["total"] / divisor, 1)
        return rows

    def voter_count(self):
        return self.votes.values("user").distinct().count()

    def user_choice_ids(self, user):
        if not user or not user.is_authenticated:
            return []
        return list(self.votes.filter(user=user).values_list("choice_id", flat=True))

    def sync_blog_post(self):
        """Create or update the linked blog post so the poll appears in the feed."""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        author = self.created_by
        if not author:
            author = (
                User.objects.filter(is_superuser=True).first() or User.objects.first()
            )
        if not author:
            return None

        content = self.description or f"Vote on **{self.title}**!"
        slug = self._blog_slug()

        if self.blog_post:
            post = self.blog_post
            post.title = self.title
            post.content = content
            if post.status != "published":
                post.status = "published"
            post.save()
        else:
            post = BlogPost.objects.create(
                title=self.title,
                slug=slug,
                author=author,
                content=content,
                status="published",
                meta_description=self._excerpt_plain()[:300],
            )
            Poll.objects.filter(pk=self.pk).update(blog_post=post)
            self.blog_post = post

        self._sync_blog_tags(post)
        return post

    def _blog_slug(self):
        slug = self.slug or slugify(self.title)
        qs = BlogPost.objects.filter(slug=slug)
        if self.blog_post_id:
            qs = qs.exclude(pk=self.blog_post_id)
        if qs.exists():
            return f"poll-{slug}"
        return slug

    def _excerpt_plain(self):
        if self.description:
            html = markdown.markdown(self.description, extensions=["extra"])
            from django.utils.html import strip_tags

            return strip_tags(html).strip()
        return self.title

    def _sync_blog_tags(self, post):
        names = ["poll"]
        if self.flair:
            names.append(self.flair)
        for name in names:
            tag, _created = Tag.objects.get_or_create(
                name=name, defaults={"slug": slugify(name)}
            )
            post.tags.add(tag)


class Choice(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "pk"]

    def __str__(self):
        return self.text


class Vote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="votes")
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="poll_votes",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["poll", "user", "choice"]]
        indexes = [
            models.Index(fields=["poll", "user"]),
        ]

    def __str__(self):
        return f"{self.user} → {self.choice} ({self.poll})"
