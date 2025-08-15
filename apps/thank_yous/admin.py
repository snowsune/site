from django.contrib import admin
from .models import ThankYou


@admin.register(ThankYou)
class ThankYouAdmin(admin.ModelAdmin):
    list_display = ["name", "role", "order", "created_at"]
    list_editable = ["order"]
    list_filter = ["role", "created_at"]
    search_fields = ["name", "role", "bio"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Basic Information", {"fields": ("name", "role", "bio", "image")}),
        (
            "Social Links",
            {
                "fields": ("social_links",),
                "description": 'Format: {"https://link.com": "Link Name", "https://other.com": "Other Name"}',
            },
        ),
        (
            "Ordering",
            {
                "fields": ("order",),
                "description": "Set order to 0 for random placement, or use positive numbers for manual ordering",
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    ordering = ["order", "name"]
