from django.db import models


class TankSettings(models.Model):
    tank_top_offset = models.PositiveIntegerField(default=360)
    tank_bottom_offset = models.PositiveIntegerField(default=101)

    class Meta:
        verbose_name_plural = "Tank settings"


class TankClone(models.Model):
    sort_order = models.PositiveIntegerField(default=0)
    name = models.CharField(max_length=200)
    banner = models.CharField(max_length=200, blank=True)
    image = models.CharField(
        max_length=500,
        blank=True,
        help_text="Relative path or URL if not using upload",
    )
    image_file = models.ImageField(
        upload_to="tanks/clones/", blank=True, null=True, max_length=500
    )
    url = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["sort_order", "id"]


class TankLiquid(models.Model):
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
    date = models.PositiveIntegerField(help_text="Unix timestamp")
    text = models.TextField()

    class Meta:
        ordering = ["date", "id"]
