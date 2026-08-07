import os

from django.conf import settings
from datetime import datetime, date

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


def matrix_widget_link(request):
    return {"matrix_widget": settings.MATRIX_WIDGET_URL}


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


def seasonal_css(request):
    """Auto apply seasonable css stuff! Yay!"""

    today = date.today()

    seasonal_dates = {
        (9, 17): "fox_day.css",  # National fox day!
        (10,): "halloween.css",  # October (whole month counts~)
        (12,): "christmas.css",  # December (whole month counts!)
        (2, 14): "valentines.css",  # February 14th (Valentines day!)
        (6,): "pride.css",  # June (Pride month!)
        (8, 8): "vore_day.css",  # 8/8 (Vore day!)
    }

    # First check for exact date match (month, day)
    css_file = seasonal_dates.get((today.month, today.day))
    # If no exact match, check for month-only match (month,)
    if not css_file:
        css_file = seasonal_dates.get((today.month,))

    return {"seasonal_css": f"css/seasonal/{css_file}" if css_file else None}
