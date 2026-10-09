from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class EmailBlastTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="vixi",
            email="vixi@snowsune.net",
            password="testpass123",
        )
        self.client.force_login(self.admin)
        self.url = reverse("admin:users_customuser_email_blast")

    def test_staff_who_is_not_superuser_is_denied(self):
        staff = User.objects.create_user(
            username="mod",
            email="mod@snowsune.net",
            password="testpass123",
            is_staff=True,
        )
        self.client.force_login(staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_page_lists_recipient_count(self):
        User.objects.create_user(username="quiet", email="", password="testpass123")
        User.objects.create_user(
            username="gone",
            email="gone@snowsune.net",
            password="testpass123",
            is_active=False,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "1 person")

    def test_send_reaches_active_unique_addresses(self):
        User.objects.create_user(
            username="ada", email="Ada@snowsune.net", password="testpass123"
        )
        User.objects.create_user(
            username="ada2", email="ada@snowsune.net", password="testpass123"
        )
        User.objects.create_user(username="nope", email="", password="testpass123")
        User.objects.create_user(
            username="inactive",
            email="inactive@snowsune.net",
            password="testpass123",
            is_active=False,
        )

        response = self.client.post(
            self.url,
            {
                "subject": "Hello",
                "body": "A note from the site.",
                "confirm": "on",
            },
        )
        self.assertRedirects(response, reverse("admin:users_customuser_changelist"))
        addresses = sorted(message.to[0].lower() for message in mail.outbox)
        self.assertEqual(addresses, ["ada@snowsune.net", "vixi@snowsune.net"])
        self.assertEqual(mail.outbox[0].subject, "Hello")
        self.assertEqual(mail.outbox[0].body, "A note from the site.")

    def test_send_requires_confirmation(self):
        response = self.client.post(
            self.url,
            {"subject": "Hello", "body": "A note from the site."},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
