
import datetime as dt
import json


from django.urls import reverse
from rest_framework import status

from .base import BaseTestBase
from api.models import JournalEntry, JournalEntryLine, Account


class JournalEntryViewTests(BaseTestBase):

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

        self.company = self.factory.create_company(self.user)
        self.period = self.factory.create_period(
            self.company, dt.date(2020, 1, 1), dt.date(2020, 3, 31))
    
    def tearDown(self):
        super().tearDown()
    

    def test_user_can_create_entry(self):
        Account.objects.create_default_accounts(self.company)
        url = reverse('je-new')
        data = {
            'date':"2020-01-15",
            'memo':'investing in biz with common stock',
            'period':self.period.slug,
            'is_adjusting_entry':False,
            'journal_entry_lines':[
                {
                    "type":"d",
                    "amount":50000,
                    "account":Account.objects.get(name='Cash').slug,
                }, {
                    "type":'c',
                    "amount":50000,
                    "account":Account.objects.get(name='Common Stock').slug,
                }
            ],
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print(response.data)
        





