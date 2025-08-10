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

            # Create notification message
            message = f"📝 **New Blog Post Published!**\n\n"
            message += f"**{self.title}**\n"
            message += f"by {self.author.username}\n\n"

            if self.excerpt:
                # Truncate excerpt if too long for Discord
                excerpt = (
                    self.excerpt[:150] + "..."
                    if len(self.excerpt) > 150
                    else self.excerpt
                )
                message += f"{excerpt}\n\n"

            message += f"Read more: {settings.SITE_URL or 'http://localhost:8000'}{self.get_absolute_url()}"

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
