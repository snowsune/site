from django import forms
from django.contrib import admin
from django.utils.html import format_html

from .models import Choice, Poll, Vote


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3
    fields = ["text", "order"]


class PollAdminForm(forms.ModelForm):
    class Meta:
        model = Poll
        fields = "__all__"
        widgets = {
            "description": forms.Textarea(
                attrs={"rows": 8, "placeholder": "Markdown is fine here~"}
            ),
            "flair": forms.TextInput(
                attrs={"placeholder": "Community, Site, Comics, Events..."}
            ),
        }


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    form = PollAdminForm
    list_display = [
        "title",
        "flair",
        "choice_type",
        "status",
        "is_open_display",
        "closes_at",
        "vote_count",
        "blog_link",
    ]
    list_filter = ["status", "choice_type", "flair"]
    search_fields = ["title", "description", "flair"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["created_at", "updated_at", "description_html", "blog_post"]
    inlines = [ChoiceInline]
    autocomplete_fields = ["created_by"]

    fieldsets = (
        (
            "Poll",
            {
                "fields": (
                    "title",
                    "slug",
                    "flair",
                    "description",
                    "description_html",
                    "choice_type",
                    "max_choices",
                )
            },
        ),
        (
            "Schedule",
            {"fields": ("status", "opens_at", "closes_at")},
        ),
        (
            "Discord votes",
            {
                "fields": ("discord_votes",),
                "description": (
                    "Paste counts after the poll closes. Keys can be choice labels "
                    'or ids, e.g. {"Tacos": 12, "Sushi": 7} or {"1": 12, "2": 7}.'
                ),
            },
        ),
        (
            "Blog",
            {"fields": ("publish_to_blog", "blog_post")},
        ),
        (
            "Meta",
            {
                "fields": ("created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    @admin.display(boolean=True, description="Open now")
    def is_open_display(self, obj):
        return obj.is_open

    @admin.display(description="Site votes")
    def vote_count(self, obj):
        return obj.votes.count()

    @admin.display(description="Blog post")
    def blog_link(self, obj):
        if not obj.blog_post:
            return "—"
        url = obj.blog_post.get_absolute_url()
        return format_html('<a href="{}">{}</a>', url, obj.blog_post.slug)


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ["user", "poll", "choice", "created_at"]
    list_filter = ["poll", "created_at"]
    search_fields = ["user__username", "poll__title", "choice__text"]
    autocomplete_fields = ["user", "poll"]
    raw_id_fields = ["choice"]
    readonly_fields = ["created_at", "updated_at"]
