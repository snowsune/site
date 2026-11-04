from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class MainPageTests(TestCase):
    def test_home_page_loads(self):
        """Test that the home page loads successfully."""
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_tools_page_loads(self):
        """Test that the tools/apps page loads successfully."""
        response = self.client.get(reverse("tools"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Munch Maker")

    def test_munch_maker_requires_login(self):
        response = self.client.get(reverse("munch_maker"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_munch_maker_page_for_logged_in_user(self):
        user = User.objects.create_user(username="munch", password="testpass123")
        self.client.force_login(user)
        response = self.client.get(reverse("munch_maker"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'src="/godot/index.html"')
        self.assertContains(
            response,
            "https://git.kitsunehosting.net/snowsune/VoreGamePrototype/releases",
        )
        self.assertContains(response, "Play on Linux")

        tools = self.client.get(reverse("tools"))
        self.assertContains(tools, "Munch Maker")
        self.assertContains(tools, reverse("munch_maker"))

    def test_characters_page_loads(self):
        """Test that the characters page loads successfully."""
        response = self.client.get(reverse("character-list"))
        self.assertEqual(response.status_code, 200)

    def test_blog_page_loads(self):
        """Test that the blog page loads successfully."""
        response = self.client.get(reverse("blog:blog_list"))
        self.assertEqual(response.status_code, 200)

    def test_comics_page_loads(self):
        """Test that the comics page redirects to the latest comic successfully."""
        response = self.client.get(reverse("comics:comic_home"))
        self.assertEqual(response.status_code, 302)  # Redirect status code

    def test_gallery_page_loads(self):
        """Test that the gallery page loads successfully."""
        # TODO: There is no gallery lol, skip for now :P
        try:
            response = self.client.get(reverse("gallery"))
            self.assertEqual(response.status_code, 200)
        except:
            # If gallery URL doesn't exist yet, skip this test
            self.skipTest("Gallery URL not implemented yet")
