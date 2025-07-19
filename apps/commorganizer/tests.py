from django.test import TestCase
from django.urls import reverse
from .models import Commission, Draft, Comment
from django.core.files.uploadedfile import SimpleUploadedFile

# Create your tests here.


class CommissionOrganizerTests(TestCase):
    def test_unauthenticated_commission_creation(self):
        """Test creating a commission without authentication (legacy password flow)."""
        create_url = reverse("commorganizer")
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
        # self.assertIsNone(commission.owner)  # Uncomment if owner field is present

    def test_viewer_can_add_and_see_comment(self):
        """Test that a viewer can add a comment to a draft and see it later."""
        # Create commission and draft
        commission = Commission.objects.create(
            name="TestCommission", artist_password="testpass123"
        )
        # Create a dummy image file
        image = SimpleUploadedFile("test.png", b"filecontent", content_type="image/png")
        draft = Draft.objects.create(commission=commission, image=image, number=1)
        # Post a comment as a viewer
        public_url = (
            reverse("commorganizer-public-view", args=[commission.name])
            + f"?draft={draft.pk}"
        )
        response = self.client.post(
            public_url,
            {
                "x": 10,
                "y": 20,
                "commenter_name": "ViewerUser",
                "content": "Nice draft!",
                "add_comment": "1",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        # The comment should exist in the database
        comment = Comment.objects.get(draft=draft, commenter_name="ViewerUser")
        self.assertEqual(comment.content, "Nice draft!")
        # The comment should appear in the response content
        self.assertContains(response, "Nice draft!")
