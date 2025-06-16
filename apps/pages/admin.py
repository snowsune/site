from django.contrib import admin
from .models import EditablePage


@admin.register(EditablePage)
class EditablePageAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "slug",
        "created_at",
        "updated_at",
        "created_by",
        "last_modified_by",
    )
    list_filter = ("created_at", "updated_at")
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at", "created_by", "last_modified_by")
