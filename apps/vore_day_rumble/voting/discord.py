"""
Talks to Discord with the site bot token.

Posts matchup cards, results, and winner announcements.
Voting itself happens on snowsune.net now.
"""

import logging
import time

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

API = "https://discord.com/api/v10"
MAX_RETRIES = 5


def _headers():
    token = getattr(settings, "DISCORD_BOT_TOKEN", None)
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN is not set")
    return {"Authorization": f"Bot {token}"}


def _request(method, url, **kwargs):
    """Discord API call that backs off on 429s using retry_after."""
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
    """Post an image + caption. Returns message id (str)."""
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
        hint = ""
        try:
            code = resp.json().get("code")
            if code == 50001:
                hint = (
                    " (bot can't see this channel - wrong channel id, bot not in the "
                    "server, or missing View Channel / Send Messages / Attach Files)"
                )
            elif code == 50013:
                hint = " (bot lacks permission in this channel)"
        except Exception:
            pass
        logger.error(
            "Discord post failed (%s)%s: %s", resp.status_code, hint, resp.text
        )
        resp.raise_for_status()
    return str(resp.json()["id"])


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
