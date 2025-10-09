from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from ..models import FopsDatabase, Subscription
from ..utils import has_fops_admin_access, get_user_fops_guilds


@login_required
def dashboard(request):
    """
    Main dashboard view!

    Im prolly gonna change this a lot and not send so much stuff at once.
    """

    # Check if user has Discord connected
    if not request.user.discord_access_token:
        context = {
            "error": "You must connect your Discord account to access Fops Bot Manager",
            "show_discord_login": True,
        }
        return render(request, "bot_manager/dashboard.html", context)

    # Check if user has admin rights in any Fops guild
    admin_access = has_fops_admin_access(request.user)
    if admin_access == "DECRYPTION_FAILED":
        messages.error(
            request, "Your Discord authentication has expired. Please log in again."
        )
        context = {
            "error": "discord_auth_expired",
            "show_discord_login": True,
        }
        return render(request, "bot_manager/dashboard.html", context)
    elif not admin_access:
        context = {
            "error": "You must have admin rights in a server where Fops Bot is present to access this dashboard",
            "show_discord_login": False,
        }
        return render(request, "bot_manager/dashboard.html", context)

    try:
        shared_guilds = get_user_fops_guilds(request.user)
        guilds_error = None
    except Exception as e:
        shared_guilds = None  # None means error, [] means no guilds
        guilds_error = str(e)

    context = {
        "shared_guilds": shared_guilds,
        "guilds_error": guilds_error,
        "error": locals().get("error", None),
    }
    response = render(request, "bot_manager/dashboard.html", context)
    response["Vary"] = "Cookie"
    return response
