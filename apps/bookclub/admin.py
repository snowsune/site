from django.contrib import admin
from .models import MonthlyComic, UserProgress, Comment


@admin.register(MonthlyComic)
class MonthlyComicAdmin(admin.ModelAdmin):
    list_display = [
        "__str__",
        "start_page",
        "end_page",
        "url",
        "use_date_format",
        "updated_at",
    ]
    readonly_fields = ["blurb_html", "updated_at"]
    search_fields = ["blurb"]
    fieldsets = (
        ("Content", {"fields": ("blurb", "blurb_html", "preview_image")}),
        ("Page Range", {"fields": ("start_page", "end_page")}),
        (
            "URLs",
            {"fields": ("url", "page_format_url", "use_date_format", "date_format")},
        ),
        ("Metadata", {"fields": ("updated_at",)}),
    )


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ["comic", "user", "page_number", "has_comment", "updated_at"]
    list_filter = ["comic", "updated_at"]
    search_fields = ["user__username", "comment"]
    autocomplete_fields = ["comic"]

    def has_comment(self, obj):
        return bool(obj.comment)

    has_comment.boolean = True
    has_comment.short_description = "Has Comment"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["comic", "user", "page_number", "created_at", "comment_preview"]
    list_filter = ["comic", "created_at"]
    search_fields = ["user__username", "comment"]
    readonly_fields = ["created_at"]
    autocomplete_fields = ["comic"]

    def comment_preview(self, obj):
        return obj.comment[:50] + "..." if len(obj.comment) > 50 else obj.comment

    comment_preview.short_description = "Comment"
