
import datetime as dt

from django.urls import reverse
from rest_framework import status

from .base import BaseTestBase
from api.models import Period


class PeriodViewTests(BaseTestBase):

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)
    
    def tearDown(self):
        super().tearDown()
    

    def is_timeconflict_response(self, response):
        return response.status_code == status.HTTP_400_BAD_REQUEST and 'start/end conflict' in response.data


    def test_user_can_add_a_period_for_their_own_company(self):
        """ Test that a user can add a new period to their own company
        """
        company = self.factory.create_company(self.user)
        self.assertEqual(Period.objects.count(), 0)
        url = reverse('period-new')
        data = {
            'company':company.slug,
            'start':dt.date(2020, 1, 1),
            'end':dt.date(2020, 3, 31),
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Period.objects.count(), 1)

        period = Period.objects.first()
        self.assertEqual(period.start, dt.date(2020, 1, 1))
        self.assertEqual(period.end, dt.date(2020, 3, 31))
        self.assertEqual(period.company, company)
        self.assertEqual(period.user, self.user)


    def test_user_cannot_add_a_period_for_another_users_company(self):
        """ Test that a user cannot add periods to another user's company
        """
        company = self.factory.create_company(self.other_user)
        self.assertEqual(Period.objects.count(), 0)
        url = reverse('period-new')
        data = {
            'company':company.slug,
            'start':dt.date(2020, 1, 1),
            'end':dt.date(2020, 3, 31),
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Period.objects.count(), 0)

        self.client.force_login(self.other_user)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Period.objects.count(), 1)


    def test_user_cannot_add_a_period_if_they_are_over_the_object_limit(self):
        """ Test that a user cannot add additional periods to a company if they are at the
            object limit for periods per company.
        """
        self.user_profile.object_limit_periods_per_company = 0
        self.user_profile.save()

        company = self.factory.create_company(self.user)
        self.assertEqual(Period.objects.count(), 0)
        url = reverse('period-new')
        data = {
            'company':company.slug,
            'start':dt.date(2020, 1, 1),
            'end':dt.date(2020, 3, 31),
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Period.objects.count(), 0)

        self.user_profile.object_limit_periods_per_company = 1
        self.user_profile.save()
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Period.objects.count(), 1)


    def test_new_period_starts_1_day_after_period_ends(self):
        """ Test user can add a period that starts 1 day after an existing period ends.
        """
        company = self.factory.create_company(self.user)
        period1 = self.factory.create_period(company, dt.date(2020, 3, 1), dt.date(2020, 3, 31))
        url = reverse('period-new')

        data = {
            'company':company.slug,
            'start':dt.date(2020, 4, 1),
            'end':dt.date(2020, 5, 15),
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


    def test_new_period_end_1_day_before_period_starts(self):
        """ Test user can add a period that starts 1 day after an existing period ends.
        """
        company = self.factory.create_company(self.user)
        period1 = self.factory.create_period(company, dt.date(2020, 3, 1), dt.date(2020, 3, 31))
        url = reverse('period-new')

        data = {
            'company':company.slug,
            'start':dt.date(2020, 1, 1),
            'end':dt.date(2020, 2, 29),
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


    def test_new_period_start_end_conflict(self):
        """ Test user cannot add a period if it conflicts
        """
        company = self.factory.create_company(self.user)
        period1 = self.factory.create_period(company, dt.date(2020, 3, 1), dt.date(2020, 3, 31))
        url = reverse('period-new')
        self.assertEqual(Period.objects.count(), 1)

        # Partial overlap start
        data = {
            'company':company.slug,
            'start':dt.date(2020, 1, 1),
            'end':dt.date(2020, 3, 15),
        }
        response = self.client.post(url, data, format='json')
        self.assertTrue(self.is_timeconflict_response(response))

        # Partial overlap end
        data = {
            'company':company.slug,
            'start':dt.date(2020, 3, 15),
            'end':dt.date(2020, 4, 15),
        }
        response = self.client.post(url, data, format='json')
        self.assertTrue(self.is_timeconflict_response(response))

        # 1 day overlap start
        data = {
            'company':company.slug,
            'start':dt.date(2020, 1, 15),
            'end':dt.date(2020, 3, 1),
        }
        response = self.client.post(url, data, format='json')
        self.assertTrue(self.is_timeconflict_response(response))

        # 1 day overlap end
        data = {
            'company':company.slug,
            'start':dt.date(2020, 3, 31),
            'end':dt.date(2020, 5, 1),
        }
        response = self.client.post(url, data, format='json')
        self.assertTrue(self.is_timeconflict_response(response))

        # total overlap
        data = {
            'company':company.slug,
            'start':dt.date(2020, 1, 1),
            'end':dt.date(2020, 5, 1),
        }
        response = self.client.post(url, data, format='json')
        self.assertTrue(self.is_timeconflict_response(response))

        # same start and end
        data = {
            'company':company.slug,
            'start':dt.date(2020, 3, 1),
            'end':dt.date(2020, 3, 31),
        }
        response = self.client.post(url, data, format='json')
        self.assertTrue(self.is_timeconflict_response(response))

        self.assertEqual(Period.objects.count(), 1)
