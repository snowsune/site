import json
import logging
import time
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .. import discord_api, virtual_discord_api
from ..models import Subscription
from ..utils import get_fops_connection, has_guild_admin_access


@login_required
def guild_detail(request, guild_id):
    """
    Display guild configuration page - ADMIN ONLY for THIS specific guild
    """

    # Check if user has admin access to THIS SPECIFIC guild
    admin_access = has_guild_admin_access(request.user, guild_id)

    if admin_access == "DECRYPTION_FAILED":
        messages.error(
            request, "Your Discord authentication has expired. Please log in again."
        )
        return redirect("bot_manager_dashboard")

    elif not admin_access:
        messages.error(
            request, "You must have admin rights in this server to configure it."
        )
        return redirect("bot_manager_dashboard")

    # Handle settings update
    if request.method == "POST" and "update_settings" in request.POST:
        try:
            with get_fops_connection() as conn:
                with conn.cursor() as cur:
                    admin_channel = request.POST.get("admin_channel_id")
                    twitter_wrapper = request.POST.get("twitter_wrapper", "")
                    twitter_wrapper = (
                        twitter_wrapper.strip() if twitter_wrapper else None
                    )

                    cur.execute(
                        """
                        UPDATE guilds 
                        SET frozen = %s,
                            allow_nsfw = %s,
                            enable_dlp = %s,
                            twitter_obfuscate = %s,
                            twitter_wrapper = %s,
                            admin_channel_id = %s
                        WHERE guild_id = %s
                        """,
                        (
                            request.POST.get("frozen") == "on",
                            request.POST.get("allow_nsfw") == "on",
                            request.POST.get("enable_dlp") == "on",
                            request.POST.get("twitter_obfuscate") == "on",
                            twitter_wrapper,
                            admin_channel if admin_channel else None,
                            guild_id,
                        ),
                    )
                    conn.commit()
                    messages.success(request, "Guild settings updated successfully!")
                    return redirect("bot_manager_guild", guild_id=guild_id)
        except Exception as e:
            messages.error(request, f"Error updating settings: {str(e)}")

    try:
        # Get guild data (virtual or real database)
        if virtual_discord_api.is_available():
            guild_data = virtual_discord_api.get_fops_guild(guild_id)
            if not guild_data:
                messages.error(request, "Guild not found in virtual dataset")
                return redirect("bot_manager_dashboard")
        else:
            with get_fops_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM guilds WHERE guild_id = %s", (guild_id,))
                    guild_data = cur.fetchone()

                    if not guild_data:
                        messages.error(request, "Guild not found in Fops database")
                        return redirect("bot_manager_dashboard")

        # Prepare recent logs (if available)
        recent_logs = []
        raw_logs = guild_data.get("recent_logs")
        if isinstance(raw_logs, str):
            try:
                raw_logs = json.loads(raw_logs)
            except json.JSONDecodeError:
                raw_logs = []
        if isinstance(raw_logs, list):
            for entry in raw_logs:
                if not isinstance(entry, dict):
                    continue
                level = str(entry.get("level", "INFO") or "INFO").upper()
                message = entry.get("message") or ""
                ts_raw = entry.get("ts") or entry.get("timestamp")
                timestamp = None
                sort_key = 0.0
                if ts_raw:
                    try:
                        timestamp = datetime.fromisoformat(
                            str(ts_raw).replace("Z", "+00:00")
                        )
                        sort_key = timestamp.timestamp()
                    except ValueError:
                        timestamp = None
                recent_logs.append(
                    {
                        "timestamp": timestamp,
                        "ts": ts_raw,
                        "level": level,
                        "level_lower": level.lower(),
                        "message": message,
                        "sort_key": sort_key,
                    }
                )
            recent_logs.sort(key=lambda log: log["sort_key"], reverse=True)
            for entry in recent_logs:
                entry.pop("sort_key", None)

        # Get channels from Discord API (cached or virtual)
        channels = discord_api.get_guild_channels(guild_id)

        # Get guild-specific subscriptions (virtual module handles debug mode)
        guild_subscriptions = Subscription.get_by_guild(guild_id)

        # Create channel ID to name mapping and enrich subscriptions with channel names
        channel_map = {str(channel["id"]): channel["name"] for channel in channels}

        # Get unique user IDs from subscriptions and fetch user info
        user_ids = set(str(sub["user_id"]) for sub in guild_subscriptions)
        user_map = {}
        for user_id in user_ids:
            user_info = discord_api.get_user_info(user_id)
            if user_info:
                user_map[user_id] = user_info

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
            "recent_logs": recent_logs,
        }
        response = render(request, "bot_manager/guild_detail.html", context)
        response["Vary"] = "Cookie"
        return response
    except Exception as e:
        messages.error(request, f"Error loading guild data: {str(e)}")
        return redirect("bot_manager_dashboard")
