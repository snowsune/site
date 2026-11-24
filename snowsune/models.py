import json

from django.core.exceptions import ValidationError
from django.db import models


def validate_calendar_sources(value):
    """CALENDAR_SOURCES must be a JSON list of {"name", "url", "color"?} objects."""
    try:
        sources = json.loads(value)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON: {e}")

    if not isinstance(sources, list):
        raise ValidationError("Must be a JSON list of calendar sources.")

    for i, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValidationError(f"Entry {i} must be an object.")
        for field in ("name", "url"):
            if not isinstance(source.get(field), str) or not source[field].strip():
                raise ValidationError(f'Entry {i} needs a non-empty "{field}" string.')
        if "color" in source and not isinstance(source["color"], str):
            raise ValidationError(f'Entry {i} "color" must be a string.')


# Per-key validators, run when a SiteSetting is saved through a form (e.g. admin).
SITE_SETTING_VALIDATORS = {
    "CALENDAR_SOURCES": validate_calendar_sources,
}


class SiteSetting(models.Model):
    """
    Site setting can store dedicated simple things. Easier than editing
    a bunch of ENV variables on the host side!
    """

    key = models.CharField(max_length=100, unique=True)
    value = models.TextField(blank=True)

    class Meta:
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return f"{self.key}: {self.value}"

    def clean(self):
        validator = SITE_SETTING_VALIDATORS.get(self.key)
        if validator and self.value.strip():
            try:
                validator(self.value)
            except ValidationError as e:
                raise ValidationError({"value": e.messages})
