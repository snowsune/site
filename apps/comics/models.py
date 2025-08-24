from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.text import slugify
import markdown
from apps.blog.models import BlogPost

User = get_user_model()


class PublishedComicPageManager(models.Manager):
    """Manager that only returns published comic pages"""

    def get_queryset(self):
        now = timezone.now()
        return (
            super()
            .get_queryset()
            .filter(published_at__isnull=False, published_at__lte=now)
        )


class ComicPage(models.Model):
    """Model for individual comic pages"""

    page_number = models.PositiveIntegerField(unique=True)
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to="comics/pages/")
    description = models.TextField(blank=True)
    description_html = models.TextField(blank=True)  # Rendered HTML version
    transcript = models.JSONField(default=dict, blank=True)
    is_nsfw = models.BooleanField(default=False)

    # Link to associated blog post for comments and discussion
    blog_post = models.OneToOneField(
        BlogPost,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comic_page",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    # Managers
    objects = models.Manager()
    published = PublishedComicPageManager()

    class Meta:
        ordering = ["page_number"]
        indexes = [
            models.Index(fields=["page_number"]),
            models.Index(fields=["is_nsfw", "published_at"]),
        ]

    def __str__(self):
        return f"Page {self.page_number}: {self.title}"

    def get_absolute_url(self):
        return reverse("comics:page_detail", kwargs={"page_number": self.page_number})

    @property
    def is_published(self):
        """Check if the comic page is published"""
        if not self.published_at:
            return False
        return self.published_at <= timezone.now()

    def get_next_page(self):
        """Get the next published page if it exists"""
        try:
            return ComicPage.published.filter(page_number__gt=self.page_number).first()
        except ComicPage.DoesNotExist:
            return None

    def get_previous_page(self):
        """Get the previous published page if it exists"""
        try:
            return (
                ComicPage.published.filter(page_number__lt=self.page_number)
                .order_by("-page_number")
                .first()
            )
        except ComicPage.DoesNotExist:
            return None

    @property
    def has_next(self):
        return self.get_next_page() is not None

    @property
    def has_previous(self):
        return self.get_previous_page() is not None

    def save(self, *args, **kwargs):
        # Generate HTML content from markdown
        if self.description:
            self.description_html = markdown.markdown(
                self.description, extensions=["extra", "codehilite", "toc"]
            )
        else:
            self.description_html = ""

        super().save(*args, **kwargs)

    def create_blog_post(self, author):
        """Create an associated blog post for this comic page"""
        if self.blog_post:
            return self.blog_post

        # Create a new blog post
        blog_post = BlogPost.objects.create(
            title=f"Comic Page {self.page_number}: {self.title}",
            slug=slugify(f"comic-page-{self.page_number}-{self.title}"),
            author=author,
            content=f"Discuss this comic page: {self.title}\n\n{self.description or ''}",
            status="draft",  # Start as draft, can be published later
            featured_image=self.image,
            meta_description=f"Discussion and comments for comic page {self.page_number}: {self.title}",
        )

        # Link the blog post to this comic page
        self.blog_post = blog_post
        self.save()

        return blog_post
