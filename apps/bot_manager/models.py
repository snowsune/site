from django.db import models
from django.conf import settings
import psycopg2
from psycopg2.extras import RealDictCursor


class FopsDatabase:
    @staticmethod
    def get_connection():
        return psycopg2.connect(settings.FOPS_DATABASE, cursor_factory=RealDictCursor)


class Guild(models.Model):
    # Local Django model for display purposes
    guild_id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    joined_at = models.DateTimeField()

    class Meta:
        managed = False  # Don't create tables for this model

    @classmethod
    def get_from_fops(cls):
        """Fetch guilds from Fops database"""
        conn = FopsDatabase.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM guilds")
                return cur.fetchall()
        finally:
            conn.close()

    @classmethod
    def get_tables(cls):
        """Get list of tables in Fops database"""
        conn = FopsDatabase.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """
                )
                return [row["table_name"] for row in cur.fetchall()]
        finally:
            conn.close()
