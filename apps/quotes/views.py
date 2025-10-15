from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Quote
from snowsune.models import SiteSetting


def cleanup_old_quotes():
    """
    Delete quotes older than a month, but keep at least 10 quotes
    """
    # Calculate the cutoff date (1 month ago)
    cutoff_date = timezone.now() - timedelta(days=30)

    # Get all quotes ordered by creation date (newest first)
    all_quotes = Quote.objects.all().order_by("-created_at")

    # If we have 10 or fewer quotes, no cleanup needed
    if all_quotes.count() <= 10:
        return

    # Find quotes older than a month
    old_quotes = Quote.objects.filter(created_at__lt=cutoff_date)

    # If we have old quotes, delete them but ensure we keep at least 10
    if old_quotes.exists():
        # Get the 10th newest quote's creation date
        tenth_newest_quote = all_quotes[9]  # 0-indexed, so 9th element is 10th newest

        # Delete quotes older than the 10th newest quote
        quotes_to_delete = Quote.objects.filter(
            created_at__lt=tenth_newest_quote.created_at
        )
        deleted_count = quotes_to_delete.count()
        quotes_to_delete.delete()

        return deleted_count

    return 0


@csrf_exempt
@require_http_methods(["POST"])
def webhook_receive(request):
    """
    Bot can send a post here to add a quote from discord

    For testing you can curl like this though!
    curl -X POST -H "Content-Type: application/json" -d '{"content": "You sent a test qoute!", "user": "test user", "discord_id": "1234567890", "key": "iamnotacrook"}' http://localhost:8000/api/quotes/webhook/
    """

    try:
        data = json.loads(request.body)

        # Extract quote data
        content = data.get("content", "").strip()
        user = data.get("user", "Unknown")
        discord_id = data.get("discord_id", "")
        bot_key = data.get("key", "")

        if bot_key != SiteSetting.objects.get(key="BOT_CONNECTOR_KEY").value:
            return JsonResponse({"error": "Invalid bot key"}, status=401)

        if not content:
            return JsonResponse({"error": "Content is required"}, status=400)

        # Create the quote
        quote = Quote.objects.create(content=content, user=user, discord_id=discord_id)

        # Clean up old quotes after adding a new one
        deleted_count = cleanup_old_quotes()

        return JsonResponse(
            {
                "success": True,
                "id": quote.id,
                "message": "Quote created successfully",
                "deleted_old_quotes": deleted_count,
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_quotes(request):
    """Get active quotes for display"""
    quotes = Quote.objects.filter(active=True).values("content", "user", "created_at")
    return JsonResponse({"quotes": list(quotes)})
