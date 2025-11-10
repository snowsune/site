import logging
from django.conf import settings
from contextlib import contextmanager
from datetime import datetime
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


def has_guild_admin_access(user, guild_id):
    """
    Check if a user has admin rights in a guild
    """

    virtual_mode = discord_api.virtual_mode_enabled()

    # Check if user has a Discord token stored
    if not user.discord_access_token and not virtual_mode:
        logger.warning(f"User {user.id} has no Discord token stored")
        return False

    if user.discord_access_token and not virtual_mode:
        # Try to decrypt the token
        if not user.get_discord_access_token():
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

    # First check if the guild is even a Fops guild
    if str(guild_id) not in fops_guild_ids:
        logger.warning(f"Guild {guild_id} is not a Fops guild")
        return False

    # Check if user has admin rights in THIS specific guild
    for guild in user_guilds:
        if str(guild["id"]) == str(guild_id):
            permissions = int(guild.get("permissions", 0))
            is_admin = bool(permissions & 0x8)
            logger.info(f"User {user.id} in guild {guild_id} - Admin: {is_admin}")
            return is_admin

    # User is not in this guild at all
    logger.warning(f"User {user.id} is not a member of guild {guild_id}")
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


def convert_subscription_timestamps(subscription_data):
    """
    Convert subscription timestamp fields to datetime objects for templating in django.
    I could have done this by just pre-rendering the text but django already has
    shortand for time since, it just takes a timezone input so. Converting the fops
    epoch-timezone became something i wanted to do more often.

    Args:
        subscription_data: Dict-like object containing subscription data

    Returns:
        Dict with timestamp fields converted to datetime objects
    """
    subscription_dict = dict(subscription_data)

    # Convert Unix timestamps to datetime objects
    timestamp_fields = ["last_ran", "subscribed_at"]
    for field in timestamp_fields:
        if subscription_dict.get(field) and isinstance(
            subscription_dict[field], (int, float)
        ):
            subscription_dict[field] = datetime.fromtimestamp(subscription_dict[field])

    return subscription_dict
