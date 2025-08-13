from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import BlogPost, Tag, BlogImage, Comment
from django.utils import timezone


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "description", "post_count"]
    list_filter = ["name"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}

    def post_count(self, obj):
        return obj.blog_posts.count()

    post_count.short_description = "Posts"


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "author",
        "status",
        "published_at",
        "created_at",
        "tag_list",
        "webhook_status",
        "comment_count",
    ]
    list_filter = ["status", "created_at", "published_at", "author", "tags"]
    search_fields = ["title", "content", "author__username"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["created_at", "updated_at", "content_html", "excerpt"]

    fieldsets = (
        (
            "Content",
            {"fields": ("title", "slug", "content", "excerpt", "content_html")},
        ),
        (
            "Metadata",
            {
                "fields": (
                    "author",
                    "tags",
                    "status",
                    "meta_description",
                    "featured_image",
                )
            },
        ),
        (
            "Dates",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "published_at",
                    "original_posting_date",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Webhook",
            {"fields": ("webhook_url", "webhook_enabled"), "classes": ("collapse",)},
        ),
    )

    def tag_list(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])

    tag_list.short_description = "Tags"

    def webhook_status(self, obj):
        if obj.webhook_url and obj.webhook_enabled:
            return format_html('<span style="color: green;">✓ Enabled</span>')
        elif obj.webhook_url:
            return format_html('<span style="color: orange;">⚠ Disabled</span>')
        else:
            return format_html('<span style="color: gray;">— Not set</span>')

    webhook_status.short_description = "Webhook"

    def comment_count(self, obj):
        approved_count = obj.comments.filter(status="approved").count()
        total_count = obj.comments.count()
        if total_count == 0:
            return "0"
        elif approved_count == total_count:
            return f"{approved_count}"
        else:
            return f"{approved_count}/{total_count}"

    comment_count.short_description = "Comments"

    def save_model(self, request, obj, form, change):
        if not change:  # New post
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(BlogImage)
class BlogImageAdmin(admin.ModelAdmin):
    list_display = [
        "filename",
        "image_preview",
        "uploaded_by",
        "uploaded_at",
        "markdown_link",
    ]
    list_filter = ["uploaded_at", "uploaded_by"]
    search_fields = ["filename", "uploaded_by__username"]
    readonly_fields = ["uploaded_at", "markdown_link"]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px;" />',
                obj.image.url,
            )
        return "No image"

    image_preview.short_description = "Preview"

    def markdown_link(self, obj):
        return format_html("<code>{}</code>", obj.markdown_link)

    markdown_link.short_description = "Markdown Link"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = [
        "author_display",
        "post_title",
        "content_preview",
        "status",
        "created_at",
        "is_reply",
    ]
    list_filter = ["status", "created_at", "post", "parent"]
    search_fields = ["author_name", "content", "post__title"]
    readonly_fields = ["created_at", "updated_at"]
    actions = ["approve_comments", "reject_comments", "mark_as_spam"]

    fieldsets = (
        (
            "Comment",
            {
                "fields": (
                    "post",
                    "parent",
                    "content",
                    "status",
                )
            },
        ),
        (
            "Author",
            {
                "fields": (
                    "user",
                    "author_name",
                    "author_email",
                    "author_website",
                )
            },
        ),
        (
            "Moderation",
            {
                "fields": (
                    "moderated_by",
                    "moderated_at",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def author_display(self, obj):
        if obj.user:
            return f"{obj.author_name} (@{obj.user.username})"
        return obj.author_name

    author_display.short_description = "Author"

    def post_title(self, obj):
        return obj.post.title

    post_title.short_description = "Post"

    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content

    content_preview.short_description = "Content"

    def is_reply(self, obj):
        return "Yes" if obj.parent else "No"

    is_reply.short_description = "Reply"

    def approve_comments(self, request, queryset):
        updated = queryset.update(
            status="approved", moderated_by=request.user, moderated_at=timezone.now()
        )
        self.message_user(request, f"{updated} comments were approved.")

    approve_comments.short_description = "Approve selected comments"

    def reject_comments(self, request, obj):
        updated = queryset.update(
            status="rejected", moderated_by=request.user, moderated_at=timezone.now()
        )
        self.message_user(request, f"{updated} comments were rejected.")

    reject_comments.short_description = "Reject selected comments"

    def mark_as_spam(self, request, queryset):
        updated = queryset.update(
            status="spam", moderated_by=request.user, moderated_at=timezone.now()
        )
        self.message_user(request, f"{updated} comments were marked as spam.")

    mark_as_spam.short_description = "Mark selected comments as spam"
