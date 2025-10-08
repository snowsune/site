import requests
from django.conf import settings
from django.core.cache import cache
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor


@contextmanager
def get_fops_connection():
    """Context manager for Fops database connections"""
    conn = psycopg2.connect(settings.FOPS_DATABASE, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()


def get_fops_guilds_from_discord():
    """Get Fops's guilds"""

    # Check cache first
    cached_guilds = cache.get("fops_bot_guilds")
    if cached_guilds is not None:
        return cached_guilds

    if not settings.DISCORD_CLIENT_ID or not settings.DISCORD_CLIENT_SECRET:
        return []

    try:
        bot_token = (
            settings.DISCORD_BOT_TOKEN
            if hasattr(settings, "DISCORD_BOT_TOKEN")
            else None
        )
        if not bot_token:
            return []

        headers = {"Authorization": f"Bot {bot_token}"}
        guilds_response = requests.get(
            "https://discord.com/api/users/@me/guilds", headers=headers
        )

        if guilds_response.status_code != 200:
            return []

        fops_guilds = guilds_response.json()
        # Cache for 2 minutes
        cache.set("fops_bot_guilds", fops_guilds, 120)
        return fops_guilds
    except Exception:
        return []


def has_fops_admin_access(user):
    """Check if user has admin rights in any guild where Fops Bot is present"""

    # Check cache first for admin access result
    cache_key = f"user_{user.id}_admin_access"
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    # Check if user has a Discord token stored
    if not user.discord_access_token:
        cache.set(cache_key, False, 300)  # Cache for 5 minutes
        return False

    # Try to decrypt the token
    access_token = user.get_discord_access_token()
    if not access_token:
        cache.set(cache_key, "DECRYPTION_FAILED", 60)  # Cache for 1 minute
        return "DECRYPTION_FAILED"

    try:
        # Get user's guilds from Discord
        headers = {"Authorization": f"Bearer {access_token}"}
        guilds_response = requests.get(
            "https://discord.com/api/users/@me/guilds", headers=headers
        )

        if guilds_response.status_code != 200:
            return False

        user_guilds = guilds_response.json()

        # Get Fops Bot guilds directly from Discord API
        fops_guilds = get_fops_guilds_from_discord()
        fops_guild_ids = {str(guild["id"]) for guild in fops_guilds}

        # Check if user has admin rights in any Fops guild
        for guild in user_guilds:
            guild_id = str(guild["id"])
            if guild_id in fops_guild_ids:
                permissions = int(guild.get("permissions", 0))
                is_admin = bool(permissions & 0x8)
                if is_admin:
                    cache.set(cache_key, True, 120)  # Cache successful result
                    return True

        cache.set(cache_key, False, 120)  # Cache negative result
        return False
    except Exception as e:
        return False


def get_user_fops_guilds(user):
    """Get guilds where user and Fops Bot are both present with admin status"""
    access_token = user.get_discord_access_token()
    if not access_token:
        return []

    # Check cache first (user-specific cache key)
    cache_key = f"user_{user.id}_fops_guilds"
    cached_shared_guilds = cache.get(cache_key)
    if cached_shared_guilds is not None:
        return cached_shared_guilds

    try:
        # Get user's guilds from Discord
        headers = {"Authorization": f"Bearer {access_token}"}
        guilds_response = requests.get(
            "https://discord.com/api/users/@me/guilds", headers=headers
        )

        if guilds_response.status_code != 200:
            return []

        user_guilds = guilds_response.json()

        # Get Fops Bot guilds directly from Discord API
        fops_guilds = get_fops_guilds_from_discord()
        fops_guild_ids = {str(guild["id"]) for guild in fops_guilds}

        shared_guilds = []
        for guild in user_guilds:
            guild_id = str(guild["id"])
            if guild_id in fops_guild_ids:
                permissions = int(guild.get("permissions", 0))
                is_admin = bool(permissions & 0x8)

                shared_guilds.append(
                    {
                        "id": guild["id"],
                        "name": guild["name"],
                        "icon": guild.get("icon"),
                        "is_admin": is_admin,
                        "permissions": permissions,
                    }
                )

        # Cache for 2 minutes
        cache.set(cache_key, shared_guilds, 120)
        return shared_guilds
    except Exception:
        return []
