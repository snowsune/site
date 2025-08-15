from django import forms
import re
from django.utils.text import slugify


class CommissionCreateForm(forms.Form):
    """Form for anonymous users - strict validation"""

    name = forms.CharField(
        max_length=64,
        help_text="Commission name (no spaces or special characters)",
        widget=forms.TextInput(
            attrs={
                "pattern": "^[A-Za-z0-9_-]+$",
                "title": "Only letters, numbers, dashes, and underscores.",
                "placeholder": "e.g., my_commission",
            }
        ),
    )
    password = forms.CharField(
        widget=forms.PasswordInput, help_text="Password required for anonymous users"
    )

    def clean_name(self):
        name = self.cleaned_data["name"]
        if not re.match(r"^[A-Za-z0-9_-]+$", name):
            raise forms.ValidationError(
                "Name can only contain letters, numbers, dashes, and underscores."
            )
        return name


class CommissionCreateFormLoggedIn(forms.Form):
    """Form for logged-in users - auto-slugification"""

    name = forms.CharField(
        max_length=64,
        help_text="Commission name (can include spaces, will be auto-formatted)",
        widget=forms.TextInput(attrs={"placeholder": "e.g., My Awesome Commission"}),
    )

    def clean_name(self):
        name = self.cleaned_data["name"]
        if not name.strip():
            raise forms.ValidationError("Commission name cannot be empty.")
        return slugify(name)


class CommissionReturnForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)
