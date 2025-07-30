from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class Webcomic(models.Model):
    """Model to track individual webcomics"""

    # Basic identification
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, help_text="URL-friendly name")

    # Visual assets
    banner = models.ImageField(upload_to="comics/banners/", blank=True, null=True)
    icon = models.ImageField(upload_to="comics/icons/", blank=True, null=True)

    # Source information
    website_url = models.URLField(max_length=500)
    rss_feed_url = models.URLField(max_length=500, blank=True, null=True)

    # Polling configuration
    POLLING_METHOD_CHOICES = [
        ("rss", "RSS Feed"),
        ("scraper", "Web Scraper"),
        ("manual", "Manual Entry"),
    ]
    polling_method = models.CharField(
        max_length=20, choices=POLLING_METHOD_CHOICES, default="rss"
    )

    # Scraper configuration (for non-RSS comics)
    scraper_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Configuration for BeautifulSoup scraper (CSS selectors, etc.)",
    )

    # Status tracking
    is_active = models.BooleanField(default=True)
    last_polled = models.DateTimeField(null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)

    # Latest comic info
    latest_comic_url = models.URLField(max_length=500, blank=True, null=True)
    latest_comic_title = models.CharField(max_length=255, blank=True, null=True)
    latest_comic_date = models.DateField(null=True, blank=True)

    # Metadata
    description = models.TextField(blank=True, null=True)
    author = models.CharField(max_length=255, blank=True, null=True)
    tags = models.JSONField(default=list, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_latest_page(self):
        """Get the most recent comic page"""
        return self.comicpage_set.order_by("-comic_date").first()

    def update_latest_info(self, page):
        """Update latest comic information from a ComicPage"""
        self.latest_comic_url = page.comic_url
        self.latest_comic_title = page.title
        self.latest_comic_date = page.comic_date
        self.last_updated = timezone.now()
        self.save()


class ComicPage(models.Model):
    """Model to store individual comic pages/updates"""

    webcomic = models.ForeignKey(Webcomic, on_delete=models.CASCADE)

    # Comic identification
    title = models.CharField(max_length=255)
    comic_url = models.URLField(max_length=500)
    comic_date = models.DateField()

    # Optional metadata
    page_number = models.PositiveIntegerField(null=True, blank=True)
    chapter = models.CharField(max_length=100, blank=True, null=True)

    # Content (if we want to store it)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    alt_text = models.TextField(blank=True, null=True)

    # Tracking
    discovered_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-comic_date", "-discovered_at"]
        unique_together = ["webcomic", "comic_url"]

    def __str__(self):
        return f"{self.webcomic.name} - {self.title} ({self.comic_date})"


class UserSubscription(models.Model):
    """Model to track user subscriptions to webcomics"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    webcomic = models.ForeignKey(Webcomic, on_delete=models.CASCADE)

    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    rss_enabled = models.BooleanField(default=True)
    discord_notifications = models.BooleanField(default=False)

    # Custom notification settings
    notification_frequency = models.CharField(
        max_length=20,
        choices=[
            ("immediate", "Immediate"),
            ("daily", "Daily Digest"),
            ("weekly", "Weekly Digest"),
        ],
        default="immediate",
    )

    # Tracking
    subscribed_at = models.DateTimeField(auto_now_add=True)
    last_notified = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ["user", "webcomic"]
        ordering = ["webcomic__name"]

    def __str__(self):
        return f"{self.user.username} -> {self.webcomic.name}"


class NotificationLog(models.Model):
    """Model to track notification history"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    webcomic = models.ForeignKey(Webcomic, on_delete=models.CASCADE)
    comic_page = models.ForeignKey(ComicPage, on_delete=models.CASCADE)

    # Notification details
    notification_type = models.CharField(
        max_length=20,
        choices=[
            ("email", "Email"),
            ("rss", "RSS"),
            ("discord", "Discord"),
        ],
    )

    sent_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-sent_at"]

    def __str__(self):
        return f"{self.user.username} - {self.webcomic.name} - {self.notification_type}"
