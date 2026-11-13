from django.test import TestCase
from django.urls import reverse


class ListsPrototypeTests(TestCase):
    def test_index(self):
        self.assertEqual(self.client.get(reverse("lists:index")).status_code, 200)

    def test_furcasts_grid(self):
        resp = self.client.get("/lists/furcasts/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "lists/placeholder.png")
        self.assertContains(resp, "/lists/furcasts/placeholder-one/")

    def test_item_detail(self):
        resp = self.client.get("/lists/furcasts/placeholder-one/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Episodes")

    def test_unknown_404s(self):
        self.assertEqual(self.client.get("/lists/nope/").status_code, 404)
        self.assertEqual(self.client.get("/lists/furcasts/nope/").status_code, 404)
