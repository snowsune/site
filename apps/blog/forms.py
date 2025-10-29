from django import forms
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from .models import BlogPost, Tag
from .models import Comment

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
            "is_poll",
            "poll_expires_at",
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
            "is_poll": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "poll_expires_at": forms.DateTimeInput(
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
                        defaults={"slug": slugify(tag_name)},
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


class CommentForm(forms.ModelForm):
    """Form for submitting blog post comments"""

    class Meta:
        model = Comment
        fields = ["author_name", "author_email", "author_website", "content", "parent"]
        widgets = {
            "author_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Your name *",
                    "required": True,
                }
            ),
            "author_email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Your email (optional)",
                }
            ),
            "author_website": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Your website (optional)",
                }
            ),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Write your comment here... *",
                    "required": True,
                }
            ),
            "parent": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.post = kwargs.pop("post", None)
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        # If user is logged in, pre-fill and hide some fields
        if self.user and self.user.is_authenticated:
            self.fields["author_name"].initial = self.user.username
            self.fields["author_email"].initial = self.user.email
            self.fields["author_email"].required = False
            self.fields["author_website"].required = False
            # Make author_name not required for authenticated users since we set it automatically
            self.fields["author_name"].required = False

            # Hide website field for logged-in users
            self.fields["author_name"].widget = forms.HiddenInput()
            self.fields["author_email"].widget = forms.HiddenInput()
            self.fields["author_website"].widget = forms.HiddenInput()
        else:
            # For anonymous users, try to get values from cookies (Commorg because it overlaps with the commissionission organizeer app)
            if self.request:
                self.fields["author_name"].initial = self.request.COOKIES.get(
                    "commorg_name", ""
                )
                self.fields["author_email"].initial = self.request.COOKIES.get(
                    "commorg_email", ""
                )
                self.fields["author_website"].initial = self.request.COOKIES.get(
                    "commorg_website", ""
                )

        # Set the post if provided
        if self.post:
            self.fields["parent"].initial = ""

    def clean_content(self):
        content = self.cleaned_data.get("content", "").strip()
        if len(content) < 10:
            raise forms.ValidationError("Comment must be at least 10 characters long.")
        if len(content) > 2000:
            raise forms.ValidationError("Comment must be less than 2000 characters.")
        return content

    def clean_author_name(self):
        # Skip validation for authenticated users since we set the name automatically
        if self.user and self.user.is_authenticated:
            return self.user.username

        name = self.cleaned_data.get("author_name", "").strip()
        if len(name) < 2:
            raise forms.ValidationError("Name must be at least 2 characters long.")
        if len(name) > 100:
            raise forms.ValidationError("Name must be less than 100 characters.")
        return name

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Set the post if provided
        if self.post:
            instance.post = self.post

        # Set the user if logged in
        if self.user and self.user.is_authenticated:
            instance.user = self.user
            # Auto-approve comments from registered users
            instance.status = "approved"
        else:
            # Anonymous users start with pending status
            instance.status = "pending"

        if commit:
            instance.save()

        return instance
