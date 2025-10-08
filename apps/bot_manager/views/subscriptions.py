from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
import requests

from ..models import Subscription
from ..utils import has_fops_admin_access, get_user_fops_guilds, get_fops_connection


@login_required
def add_subscription(request):
    """Add a new subscription"""
    admin_access = has_fops_admin_access(request.user)
    if admin_access == "DECRYPTION_FAILED":
        messages.error(
            request, "Your Discord authentication has expired. Please log in again."
        )
        return redirect("bot_manager_dashboard")
    elif not request.user.discord_access_token or not admin_access:
        return redirect("bot_manager_dashboard")

    if request.method == "POST":
        try:
            guild_id = request.POST.get("guild_id")

            # Use the logged-in user's Discord ID
            user_discord_id = request.user.discord_id
            if not user_discord_id:
                messages.error(
                    request,
                    "What? How! You must have a Discord account connected to add subscriptions!",
                )
                return redirect("bot_manager_dashboard")

            subscription = Subscription(
                service_type=request.POST.get("service_type"),
                user_id=user_discord_id,
                guild_id=guild_id,
                channel_id=request.POST.get("channel_id"),
                search_criteria=request.POST.get("search_criteria"),
                filters=request.POST.get("filters", ""),
                is_pm=request.POST.get("is_pm") == "on",
            )
            subscription.clean()  # Validate
            subscription.save_to_fops()
            messages.success(request, "Subscription added successfully!")
            return redirect("bot_manager_guild", guild_id=guild_id)
        except Exception as e:
            messages.error(request, f"Error adding subscription: {str(e)}")

    # Get channels for all shared guilds
    shared_guilds = get_user_fops_guilds(request.user)
    bot_token = settings.DISCORD_BOT_TOKEN
    headers = {"Authorization": f"Bot {bot_token}"}

    # Fetch channels for each guild
    guild_channels = {}
    for guild in shared_guilds:
        try:
            channels_response = requests.get(
                f"https://discord.com/api/guilds/{guild['id']}/channels",
                headers=headers,
            )
            if channels_response.status_code == 200:
                channels = channels_response.json()
                guild_channels[str(guild["id"])] = sorted(
                    [c for c in channels if c["type"] in [0, 5]],
                    key=lambda x: x.get("position", 0),
                )
        except Exception:
            guild_channels[str(guild["id"])] = []

    import json

    context = {
        "service_choices": Subscription.SERVICE_CHOICES,
        "shared_guilds": shared_guilds,
        "guild_channels": guild_channels,
        "guild_channels_json": json.dumps(guild_channels),
    }
    return render(request, "bot_manager/add_subscription.html", context)


@login_required
def edit_subscription(request, subscription_id):
    """Edit an existing subscription"""
    admin_access = has_fops_admin_access(request.user)
    if admin_access == "DECRYPTION_FAILED":
        messages.error(
            request, "Your Discord authentication has expired. Please log in again."
        )
        return redirect("bot_manager_dashboard")
    elif not request.user.discord_access_token or not admin_access:
        return redirect("bot_manager_dashboard")

    # Get subscription from database
    with get_fops_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM subscriptions WHERE id = %s", (subscription_id,))
            subscription_data = cur.fetchone()
            if not subscription_data:
                messages.error(request, "Subscription not found")
                return redirect("bot_manager_dashboard")

    if request.method == "POST":
        try:
            guild_id = request.POST.get("guild_id")
            # Update subscription in database
            with get_fops_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE subscriptions 
                        SET service_type = %s, guild_id = %s, 
                            channel_id = %s, search_criteria = %s, 
                            filters = %s, is_pm = %s
                        WHERE id = %s
                        """,
                        (
                            request.POST.get("service_type"),
                            guild_id,
                            request.POST.get("channel_id"),
                            request.POST.get("search_criteria"),
                            request.POST.get("filters", ""),
                            request.POST.get("is_pm") == "on",
                            subscription_id,
                        ),
                    )
                    conn.commit()
                    messages.success(request, "Subscription updated successfully!")
                    return redirect("bot_manager_guild", guild_id=guild_id)
        except Exception as e:
            messages.error(request, f"Error updating subscription: {str(e)}")

    # Get channels for the subscription's guild
    guild_id = str(subscription_data["guild_id"])
    bot_token = settings.DISCORD_BOT_TOKEN
    headers = {"Authorization": f"Bot {bot_token}"}

    try:
        channels_response = requests.get(
            f"https://discord.com/api/guilds/{guild_id}/channels", headers=headers
        )
        if channels_response.status_code == 200:
            channels = channels_response.json()
            guild_channels = sorted(
                [c for c in channels if c["type"] in [0, 5]],
                key=lambda x: x.get("position", 0),
            )
        else:
            guild_channels = []
    except Exception:
        guild_channels = []

    context = {
        "subscription": subscription_data,
        "service_choices": Subscription.SERVICE_CHOICES,
        "shared_guilds": get_user_fops_guilds(request.user),
        "guild_channels": guild_channels,
    }
    return render(request, "bot_manager/edit_subscription.html", context)


@login_required
def delete_subscription(request, subscription_id):
    """Delete a subscription"""
    admin_access = has_fops_admin_access(request.user)
    if admin_access == "DECRYPTION_FAILED":
        messages.error(
            request, "Your Discord authentication has expired. Please log in again."
        )
        return redirect("bot_manager_dashboard")
    elif not request.user.discord_access_token or not admin_access:
        return redirect("bot_manager_dashboard")

    if request.method == "POST":
        try:
            # Get the guild_id before deleting
            with get_fops_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT guild_id FROM subscriptions WHERE id = %s",
                        (subscription_id,),
                    )
                    result = cur.fetchone()
                    guild_id = result["guild_id"] if result else None

                    cur.execute(
                        "DELETE FROM subscriptions WHERE id = %s", (subscription_id,)
                    )
                    conn.commit()
                    messages.success(request, "Subscription deleted successfully!")

                    if guild_id:
                        return redirect("bot_manager_guild", guild_id=guild_id)
        except Exception as e:
            messages.error(request, f"Error deleting subscription: {str(e)}")

    return redirect("bot_manager_dashboard")
