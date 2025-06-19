from django.contrib import admin
from .models import SiteSetting


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    """So you can edit site settings in the admin page."""

    list_display = ("key", "value")
    search_fields = ("key", "value")
