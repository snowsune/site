from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
import markdown
from django.utils.html import strip_tags

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

        # Set published_at when status changes to published
        if self.status == "published" and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

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
