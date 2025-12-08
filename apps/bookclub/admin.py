from django.contrib import admin
from .models import MonthlyComic, UserProgress, Comment


@admin.register(MonthlyComic)
class MonthlyComicAdmin(admin.ModelAdmin):
    list_display = ["__str__", "start_page", "end_page", "url", "updated_at"]
    readonly_fields = ["blurb_html", "updated_at"]
    fieldsets = (
        ("Content", {"fields": ("blurb", "blurb_html", "preview_image")}),
        ("Page Range", {"fields": ("start_page", "end_page")}),
        ("URLs", {"fields": ("url", "page_format_url")}),
        ("Metadata", {"fields": ("updated_at",)}),
    )


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ["user", "page_number", "has_comment", "updated_at"]
    list_filter = ["updated_at"]
    search_fields = ["user__username", "comment"]

    def has_comment(self, obj):
        return bool(obj.comment)
    has_comment.boolean = True
    has_comment.short_description = "Has Comment"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["user", "page_number", "created_at", "comment_preview"]
    list_filter = ["created_at"]
    search_fields = ["user__username", "comment"]
    readonly_fields = ["created_at"]

    def comment_preview(self, obj):
        return obj.comment[:50] + "..." if len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = "Comment"
