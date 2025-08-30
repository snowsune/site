import os

from django.conf import settings
from django.utils.safestring import mark_safe

from datetime import datetime, timezone
from django.utils import timezone as django_timezone

from tracking.models import Visitor
from .models import SiteSetting


# Returns the git version directly
def version_processor(request):
    return {
        "version": os.getenv("GIT_COMMIT"),
    }


# Processor for the current year
def year_processor(request):
    return {"year": datetime.now().year}


# True if we're in debug or not!
def debug_mode(request):
    return {
        "debug": settings.DEBUG,
    }


# Expiry links
def expiry_links(request):
    return {
        "discord": mark_safe(
            f"<a href=\"{os.getenv('DISCORD_URL','#')}\">Discord Server</a>"
        ),
    }


# Visitor/site stats
def visit_stats(request):
    """
    Just because I want to have these stats on every page
    """

    # Get today's date in the site's timezone
    today = django_timezone.now().date()

    # Get today's visits
    today_visits = Visitor.objects.filter(start_time__date=today).count()

    # Get today's unique visitors (by IP)
    today_unique_visitors = (
        Visitor.objects.filter(start_time__date=today)
        .values("ip_address")
        .distinct()
        .count()
    )

    # Check for new concurrent user record
    check_concurrent_user_record(today_unique_visitors)

    return {
        "today_visits": today_visits,
        "today_unique_visitors": today_unique_visitors,
    }


def check_concurrent_user_record(current_count):
    """
    Check if we've hit a new concurrent user record and trigger webhook if so.
    Stores the last record in site settings to avoid performance drag.
    """
    try:
        # Get the last recorded concurrent user count
        record_setting = SiteSetting.objects.filter(
            key="last_concurrent_user_record"
        ).first()
        last_record = (
            int(record_setting.value)
            if record_setting and record_setting.value.isdigit()
            else 0
        )

        # Check if we've hit a new record
        if current_count > last_record:
            # Check if we've crossed a multiple of 10 threshold
            last_threshold = (last_record // 10) * 10
            current_threshold = (current_count // 10) * 10

            # Update the record
            if record_setting:
                record_setting.value = str(current_count)
                record_setting.save()
            else:
                SiteSetting.objects.create(
                    key="last_concurrent_user_record", value=str(current_count)
                )

            # Only trigger webhook if we've crossed a new multiple of 10
            if current_threshold > last_threshold:
                trigger_concurrent_user_webhook(current_count)

    except Exception as e:
        # Log error but don't break the context processor
        print(f"Failed to check concurrent user record: {e}")


def trigger_concurrent_user_webhook(record_count):
    """
    Send webhook notification for new concurrent user record
    """
    try:
        # Get webhook URL from site settings
        webhook_setting = SiteSetting.objects.filter(key="moderator_webhook").first()
        if not webhook_setting or not webhook_setting.value:
            return  # No webhook configured

        webhook_url = webhook_setting.value.strip()
        if not webhook_url:
            return

        # Import here to avoid circular imports
        from apps.commorganizer.utils import send_discord_webhook

        # Create notification message
        message = f"🎉 **New Concurrent User Record!**\n\n"
        message += f"**{record_count}** concurrent users today!\n"
        message += f"Timestamp: <t:{int(django_timezone.now().timestamp())}:R>"

        # Send webhook
        send_discord_webhook(webhook_url, message)

    except Exception as e:
        # Log error but don't break the process
        print(f"Failed to send concurrent user record webhook: {e}")


# Quick processor for the discord invite link
# TODO: Could be made generic for all SiteSettings
def discord_invite_link(request):
    invite = SiteSetting.objects.filter(key="discord_invite").first()
    return {"discord_invite": invite.value if invite else ""}


def ko_fi_url(request):
    """Add Ko-fi URL to all template contexts"""
    try:
        ko_fi_setting = SiteSetting.objects.filter(key="KO_FI_URL").first()
        ko_fi_url = (
            ko_fi_setting.value if ko_fi_setting else "https://ko-fi.com/snowsune"
        )
    except:
        ko_fi_url = "https://ko-fi.com/snowsune"

    return {"ko_fi_url": ko_fi_url}


def google_analytics_id(request):
    """Add Google Analytics tag to all template contexts"""
    try:
        ga_setting = SiteSetting.objects.filter(key="GOOGLE_TAG").first()
        google_tag = ga_setting.value if ga_setting else None
    except:
        google_tag = None

    return {"google_tag": google_tag}
