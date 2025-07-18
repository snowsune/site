from django.test import TestCase
from django.urls import reverse
from .models import Commission

# Create your tests here.


class CommissionOrganizerTests(TestCase):
    def test_unauthenticated_commission_creation(self):
        """Test creating a commission without authentication (legacy password flow)."""
        create_url = reverse("commorganizer-landing")
        response = self.client.post(
            create_url,
            {
                "action": "create",
                "name": "TestCommission",
                "password": "testpass123",
            },
            follow=True,
        )
        # Should redirect to the artist dashboard for the new commission
        self.assertRedirects(
            response, reverse("commorganizer-artist-dashboard", args=["TestCommission"])
        )
        # The commission should exist in the database
        commission = Commission.objects.get(name="TestCommission")
        self.assertEqual(commission.artist_password, "testpass123")
