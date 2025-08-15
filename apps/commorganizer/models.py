from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your models here.


class Commission(models.Model):
    name = models.CharField(max_length=64, unique=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="commissions",
    )
    artist_password = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    webhook_url = models.URLField(
        blank=True, null=True, help_text="Optional: Discord webhook for notifications."
    )

    def __str__(self):
        return self.name

    @property
    def requires_password(self):
        return self.user is None and self.artist_password


class Draft(models.Model):
    id = models.AutoField(primary_key=True)
    commission = models.ForeignKey(
        Commission, related_name="drafts", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="commorganizer/drafts/")
    created_at = models.DateTimeField(auto_now_add=True)
    number = models.PositiveIntegerField()

    def save(self, *args, **kwargs):
        if not self.pk:
            # Assign the next draft number for this commission
            last = (
                Draft.objects.filter(commission=self.commission)
                .order_by("-number")
                .first()
            )
            self.number = (last.number + 1) if last else 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Draft {self.number} for {self.commission.name} (ID {self.pk})"


class Comment(models.Model):
    draft = models.ForeignKey(Draft, related_name="comments", on_delete=models.CASCADE)
    x = models.PositiveIntegerField()
    y = models.PositiveIntegerField()
    commenter_name = models.CharField(max_length=32)
    resolved = models.BooleanField(default=False)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.commenter_name} on Draft {self.draft.number} at ({self.x},{self.y})"
