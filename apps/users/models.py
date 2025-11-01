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

    def get_discord_access_token(self, auto_refresh=True):
        """
        Get decrypted Discord access token.

        Args:
            auto_refresh: If this is true, we'll also do the auro-refresh thing

        Returns:
            Decrypted access token or None
        """
        if not self.discord_access_token:
            return None

        # Check if token is expired and refresh if needed
        if auto_refresh and self.is_discord_token_expired():
            if self.refresh_discord_token():
                # Token refreshed successfully, continue with new token
                pass
            else:
                # Refresh failed, return None
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

    def is_discord_token_expired(self):
        """Check if Discord access token is expired or about to expire"""
        if not self.discord_token_expires:
            return True  # No expiry set, assume expired

        from django.utils import timezone
        from datetime import timedelta

        # Consider expired if less than 5 minutes remaining
        buffer = timedelta(minutes=5)
        return timezone.now() >= (self.discord_token_expires - buffer)

    def refresh_discord_token(self):
        """
        Refresh Discord access token using refresh token.

        Returns:
            True if refresh successful, False otherwise
        """
        import requests
        import logging
        from django.conf import settings
        from django.utils import timezone
        from datetime import timedelta

        logger = logging.getLogger(__name__)

        refresh_token = self.get_discord_refresh_token()
        if not refresh_token:
            logger.warning(f"User {self.id} has no refresh token")
            return False

        try:
            # Exchange refresh token for new access token
            data = {
                "client_id": settings.DISCORD_CLIENT_ID,
                "client_secret": settings.DISCORD_CLIENT_SECRET,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            }

            response = requests.post(
                "https://discord.com/api/oauth2/token",
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                logger.error(
                    f"Failed to refresh token for user {self.id}: {response.status_code} - {response.text}"
                )
                return False

            token_data = response.json()

            # Update tokens
            self.set_discord_access_token(token_data["access_token"])
            self.set_discord_refresh_token(token_data["refresh_token"])
            self.discord_token_expires = timezone.now() + timedelta(
                seconds=token_data["expires_in"]
            )
            self.save()

            logger.info(f"Successfully refreshed Discord token for user {self.id}")
            return True

        except Exception as e:
            logger.error(f"Exception refreshing token for user {self.id}: {e}")
            return False

    # Content
    bio = models.TextField("User Bio", blank=True, null=True)
    size_diff_image = models.ImageField(
        upload_to="profile/size_diff/", blank=True, null=True
    )

    # Roles/flags
    is_verified = models.BooleanField(default=False)  # Only i add this one

    # Badges! (Not really implemented yet but~)
    badges = models.JSONField(default=list, blank=True)

    # Email verification
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=64, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(blank=True, null=True)

    def get_profile_picture_url(self):
        """
        Just because some ppl dont set theirs and I always wanna draw something valid
        for their PFP (even if its just a placeholder).
        """

        try:
            if self.profile_picture and self.profile_picture.name:
                return self.profile_picture.url
        except (ValueError, AttributeError):
            pass
        return None

    def __str__(self):
        return self.username
