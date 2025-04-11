from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "External/Profile Info",
            {
                "fields": (
                    "profile_picture",
                    "fa_url",
                    "flist_url",
                    "bio",
                    "discord_id",
                    "size_diff_image",
                )
            },
        ),
        (
            "Roles",
            {"fields": ("is_moderator", "is_verified")},
        ),
    )

    list_display = ["username", "email", "is_staff", "is_moderator", "is_verified"]
