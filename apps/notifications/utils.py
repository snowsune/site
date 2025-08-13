"""
Notification utilities for Django apps
Provides easy ways to show notifications from Python code
"""


def show_notification(request, message, type="info", duration=0):
    """
    Show a notification by adding it to the request session

    Usage:
    from apps.notifications.utils import show_notification

    def my_view(request):
        show_notification(request, "Success!", "success")
        return render(request, "template.html")
    """
    if not hasattr(request, "notifications"):
        request.notifications = []

    if duration == 0:
        duration = get_default_duration(type)

    notification = {"message": message, "type": type, "duration": duration}

    request.notifications.append(notification)


def show_success_notification(request, message, duration=5000):
    """Show a success notification"""
    show_notification(request, message, "success", duration)


def show_error_notification(request, message, duration=15000):
    """Show an error notification"""
    show_notification(request, message, "error", duration)


def show_warning_notification(request, message, duration=10000):
    """Show a warning notification"""
    show_notification(request, message, "warning", duration)


def show_info_notification(request, message, duration=8000):
    """Show an info notification"""
    show_notification(request, message, "info", duration)


def get_default_duration(type):
    """Get default duration for notification type"""
    durations = {"success": 5000, "error": 15000, "warning": 10000, "info": 8000}
    return durations.get(type, 8000)
