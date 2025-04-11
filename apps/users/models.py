from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    profile_picture = models.ImageField(
        upload_to="profile_pics/", blank=True, null=True
    )

    # Links to external profiles
    fa_url = models.URLField(
        "FurAffinity Profile", max_length=255, blank=True, null=True
    )
    flist_url = models.URLField("F-List Profile", max_length=255, blank=True, null=True)
    discord_id = models.CharField("Discord ID", max_length=50, blank=True, null=True)

    # Content
    bio = models.TextField("User Bio", blank=True, null=True)
    size_diff_image = models.ImageField(
        upload_to="profile/size_diff/", blank=True, null=True
    )

    # Roles/flags
    is_moderator = models.BooleanField(default=False)
    # is_admin = models.BooleanField(default=False) # use staff instead
    is_verified = models.BooleanField(default=False)  # Only i add this one

    # Badges! (Not really implemented yet but~)
    badges = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.username
