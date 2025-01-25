from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = UserAdmin.fieldsets + (
        ("Profile Info", {"fields": ("profile_picture", "fa_url", "flist_url", "bio")}),
        ("Roles", {"fields": ("is_moderator", "is_admin")}),
    )
    list_display = ["username", "email", "is_staff", "is_moderator", "is_admin"]


admin.site.register(CustomUser, CustomUserAdmin)
