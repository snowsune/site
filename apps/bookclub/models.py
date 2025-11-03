from django.db import models
from django.contrib.auth import get_user_model
import markdown

User = get_user_model()


class MonthlyComic(models.Model):
    """The monthly webcomic info - editable from admin"""

    blurb = models.TextField(help_text="Markdown content describing the webcomic")
    blurb_html = models.TextField(blank=True)  # Rendered HTML version
    preview_image = models.ImageField(
        upload_to="bookclub/previews/", blank=True, null=True
    )
    start_page = models.IntegerField(
        default=0, help_text="Starting page number (e.g., 0)"
    )
    end_page = models.IntegerField(
        default=719, help_text="Ending page number (e.g., 719)"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Monthly Comic ({self.updated_at.date()})"

    def save(self, *args, **kwargs):
        # Generate HTML content from markdown
        if self.blurb:
            self.blurb_html = markdown.markdown(
                self.blurb, extensions=["extra", "codehilite"]
            )
        super().save(*args, **kwargs)


class UserProgress(models.Model):
    """User's reading progress - stores page number"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="bookclub_progress"
    )
    page_number = models.IntegerField(default=0, help_text="Current page number")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-page_number", "-updated_at"]
        unique_together = [["user"]]

    def __str__(self):
        return f"{self.user.username}: Page {self.page_number}"

    def get_position_percentage(self, start_page, end_page):
        """Calculate position as percentage (0-100) based on page range"""
        if end_page == start_page:
            return 100 if self.page_number >= start_page else 0

        range_size = end_page - start_page
        position_in_range = self.page_number - start_page

        if position_in_range < 0:
            return 0
        if position_in_range > range_size:
            return 100

        percentage = int((position_in_range / range_size) * 100)
        return min(100, max(0, percentage))
