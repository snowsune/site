from django.contrib import admin
from .models import Quote


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ["content", "user", "discord_id", "created_at", "active"]
    list_filter = ["active", "created_at"]
    search_fields = ["content", "user"]
    list_editable = ["active"]
