from django.test import TestCase
from django.urls import reverse
from log.models import Entry


class IndexViewTest(TestCase):
    def test_index_view_status_code(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)


class BatteryDetailViewTest(TestCase):
    def setUp(self):
        Entry.objects.create(battery="AA0", condition=Entry.Condition.GOOD)

    def test_battery_detail_view_status_code(self):
        response = self.client.get(reverse("battery_detail", args=["AA0"]))
        self.assertEqual(response.status_code, 200)

    def test_battery_detail_view_404(self):
        response = self.client.get(reverse("battery_detail", args=["NONEXISTENT"]))
        self.assertEqual(response.status_code, 404)


class MetaImageViewTest(TestCase):
    def setUp(self):
        # Create a sample entry to test the meta image generation
        Entry.objects.create(
            battery="AA0",
            condition=Entry.Condition.GOOD,
            charge=80,
            rint=0.02,
            memo="Test memo",
        )

    def test_meta_image_generation(self):
        # Request the meta image for the existing battery
        response = self.client.get(reverse("get_cover_image", args=["AA0"]))

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Check the content type is 'image/png'
        self.assertEqual(response["Content-Type"], "image/png")

        # Check that the content is not empty
        self.assertTrue(len(response.content) > 0)

    def test_meta_image_404(self):
        # Request the meta image for a non-existent battery
        response = self.client.get(reverse("get_cover_image", args=["NONEXISTENT"]))

        # Check that a 404 is returned
        self.assertEqual(response.status_code, 404)
