
from django.test import TestCase, override_settings

from api.utils import generate_slugs_batch
from api.models import Company

class BaseTestBase(TestCase):

    @override_settings(SLUG_LENGTH=4)
    def test_generate_slugs_batch(self):
        """ Test that generate_slugs_batch generates a list of unique slugs
        """
        count = 10000
        slugs = generate_slugs_batch(Company, count)
        self.assertEqual(len(slugs), count)
        self.assertEqual(len(set(slugs)), count)
