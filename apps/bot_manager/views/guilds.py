import requests
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings

from ..models import Subscription
from ..utils import has_fops_admin_access, get_fops_connection


@login_required
def guild_detail(request, guild_id):
    """Display guild configuration page"""
    admin_access = has_fops_admin_access(request.user)
    if admin_access == "DECRYPTION_FAILED":
        messages.error(
            request, "Your Discord authentication has expired. Please log in again."
        )
        return redirect("bot_manager_dashboard")

    elif not request.user.discord_access_token or not admin_access:
        return redirect("bot_manager_dashboard")

    try:
        # Get guild data from Fops database
        with get_fops_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM guilds WHERE guild_id = %s", (guild_id,))
                guild_data = cur.fetchone()

                if not guild_data:
                    messages.error(request, "Guild not found in Fops database")
                    return redirect("bot_manager_dashboard")

        # Get channels from Discord API using bot token
        bot_token = settings.DISCORD_BOT_TOKEN
        headers = {"Authorization": f"Bot {bot_token}"}
        channels_response = requests.get(
            f"https://discord.com/api/guilds/{guild_id}/channels", headers=headers
        )

        if channels_response.status_code == 200:
            channels = channels_response.json()
            # Sort by position and filter text channels
            channels = sorted(
                [
                    c for c in channels if c["type"] in [0, 5]
                ],  # Text and announcement channels
                key=lambda x: x.get("position", 0),
            )
        else:
            logging.error(
                f"Failed to get channels for guild {guild_id}. Status code: {channels_response.status_code}"
            )
            channels = []

        # Get guild-specific subscriptions
        guild_subscriptions = Subscription.get_by_guild(guild_id)

        context = {
            "guild": guild_data,
            "guild_id": guild_id,
            "channels": channels,
            "subscriptions": guild_subscriptions,
        }
        return render(request, "bot_manager/guild_detail.html", context)
    except Exception as e:
        messages.error(request, f"Error loading guild data: {str(e)}")
        return redirect("bot_manager_dashboard")
