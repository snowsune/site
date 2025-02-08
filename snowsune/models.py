from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    profile_picture = models.ImageField(
        upload_to="profile_pics/", blank=True, null=True
    )
    fa_url = models.URLField(
        "FurAffinity Profile", max_length=255, blank=True, null=True
    )
    flist_url = models.URLField("F-List Profile", max_length=255, blank=True, null=True)
    bio = models.TextField("User Bio", blank=True, null=True)
    # Optional: Add more fields as needed, e.g., roles
    is_moderator = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
