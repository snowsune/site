from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
import markdown
from django.utils.html import strip_tags
from django.conf import settings
from snowsune.models import SiteSetting

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BlogPost(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="blog_posts"
    )
    content = models.TextField()
    content_html = models.TextField(blank=True)  # Rendered HTML version
    excerpt = models.TextField(blank=True)  # Auto-generated excerpt

    tags = models.ManyToManyField(Tag, blank=True, related_name="blog_posts")

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")

    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    original_posting_date = models.DateTimeField(
        null=True, blank=True
    )  # For imported posts

    # SEO and display
    meta_description = models.TextField(blank=True)
    featured_image = models.ImageField(
        upload_to="blog/featured/", blank=True, null=True
    )

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["status", "published_at"]),
            models.Index(fields=["author", "status"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Generate slug if not provided
        if not self.slug:
            self.slug = slugify(self.title)

        # Generate HTML content from markdown
        if self.content:
            self.content_html = markdown.markdown(
                self.content, extensions=["extra", "codehilite", "toc"]
            )
            # Generate excerpt from first paragraph
            if not self.excerpt:
                html_text = strip_tags(self.content_html)
                if len(html_text) > 200:
                    self.excerpt = html_text[:200] + "..."
                else:
                    self.excerpt = html_text

        # Check if status is changing to published
        was_published = (
            self.pk and BlogPost.objects.get(pk=self.pk).status == "published"
        )
        is_now_published = self.status == "published"

        # Set published_at when status changes to published
        if self.status == "published" and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

        # Send Discord webhook notification when post is newly published
        if is_now_published and not was_published:
            self.send_discord_notification()

    def send_discord_notification(self):
        """Send Discord webhook notification for newly published blog post"""
        try:
            # Get webhook URL from site settings
            webhook_setting = SiteSetting.objects.filter(key="blogpost_webhook").first()
            if not webhook_setting or not webhook_setting.value:
                return  # No webhook configured

            webhook_url = webhook_setting.value.strip()
            if not webhook_url:
                return

            # Import here to avoid circular imports
            from apps.commorganizer.utils import send_discord_webhook

            # Create notification message with Discord markdown
            message = f"📝 **New Blog Post Published!**\n\n"
            message += f"**{self.title}**\n"
            message += f"*by {self.author.username}*\n\n"

            # Add more content - Discord has 2000 character limit, so we can be generous
            if self.excerpt:
                # Use more of the excerpt - Discord supports markdown
                excerpt = self.excerpt
                if len(excerpt) > 800:  # Leave room for other content
                    excerpt = excerpt[:800] + "..."
                message += f"**Excerpt:**\n{excerpt}\n\n"

            # Add tags if available
            if self.tags.exists():
                tag_names = [tag.name for tag in self.tags.all()]
                message += f"**Tags:** {', '.join(tag_names)}\n\n"

            # Add the full URL
            full_url = f"{settings.SITE_URL}{self.get_absolute_url()}"
            message += f"**Read the full post:** {full_url}"

            # Check message length and truncate if needed
            if len(message) > 1900:  # Leave some buffer
                # Truncate excerpt to fit
                if self.excerpt:
                    available_chars = 1900 - len(message) + len(self.excerpt)
                    if available_chars > 100:  # Only if we have meaningful space
                        excerpt = self.excerpt[: available_chars - 50] + "..."
                        # Rebuild message with truncated excerpt
                        message = f"📝 **New Blog Post Published!**\n\n"
                        message += f"**{self.title}**\n"
                        message += f"*by {self.author.username}*\n\n"
                        message += f"**Excerpt:**\n{excerpt}\n\n"
                        if self.tags.exists():
                            tag_names = [tag.name for tag in self.tags.all()]
                            message += f"**Tags:** {', '.join(tag_names)}\n\n"
                        message += f"**Read the full post:** {full_url}"

            # Send webhook
            send_discord_webhook(webhook_url, message)

        except Exception as e:
            # Log error but don't break the save process
            print(f"Failed to send Discord webhook for blog post {self.title}: {e}")

    def get_absolute_url(self):
        return reverse("blog:post_detail", kwargs={"slug": self.slug})

    @property
    def is_published(self):
        return self.status == "published" and self.published_at is not None

    @property
    def display_date(self):
        """Return the date to display (original posting date if available, otherwise published date)"""
        return self.original_posting_date or self.published_at or self.created_at


class BlogImage(models.Model):
    """Model for storing images uploaded via the blog editor"""

    image = models.ImageField(upload_to="blog/images/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    filename = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.filename or self.image.name

    def save(self, *args, **kwargs):
        if not self.filename:
            self.filename = self.image.name
        super().save(*args, **kwargs)

    @property
    def markdown_link(self):
        """Return the markdown image link for this image"""
        return f"![{self.filename}]({self.image.url})"


class Comment(models.Model):
    """Model for blog post comments"""

    STATUS_CHOICES = [
        ("pending", "Pending Moderation"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("spam", "Spam"),
    ]

    post = models.ForeignKey(
        BlogPost, on_delete=models.CASCADE, related_name="comments"
    )
    author_name = models.CharField(max_length=100)
    author_email = models.EmailField(blank=True)
    author_website = models.URLField(blank=True)
    content = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moderated_comments",
    )

    # For registered users
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blog_comments",
    )

    # Parent comment for replies (threading)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["post", "status", "created_at"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"Comment by {self.author_name} on {self.post.title}"

    @property
    def is_approved(self):
        return self.status == "approved"

    @property
    def is_pending(self):
        return self.status == "pending"

    @property
    def has_replies(self):
        return self.replies.exists()

    def get_display_name(self):
        """Get the display name for the comment author"""
        if self.user:
            return self.user.username
        return self.author_name
