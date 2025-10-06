from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import login
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
import requests
import json
from .models import Guild, FopsDatabase


def has_fops_admin_access(user):
    """Check if user has admin rights in any guild where Fops Bot is present"""
    if not user.discord_access_token:
        return False

    try:
        # Get user's guilds from Discord
        headers = {"Authorization": f"Bearer {user.discord_access_token}"}
        guilds_response = requests.get(
            "https://discord.com/api/users/@me/guilds", headers=headers
        )

        if guilds_response.status_code != 200:
            return False

        user_guilds = guilds_response.json()

        # Get Fops Bot guilds directly from Discord API
        fops_guilds = get_fops_guilds_from_discord()
        fops_guild_ids = {str(guild["id"]) for guild in fops_guilds}

        # Check if user has admin rights in any Fops guild
        for guild in user_guilds:
            if str(guild["id"]) in fops_guild_ids:
                # Check if user has administrator permission
                permissions = int(guild.get("permissions", 0))
                if permissions & 0x8:  # Administrator permission bit
                    return True

        return False
    except Exception:
        return False


def get_fops_guilds_from_discord():
    """Get Fops Bot's guilds directly from Discord API with caching"""
    # Check cache first
    cached_guilds = cache.get("fops_bot_guilds")
    if cached_guilds is not None:
        return cached_guilds

    if not settings.DISCORD_CLIENT_ID or not settings.DISCORD_CLIENT_SECRET:
        return []

    try:
        bot_token = (
            settings.DISCORD_BOT_TOKEN
            if hasattr(settings, "DISCORD_BOT_TOKEN")
            else None
        )
        if not bot_token:
            return []

        headers = {"Authorization": f"Bot {bot_token}"}
        guilds_response = requests.get(
            "https://discord.com/api/users/@me/guilds", headers=headers
        )

        if guilds_response.status_code != 200:
            return []

        fops_guilds = guilds_response.json()
        # Cache for 5 minutes
        cache.set("fops_bot_guilds", fops_guilds, 300)
        return fops_guilds
    except Exception:
        return []


def get_user_fops_guilds(user):
    """Get guilds where user and Fops Bot are both present with admin status"""
    if not user.discord_access_token:
        return []

    # Check cache first (user-specific cache key)
    cache_key = f"user_{user.id}_fops_guilds"
    cached_shared_guilds = cache.get(cache_key)
    if cached_shared_guilds is not None:
        return cached_shared_guilds

    try:
        # Get user's guilds from Discord
        headers = {"Authorization": f"Bearer {user.discord_access_token}"}
        guilds_response = requests.get(
            "https://discord.com/api/users/@me/guilds", headers=headers
        )

        if guilds_response.status_code != 200:
            return []

        user_guilds = guilds_response.json()

        # Get Fops Bot guilds directly from Discord API
        fops_guilds = get_fops_guilds_from_discord()
        fops_guild_ids = {str(guild["id"]) for guild in fops_guilds}

        shared_guilds = []
        for guild in user_guilds:
            guild_id = str(guild["id"])
            if guild_id in fops_guild_ids:
                permissions = int(guild.get("permissions", 0))
                is_admin = bool(permissions & 0x8)

                shared_guilds.append(
                    {
                        "id": guild["id"],
                        "name": guild["name"],
                        "icon": guild.get("icon"),
                        "is_admin": is_admin,
                        "permissions": permissions,
                    }
                )

        # Cache for 2 minutes
        cache.set(cache_key, shared_guilds, 120)
        return shared_guilds
    except Exception:
        return []


@login_required
def dashboard(request):
    """Main dashboard showing guilds and tables"""
    # Check if user has Discord connected
    if not request.user.discord_access_token:
        context = {
            "error": "You must connect your Discord account to access Fops Bot Manager",
            "show_discord_login": True,
        }
        return render(request, "bot_manager/dashboard.html", context)

    # Check if user has admin rights in any Fops guild
    if not has_fops_admin_access(request.user):
        context = {
            "error": "You must have admin rights in a server where Fops Bot is present to access this dashboard",
            "show_discord_login": False,
        }
        return render(request, "bot_manager/dashboard.html", context)

    try:
        guilds = Guild.get_from_fops()
        tables = Guild.get_tables()
        shared_guilds = get_user_fops_guilds(request.user)
    except Exception as e:
        guilds = []
        tables = []
        shared_guilds = []
        error = str(e)

    context = {
        "guilds": guilds,
        "tables": tables,
        "shared_guilds": shared_guilds,
        "error": locals().get("error", None),
    }
    return render(request, "bot_manager/dashboard.html", context)


def discord_login(request):
    """Redirect to Discord OAuth"""
    if not settings.DISCORD_CLIENT_ID:
        return JsonResponse({"error": "Discord OAuth not configured"}, status=500)

    discord_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={settings.DISCORD_CLIENT_ID}"
        f"&redirect_uri={settings.DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify%20guilds"
    )
    return redirect(discord_url)


def discord_callback(request):
    """Handle Discord OAuth callback"""
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

    # Update or create user
    from apps.users.models import CustomUser

    user, created = CustomUser.objects.get_or_create(
        discord_id=discord_id,
        defaults={
            "username": f"discord_{discord_id}",
            "discord_username": discord_username,
        },
    )

    # Update Discord info
    user.discord_username = discord_username
    user.discord_access_token = access_token
    user.discord_refresh_token = refresh_token
    user.discord_token_expires = timezone.now() + timedelta(seconds=expires_in)
    user.save()

    # Log them in
    login(request, user)

    return redirect("bot_manager_dashboard")


@login_required
def table_data(request, table_name):
    """Display data from a specific table"""
    # Check Discord connection and admin access
    if not request.user.discord_access_token or not has_fops_admin_access(request.user):
        return redirect("bot_manager_dashboard")

    conn = FopsDatabase.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {table_name} LIMIT 100")
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description] if cur.description else []

        context = {"table_name": table_name, "columns": columns, "rows": rows}
        return render(request, "bot_manager/table_data.html", context)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    finally:
        conn.close()
