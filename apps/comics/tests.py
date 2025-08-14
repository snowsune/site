from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import ComicPage

User = get_user_model()


class ComicPageModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_comic_page_creation(self):
        page = ComicPage.objects.create(
            page_number=1,
            title="Test Page",
            description="A test comic page with **bold** and *italic* text",
            is_nsfw=False,
        )
        self.assertEqual(page.page_number, 1)
        self.assertEqual(page.title, "Test Page")
        self.assertFalse(page.is_nsfw)

        # Check that Markdown is rendered to HTML
        self.assertIn("<strong>bold</strong>", page.description_html)
        self.assertIn("<em>italic</em>", page.description_html)

    def test_comic_page_navigation(self):
        page1 = ComicPage.objects.create(page_number=1, title="Page 1")
        page2 = ComicPage.objects.create(page_number=2, title="Page 2")
        page3 = ComicPage.objects.create(page_number=3, title="Page 3")

        self.assertEqual(page1.get_next_page(), page2)
        self.assertEqual(page2.get_previous_page(), page1)
        self.assertEqual(page3.get_previous_page(), page2)
        self.assertIsNone(page1.get_previous_page())
        self.assertIsNone(page3.get_next_page())

    def test_blog_post_creation(self):
        page = ComicPage.objects.create(
            page_number=1,
            title="Test Page",
            description="A test comic page",
            is_nsfw=False,
        )

        # Create blog post
        blog_post = page.create_blog_post(self.user)

        self.assertIsNotNone(blog_post)
        self.assertEqual(blog_post.title, f"Comic Page 1: Test Page")
        self.assertEqual(blog_post.author, self.user)
        self.assertEqual(blog_post.status, "draft")
        self.assertEqual(page.blog_post, blog_post)


class ComicViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        # Create a mock image file for testing
        self.mock_image = SimpleUploadedFile(
            name="test_image.jpg",
            content=b"fake image content",
            content_type="image/jpeg",
        )

        self.page = ComicPage.objects.create(
            page_number=1, title="Test Page", is_nsfw=False, image=self.mock_image
        )

    def test_comic_home_view(self):
        response = self.client.get(reverse("comics:comic_home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "comics/comic_home.html")

    def test_page_detail_view(self):
        response = self.client.get(reverse("comics:page_detail", args=[1]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "comics/page_detail.html")
        self.assertEqual(response.context["page"], self.page)

    def test_nsfw_page_loads(self):
        """Test that NSFW pages load properly (NSFW handling is now in the template)"""
        nsfw_page = ComicPage.objects.create(
            page_number=2, title="NSFW Page", is_nsfw=True, image=self.mock_image
        )
        response = self.client.get(reverse("comics:page_detail", args=[2]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "comics/page_detail.html")
        self.assertEqual(response.context["page"], nsfw_page)
        self.assertTrue(response.context["page"].is_nsfw)
