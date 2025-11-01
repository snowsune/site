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
                    "badges",
                )
            },
        ),
        (
            "Email Verification",
            {
                "fields": (
                    "email_verified",
                    "email_verification_token",
                    "email_verification_sent_at",
                )
            },
        ),
    )

    list_display = ["username", "email", "is_staff", "email_verified"]
