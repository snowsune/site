from django import forms

from .models import Contestant


class ContestantEntryForm(forms.ModelForm):
    class Meta:
        model = Contestant
        fields = ["display_name", "profile_picture"]
        labels = {
            "display_name": "Display name",
            "profile_picture": "Profile picture",
        }
        help_texts = {
            "display_name": "Username or character name <3",
            "profile_picture": "Optional but encouraged!",
        }
