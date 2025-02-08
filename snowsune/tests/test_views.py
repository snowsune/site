from django.test import TestCase

from snowsune.models import CustomUser


class IndexViewTest(TestCase):
    def test_nothing(self):
        self.assertEqual(True, True)
