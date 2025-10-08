"""Discord OAuth authentication views"""

import requests
from django.shortcuts import redirect
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from apps.users.models import CustomUser


def discord_login(request):
    """Redirect to Discord OAuth"""
    if not settings.DISCORD_CLIENT_ID:
        return JsonResponse({"error": "Discord OAuth not configured"}, status=500)

    discord_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={settings.DISCORD_CLIENT_ID}"
        f"&redirect_uri={settings.DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify%20guilds"  # Just the two we need.
    )
    return redirect(discord_url)


@login_required
def discord_callback(request):
    """Handle Discord OAuth callback - attach Discord to existing Snowsune account"""
    code = request.GET.get("code")
    if not code:
        return JsonResponse({"error": "No authorization code provided"}, status=400)

    # Exchange code for access token
    data = {
        "client_id": settings.DISCORD_CLIENT_ID,
        "client_secret": settings.DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.DISCORD_REDIRECT_URI,
    }

    response = requests.post("https://discord.com/api/oauth2/token", data=data)
    if response.status_code != 200:
        return JsonResponse({"error": "Failed to get access token"}, status=400)

    token_data = response.json()
    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]
    expires_in = token_data["expires_in"]

    # Get user info
    headers = {"Authorization": f"Bearer {access_token}"}
    user_response = requests.get("https://discord.com/api/users/@me", headers=headers)
    if user_response.status_code != 200:
        return JsonResponse({"error": "Failed to get user info"}, status=400)

    user_data = user_response.json()
    discord_id = user_data["id"]
    discord_username = f"{user_data['username']}#{user_data['discriminator']}"

    # Check if Discord account is already attached to another user
    existing_discord_user = (
        CustomUser.objects.filter(discord_id=discord_id)
        .exclude(id=request.user.id)
        .first()
    )
    if existing_discord_user:
        messages.error(
            request,
            "This Discord account is already attached to another Snowsune account.",
        )
        return redirect("bot_manager_dashboard")

    # Attach Discord to current logged-in user
    request.user.discord_id = discord_id
    request.user.discord_username = discord_username
    request.user.set_discord_access_token(access_token)
    request.user.set_discord_refresh_token(refresh_token)
    request.user.discord_token_expires = timezone.now() + timedelta(seconds=expires_in)
    request.user.save()

    messages.success(request, "Discord account successfully attached!")
    return redirect("bot_manager_dashboard")
