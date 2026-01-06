from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
import requests
from icalendar import Calendar
from datetime import datetime, date, timedelta
import pytz


# Calendar configuration - easily extensible
CALENDAR_SOURCES = [
    {
        "name": "Hunner's Calendar",
        "url": "https://calendar.google.com/calendar/ical/hunner.the.squeaky%40gmail.com/public/basic.ics",
        "color": "#3788d8",  # Default blue color
    },
    # Add more calendars here as needed
    # {
    #     'name': 'Another Calendar',
    #     'url': 'https://example.com/calendar.ics',
    #     'color': '#ff6b6b',
    # },
]


class CalendarView(View):
    """Main calendar page view"""

    def get(self, request, *args, **kwargs):
        return render(
            request,
            "calendar.html",
            {
                "calendar_sources": CALENDAR_SOURCES,
            },
        )


@method_decorator(cache_page(60 * 15), name="dispatch")  # Cache for 15 minutes
class CalendarEventsAPIView(View):
    """API endpoint that fetches and parses ICS files, returns JSON events"""

    def get(self, request, *args, **kwargs):
        all_events = []

        for calendar_config in CALENDAR_SOURCES:
            try:
                # Fetch the ICS file
                response = requests.get(
                    calendar_config["url"],
                    timeout=10,
                    headers={"User-Agent": "Snowsune Calendar Fetcher"},
                )
                response.raise_for_status()

                # Parse the ICS file
                cal = Calendar.from_ical(response.content)

                # Extract events
                for component in cal.walk("vevent"):
                    event = {
                        "title": str(component.get("summary", "No Title")),
                        "start": self._parse_datetime(component.get("dtstart")),
                        "end": self._parse_datetime(component.get("dtend")),
                        "description": str(component.get("description", "")),
                        "location": str(component.get("location", "")),
                        "url": str(component.get("url", "")),
                        "calendar": calendar_config["name"],
                        "color": calendar_config.get("color", "#3788d8"),
                    }

                    # Handle all-day events and serialize datetimes
                    if isinstance(event["start"], str):
                        # All-day event (date only)
                        event["allDay"] = True
                    else:
                        event["allDay"] = False
                        # Ensure timezone-aware datetime and convert to ISO string
                        if event["start"]:
                            if not event["start"].tzinfo:
                                event["start"] = pytz.UTC.localize(event["start"])
                            event["start"] = event["start"].isoformat()
                        if event["end"]:
                            if not event["end"].tzinfo:
                                event["end"] = pytz.UTC.localize(event["end"])
                            event["end"] = event["end"].isoformat()

                    all_events.append(event)

            except Exception as e:
                # Log error but continue with other calendars
                import logging

                logger = logging.getLogger(__name__)
                logger.error(f"Error fetching calendar {calendar_config['name']}: {e}")
                continue

        # Sort events by start time (all strings now, so simple string sort works)
        all_events.sort(key=lambda x: x["start"] or "")

        return JsonResponse(all_events, safe=False)

    def _parse_datetime(self, dt_value):
        """Parse iCalendar datetime/date value to Python datetime or date string"""
        if dt_value is None:
            return None

        # Get the underlying datetime/date value
        dt = dt_value.dt if hasattr(dt_value, "dt") else dt_value

        # Handle date-only (all-day events)
        if isinstance(dt, date) and not isinstance(dt, datetime):
            # Return ISO format string for all-day events
            return dt.isoformat()
        elif isinstance(dt, datetime):
            return dt

        return None
