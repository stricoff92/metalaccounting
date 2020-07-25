
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
        """ Test that a user can create journal entry with 1 DR account and 1 CR account
        """
        Account.objects.create_default_accounts(self.company)
        url = reverse('je-new')
        data = {
            'date':"2020-01-15",
            'memo':'investing in biz with common stock',
            'period':self.period.slug,
            'journal_entry_lines':[
                {
                    "type":"d",
                    "amount":50000,
                    "account":Account.objects.get(name='Cash').slug,
                }, {
                    "type":"c",
                    "amount":50000,
                    "account":Account.objects.get(name='Common Stock').slug,
                }
            ],
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        journal_entry = JournalEntry.objects.get(slug=response.data['slug'])
        
        self.assertEqual(journal_entry.date, dt.date(2020, 1, 15))
        self.assertEqual(journal_entry.memo, 'investing in biz with common stock')
        self.assertEqual(journal_entry.period, self.period)
        self.assertFalse(journal_entry.is_adjusting_entry)
        self.assertEqual(journal_entry.dr_total, 50000)
        self.assertEqual(journal_entry.cr_total, 50000)  

        self.assertEqual(journal_entry.lines.count(), 2)
        cr_line = journal_entry.lines.get(type=JournalEntryLine.TYPE_CREDIT)
        dr_line = journal_entry.lines.get(type=JournalEntryLine.TYPE_DEBIT)
        self.assertEqual(cr_line.amount, 50000)
        self.assertEqual(dr_line.amount, 50000)
