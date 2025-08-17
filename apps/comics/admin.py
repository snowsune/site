from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.template.response import TemplateResponse
from django.http import JsonResponse
from .models import ComicPage


@admin.register(ComicPage)
class ComicPageAdmin(admin.ModelAdmin):
    list_display = [
        "page_number",
        "title",
        "is_nsfw",
        "published_at",
        "blog_post_link",
        "has_blog_post",
        "transcript_elements_count",
    ]
    list_filter = ["is_nsfw", "published_at", "created_at"]
    search_fields = ["title", "description"]
    ordering = ["page_number"]

    fieldsets = (
        (
            "Comic Content",
            {
                "fields": (
                    "page_number",
                    "title",
                    "image",
                    "description",
                    "description_html",
                    "transcript",
                    "is_nsfw",
                )
            },
        ),
        (
            "Publishing",
            {
                "fields": ("published_at", "blog_post_link", "has_blog_post"),
                "classes": ("collapse",),
                "description": "Blog posts are automatically created when you save a comic page. They start as drafts and can be published later.",
            },
        ),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    readonly_fields = [
        "created_at",
        "updated_at",
        "blog_post_link",
        "has_blog_post",
        "description_html",
    ]

    change_form_template = "admin/comics/comicpage/change_form.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:page_id>/transcript-editor/",
                self.admin_site.admin_view(self.transcript_editor_view),
                name="comics_comicpage_transcript_editor",
            ),
            path(
                "<int:page_id>/transcript-data/",
                self.admin_site.admin_view(self.transcript_data_view),
                name="comics_comicpage_transcript_data",
            ),
        ]
        return custom_urls + urls

    def transcript_editor_view(self, request, page_id):
        """View for the transcript editor interface"""
        try:
            comic_page = ComicPage.objects.get(id=page_id)
        except ComicPage.DoesNotExist:
            return JsonResponse({"error": "Comic page not found"}, status=404)

        context = {
            "title": f"Transcript Editor - {comic_page.title}",
            "comic_page": comic_page,
            "transcript_elements": comic_page.transcript.get("elements", []),
            "opts": self.model._meta,
        }

        return TemplateResponse(
            request, "admin/comics/comicpage/transcript_editor.html", context
        )

    def transcript_data_view(self, request, page_id):
        """API endpoint for getting/setting transcript data"""
        try:
            comic_page = ComicPage.objects.get(id=page_id)
        except ComicPage.DoesNotExist:
            return JsonResponse({"error": "Comic page not found"}, status=404)

        if request.method == "GET":
            # Return current transcript elements from JSONField
            elements = comic_page.transcript.get("elements", [])
            return JsonResponse({"elements": elements})

        elif request.method == "POST":
            # Save transcript elements to JSONField
            try:
                import json

                data = json.loads(request.body)
                elements_data = data.get("elements", [])

                # Update the transcript JSONField
                comic_page.transcript = {"elements": elements_data}
                comic_page.save()

                return JsonResponse(
                    {"success": True, "message": "Transcript saved successfully"}
                )
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=400)

    def transcript_elements_count(self, obj):
        elements = obj.transcript.get("elements", [])
        count = len(elements)
        if count > 0:
            return format_html(
                '<a href="{}">{}</a>',
                f"admin:comics_comicpage_transcript_editor",
                count,
            )
        return count

    transcript_elements_count.short_description = "Transcript Elements"

    def blog_post_link(self, obj):
        if obj.blog_post:
            return format_html(
                '<a href="{}">View Blog Post</a>', obj.blog_post.get_absolute_url()
            )
        return "No blog post created"

    blog_post_link.short_description = "Blog Post"

    def has_blog_post(self, obj):
        return bool(obj.blog_post)

    has_blog_post.boolean = True
    has_blog_post.short_description = "Has Blog Post"

    def save_model(self, request, obj, form, change):
        # Create blog post if it doesn't exist
        if not obj.blog_post:
            obj.create_blog_post(request.user)
        super().save_model(request, obj, form, change)
