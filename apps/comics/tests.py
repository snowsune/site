from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import timedelta
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

    def test_published_manager(self):
        """Test that the published manager only returns published comics"""
        # Create unpublished comic (no published_at date)
        unpublished_page = ComicPage.objects.create(
            page_number=1, title="Unpublished Page", is_nsfw=False
        )

        # Create future comic
        future_date = timezone.now() + timedelta(days=1)
        future_page = ComicPage.objects.create(
            page_number=2, title="Future Page", is_nsfw=False, published_at=future_date
        )

        # Create published comic
        past_date = timezone.now() - timedelta(days=1)
        published_page = ComicPage.objects.create(
            page_number=3, title="Published Page", is_nsfw=False, published_at=past_date
        )

        # Test published manager
        published_pages = ComicPage.published.all()
        self.assertEqual(published_pages.count(), 1)
        self.assertEqual(published_pages.first(), published_page)

        # Test is_published property
        self.assertFalse(unpublished_page.is_published)
        self.assertFalse(future_page.is_published)
        self.assertTrue(published_page.is_published)

    def test_comic_page_navigation_only_published(self):
        """Test that navigation only considers published comics"""
        # Create unpublished comic
        unpublished_page = ComicPage.objects.create(
            page_number=1, title="Unpublished Page", is_nsfw=False
        )

        # Create published comics
        past_date = timezone.now() - timedelta(days=1)
        page2 = ComicPage.objects.create(
            page_number=2, title="Page 2", is_nsfw=False, published_at=past_date
        )
        page3 = ComicPage.objects.create(
            page_number=3, title="Page 3", is_nsfw=False, published_at=past_date
        )

        # Navigation should skip unpublished pages
        self.assertEqual(page2.get_previous_page(), None)  # No published previous page
        self.assertEqual(page2.get_next_page(), page3)
        self.assertEqual(page3.get_previous_page(), page2)
        self.assertEqual(page3.get_next_page(), None)

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

        # Create a published comic page
        past_date = timezone.now() - timedelta(days=1)
        self.page = ComicPage.objects.create(
            page_number=1,
            title="Test Page",
            is_nsfw=False,
            image=self.mock_image,
            published_at=past_date,
        )

    def test_comic_home_view_redirects_to_latest(self):
        """Test that comic home redirects to the latest comic page"""
        response = self.client.get(reverse("comics:comic_home"))
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertEqual(response["Location"], reverse("comics:page_detail", args=[1]))

    def test_comic_home_view_no_comics_redirects_to_home(self):
        """Test that comic home redirects to home when no comics exist"""
        # Delete all comic pages
        ComicPage.objects.all().delete()

        response = self.client.get(reverse("comics:comic_home"))
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertEqual(response["Location"], reverse("home"))

    def test_page_detail_view_unpublished_404(self):
        """Test that unpublished comics return 404"""
        # Create an unpublished comic
        unpublished_page = ComicPage.objects.create(
            page_number=2,
            title="Unpublished Page",
            is_nsfw=False,
            image=self.mock_image,
        )

        response = self.client.get(reverse("comics:page_detail", args=[2]))
        self.assertEqual(response.status_code, 404)

    def test_page_detail_view_published_works(self):
        """Test that published comics are accessible"""
        response = self.client.get(reverse("comics:page_detail", args=[1]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "comics/page_detail.html")
        self.assertEqual(response.context["page"], self.page)

    def test_nsfw_page_loads(self):
        """Test that NSFW pages load properly (NSFW handling is now in the template)"""
        past_date = timezone.now() - timedelta(days=1)
        nsfw_page = ComicPage.objects.create(
            page_number=2,
            title="NSFW Page",
            is_nsfw=True,
            image=self.mock_image,
            published_at=past_date,
        )
        response = self.client.get(reverse("comics:page_detail", args=[2]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "comics/page_detail.html")
        self.assertEqual(response.context["page"], nsfw_page)
        self.assertTrue(response.context["page"].is_nsfw)
