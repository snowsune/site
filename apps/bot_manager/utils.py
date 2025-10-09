import logging
from django.conf import settings
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from . import discord_api

logger = logging.getLogger(__name__)


@contextmanager
def get_fops_connection():
    """Context manager for Fops database connections"""
    conn = psycopg2.connect(settings.FOPS_DATABASE, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()


def has_fops_admin_access(user):
    """Check if user has admin rights in any guild where Fops Bot is present"""
    logger.info(f"Checking admin access for user {user.id} ({user.username})")

    # Check if user has a Discord token stored
    if not user.discord_access_token:
        logger.warning(f"User {user.id} has no Discord token stored")
        return False

    # Try to decrypt the token
    access_token = user.get_discord_access_token()
    if not access_token:
        logger.error(f"User {user.id} - token decryption failed")
        return "DECRYPTION_FAILED"

    # Get user's guilds (cached to avoid rate limiting)
    user_guilds = discord_api.get_user_guilds(user)
    if user_guilds is None:
        logger.error(f"Failed to get guilds for user {user.id}")
        return False

    # Get Fops Bot guilds directly from Discord API
    fops_guilds = discord_api.get_bot_guilds()
    fops_guild_ids = {str(guild["id"]) for guild in fops_guilds}
    logger.info(f"Comparing with {len(fops_guild_ids)} Fops guilds")

    # Check if user has admin rights in any Fops guild
    for guild in user_guilds:
        guild_id = str(guild["id"])
        if guild_id in fops_guild_ids:
            permissions = int(guild.get("permissions", 0))
            is_admin = bool(permissions & 0x8)
            logger.info(
                f"User {user.id} in shared guild {guild['name']} - Admin: {is_admin}"
            )
            if is_admin:
                logger.info(
                    f"User {user.id} has admin access via guild {guild['name']}"
                )
                return True

    logger.warning(f"User {user.id} has no admin access in any Fops guild")
    return False


def get_user_fops_guilds(user):
    """Get guilds where user and Fops Bot are both present with admin status"""
    logger.info(f"Getting shared guilds for user {user.id}")

    # Get user's guilds (cached to avoid rate limiting)
    user_guilds = discord_api.get_user_guilds(user)
    if user_guilds is None:
        logger.error(f"Failed to get guilds for user {user.id}")
        return []

    # Get Fops Bot guilds directly from Discord API
    fops_guilds = discord_api.get_bot_guilds()
    fops_guild_ids = {str(guild["id"]) for guild in fops_guilds}

    shared_guilds = []
    for guild in user_guilds:
        guild_id = str(guild["id"])
        if guild_id in fops_guild_ids:
            permissions = int(guild.get("permissions", 0))
            is_admin = bool(permissions & 0x8)
            logger.info(f"Found shared guild: {guild['name']} (Admin: {is_admin})")

            shared_guilds.append(
                {
                    "id": guild["id"],
                    "name": guild["name"],
                    "icon": guild.get("icon"),
                    "is_admin": is_admin,
                    "permissions": permissions,
                }
            )

    admin_count = sum(1 for g in shared_guilds if g["is_admin"])
    logger.info(
        f"User {user.id} shares {len(shared_guilds)} guilds with Fops (admin in {admin_count})"
    )
    return shared_guilds
