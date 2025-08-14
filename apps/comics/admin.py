from django.contrib import admin
from .models import ComicPage, ComicComment
from django.utils import timezone


@admin.register(ComicPage)
class ComicPageAdmin(admin.ModelAdmin):
    list_display = ["page_number", "title", "is_nsfw", "published_at", "created_at"]
    list_filter = ["is_nsfw", "published_at", "created_at"]
    search_fields = ["title", "description"]
    ordering = ["page_number"]

    fieldsets = (
        ("Basic Info", {"fields": ("page_number", "title", "image", "description")}),
        ("Content", {"fields": ("transcript", "is_nsfw")}),
        ("Publishing", {"fields": ("published_at",)}),
    )

    readonly_fields = ["created_at", "updated_at"]


@admin.register(ComicComment)
class ComicCommentAdmin(admin.ModelAdmin):
    list_display = ["author_name", "page", "status", "created_at"]
    list_filter = ["status", "created_at", "page"]
    search_fields = ["author_name", "content", "page__title"]
    ordering = ["-created_at"]

    fieldsets = (
        (
            "Comment Info",
            {"fields": ("page", "author_name", "author_email", "content")},
        ),
        ("User Info", {"fields": ("user", "author_website")}),
        ("Moderation", {"fields": ("status", "moderated_by", "moderated_at")}),
        ("Threading", {"fields": ("parent",)}),
    )

    readonly_fields = ["created_at", "updated_at"]

    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data:
            obj.moderated_by = request.user
            obj.moderated_at = timezone.now()
        super().save_model(request, obj, form, change)
