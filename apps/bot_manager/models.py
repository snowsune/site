from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

from . import virtual_discord_api
from .utils import get_fops_connection


class FopsDatabase:
    @staticmethod
    def get_tables():
        """Get list of tables in Fops database"""
        with get_fops_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """
                )
                return [row["table_name"] for row in cur.fetchall()]


class Subscription(models.Model):
    SERVICE_CHOICES = [
        ("BixiBooru", "BixiBooru"),
        ("FurAffinity", "FurAffinity"),
        ("e621", "e621"),
    ]

    # Editable fields
    service_type = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    user_id = models.BigIntegerField()
    guild_id = models.BigIntegerField()
    channel_id = models.BigIntegerField()
    search_criteria = models.CharField(max_length=255)
    filters = models.TextField(blank=True, null=True)
    is_pm = models.BooleanField(default=False)

    # Read-only fields (managed by bot)
    id = models.AutoField(primary_key=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    last_reported_id = models.BigIntegerField(default=0)
    last_ran = models.BigIntegerField(default=0)

    class Meta:
        managed = False  # Don't create Django tables, use existing Fops DB
        db_table = "subscriptions"

    def clean(self):
        """Validate subscription data"""
        if not self.search_criteria.strip():
            raise ValidationError("Search criteria cannot be empty")

        if len(self.search_criteria) > 255:
            raise ValidationError("Search criteria too long (max 255 characters)")

    def __str__(self):
        return f"{self.service_type} subscription for {self.search_criteria} in guild {self.guild_id}"

    @classmethod
    def get_all(cls):
        """Get all subscriptions from Fops database"""
        if virtual_discord_api.is_available():
            return virtual_discord_api.get_all_fops_subscriptions()

        with get_fops_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM subscriptions ORDER BY subscribed_at DESC")
                return cur.fetchall()

    @classmethod
    def get_by_guild(cls, guild_id):
        """Get subscriptions for a specific guild"""
        if virtual_discord_api.is_available():
            return virtual_discord_api.get_fops_subscriptions(guild_id)

        with get_fops_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM subscriptions WHERE guild_id = %s ORDER BY subscribed_at DESC",
                    (guild_id,),
                )
                return cur.fetchall()

    def save_to_fops(self):
        """Save subscription to Fops database"""
        from .utils import get_fops_connection
        from django.utils import timezone

        with get_fops_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO subscriptions 
                    (service_type, user_id, guild_id, channel_id, search_criteria, 
                     filters, is_pm, last_reported_id, last_ran, subscribed_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        self.service_type,
                        self.user_id,
                        self.guild_id,
                        self.channel_id,
                        self.search_criteria,
                        self.filters if self.filters else None,
                        self.is_pm,
                        None,  # last_reported_id should be NULL for new subscriptions
                        None,  # last_ran should be NULL for new subscriptions
                        timezone.now(),
                    ),
                )
                conn.commit()

    def delete_from_fops(self):
        """Delete subscription from Fops database"""
        from .utils import get_fops_connection

        with get_fops_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM subscriptions WHERE id = %s", (self.id,))
                conn.commit()
