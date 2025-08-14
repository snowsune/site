from django.contrib import admin
from django.utils.html import format_html
from .models import ComicPage


@admin.register(ComicPage)
class ComicPageAdmin(admin.ModelAdmin):
    list_display = [
        "page_number",
        "title",
        "is_nsfw",
        "published_at",
        "blog_post_link",
        "has_blog_post",
    ]
    list_filter = ["is_nsfw", "published_at", "created_at"]
    search_fields = ["title", "description"]
    ordering = ["page_number"]

    fieldsets = (
        (
            "Comic Content",
            {
                "fields": (
                    "page_number",
                    "title",
                    "image",
                    "description",
                    "transcript",
                    "is_nsfw",
                )
            },
        ),
        (
            "Publishing",
            {
                "fields": ("published_at", "blog_post_link", "has_blog_post"),
                "classes": ("collapse",),
                "description": "Blog posts are automatically created when you save a comic page. They start as drafts and can be published later.",
            },
        ),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    readonly_fields = ["created_at", "updated_at", "blog_post_link", "has_blog_post"]

    def blog_post_link(self, obj):
        if obj.blog_post:
            return format_html(
                '<a href="{}">View Blog Post</a>', obj.blog_post.get_absolute_url()
            )
        return "No blog post created"

    blog_post_link.short_description = "Blog Post"

    def has_blog_post(self, obj):
        return bool(obj.blog_post)

    has_blog_post.boolean = True
    has_blog_post.short_description = "Has Blog Post"

    def save_model(self, request, obj, form, change):
        # Create blog post if it doesn't exist
        if not obj.blog_post:
            obj.create_blog_post(request.user)
        super().save_model(request, obj, form, change)
