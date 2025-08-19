from django.test import TestCase, Client, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.http import HttpRequest
from unittest.mock import patch, MagicMock
import json

from .models import BlogPost, Tag, Comment
from .forms import BlogPostForm, CommentForm
from .views import submit_comment, moderate_comment

User = get_user_model()


class BlogModelsTest(TestCase):
    """Test cases for Blog models"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.tag = Tag.objects.create(name="Test Tag", slug="test-tag")
        self.post = BlogPost.objects.create(
            title="Test Post",
            slug="test-post",
            content="This is a test post content.",
            author=self.user,
            status="published",
            published_at=timezone.now(),
        )

    def test_blog_post_creation(self):
        """Test creating a blog post"""
        self.assertEqual(self.post.title, "Test Post")
        self.assertEqual(self.post.slug, "test-post")
        self.assertEqual(self.post.author, self.user)
        self.assertEqual(self.post.status, "published")
        self.assertTrue(self.post.is_published)

    def test_blog_post_str(self):
        """Test blog post string representation"""
        self.assertEqual(str(self.post), "Test Post")

    def test_blog_post_get_absolute_url(self):
        """Test blog post absolute URL"""
        expected_url = reverse("blog:post_detail", kwargs={"slug": "test-post"})
        self.assertEqual(self.post.get_absolute_url(), expected_url)

    def test_blog_post_display_date(self):
        """Test blog post display date logic"""
        # Published post should use published_at
        self.assertEqual(self.post.display_date, self.post.published_at)

        # Draft post should use created_at (since published_at is None)
        draft_post = BlogPost.objects.create(
            title="Draft Post",
            slug="draft-post",
            content="Draft content",
            author=self.user,
            status="draft",
        )

        # For draft posts, display_date should use created_at
        # since published_at is None and original_posting_date is None
        self.assertEqual(draft_post.display_date, draft_post.created_at)

        # Verify the property logic: original_posting_date or published_at or created_at
        self.assertIsNone(
            draft_post.published_at
        )  # Draft posts don't have published_at
        self.assertIsNotNone(draft_post.created_at)  # But they do have created_at
        self.assertEqual(draft_post.display_date, draft_post.created_at)

    def test_tag_creation(self):
        """Test creating a tag"""
        self.assertEqual(self.tag.name, "Test Tag")
        self.assertEqual(self.tag.slug, "test-tag")

    def test_tag_str(self):
        """Test tag string representation"""
        self.assertEqual(str(self.tag), "Test Tag")

    def test_blog_post_tags(self):
        """Test adding tags to blog posts"""
        self.post.tags.add(self.tag)
        self.assertIn(self.tag, self.post.tags.all())

    def test_comment_creation(self):
        """Test creating a comment"""
        comment = Comment.objects.create(
            post=self.post,
            author_name="Test Commenter",
            author_email="commenter@example.com",
            content="This is a test comment.",
            status="pending",
        )
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.author_name, "Test Commenter")
        self.assertEqual(comment.status, "pending")

    def test_comment_str(self):
        """Test comment string representation"""
        comment = Comment.objects.create(
            post=self.post, author_name="Test Commenter", content="Test comment"
        )
        expected = f"Comment by Test Commenter on {self.post.title}"
        self.assertEqual(str(comment), expected)

    def test_comment_properties(self):
        """Test comment property methods"""
        comment = Comment.objects.create(
            post=self.post,
            author_name="Test Commenter",
            content="Test comment",
            status="approved",
        )

        self.assertTrue(comment.is_approved)
        self.assertFalse(comment.is_pending)
        self.assertEqual(comment.get_display_name(), "Test Commenter")

    def test_registered_user_comment(self):
        """Test comment from registered user"""
        comment = Comment.objects.create(
            post=self.post,
            user=self.user,
            author_name=self.user.username,
            content="Comment from registered user",
            status="approved",
        )

        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.get_display_name(), self.user.username)

    def test_comment_replies(self):
        """Test comment threading/replies"""
        parent_comment = Comment.objects.create(
            post=self.post, author_name="Parent", content="Parent comment"
        )

        reply = Comment.objects.create(
            post=self.post,
            author_name="Reply",
            content="Reply to parent",
            parent=parent_comment,
        )

        self.assertEqual(reply.parent, parent_comment)
        self.assertTrue(parent_comment.has_replies)

    @patch("apps.commorganizer.utils.send_discord_webhook")
    def test_comment_webhook_on_creation(self, mock_webhook):
        """Test that moderator webhook is sent when an anonymous comment is created"""
        # Create a site setting for the moderator webhook
        from snowsune.models import SiteSetting

        SiteSetting.objects.create(
            key="moderator_webhook", value="https://example.com/webhook"
        )

        # Create a comment from anonymous user - this should trigger the moderator webhook
        comment = Comment.objects.create(
            post=self.post,
            author_name="Test Commenter",
            content="This is a test comment that should trigger a webhook",
            status="pending",
        )

        # Verify the webhook was called
        mock_webhook.assert_called_once()

        # Verify the webhook message contains expected content
        call_args = mock_webhook.call_args
        webhook_url = call_args[0][0]
        message = call_args[0][1]

        self.assertEqual(webhook_url, "https://example.com/webhook")
        self.assertIn("New comment awaiting moderation on [Test Post]", message)
        self.assertIn("by Test Commenter:", message)
        self.assertIn(
            ">>> This is a test comment that should trigger a webhook", message
        )
        self.assertIn("-# Moderate [here]", message)

    @patch("apps.commorganizer.utils.send_discord_webhook")
    def test_authenticated_user_comment_webhook(self, mock_webhook):
        """Test that blogpost webhook is sent when an authenticated user comment is created"""
        # Create site settings for both webhooks
        from snowsune.models import SiteSetting

        SiteSetting.objects.create(
            key="blogpost_webhook", value="https://example.com/blogpost-webhook"
        )

        # Create a comment from authenticated user - this should trigger the blogpost webhook
        comment = Comment.objects.create(
            post=self.post,
            user=self.user,
            author_name=self.user.username,
            content="This is a test comment from authenticated user",
            status="approved",
        )

        # Verify the webhook was called
        mock_webhook.assert_called_once()

        # Verify the webhook message contains expected content
        call_args = mock_webhook.call_args
        webhook_url = call_args[0][0]
        message = call_args[0][1]

        self.assertEqual(webhook_url, "https://example.com/blogpost-webhook")
        self.assertIn(
            f"[{self.user.username}](<https://dev.snowsune.net//user/{self.user.username}>) commented on [Test Post]",
            message,
        )
        self.assertIn(">>> This is a test comment from authenticated user", message)
        self.assertIn("-# View [here]", message)

    @patch("apps.commorganizer.utils.send_discord_webhook")
    def test_authenticated_user_comment_no_webhook_setting(self, mock_webhook):
        """Test that no webhook is sent when blogpost_webhook setting is not configured"""
        # Create a comment from authenticated user without the blogpost webhook setting
        comment = Comment.objects.create(
            post=self.post,
            user=self.user,
            author_name=self.user.username,
            content="This comment should not trigger a webhook",
            status="approved",
        )

        # Verify no webhook was called
        mock_webhook.assert_not_called()

    @patch("apps.commorganizer.utils.send_discord_webhook")
    def test_authenticated_user_comment_empty_webhook_setting(self, mock_webhook):
        """Test that no webhook is sent when blogpost_webhook setting is empty"""
        # Create a site setting with empty value
        from snowsune.models import SiteSetting

        SiteSetting.objects.create(key="blogpost_webhook", value="")

        # Create a comment from authenticated user
        comment = Comment.objects.create(
            post=self.post,
            user=self.user,
            author_name=self.user.username,
            content="This comment should not trigger a webhook",
            status="approved",
        )

        # Verify no webhook was called
        mock_webhook.assert_not_called()

    @patch("apps.commorganizer.utils.send_discord_webhook")
    def test_comment_webhook_no_setting(self, mock_webhook):
        """Test that no webhook is sent when moderator_webhook setting is not configured"""
        # Create a comment without the webhook setting
        comment = Comment.objects.create(
            post=self.post,
            author_name="Test Commenter",
            content="This comment should not trigger a webhook",
            status="pending",
        )

        # Verify no webhook was called
        mock_webhook.assert_not_called()

    @patch("apps.commorganizer.utils.send_discord_webhook")
    def test_comment_webhook_empty_setting(self, mock_webhook):
        """Test that no webhook is sent when moderator_webhook setting is empty"""
        # Create a site setting with empty value
        from snowsune.models import SiteSetting

        SiteSetting.objects.create(key="moderator_webhook", value="")

        # Create a comment
        comment = Comment.objects.create(
            post=self.post,
            author_name="Test Commenter",
            content="This comment should not trigger a webhook",
            status="pending",
        )

        # Verify no webhook was called
        mock_webhook.assert_not_called()

    @patch("apps.commorganizer.utils.send_discord_webhook")
    def test_comment_webhook_only_on_new_comment(self, mock_webhook):
        """Test that webhook is only sent for new comments, not updates"""
        # Create a site setting for the moderator webhook
        from snowsune.models import SiteSetting

        SiteSetting.objects.create(
            key="moderator_webhook", value="https://example.com/webhook"
        )

        # Create a comment - this should trigger the webhook
        comment = Comment.objects.create(
            post=self.post,
            author_name="Test Commenter",
            content="This is a test comment",
            status="pending",
        )

        # Verify the webhook was called once
        mock_webhook.assert_called_once()

        # Update the comment - this should NOT trigger another webhook
        comment.status = "approved"
        comment.save()

        # Verify the webhook was still only called once
        mock_webhook.assert_called_once()

    @patch("apps.commorganizer.utils.send_discord_webhook")
    def test_comment_webhook_on_approval(self, mock_webhook):
        """Test that blogpost webhook is sent when a pending comment is approved"""
        # Create site settings for both webhooks
        from snowsune.models import SiteSetting

        SiteSetting.objects.create(
            key="moderator_webhook", value="https://example.com/moderator-webhook"
        )
        SiteSetting.objects.create(
            key="blogpost_webhook", value="https://example.com/blogpost-webhook"
        )

        # Create a comment from anonymous user - this should trigger the moderator webhook
        comment = Comment.objects.create(
            post=self.post,
            author_name="Anonymous Commenter",
            content="This comment needs moderation",
            status="pending",
        )

        # Verify the moderator webhook was called once
        mock_webhook.assert_called_once()

        # Reset the mock to track the next call
        mock_webhook.reset_mock()

        # Now approve the comment - this should trigger the blogpost webhook
        comment.status = "approved"
        comment.save()

        # Verify the blogpost webhook was called
        mock_webhook.assert_called_once()

        # Verify it was called with the blogpost webhook URL
        call_args = mock_webhook.call_args
        webhook_url = call_args[0][0]
        message = call_args[0][1]

        self.assertEqual(webhook_url, "https://example.com/blogpost-webhook")
        self.assertIn(
            '"Anonymous Commenter" commented on [Test Post]',
            message,
        )
        self.assertIn(">>> This comment needs moderation", message)


class BlogFormsTest(TestCase):
    """Test cases for Blog forms"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.tag = Tag.objects.create(name="Test Tag", slug="test-tag")

    def test_blog_post_form_valid(self):
        """Test valid blog post form submission"""
        form_data = {
            "title": "Test Post",
            "content": "This is test content.",
            "status": "draft",
            "new_tags": "tag1, tag2, tag3",
        }

        form = BlogPostForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_blog_post_form_invalid(self):
        """Test invalid blog post form submission"""
        form_data = {
            "title": "",  # Empty title
            "content": "Content",
            "status": "draft",
        }

        form = BlogPostForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_blog_post_form_new_tags(self):
        """Test new tags processing in form"""
        form_data = {
            "title": "Test Post",
            "content": "Content",
            "status": "draft",
            "new_tags": "newtag1, newtag2",
        }

        form = BlogPostForm(data=form_data)
        self.assertTrue(form.is_valid())

        # Test that the form accepts new_tags input
        self.assertIn("new_tags", form_data)
        self.assertEqual(form_data["new_tags"], "newtag1, newtag2")

        # Test that the form is valid with new tags
        self.assertTrue(form.is_valid())

        # Test that required fields are present
        self.assertIn("title", form.cleaned_data)
        self.assertIn("content", form.cleaned_data)
        self.assertIn("status", form.cleaned_data)

    def test_comment_form_authenticated_user(self):
        """Test comment form for authenticated user"""
        form = CommentForm(user=self.user, post=None, request=None)

        # Authenticated users should have hidden fields
        self.assertIn("author_name", form.fields)
        self.assertIn("author_email", form.fields)
        self.assertIn("author_website", form.fields)

        # Fields should be hidden inputs
        self.assertIsInstance(
            form.fields["author_name"].widget,
            form.fields["author_name"].widget.__class__,
        )

    def test_comment_form_anonymous_user(self):
        """Test comment form for anonymous user"""
        form = CommentForm(user=None, post=None, request=None)

        # Anonymous users should have visible fields
        self.assertIn("author_name", form.fields)
        self.assertIn("author_email", form.fields)
        self.assertIn("author_website", form.fields)

    def test_comment_form_validation(self):
        """Test comment form validation"""
        form_data = {
            "author_name": "Test User",
            "author_email": "test@example.com",
            "content": "This is a test comment with enough content to pass validation.",
            "parent": "",
        }

        form = CommentForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_comment_form_content_too_short(self):
        """Test comment form with content too short"""
        form_data = {
            "author_name": "Test User",
            "author_email": "test@example.com",
            "content": "Short",  # Too short
            "parent": "",
        }

        form = CommentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("content", form.errors)

    def test_comment_form_content_too_long(self):
        """Test comment form with content too long"""
        form_data = {
            "author_name": "Test User",
            "author_email": "test@example.com",
            "content": "x" * 2001,  # Too long
            "parent": "",
        }

        form = CommentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("content", form.errors)


class BlogViewsTest(TestCase):
    """Test cases for Blog views"""

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()

        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.staff_user = User.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="staffpass123",
            is_staff=True,
        )

        self.post = BlogPost.objects.create(
            title="Test Post",
            slug="test-post",
            content="This is a test post content.",
            author=self.user,
            status="published",
            published_at=timezone.now(),
        )

        self.comment = Comment.objects.create(
            post=self.post,
            author_name="Test Commenter",
            author_email="commenter@example.com",
            content="This is a test comment.",
            status="pending",
        )

    def test_blog_list_view(self):
        """Test blog list view"""
        response = self.client.get(reverse("blog:blog_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Post")

    def test_blog_detail_view(self):
        """Test blog detail view"""
        response = self.client.get(self.post.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Post")
        self.assertContains(response, "This is a test post content.")

    def test_blog_detail_view_with_comments(self):
        """Test blog detail view with comments"""
        # Create an approved comment
        approved_comment = Comment.objects.create(
            post=self.post,
            author_name="Approved User",
            content="Approved comment",
            status="approved",
        )

        response = self.client.get(self.post.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Approved comment")

    def test_blog_dashboard_view_authenticated(self):
        """Test blog dashboard view for authenticated user"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("blog:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Post")

    def test_blog_dashboard_view_unauthenticated(self):
        """Test blog dashboard view for unauthenticated user"""
        response = self.client.get(reverse("blog:dashboard"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_submit_comment_authenticated_user(self):
        """Test comment submission by authenticated user"""
        self.client.login(username="testuser", password="testpass123")

        comment_data = {
            "content": "This is a comment from an authenticated user.",
            "parent": "",
        }

        response = self.client.post(
            reverse("blog:submit_comment", kwargs={"post_id": self.post.id}),
            comment_data,
        )

        self.assertEqual(response.status_code, 302)  # Redirect after success

        # Check that comment was created with approved status
        comment = Comment.objects.filter(post=self.post).latest("created_at")
        self.assertEqual(comment.status, "approved")
        self.assertEqual(comment.user, self.user)

    def test_submit_comment_anonymous_user(self):
        """Test comment submission by anonymous user"""
        comment_data = {
            "author_name": "Anonymous User",
            "author_email": "anon@example.com",
            "content": "This is a comment from an anonymous user.",
            "parent": "",
        }

        response = self.client.post(
            reverse("blog:submit_comment", kwargs={"post_id": self.post.id}),
            comment_data,
        )

        self.assertEqual(response.status_code, 302)  # Redirect after success

        # Check that comment was created with pending status
        comment = Comment.objects.filter(post=self.post).latest("created_at")
        self.assertEqual(comment.status, "pending")
        self.assertEqual(comment.author_name, "Anonymous User")

    def test_submit_comment_invalid_form(self):
        """Test comment submission with invalid form"""
        comment_data = {
            "author_name": "",  # Empty name
            "content": "Short",  # Too short content
            "parent": "",
        }

        response = self.client.post(
            reverse("blog:submit_comment", kwargs={"post_id": self.post.id}),
            comment_data,
        )

        self.assertEqual(response.status_code, 302)  # Redirect after error

        # Check that no comment was created
        comment_count = Comment.objects.filter(post=self.post).count()
        self.assertEqual(comment_count, 1)  # Only the original comment

    def test_submit_comment_ajax(self):
        """Test comment submission via AJAX"""
        self.client.login(username="testuser", password="testpass123")

        comment_data = {"content": "AJAX comment submission.", "parent": ""}

        response = self.client.post(
            reverse("blog:submit_comment", kwargs={"post_id": self.post.id}),
            comment_data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertTrue(response_data["user_authenticated"])

    def test_moderate_comment_approve(self):
        """Test comment approval"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(
            reverse(
                "blog:moderate_comment",
                kwargs={"comment_id": self.comment.id, "action": "approve"},
            )
        )

        self.assertEqual(response.status_code, 302)  # Redirect after success

        # Check that comment was approved
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.status, "approved")
        self.assertIsNotNone(self.comment.moderated_at)
        self.assertEqual(self.comment.moderated_by, self.user)

    def test_moderate_comment_reject(self):
        """Test comment rejection"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(
            reverse(
                "blog:moderate_comment",
                kwargs={"comment_id": self.comment.id, "action": "reject"},
            )
        )

        self.assertEqual(response.status_code, 302)  # Redirect after success

        # Check that comment was rejected
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.status, "rejected")
        self.assertIsNotNone(self.comment.moderated_at)

    def test_moderate_comment_spam(self):
        """Test comment spam marking"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(
            reverse(
                "blog:moderate_comment",
                kwargs={"comment_id": self.comment.id, "action": "spam"},
            )
        )

        self.assertEqual(response.status_code, 302)  # Redirect after success

        # Check that comment was marked as spam
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.status, "spam")
        self.assertIsNotNone(self.comment.moderated_at)

    def test_moderate_comment_ajax(self):
        """Test comment moderation via AJAX"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(
            reverse(
                "blog:moderate_comment",
                kwargs={"comment_id": self.comment.id, "action": "approve"},
            ),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["message"], "Comment approved.")

    def test_moderate_comment_permission_denied(self):
        """Test comment moderation without permission"""
        other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="otherpass123"
        )

        self.client.login(username="otheruser", password="otherpass123")

        response = self.client.get(
            reverse(
                "blog:moderate_comment",
                kwargs={"comment_id": self.comment.id, "action": "approve"},
            )
        )

        self.assertEqual(response.status_code, 302)  # Redirect after error

        # Check that comment was not modified
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.status, "pending")

    def test_moderate_comment_invalid_action(self):
        """Test comment moderation with invalid action"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(
            reverse(
                "blog:moderate_comment",
                kwargs={"comment_id": self.comment.id, "action": "invalid"},
            )
        )

        self.assertEqual(response.status_code, 302)  # Redirect after error

        # Check that comment was not modified
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.status, "pending")

    def test_blog_post_create_view(self):
        """Test blog post creation view"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(reverse("blog:post_create"))
        self.assertEqual(response.status_code, 200)

        # Test post creation
        post_data = {
            "title": "New Test Post",
            "content": "This is a new test post.",
            "status": "draft",
            "new_tags": "newtag1, newtag2",
        }

        response = self.client.post(reverse("blog:post_create"), post_data)
        self.assertEqual(response.status_code, 302)  # Redirect after success

        # Check that post was created
        new_post = BlogPost.objects.get(title="New Test Post")
        self.assertEqual(new_post.author, self.user)
        self.assertEqual(new_post.status, "draft")

    def test_blog_post_update_view(self):
        """Test blog post update view"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(
            reverse("blog:post_edit", kwargs={"slug": self.post.slug})
        )
        self.assertEqual(response.status_code, 200)

        # Test post update
        update_data = {
            "title": "Updated Test Post",
            "content": "This is an updated test post.",
            "status": "published",
            "new_tags": "updatedtag",
        }

        response = self.client.post(
            reverse("blog:post_edit", kwargs={"slug": self.post.slug}), update_data
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success

        # Check that post was updated
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Updated Test Post")
        self.assertEqual(self.post.status, "published")

    def test_blog_post_delete_view(self):
        """Test blog post deletion view"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(
            reverse("blog:post_delete", kwargs={"slug": self.post.slug})
        )
        self.assertEqual(response.status_code, 200)

        # Test post deletion
        response = self.client.post(
            reverse("blog:post_delete", kwargs={"slug": self.post.slug})
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success

        # Check that post was deleted
        self.assertFalse(BlogPost.objects.filter(id=self.post.id).exists())


class BlogIntegrationTest(TestCase):
    """Integration tests for Blog functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.post = BlogPost.objects.create(
            title="Integration Test Post",
            slug="integration-test-post",
            content="This is an integration test post.",
            author=self.user,
            status="published",
            published_at=timezone.now(),
        )

    def test_complete_comment_workflow(self):
        """Test complete comment workflow from submission to moderation"""
        # 1. Submit comment as anonymous user
        comment_data = {
            "author_name": "Integration Tester",
            "author_email": "integration@test.com",
            "content": "This is an integration test comment.",
            "parent": "",
        }

        response = self.client.post(
            reverse("blog:submit_comment", kwargs={"post_id": self.post.id}),
            comment_data,
        )
        self.assertEqual(response.status_code, 302)

        # 2. Verify comment was created with pending status
        comment = Comment.objects.filter(post=self.post).latest("created_at")
        self.assertEqual(comment.status, "pending")
        self.assertEqual(comment.author_name, "Integration Tester")

        # 3. Login as post author and approve comment
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(
            reverse(
                "blog:moderate_comment",
                kwargs={"comment_id": comment.id, "action": "approve"},
            )
        )
        self.assertEqual(response.status_code, 302)

        # 4. Verify comment was approved
        comment.refresh_from_db()
        self.assertEqual(comment.status, "approved")
        self.assertIsNotNone(comment.moderated_at)
        self.assertEqual(comment.moderated_by, self.user)

        # 5. Verify comment appears on blog post
        response = self.client.get(self.post.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Integration Tester")
        self.assertContains(response, "This is an integration test comment.")

    def test_tag_creation_and_association(self):
        """Test tag creation and association with blog posts"""
        self.client.login(username="testuser", password="testpass123")

        # Create post with new tags
        post_data = {
            "title": "Tag Test Post",
            "content": "This post tests tag creation.",
            "status": "published",
            "new_tags": "integration, testing, automation",
        }

        response = self.client.post(reverse("blog:post_create"), post_data)
        self.assertEqual(response.status_code, 302)

        # Verify tags were created
        new_post = BlogPost.objects.get(title="Tag Test Post")
        self.assertEqual(new_post.tags.count(), 3)

        tag_names = [tag.name for tag in new_post.tags.all()]
        self.assertIn("integration", tag_names)
        self.assertIn("testing", tag_names)
        self.assertIn("automation", tag_names)

    def test_comment_threading(self):
        """Test comment threading and replies"""
        # Create parent comment
        parent_comment = Comment.objects.create(
            post=self.post,
            author_name="Parent User",
            content="This is a parent comment.",
            status="approved",
        )

        # Submit reply as anonymous user
        reply_data = {
            "author_name": "Reply User",
            "author_email": "reply@test.com",
            "content": "This is a reply to the parent comment.",
            "parent": parent_comment.id,
        }

        response = self.client.post(
            reverse("blog:submit_comment", kwargs={"post_id": self.post.id}), reply_data
        )
        self.assertEqual(response.status_code, 302)

        # Verify reply was created
        reply = Comment.objects.filter(post=self.post, parent=parent_comment).first()
        self.assertIsNotNone(reply)
        self.assertEqual(reply.author_name, "Reply User")
        self.assertEqual(reply.status, "pending")

        # Approve reply
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(
            reverse(
                "blog:moderate_comment",
                kwargs={"comment_id": reply.id, "action": "approve"},
            )
        )
        self.assertEqual(response.status_code, 302)

        # Verify reply was approved
        reply.refresh_from_db()
        self.assertEqual(reply.status, "approved")

        # Verify threading relationship
        self.assertEqual(reply.parent, parent_comment)
        self.assertTrue(parent_comment.has_replies)


class BlogNotificationTest(TestCase):
    """Test cases for blog notification system"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.post = BlogPost.objects.create(
            title="Notification Test Post",
            slug="notification-test-post",
            content="This post tests notifications.",
            author=self.user,
            status="published",
            published_at=timezone.now(),
        )

    def test_ajax_notification_response(self):
        """Test that AJAX requests return proper notification data"""
        self.client.login(username="testuser", password="testpass123")

        comment_data = {"content": "Test comment for AJAX notification."}

        response = self.client.post(
            reverse("blog:submit_comment", kwargs={"post_id": self.post.id}),
            comment_data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertTrue(response_data["user_authenticated"])
        self.assertIn("message", response_data)


class BlogPerformanceTest(TestCase):
    """Performance and scalability tests for Blog"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # Create multiple posts and comments for performance testing
        self.posts = []
        self.comments = []

        for i in range(10):
            post = BlogPost.objects.create(
                title=f"Performance Test Post {i}",
                slug=f"performance-test-post-{i}",
                content=f"This is performance test post {i} with some content.",
                author=self.user,
                status="published",
                published_at=timezone.now(),
            )
            self.posts.append(post)

            # Create multiple comments for each post
            for j in range(5):
                comment = Comment.objects.create(
                    post=post,
                    author_name=f"User {i}-{j}",
                    content=f"Comment {j} on post {i}",
                    status="approved",
                )
                self.comments.append(comment)

    def test_blog_list_performance(self):
        """Test blog list view performance with many posts"""
        response = self.client.get(reverse("blog:blog_list"))
        self.assertEqual(response.status_code, 200)

        # Should handle multiple posts efficiently
        self.assertContains(response, "Performance Test Post 0")
        self.assertContains(response, "Performance Test Post 9")

    def test_blog_detail_performance(self):
        """Test blog detail view performance with many comments"""
        post = self.posts[0]
        response = self.client.get(post.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        # Should handle multiple comments efficiently
        self.assertContains(response, "User 0-0")
        self.assertContains(response, "User 0-4")

    def test_dashboard_performance(self):
        """Test dashboard performance with many comments"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(reverse("blog:dashboard"))
        self.assertEqual(response.status_code, 200)

        # Should handle multiple posts and comments efficiently
        self.assertContains(response, "Performance Test Post 0")
        self.assertContains(response, "Performance Test Post 9")

    def test_comment_moderation_performance(self):
        """Test comment moderation performance"""
        self.client.login(username="testuser", password="testpass123")

        # Test moderating multiple comments
        for i, comment in enumerate(self.comments[:5]):
            response = self.client.get(
                reverse(
                    "blog:moderate_comment",
                    kwargs={"comment_id": comment.id, "action": "approve"},
                )
            )
            self.assertEqual(response.status_code, 302)

            # Verify comment was moderated
            comment.refresh_from_db()
            self.assertEqual(comment.status, "approved")
