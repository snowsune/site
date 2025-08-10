from django import forms
from django.contrib.auth import get_user_model
from .models import BlogPost, Tag

User = get_user_model()


class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = [
            "title",
            "content",
            "tags",
            "status",
            "meta_description",
            "featured_image",
            "original_posting_date",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter blog post title...",
                }
            ),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control markdown-editor",
                    "rows": 20,
                    "placeholder": "Write your blog post in Markdown...\n\n# Headers\n**Bold text**\n*Italic text*\n[Links](url)\n![Images](image_url)",
                }
            ),
            "tags": forms.SelectMultiple(
                attrs={
                    "class": "form-control select2",
                    "data-placeholder": "Select tags...",
                    "size": "6",
                    "style": "min-height: 120px;",
                }
            ),
            "status": forms.Select(attrs={"class": "form-control"}),
            "meta_description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Brief description for search engines...",
                }
            ),
            "featured_image": forms.FileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
            "original_posting_date": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Make tags field more user-friendly
        self.fields["tags"].queryset = Tag.objects.all().order_by("name")
        self.fields["tags"].required = False


class BlogPostCreateForm(BlogPostForm):
    """Form for creating new blog posts"""

    class Meta(BlogPostForm.Meta):
        fields = BlogPostForm.Meta.fields + ["slug"]
        widgets = BlogPostForm.Meta.widgets.copy()
        widgets["slug"] = forms.TextInput(
            attrs={"class": "form-control", "placeholder": "auto-generated from title"}
        )

    def clean_slug(self):
        slug = self.cleaned_data.get("slug")
        if not slug:
            # Auto-generate slug from title
            title = self.cleaned_data.get("title", "")
            if title:
                from django.utils.text import slugify

                slug = slugify(title)

        # Check if slug is unique
        if BlogPost.objects.filter(slug=slug).exists():
            raise forms.ValidationError("A blog post with this slug already exists.")

        return slug


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter tag name..."}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Optional description...",
                }
            ),
        }
