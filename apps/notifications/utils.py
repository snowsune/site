"""Flash messages for views. Uses Django's messages framework."""

from django.contrib import messages


def show_notification(request, message, type="info", duration=0):
    level = {
        "success": messages.SUCCESS,
        "error": messages.ERROR,
        "warning": messages.WARNING,
        "info": messages.INFO,
        "debug": messages.DEBUG,
    }.get(type, messages.INFO)
    messages.add_message(request, level, message)


def show_success_notification(request, message, duration=5000):
    show_notification(request, message, "success", duration)


def show_error_notification(request, message, duration=15000):
    show_notification(request, message, "error", duration)


def show_warning_notification(request, message, duration=10000):
    show_notification(request, message, "warning", duration)


def show_info_notification(request, message, duration=8000):
    show_notification(request, message, "info", duration)
