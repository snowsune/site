from django.db import models


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
