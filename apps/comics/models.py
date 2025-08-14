from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from apps.blog.models import Comment

User = get_user_model()


class ComicPage(models.Model):
    """Model for individual comic pages"""

    page_number = models.PositiveIntegerField(unique=True)
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to="comics/pages/")
    description = models.TextField(blank=True)
    transcript = models.JSONField(default=dict, blank=True)
    is_nsfw = models.BooleanField(default=False)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

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

    def get_next_page(self):
        """Get the next page if it exists"""
        try:
            return ComicPage.objects.filter(page_number__gt=self.page_number).first()
        except ComicPage.DoesNotExist:
            return None

    def get_previous_page(self):
        """Get the previous page if it exists"""
        try:
            return (
                ComicPage.objects.filter(page_number__lt=self.page_number)
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


class ComicComment(Comment):
    """Model for comic page comments, extending the blog Comment model"""

    page = models.ForeignKey(
        ComicPage, on_delete=models.CASCADE, related_name="comments"
    )

    def __str__(self):
        return f"Comment by {self.author_name} on page {self.page.page_number}"
