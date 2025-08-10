from django import forms
from django.contrib.auth import get_user_model
from .models import BlogPost, Tag

User = get_user_model()


class BlogPostForm(forms.ModelForm):
    # Custom field for creating new tags (not a model field)
    new_tags = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter new tags separated by commas...",
            }
        ),
        help_text="Add new tags separated by commas (e.g., 'python, django, web')",
    )

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
                    "placeholder": "Write your blog post in Markdown...\n\n# Headers\n**Bold text**\n*Italic text**\n[Links](url)\n![Images](image_url)",
                }
            ),
            "tags": forms.SelectMultiple(
                attrs={
                    "class": "form-control select2",
                    "data-placeholder": "Select existing tags...",
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

    def clean_new_tags(self):
        """Clean and validate new tags input"""
        new_tags = self.cleaned_data.get("new_tags", "")

        # If no input, return empty list
        if not new_tags:
            return []

        # Ensure it's a string and split by comma
        tag_names = [name.strip() for name in str(new_tags).split(",") if name.strip()]

        # Validate tag names (basic validation)
        for name in tag_names:
            if len(name) < 2:
                raise forms.ValidationError(
                    f"Tag '{name}' is too short. Tags must be at least 2 characters."
                )
            if len(name) > 50:
                raise forms.ValidationError(
                    f"Tag '{name}' is too long. Tags must be 50 characters or less."
                )
            if not name.replace("-", "").replace("_", "").isalnum():
                raise forms.ValidationError(
                    f"Tag '{name}' contains invalid characters. Use only letters, numbers, hyphens, and underscores."
                )

        return tag_names

    def save(self, commit=True):
        """Save the blog post and create new tags if needed"""
        instance = super().save(commit=False)

        if commit:
            instance.save()

            # Handle new tags
            new_tags_input = self.cleaned_data.get("new_tags", "")
            has_new_tags = False

            if new_tags_input:
                # Handle different input types
                if isinstance(new_tags_input, list):
                    # If it's already a list, use it directly
                    tag_names = [str(name).strip() for name in new_tags_input if name]
                elif isinstance(new_tags_input, str):
                    # If it's a string, check if it looks like a list representation
                    if new_tags_input.startswith("[") and new_tags_input.endswith("]"):
                        # It's a string representation of a list, parse it safely
                        import ast

                        try:
                            parsed_list = ast.literal_eval(new_tags_input)
                            tag_names = [
                                str(name).strip() for name in parsed_list if name
                            ]
                        except (ValueError, SyntaxError):
                            # Fallback to comma splitting
                            tag_names = [
                                name.strip()
                                for name in new_tags_input.split(",")
                                if name.strip()
                            ]
                    else:
                        # Regular comma-separated string
                        tag_names = [
                            name.strip()
                            for name in new_tags_input.split(",")
                            if name.strip()
                        ]
                else:
                    # Convert to string and split
                    tag_names = [
                        name.strip()
                        for name in str(new_tags_input).split(",")
                        if name.strip()
                    ]

                # Create new tags and add them to the post
                for tag_name in tag_names:
                    tag, created = Tag.objects.get_or_create(
                        name=tag_name,
                        defaults={"slug": tag_name.lower().replace(" ", "-")},
                    )
                    instance.tags.add(tag)
                    has_new_tags = True

            # Only call save_m2m if we don't have new tags
            # If we have new tags, we've already handled the many-to-many relationships manually
            if not has_new_tags:
                self.save_m2m()

        return instance


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
