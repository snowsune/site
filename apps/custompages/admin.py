from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import CustomPage


@admin.register(CustomPage)
class CustomPageAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "path",
        "is_published",
        "preview_image_thumbnail",
        "sidebar_links_count",
        "created_at",
        "updated_at",
    ]
    list_filter = ["is_published", "created_at", "updated_at"]
    search_fields = ["title", "path", "content", "meta_description"]
    prepopulated_fields = {"path": ("title",)}
    readonly_fields = [
        "created_at",
        "updated_at",
        "content_html",
        "preview_image_display",
    ]

    fieldsets = (
        (
            "Content",
            {
                "fields": (
                    "title",
                    "path",
                    "content",
                    "content_html",
                )
            },
        ),
        (
            "Media",
            {
                "fields": (
                    "preview_image",
                    "preview_image_display",
                )
            },
        ),
        (
            "Sidebar",
            {
                "fields": ("sidebar_links",),
                "description": 'Enter sidebar links as JSON array. Format: [{"label": "Link Name", "url": "/path"}, ...]',
            },
        ),
        (
            "SEO",
            {
                "fields": (
                    "meta_title",
                    "meta_description",
                )
            },
        ),
        (
            "Status",
            {"fields": ("is_published",)},
        ),
        (
            "Dates",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def preview_image_thumbnail(self, obj):
        if obj.preview_image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px;" />',
                obj.preview_image.url,
            )
        return "No image"

    preview_image_thumbnail.short_description = "Preview"

    def preview_image_display(self, obj):
        if obj.preview_image:
            return format_html(
                '<img src="{}" style="max-width: 100%; height: auto;" />',
                obj.preview_image.url,
            )
        return "No preview image set"

    preview_image_display.short_description = "Preview Image"

    def sidebar_links_count(self, obj):
        if obj.sidebar_links and isinstance(obj.sidebar_links, list):
            return len(obj.sidebar_links)
        return 0

    sidebar_links_count.short_description = "Sidebar Links"
