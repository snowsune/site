from django.db import models


class ThankYou(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    bio = models.TextField()
    image = models.ImageField(upload_to="thank_yous/", blank=True, null=True)
    order = models.PositiveIntegerField(
        default=0, help_text="Order for manual sorting (0 = random)"
    )

    # Social links as JSON - format: {"https://link.com": "Link Name", "https://other.com": "Other Name"}
    social_links = models.JSONField(
        default=dict,
        blank=True,
        help_text='Social links as JSON: {"https://link.com": "Link Name"}',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Thank You"
        verbose_name_plural = "Thank Yous"

    def __str__(self):
        return f"{self.name} - {self.role}"

    def get_links(self):
        """Return a list of (label, url) tuples for all social links"""
        if not self.social_links:
            return []
        return [(label, url) for url, label in self.social_links.items()]
