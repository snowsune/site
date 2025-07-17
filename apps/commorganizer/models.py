from django.db import models

# Create your models here.


class Commission(models.Model):
    name = models.CharField(max_length=32, unique=True)
    artist_password = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Draft(models.Model):
    commission = models.ForeignKey(
        Commission, related_name="drafts", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="commorganizer/drafts/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Draft for {self.commission.name} ({self.pk})"


class Comment(models.Model):
    draft = models.ForeignKey(Draft, related_name="comments", on_delete=models.CASCADE)
    x = models.PositiveIntegerField()
    y = models.PositiveIntegerField()
    commenter_name = models.CharField(max_length=32)
    resolved = models.BooleanField(default=False)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.commenter_name} on Draft {self.draft.pk} at ({self.x},{self.y})"
