"""
Context processor for notifications
Makes notifications available in all templates
"""


def notifications_processor(request):
    """
    Add notifications to template context

    This allows any template to access notifications from the request
    """
    notifications = getattr(request, "notifications", [])

    return {"notifications": notifications, "has_notifications": len(notifications) > 0}
