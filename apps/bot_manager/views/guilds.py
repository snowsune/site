import requests
import logging
import time
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

    # Handle settings update
    if request.method == "POST" and "update_settings" in request.POST:
        try:
            with get_fops_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE guilds 
                        SET frozen = %s, allow_nsfw = %s, enable_dlp = %s
                        WHERE guild_id = %s
                        """,
                        (
                            request.POST.get("frozen") == "on",
                            request.POST.get("allow_nsfw") == "on",
                            request.POST.get("enable_dlp") == "on",
                            guild_id,
                        ),
                    )
                    conn.commit()
                    messages.success(request, "Guild settings updated successfully!")
                    return redirect("bot_manager_guild", guild_id=guild_id)
        except Exception as e:
            messages.error(request, f"Error updating settings: {str(e)}")

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

        # Create channel ID to name mapping and enrich subscriptions with channel names
        channel_map = {str(channel["id"]): channel["name"] for channel in channels}

        # Get unique user IDs from subscriptions
        user_ids = set(str(sub["user_id"]) for sub in guild_subscriptions)

        # Fetch user info from Discord API
        # I think we wont get rate limited :O --vixi
        user_map = {}
        for user_id in user_ids:
            try:
                user_response = requests.get(
                    f"https://discord.com/api/users/{user_id}", headers=headers
                )
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    user_map[user_id] = {
                        "username": user_data.get("username"),
                        "avatar": user_data.get("avatar"),
                        "id": user_id,
                    }
            except Exception:
                pass

        # Add channel names and calculate last_ran time to subscriptions
        current_time = int(time.time())
        for sub in guild_subscriptions:
            sub["channel_name"] = channel_map.get(str(sub["channel_id"]), None)
            sub["user_info"] = user_map.get(str(sub["user_id"]), None)

            # Really qucik and dirty calculate time since last_ran
            if sub.get("last_ran"):
                seconds_ago = current_time - int(sub["last_ran"])
                if seconds_ago < 60:
                    sub["last_ran_ago"] = f"{seconds_ago} seconds ago"
                elif seconds_ago < 3600:
                    minutes = seconds_ago // 60
                    sub["last_ran_ago"] = (
                        f"{minutes} minute{'s' if minutes != 1 else ''} ago"
                    )
                elif seconds_ago < 86400:
                    hours = seconds_ago // 3600
                    sub["last_ran_ago"] = f"{hours} hour{'s' if hours != 1 else ''} ago"
                else:
                    days = seconds_ago // 86400
                    sub["last_ran_ago"] = f"{days} day{'s' if days != 1 else ''} ago"
            else:
                sub["last_ran_ago"] = None

        context = {
            "guild": guild_data,
            "guild_id": guild_id,
            "channels": channels,
            "subscriptions": guild_subscriptions,
            "channel_map": channel_map,
        }
        return render(request, "bot_manager/guild_detail.html", context)
    except Exception as e:
        messages.error(request, f"Error loading guild data: {str(e)}")
        return redirect("bot_manager_dashboard")
