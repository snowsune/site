from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import json

from ..models import Subscription
from ..utils import (
    has_guild_admin_access,
    get_user_fops_guilds,
    get_fops_connection,
    convert_subscription_timestamps,
)
from .. import discord_api


def _clean_thread_id(guild_id, channel_id, thread_id, current=None):
    """
    Return the thread_id to save (or None), making sure it belongs to channel_id.
    Fops refuses to post when a thread's parent doesn't match the channel.
    """
    targets = discord_api.get_guild_subscription_targets(guild_id)
    channel = next((c for c in targets if c["id"] == str(channel_id)), None)

    if not thread_id:
        if channel and channel["is_forum"]:
            raise ValueError("Forum channels need a post selected to post into")
        return None

    if channel and any(t["id"] == str(thread_id) for t in channel["threads"]):
        return int(thread_id)

    # Archived threads drop out of the active list, so allow keeping the saved one
    if current and (str(current.get("channel_id")), str(current.get("thread_id"))) == (
        str(channel_id),
        str(thread_id),
    ):
        return int(thread_id)

    raise ValueError("That thread doesn't belong to the selected channel")


@login_required
def add_subscription(request, guild_id=None):
    """Add a new subscription"""

    # Check Discord token on GET, guild-specific admin on POST
    if not request.user.discord_access_token:
        messages.error(request, "You must connect your Discord account first.")
        return redirect("bot_manager_dashboard")

    if request.method == "POST":
        try:
            guild_id = request.POST.get("guild_id")

            # Check admin access for the specific guild
            admin_access = has_guild_admin_access(request.user, guild_id)
            if admin_access == "DECRYPTION_FAILED":
                messages.error(
                    request,
                    "Your Discord authentication has expired. Please log in again.",
                )
                return redirect("bot_manager_dashboard")
            elif not admin_access:
                messages.error(
                    request,
                    "You must have admin rights in this server to add subscriptions.",
                )
                return redirect("bot_manager_dashboard")

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
                thread_id=_clean_thread_id(
                    guild_id,
                    request.POST.get("channel_id"),
                    request.POST.get("thread_id"),
                ),
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

    # Get channels (with their active threads) for every guild the user admins
    admin_guilds = [
        guild for guild in get_user_fops_guilds(request.user) if guild["is_admin"]
    ]

    context = {
        "service_choices": Subscription.SERVICE_CHOICES,
        "shared_guilds": admin_guilds,
        "guild_targets": {
            str(guild["id"]): discord_api.get_guild_subscription_targets(guild["id"])
            for guild in admin_guilds
        },
        "preselected_guild_id": guild_id,  # Pass the guild_id to pre-select
    }
    response = render(request, "bot_manager/add_subscription.html", context)
    response["Vary"] = "Cookie"
    return response


@login_required
def edit_subscription(request, subscription_id):
    """Edit an existing subscription"""
    if not request.user.discord_access_token:
        messages.error(request, "You must connect your Discord account first.")
        return redirect("bot_manager_dashboard")

    # Get subscription from database
    with get_fops_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM subscriptions WHERE id = %s", (subscription_id,))
            subscription_data = cur.fetchone()
            if not subscription_data:
                messages.error(request, "Subscription not found")
                return redirect("bot_manager_dashboard")

    # Check admin access for the subscription's guild
    guild_id = str(subscription_data["guild_id"])
    admin_access = has_guild_admin_access(request.user, guild_id)
    if admin_access == "DECRYPTION_FAILED":
        messages.error(
            request, "Your Discord authentication has expired. Please log in again."
        )
        return redirect("bot_manager_dashboard")
    elif not admin_access:
        messages.error(
            request, "You must have admin rights in this server to edit subscriptions."
        )
        return redirect("bot_manager_dashboard")

    if request.method == "POST":
        try:
            # Guild cannot be changed in edit mode - use the original guild_id
            thread_id = _clean_thread_id(
                guild_id,
                request.POST.get("channel_id"),
                request.POST.get("thread_id"),
                current=subscription_data,
            )
            # Update subscription in database
            with get_fops_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE subscriptions 
                        SET service_type = %s, 
                            channel_id = %s, thread_id = %s, search_criteria = %s, 
                            filters = %s, is_pm = %s
                        WHERE id = %s
                        """,
                        (
                            request.POST.get("service_type"),
                            request.POST.get("channel_id"),
                            thread_id,
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

    # Convert timestamp fields to datetime objects for template filters
    subscription_dict = convert_subscription_timestamps(subscription_data)

    context = {
        "subscription": subscription_dict,
        "service_choices": Subscription.SERVICE_CHOICES,
        "shared_guilds": get_user_fops_guilds(request.user),
        "guild_targets": {
            guild_id: discord_api.get_guild_subscription_targets(guild_id)
        },
    }
    response = render(request, "bot_manager/edit_subscription.html", context)
    response["Vary"] = "Cookie"
    return response


@login_required
def delete_subscription(request, subscription_id):
    """Delete a subscription"""
    if not request.user.discord_access_token:
        messages.error(request, "You must connect your Discord account first.")
        return redirect("bot_manager_dashboard")

    if request.method == "POST":
        try:
            # Get the guild_id and check admin access before deleting
            with get_fops_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT guild_id FROM subscriptions WHERE id = %s",
                        (subscription_id,),
                    )
                    result = cur.fetchone()
                    if not result:
                        messages.error(request, "Subscription not found")
                        return redirect("bot_manager_dashboard")

                    guild_id = result["guild_id"]

                    # Check admin access for this guild
                    admin_access = has_guild_admin_access(request.user, str(guild_id))
                    if admin_access == "DECRYPTION_FAILED":
                        messages.error(
                            request,
                            "Your Discord authentication has expired. Please log in again.",
                        )
                        return redirect("bot_manager_dashboard")
                    elif not admin_access:
                        messages.error(
                            request,
                            "You must have admin rights in this server to delete subscriptions.",
                        )
                        return redirect("bot_manager_dashboard")

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
