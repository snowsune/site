from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def show_notification(message, type="info", duration=0):
    """
    Show a notification from a Django template

    Usage:
    {% show_notification "Your comment was posted!" "success" 5000 %}
    {% show_notification "Something went wrong" "error" %}
    """
    if duration == 0:
        duration = get_default_duration(type)

    script = f"""
    <script>
        if (window.notifications) {{
            window.notifications.show("{message}", "{type}", {duration});
        }}
    </script>
    """
    return mark_safe(script)


@register.simple_tag
def show_success_notification(message, duration=5000):
    """Show a success notification"""
    return show_notification(message, "success", duration)


@register.simple_tag
def show_error_notification(message, duration=15000):
    """Show an error notification"""
    return show_notification(message, "error", duration)


@register.simple_tag
def show_warning_notification(message, duration=10000):
    """Show a warning notification"""
    return show_notification(message, "warning", duration)


@register.simple_tag
def show_info_notification(message, duration=8000):
    """Show an info notification"""
    return show_notification(message, "info", duration)


def get_default_duration(type):
    """Get default duration for notification type"""
    durations = {"success": 5000, "error": 15000, "warning": 10000, "info": 8000}
    return durations.get(type, 8000)
