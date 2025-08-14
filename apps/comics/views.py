from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Webcomic, ComicPage, UserSubscription, NotificationLog


def comics_landing(request):
    """Landing page for the comics section"""
    # Get featured or popular webcomics
    featured_webcomics = Webcomic.objects.filter(is_active=True)[:6]

    context = {
        "featured_webcomics": featured_webcomics,
    }
    return render(request, "comics_home.html", context)


@login_required
def webcomic_list(request):
    """Browse all available webcomics"""
    webcomics = Webcomic.objects.filter(is_active=True)

    # Search functionality
    search_query = request.GET.get("search", "")
    if search_query:
        webcomics = webcomics.filter(
            Q(name__icontains=search_query)
            | Q(author__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    # Filter by polling method
    polling_method = request.GET.get("method", "")
    if polling_method:
        webcomics = webcomics.filter(polling_method=polling_method)

    # Get user's current subscriptions
    user_subscriptions = UserSubscription.objects.filter(
        user=request.user, is_active=True
    ).values_list("webcomic_id", flat=True)

    # Pagination
    paginator = Paginator(webcomics, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "webcomics": page_obj,
        "user_subscriptions": user_subscriptions,
        "search_query": search_query,
        "polling_method": polling_method,
        "polling_methods": Webcomic.POLLING_METHOD_CHOICES,
    }
    return render(request, "comics/webcomic_list.html", context)


@login_required
def webcomic_detail(request, slug):
    """View details of a specific webcomic"""
    webcomic = get_object_or_404(Webcomic, slug=slug, is_active=True)

    # Get recent comic pages
    recent_pages = ComicPage.objects.filter(webcomic=webcomic)[:10]

    # Check if user is subscribed
    user_subscription = UserSubscription.objects.filter(
        user=request.user, webcomic=webcomic, is_active=True
    ).first()

    context = {
        "webcomic": webcomic,
        "recent_pages": recent_pages,
        "user_subscription": user_subscription,
    }
    return render(request, "comics/webcomic_detail.html", context)


@login_required
def subscribe_to_webcomic(request, webcomic_id):
    """Subscribe to a webcomic"""
    if request.method == "POST":
        webcomic = get_object_or_404(Webcomic, id=webcomic_id, is_active=True)

        # Get or create subscription
        subscription, created = UserSubscription.objects.get_or_create(
            user=request.user,
            webcomic=webcomic,
            defaults={
                "email_notifications": request.POST.get("email_notifications", True),
                "rss_enabled": request.POST.get("rss_enabled", True),
                "discord_notifications": request.POST.get(
                    "discord_notifications", False
                ),
                "notification_frequency": request.POST.get(
                    "notification_frequency", "immediate"
                ),
            },
        )

        if not created:
            # Update existing subscription
            subscription.email_notifications = request.POST.get(
                "email_notifications", subscription.email_notifications
            )
            subscription.rss_enabled = request.POST.get(
                "rss_enabled", subscription.rss_enabled
            )
            subscription.discord_notifications = request.POST.get(
                "discord_notifications", subscription.discord_notifications
            )
            subscription.notification_frequency = request.POST.get(
                "notification_frequency", subscription.notification_frequency
            )
            subscription.is_active = True
            subscription.save()

        messages.success(request, f"Successfully subscribed to {webcomic.name}!")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {"success": True, "message": f"Subscribed to {webcomic.name}"}
            )

        return redirect("comics:webcomic_detail", slug=webcomic.slug)

    return redirect("comics:webcomic_list")


@login_required
def unsubscribe_from_webcomic(request, webcomic_id):
    """Unsubscribe from a webcomic"""
    if request.method == "POST":
        subscription = get_object_or_404(
            UserSubscription, user=request.user, webcomic_id=webcomic_id
        )
        webcomic_name = subscription.webcomic.name
        subscription.is_active = False
        subscription.save()

        messages.success(request, f"Unsubscribed from {webcomic_name}")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {"success": True, "message": f"Unsubscribed from {webcomic_name}"}
            )

        return redirect("comics:webcomic_list")

    return redirect("comics:webcomic_list")


@login_required
def my_subscriptions(request):
    """View user's current subscriptions"""
    subscriptions = UserSubscription.objects.filter(
        user=request.user, is_active=True
    ).select_related("webcomic")

    # Get recent updates for subscribed webcomics
    recent_updates = []
    for subscription in subscriptions:
        latest_page = subscription.webcomic.get_latest_page()
        if latest_page:
            recent_updates.append(
                {
                    "webcomic": subscription.webcomic,
                    "latest_page": latest_page,
                    "subscription": subscription,
                }
            )

    # Sort by latest update date
    recent_updates.sort(key=lambda x: x["latest_page"].comic_date, reverse=True)

    context = {
        "subscriptions": subscriptions,
        "recent_updates": recent_updates[:20],  # Show last 20 updates
    }
    return render(request, "comics/my_subscriptions.html", context)


@login_required
def subscription_settings(request, subscription_id):
    """Edit subscription settings"""
    subscription = get_object_or_404(
        UserSubscription, id=subscription_id, user=request.user
    )

    if request.method == "POST":
        subscription.email_notifications = (
            request.POST.get("email_notifications") == "on"
        )
        subscription.rss_enabled = request.POST.get("rss_enabled") == "on"
        subscription.discord_notifications = (
            request.POST.get("discord_notifications") == "on"
        )
        subscription.notification_frequency = request.POST.get(
            "notification_frequency", "immediate"
        )
        subscription.save()

        messages.success(request, "Subscription settings updated!")
        return redirect("comics:my_subscriptions")

    context = {
        "subscription": subscription,
    }
    return render(request, "comics/subscription_settings.html", context)


def user_rss_feed(request, user_id):
    """Generate RSS feed for a specific user's subscriptions"""
    # This would require a proper RSS library like feedgenerator
    # For now, just return a placeholder
    return HttpResponse(
        "RSS feed functionality coming soon!", content_type="text/plain"
    )
