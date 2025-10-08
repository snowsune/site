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

    # Discord
    discord_id = models.CharField("Discord ID", max_length=50, blank=True, null=True)
    discord_username = models.CharField(
        "Discord Username", max_length=100, blank=True, null=True
    )
    discord_access_token = models.TextField(
        "Discord Access Token", blank=True, null=True
    )
    discord_refresh_token = models.TextField(
        "Discord Refresh Token", blank=True, null=True
    )
    discord_token_expires = models.DateTimeField(
        "Discord Token Expires", blank=True, null=True
    )

    def get_discord_access_token(self):
        """Get decrypted Discord access token with caching"""
        if not self.discord_access_token:
            return None

        # Check cache first to avoid repeated decryption
        cache_key = f"user_{self.id}_discord_access_token"
        from django.core.cache import cache

        cached_token = cache.get(cache_key)
        if cached_token:
            return cached_token

        from snowsune.encryption import decrypt_token

        decrypted = decrypt_token(self.discord_access_token)
        if decrypted:
            # Cache for 1 minute
            cache.set(cache_key, decrypted, 60)
            return decrypted
        else:
            # Token decryption failed
            return None

    def set_discord_access_token(self, token):
        """Set encrypted Discord access token"""
        from snowsune.encryption import encrypt_token
        from django.core.cache import cache

        self.discord_access_token = encrypt_token(token)
        # Clear cached token when setting new one
        cache_key = f"user_{self.id}_discord_access_token"
        cache.delete(cache_key)

    def get_discord_refresh_token(self):
        """Get decrypted Discord refresh token"""
        from snowsune.encryption import decrypt_token

        return decrypt_token(self.discord_refresh_token)

    def set_discord_refresh_token(self, token):
        """Set encrypted Discord refresh token"""
        from snowsune.encryption import encrypt_token

        self.discord_refresh_token = encrypt_token(token)

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
