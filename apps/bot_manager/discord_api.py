import logging
from typing import List, Optional

import requests
from django.conf import settings
from django.core.cache import cache

from . import virtual_discord_api

logger = logging.getLogger(__name__)


def virtual_mode_enabled() -> bool:
    """Return True when the debug virtual dataset is active."""
    return virtual_discord_api.is_available()


def get_bot_guilds() -> List[dict]:
    cache_key = "fops_bot_guilds"
    cached = cache.get(cache_key)

    if cached is not None:
        logger.debug("Returning cached bot guilds")
        return cached

    if virtual_mode_enabled():
        guilds = virtual_discord_api.get_bot_guilds()
        cache.set(cache_key, guilds, 300)
        logger.info("Loaded %d virtual bot guild(s)", len(guilds))
        return guilds

    bot_token = getattr(settings, "DISCORD_BOT_TOKEN", None)
    if not bot_token:
        logger.warning("Discord bot token not configured")
        return []

    try:
        headers = {"Authorization": f"Bot {bot_token}"}
        response = requests.get(
            "https://discord.com/api/users/@me/guilds", headers=headers
        )

        logger.info(f"Bot guilds API response: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Failed to fetch bot guilds: {response.text}")
            return []

        guilds = response.json()
        logger.info(f"Fops Bot is in {len(guilds)} guilds")

        cache.set(cache_key, guilds, 300)
        return guilds
    except Exception as e:
        logger.error(f"Exception fetching bot guilds: {e}")
        return []


def get_user_guilds(user) -> Optional[List[dict]]:
    cache_key = f"user_{user.id}_discord_guilds"
    cached = cache.get(cache_key)
    if cached is not None:
        logger.info(f"Using cached guilds for user {user.id}")
        return cached

    if virtual_mode_enabled():
        guilds = virtual_discord_api.get_user_guilds(user)
        cache.set(cache_key, guilds, 300)
        logger.info(
            "Returning %d virtual guild(s) for user %s in debug mode",
            len(guilds),
            user.id,
        )
        return guilds

    logger.info(f"Fetching guilds for user {user.id} from Discord API")

    access_token = user.get_discord_access_token()
    if not access_token:
        logger.warning(f"User {user.id} has no access token")
        return None

    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            "https://discord.com/api/users/@me/guilds", headers=headers
        )

        logger.info(f"User {user.id} guilds API response: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"User {user.id} guilds API failed: {response.text}")
            return None

        guilds = response.json()
        logger.info(f"User {user.id} is in {len(guilds)} guilds")

        cache.set(cache_key, guilds, 300)
        return guilds
    except Exception as e:
        logger.error(f"Exception fetching user {user.id} guilds: {e}")
        return None


def get_guild_channels(guild_id) -> List[dict]:
    cache_key = f"guild_{guild_id}_channels"
    cached = cache.get(cache_key)
    if cached is not None:
        logger.info(f"Using cached channels for guild {guild_id}")
        return cached

    if virtual_mode_enabled():
        channels = virtual_discord_api.get_guild_channels(guild_id)
        text_channels = sorted(
            [c for c in channels if c.get("type") in [0, 5]],
            key=lambda x: x.get("position", 0),
        )
        cache.set(cache_key, text_channels, 300)
        logger.info(
            "Loaded %d virtual text channels for guild %s in debug mode",
            len(text_channels),
            guild_id,
        )
        return text_channels

    logger.info(f"Fetching channels for guild {guild_id} from Discord API")

    bot_token = getattr(settings, "DISCORD_BOT_TOKEN", None)
    if not bot_token:
        logger.warning("Discord bot token not configured")
        return []

    try:
        headers = {"Authorization": f"Bot {bot_token}"}
        response = requests.get(
            f"https://discord.com/api/guilds/{guild_id}/channels", headers=headers
        )

        logger.info(f"Guild {guild_id} channels API response: {response.status_code}")
        if response.status_code != 200:
            logger.error(
                f"Failed to fetch channels for guild {guild_id}: {response.text}"
            )
            return []

        channels = response.json()
        text_channels = sorted(
            [c for c in channels if c["type"] in [0, 5]],
            key=lambda x: x.get("position", 0),
        )
        logger.info(f"Guild {guild_id} has {len(text_channels)} text channels")

        cache.set(cache_key, text_channels, 300)
        return text_channels
    except Exception as e:
        logger.error(f"Exception fetching channels for guild {guild_id}: {e}")
        return []


def get_user_info(user_id) -> Optional[dict]:
    cache_key = f"discord_user_{user_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    if virtual_mode_enabled():
        user_info = virtual_discord_api.get_user_info(user_id)
        if user_info:
            cache.set(cache_key, user_info, 600)
        return user_info

    bot_token = getattr(settings, "DISCORD_BOT_TOKEN", None)
    if not bot_token:
        return None

    try:
        headers = {"Authorization": f"Bot {bot_token}"}
        response = requests.get(
            f"https://discord.com/api/users/{user_id}", headers=headers
        )

        if response.status_code != 200:
            logger.error(f"Failed to fetch user {user_id}: {response.text}")
            return None

        user_data = response.json()
        user_info = {
            "username": user_data.get("username"),
            "avatar": user_data.get("avatar"),
            "id": str(user_id),
        }

        cache.set(cache_key, user_info, 600)
        return user_info
    except Exception as e:
        logger.error(f"Exception fetching user {user_id}: {e}")
        return None


def get_guild_members(guild_id, max_members=5000) -> List[dict]:
    cache_key = f"guild_{guild_id}_members"
    cached = cache.get(cache_key)
    if cached is not None:
        logger.info(f"Using cached members for guild {guild_id}")
        return cached

    if virtual_mode_enabled():
        members = virtual_discord_api.get_guild_members(
            guild_id, max_members=max_members
        )
        cache.set(cache_key, members, 300)
        logger.info(
            "Loaded %d virtual members for guild %s in debug mode",
            len(members),
            guild_id,
        )
        return members

    bot_token = getattr(settings, "DISCORD_BOT_TOKEN", None)
    if not bot_token:
        logger.warning("Discord bot token not configured")
        return []

    headers = {"Authorization": f"Bot {bot_token}"}
    members: List[dict] = []
    after = 0

    try:
        while True:
            params = {"limit": 1000}
            if after:
                params["after"] = after
            response = requests.get(
                f"https://discord.com/api/guilds/{guild_id}/members",
                headers=headers,
                params=params,
            )
            logger.info(
                f"Guild {guild_id} members API response: {response.status_code} (after={after})"
            )
            if response.status_code != 200:
                logger.error(
                    f"Failed to fetch members for guild {guild_id}: {response.text}"
                )
                break

            batch = response.json()
            if not isinstance(batch, list):
                break
            members.extend(batch)

            if len(batch) < 1000 or len(members) >= max_members:
                break
            after = int(batch[-1]["user"]["id"])

        cache.set(cache_key, members, 300)
    except Exception as e:
        logger.error(f"Exception fetching members for guild {guild_id}: {e}")
        return []

    return members
