from django import forms
import re


class CommissionCreateForm(forms.Form):
    name = forms.CharField(
        max_length=32,
        help_text="Commission name (no spaces or special characters)",
        widget=forms.TextInput(
            attrs={
                "pattern": "^[A-Za-z0-9_-]+$",
                "title": "Only letters, numbers, dashes, and underscores.",
            }
        ),
    )
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_name(self):
        name = self.cleaned_data["name"]
        if not re.match(r"^[A-Za-z0-9_-]+$", name):
            raise forms.ValidationError(
                "Name can only contain letters, numbers, dashes, and underscores."
            )
        return name


class CommissionReturnForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)
