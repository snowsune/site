from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import BlogPost, Tag, BlogImage


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "description", "post_count"]
    list_filter = ["name"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}

    def post_count(self, obj):
        return obj.blog_posts.count()

    post_count.short_description = "Posts"


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "author",
        "status",
        "published_at",
        "created_at",
        "tag_list",
        "webhook_status",
    ]
    list_filter = ["status", "created_at", "published_at", "author", "tags"]
    search_fields = ["title", "content", "author__username"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["created_at", "updated_at", "content_html", "excerpt"]

    fieldsets = (
        (
            "Content",
            {"fields": ("title", "slug", "content", "excerpt", "content_html")},
        ),
        (
            "Metadata",
            {
                "fields": (
                    "author",
                    "tags",
                    "status",
                    "meta_description",
                    "featured_image",
                )
            },
        ),
        (
            "Dates",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "published_at",
                    "original_posting_date",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Webhook",
            {"fields": ("webhook_url", "webhook_enabled"), "classes": ("collapse",)},
        ),
    )

    def tag_list(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])

    tag_list.short_description = "Tags"

    def webhook_status(self, obj):
        if obj.webhook_url and obj.webhook_enabled:
            return format_html('<span style="color: green;">✓ Enabled</span>')
        elif obj.webhook_url:
            return format_html('<span style="color: orange;">⚠ Disabled</span>')
        else:
            return format_html('<span style="color: gray;">— Not set</span>')

    webhook_status.short_description = "Webhook"

    def save_model(self, request, obj, form, change):
        if not change:  # New post
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(BlogImage)
class BlogImageAdmin(admin.ModelAdmin):
    list_display = [
        "filename",
        "image_preview",
        "uploaded_by",
        "uploaded_at",
        "markdown_link",
    ]
    list_filter = ["uploaded_at", "uploaded_by"]
    search_fields = ["filename", "uploaded_by__username"]
    readonly_fields = ["uploaded_at", "markdown_link"]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px;" />',
                obj.image.url,
            )
        return "No image"

    image_preview.short_description = "Preview"

    def markdown_link(self, obj):
        return format_html("<code>{}</code>", obj.markdown_link)

    markdown_link.short_description = "Markdown Link"
