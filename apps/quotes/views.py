from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import Quote


@csrf_exempt
@require_http_methods(["POST"])
def webhook_receive(request):
    """Receive quotes from Discord webhook"""
    try:
        data = json.loads(request.body)

        # Extract quote data
        content = data.get("content", "").strip()
        user = data.get("user", "Unknown")
        discord_id = data.get("discord_id", "")

        if not content:
            return JsonResponse({"error": "Content is required"}, status=400)

        # Create the quote
        quote = Quote.objects.create(content=content, user=user, discord_id=discord_id)

        return JsonResponse(
            {"success": True, "id": quote.id, "message": "Quote created successfully"}
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_quotes(request):
    """Get active quotes for display"""
    quotes = Quote.objects.filter(active=True).values("content", "user", "created_at")
    return JsonResponse({"quotes": list(quotes)})
