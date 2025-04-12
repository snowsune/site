from django.test import TestCase

from apps.users.models import CustomUser


class IndexViewTest(TestCase):
    def test_nothing(self):
        self.assertEqual(True, True)
