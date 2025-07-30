from django.contrib import admin
from .models import Webcomic, ComicPage, UserSubscription, NotificationLog


@admin.register(Webcomic)
class WebcomicAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "polling_method",
        "is_active",
        "last_polled",
        "latest_comic_date",
    ]
    list_filter = ["polling_method", "is_active", "created_at"]
    search_fields = ["name", "author", "description"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["last_polled", "last_updated", "created_at", "updated_at"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "slug", "description", "author", "tags")},
        ),
        ("Visual Assets", {"fields": ("banner", "icon"), "classes": ("collapse",)}),
        (
            "Source Configuration",
            {
                "fields": (
                    "website_url",
                    "rss_feed_url",
                    "polling_method",
                    "scraper_config",
                )
            },
        ),
        ("Status", {"fields": ("is_active", "last_polled", "last_updated")}),
        (
            "Latest Comic",
            {
                "fields": (
                    "latest_comic_url",
                    "latest_comic_title",
                    "latest_comic_date",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(ComicPage)
class ComicPageAdmin(admin.ModelAdmin):
    list_display = ["webcomic", "title", "comic_date", "discovered_at", "is_processed"]
    list_filter = ["webcomic", "comic_date", "is_processed", "discovered_at"]
    search_fields = ["title", "webcomic__name"]
    readonly_fields = ["discovered_at"]

    fieldsets = (
        (
            "Comic Information",
            {"fields": ("webcomic", "title", "comic_url", "comic_date")},
        ),
        (
            "Metadata",
            {
                "fields": ("page_number", "chapter", "image_url", "alt_text"),
                "classes": ("collapse",),
            },
        ),
        ("Status", {"fields": ("is_processed", "discovered_at")}),
    )


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "webcomic",
        "notification_frequency",
        "is_active",
        "subscribed_at",
    ]
    list_filter = ["notification_frequency", "is_active", "subscribed_at", "webcomic"]
    search_fields = ["user__username", "webcomic__name"]
    readonly_fields = ["subscribed_at", "last_notified"]

    fieldsets = (
        ("Subscription", {"fields": ("user", "webcomic", "is_active")}),
        (
            "Notification Preferences",
            {
                "fields": (
                    "email_notifications",
                    "rss_enabled",
                    "discord_notifications",
                    "notification_frequency",
                )
            },
        ),
        (
            "Timestamps",
            {"fields": ("subscribed_at", "last_notified"), "classes": ("collapse",)},
        ),
    )


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ["user", "webcomic", "notification_type", "success", "sent_at"]
    list_filter = ["notification_type", "success", "sent_at", "webcomic"]
    search_fields = ["user__username", "webcomic__name"]
    readonly_fields = ["sent_at"]

    fieldsets = (
        (
            "Notification Details",
            {"fields": ("user", "webcomic", "comic_page", "notification_type")},
        ),
        ("Status", {"fields": ("success", "error_message", "sent_at")}),
    )
