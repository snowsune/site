from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
import markdown


class CustomPage(models.Model):
    """Custompages Model"""

    title = models.CharField(max_length=200)
    path = models.SlugField(
        max_length=200,
        unique=True,
        help_text="URL path for this page (e.g., 'my-page' will be accessible at /cust/my-page)",
    )
    content = models.TextField(help_text="Markdown content for the page")
    content_html = models.TextField(blank=True, editable=False)  # Rendered HTML version

    # Preview image for social media/embeds
    preview_image = models.ImageField(
        upload_to="custompages/previews/", blank=True, null=True
    )

    # Sidebar links stored as JSON: [{"label": "Link Name", "url": "/path"}, ...]
    sidebar_links = models.JSONField(
        default=list,
        blank=True,
        help_text='JSON array of sidebar links. Format: [{"label": "Link Name", "url": "/path"}, ...]',
    )

    # SEO and metadata
    meta_description = models.TextField(blank=True)
    meta_title = models.CharField(
        max_length=200, blank=True, help_text="Override page title for SEO"
    )

    # Status
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["path", "is_published"]),
            models.Index(fields=["is_published"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Generate HTML content from markdown
        if self.content:
            self.content_html = markdown.markdown(
                self.content, extensions=["extra", "codehilite", "toc"]
            )
        else:
            self.content_html = ""

        # Validate sidebar_links format
        if self.sidebar_links:
            if not isinstance(self.sidebar_links, list):
                self.sidebar_links = []
            else:
                # Validate each link has required fields
                validated_links = []
                for link in self.sidebar_links:
                    if isinstance(link, dict) and "label" in link and "url" in link:
                        validated_links.append(link)
                self.sidebar_links = validated_links

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("custompages:page_detail", kwargs={"path": self.path})

    @property
    def display_title(self):
        """Return meta_title if set, otherwise title"""
        return self.meta_title or self.title
