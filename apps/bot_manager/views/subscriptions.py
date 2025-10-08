from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

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
            subscription = Subscription(
                service_type=request.POST.get("service_type"),
                user_id=request.POST.get("user_id"),
                guild_id=request.POST.get("guild_id"),
                channel_id=request.POST.get("channel_id"),
                search_criteria=request.POST.get("search_criteria"),
                filters=request.POST.get("filters", ""),
                is_pm=request.POST.get("is_pm") == "on",
            )
            subscription.clean()  # Validate
            subscription.save_to_fops()
            messages.success(request, "Subscription added successfully!")
            return redirect("bot_manager_dashboard")
        except Exception as e:
            messages.error(request, f"Error adding subscription: {str(e)}")

    context = {
        "service_choices": Subscription.SERVICE_CHOICES,
        "shared_guilds": get_user_fops_guilds(request.user),
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
            # Update subscription in database
            with get_fops_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE subscriptions 
                        SET service_type = %s, user_id = %s, guild_id = %s, 
                            channel_id = %s, search_criteria = %s, 
                            filters = %s, is_pm = %s
                        WHERE id = %s
                        """,
                        (
                            request.POST.get("service_type"),
                            request.POST.get("user_id"),
                            request.POST.get("guild_id"),
                            request.POST.get("channel_id"),
                            request.POST.get("search_criteria"),
                            request.POST.get("filters", ""),
                            request.POST.get("is_pm") == "on",
                            subscription_id,
                        ),
                    )
                    conn.commit()
                    messages.success(request, "Subscription updated successfully!")
                    return redirect("bot_manager_dashboard")
        except Exception as e:
            messages.error(request, f"Error updating subscription: {str(e)}")

    context = {
        "subscription": subscription_data,
        "service_choices": Subscription.SERVICE_CHOICES,
        "shared_guilds": get_user_fops_guilds(request.user),
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
            with get_fops_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM subscriptions WHERE id = %s", (subscription_id,)
                    )
                    conn.commit()
                    messages.success(request, "Subscription deleted successfully!")
        except Exception as e:
            messages.error(request, f"Error deleting subscription: {str(e)}")

    return redirect("bot_manager_dashboard")
