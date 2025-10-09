import logging

from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings

from snowsune.encryption import get_encryption_key


@login_required
def debug_clear_discord(request):
    """Debug view to clear Discord tokens"""

    logging.warning("Debug clear used.")

    request.user.discord_access_token = None
    request.user.discord_refresh_token = None
    request.user.discord_token_expires = None
    request.user.save()
    messages.success(request, "Discord tokens cleared. Please reconnect Discord.")
    return redirect("account-edit")


@login_required
def debug_secret_key(request):
    """Debug view to show SECRET_KEY info"""

    logging.warning("Debug secret key used.")

    secret_key = settings.SECRET_KEY
    encryption_key = get_encryption_key()

    debug_info = {
        "secret_key_length": len(secret_key),
        "secret_key_start": secret_key[:20] + "...",
        "secret_key_end": "..." + secret_key[-10:],
        "encryption_key_length": len(encryption_key),
        "encryption_key_start": encryption_key[:20].decode() + "...",
        "discord_token_exists": bool(request.user.discord_access_token),
        "discord_token_length": (
            len(request.user.discord_access_token)
            if request.user.discord_access_token
            else 0
        ),
    }

    return JsonResponse(debug_info)
