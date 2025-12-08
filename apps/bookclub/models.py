import logging
import markdown

from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()
logger = logging.getLogger(__name__)


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
    url = models.URLField(
        blank=True, null=True, help_text="Base URL for the comic (optional)"
    )
    page_format_url = models.CharField(
        max_length=255,
        blank=True,
        help_text="URL format with {page_number} placeholder (e.g., https://example.com/page/{page_number})",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Monthly Comic ({self.updated_at.date()})"

    def get_page_url(self, page_number):
        """Generate URL for a specific page number"""
        if self.page_format_url:
            return self.page_format_url.format(page_number=page_number)
        elif self.url:
            return f"{self.url}#page-{page_number}"
        return None

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
    comment = models.TextField(blank=True, help_text="Optional comment about progress")
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

    def save(self, *args, **kwargs):
        # Find and compare the old leader before this save <3
        # This is just for fun! Just to trigger the webhook when the leader changes!

        # Find the current leader (before this save)
        old_leader_id = None
        try:
            all_before = UserProgress.objects.all()
            if all_before.exists():
                old_leader = all_before.order_by("-page_number", "-updated_at").first()
                if old_leader:
                    old_leader_id = old_leader.pk
        except Exception as e:
            logger.error(f"Error finding old leader: {e}")

        super().save(*args, **kwargs)

        # Determine who is the leader now (after save)
        all_progress = UserProgress.objects.all()
        if all_progress.exists():
            new_leader = all_progress.order_by("-page_number", "-updated_at").first()

            # Send if:
            # - New leader is different from old leader
            # - This user is the new leader
            if (
                new_leader
                and new_leader.pk != old_leader_id
                and new_leader.pk == self.pk
            ):
                # Leader changed and this user is the new leader! Send webhook
                from .webhooks import send_leader_change_webhook

                send_leader_change_webhook(
                    new_leader.user.username, new_leader.page_number
                )


class Comment(models.Model):
    """Individual comment entries - stores comment history"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="bookclub_comments"
    )
    page_number = models.IntegerField(help_text="Page number when comment was made")
    comment = models.TextField(help_text="Comment text")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.user.username} - Page {self.page_number} ({self.created_at.date()})"
        )
