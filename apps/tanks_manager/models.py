from django.conf import settings
from django.db import models


class TankSite(models.Model):
    """One public tank page per owner; URL is /tanks/&lt;slug&gt;/."""

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tank_site",
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="URL segment, e.g. vixi → /tanks/vixi/",
    )
    tank_top_offset = models.PositiveIntegerField(default=360)
    tank_bottom_offset = models.PositiveIntegerField(default=101)
    character_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Shown as the main title on the public tank page when set.",
    )
    character_url = models.CharField(
        max_length=500,
        blank=True,
        help_text="Optional; makes the title a link (e.g. profile or ref sheet).",
    )
    stage_background = models.ImageField(
        upload_to="tanks/stage/",
        blank=True,
        null=True,
        max_length=500,
        help_text="Optional; sample Alice tank art is used when empty.",
    )
    stage_foreground = models.ImageField(
        upload_to="tanks/stage/",
        blank=True,
        null=True,
        max_length=500,
        help_text="Optional; sample overlay is used when empty.",
    )

    class Meta:
        ordering = ["slug"]

    def __str__(self):
        return f"/tanks/{self.slug}/ ({self.owner})"


class TankLiquid(models.Model):
    tank_site = models.ForeignKey(
        TankSite,
        on_delete=models.CASCADE,
        related_name="liquids",
    )
    sort_order = models.PositiveIntegerField(default=0)
    name = models.CharField(max_length=200)
    volume = models.PositiveSmallIntegerField(default=0)
    color = models.CharField(max_length=32, default="#ffffff")
    url = models.CharField(max_length=500, blank=True)
    image = models.CharField(max_length=500, blank=True)
    image_file = models.ImageField(
        upload_to="tanks/liquids/", blank=True, null=True, max_length=500
    )

    class Meta:
        ordering = ["sort_order", "id"]


class TankLog(models.Model):
    tank_site = models.ForeignKey(
        TankSite,
        on_delete=models.CASCADE,
        related_name="logs",
    )
    date = models.PositiveIntegerField(help_text="Unix timestamp")
    text = models.TextField()

    class Meta:
        ordering = ["date", "id"]


def tank_site_slug_for_user(user):
    """Return this user's tank URL slug, or None if anonymous or they have no TankSite."""
    if not getattr(user, "is_authenticated", False):
        return None
    return (
        TankSite.objects.filter(owner_id=user.pk)
        .values_list("slug", flat=True)
        .first()
    )
