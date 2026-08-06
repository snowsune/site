"""
Talks to discord with the fops/site token
"""

import logging
import time
from urllib.parse import quote

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

API = "https://discord.com/api/v10"

# Left = contestant A, Right = contestant B
LEFT_EMOJI = "◀"
RIGHT_EMOJI = "▶"

MAX_RETRIES = 5


def _headers():
    token = getattr(settings, "DISCORD_BOT_TOKEN", None)
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN is not set")
    return {"Authorization": f"Bot {token}"}


def _request(method, url, **kwargs):
    """
    Discord API call that backs off on 429s using retry_after.
    """
    timeout = kwargs.pop("timeout", 30)
    for attempt in range(1, MAX_RETRIES + 1):
        resp = requests.request(
            method, url, headers=_headers(), timeout=timeout, **kwargs
        )
        if resp.status_code != 429:
            return resp

        try:
            payload = resp.json()
            wait = float(payload.get("retry_after", 1))
        except Exception:
            wait = float(resp.headers.get("Retry-After", 1))

        # Tiny cushion so we don't bounce off the same window
        wait = max(wait, 0.2) + 0.15
        logger.warning(
            "Discord 429 on %s %s (attempt %s/%s), sleeping %.2fs",
            method,
            url,
            attempt,
            MAX_RETRIES,
            wait,
        )
        time.sleep(wait)

    return resp


def post_matchup(channel_id, content, image_bytes, filename="matchup.png"):
    """
    Post the VS card to a channel.
    Returns the message id (str).
    """
    files = {"files[0]": (filename, image_bytes, "image/png")}
    data = {"content": content}
    resp = _request(
        "POST",
        f"{API}/channels/{channel_id}/messages",
        data=data,
        files=files,
        timeout=30,
    )
    if resp.status_code >= 400:
        logger.error("Discord post failed (%s): %s", resp.status_code, resp.text)
        resp.raise_for_status()
    return str(resp.json()["id"])


def add_reaction(channel_id, message_id, emoji):
    """Add a reaction as the bot (retries on rate limit)."""
    encoded = quote(emoji)
    resp = _request(
        "PUT",
        f"{API}/channels/{channel_id}/messages/{message_id}/reactions/{encoded}/@me",
        timeout=15,
    )
    if resp.status_code >= 400:
        logger.error(
            "Discord react failed (%s) emoji=%s: %s",
            resp.status_code,
            emoji,
            resp.text,
        )
        resp.raise_for_status()


def count_reactions(channel_id, message_id, emoji):
    """
    How many people reacted with this emoji (excluding the bot itself).
    Discord caps this endpoint at 100 users; fine for our scale.
    """
    encoded = quote(emoji)
    resp = _request(
        "GET",
        f"{API}/channels/{channel_id}/messages/{message_id}/reactions/{encoded}",
        params={"limit": 100},
        timeout=15,
    )
    if resp.status_code >= 400:
        logger.error(
            "Discord reaction fetch failed (%s): %s", resp.status_code, resp.text
        )
        resp.raise_for_status()

    users = resp.json()
    bot_id = _bot_user_id()
    return sum(1 for u in users if str(u.get("id")) != bot_id)


def post_text(channel_id, content):
    """Simple text follow-up (results announcement etc)."""
    resp = _request(
        "POST",
        f"{API}/channels/{channel_id}/messages",
        json={"content": content},
        timeout=15,
    )
    if resp.status_code >= 400:
        logger.error("Discord text post failed (%s): %s", resp.status_code, resp.text)
        resp.raise_for_status()
    return str(resp.json()["id"])


_cached_bot_id = None


def _bot_user_id():
    global _cached_bot_id
    if _cached_bot_id:
        return _cached_bot_id
    resp = _request("GET", f"{API}/users/@me", timeout=10)
    resp.raise_for_status()
    _cached_bot_id = str(resp.json()["id"])
    return _cached_bot_id
