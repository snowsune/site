from django.shortcuts import render
from django.contrib import messages

from ..models import FopsDatabase, Subscription
from ..utils import get_user_fops_guilds


def dashboard(request):
    """
    Main dashboard view - publicly accessible with info about Fops Bot.
    Shows guild management interface only for logged-in users with Discord connected.
    """

    # Public context - always available
    context = {
        "shared_guilds": None,
        "guilds_error": None,
        "show_discord_login": False,
    }

    # If user is logged in, check for Discord connection and guilds
    if request.user.is_authenticated:
        # Check if user has Discord connected
        if not request.user.discord_access_token:
            context["show_discord_login"] = True
        else:
            # Get shared guilds
            try:
                shared_guilds = get_user_fops_guilds(request.user)
                context["shared_guilds"] = shared_guilds
            except Exception as e:
                context["shared_guilds"] = None  # None means error, [] means no guilds
                context["guilds_error"] = str(e)

    response = render(request, "bot_manager/dashboard.html", context)
    response["Vary"] = "Cookie"
    return response
