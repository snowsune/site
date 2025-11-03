from django.contrib import admin
from .models import MonthlyComic, UserProgress


@admin.register(MonthlyComic)
class MonthlyComicAdmin(admin.ModelAdmin):
    list_display = ["__str__", "start_page", "end_page", "updated_at"]
    readonly_fields = ["blurb_html", "updated_at"]
    fieldsets = (
        ("Content", {"fields": ("blurb", "blurb_html", "preview_image")}),
        ("Page Range", {"fields": ("start_page", "end_page")}),
        ("Metadata", {"fields": ("updated_at",)}),
    )


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ["user", "page_number", "updated_at"]
    list_filter = ["updated_at"]
    search_fields = ["user__username"]
