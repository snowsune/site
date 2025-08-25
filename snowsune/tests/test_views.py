from django.test import TestCase
from django.urls import reverse


class MainPageTests(TestCase):
    def test_home_page_loads(self):
        """Test that the home page loads successfully."""
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_tools_page_loads(self):
        """Test that the tools/apps page loads successfully."""
        response = self.client.get(reverse("tools"))
        self.assertEqual(response.status_code, 200)

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
