from django.db import models


class Quote(models.Model):
    content = models.TextField(max_length=500)
    user = models.CharField(max_length=100)  # Discord username
    discord_id = models.CharField(max_length=20, blank=True)  # Discord user ID
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)  # Is active or not, expires eventually!

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f'"{self.content[:50]}..." - {self.user}'
