
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

        self.other_company = self.factory.create_company(self.other_user)
        self.other_period = self.factory.create_period(
            self.other_company, dt.date(2020, 1, 1), dt.date(2020, 3, 31))
    
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
                    "type":JournalEntryLine.TYPE_DEBIT,
                    "amount":50000,
                    "account":Account.objects.get(name='Cash').slug,
                }, {
                    "type":JournalEntryLine.TYPE_CREDIT,
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
        self.assertFalse(journal_entry.is_closing_entry)
        self.assertEqual(journal_entry.dr_total, 50000)
        self.assertEqual(journal_entry.cr_total, 50000)  

        self.assertEqual(journal_entry.lines.count(), 2)
        cr_line = journal_entry.lines.get(type=JournalEntryLine.TYPE_CREDIT)
        dr_line = journal_entry.lines.get(type=JournalEntryLine.TYPE_DEBIT)
        self.assertEqual(cr_line.amount, 50000)
        self.assertEqual(dr_line.amount, 50000)
        self.assertEqual(cr_line.account, Account.objects.get(name='Common Stock'))
        self.assertEqual(dr_line.account, Account.objects.get(name='Cash'))


    def test_user_can_create_adjustment_entry(self):
        """ Test that a user can create an adjusting journal entry with 1 DR account and 1 CR account
        """
        Account.objects.create_default_accounts(self.company)
        url = reverse('je-new')
        data = {
            'date':"2020-01-15",
            'memo':'investing in biz with common stock',
            'period':self.period.slug,
            'is_adjusting_entry':True,
            'journal_entry_lines':[
                {
                    "type":JournalEntryLine.TYPE_DEBIT,
                    "amount":50000,
                    "account":Account.objects.get(name='Cash').slug,
                }, {
                    "type":JournalEntryLine.TYPE_CREDIT,
                    "amount":50000,
                    "account":Account.objects.get(name='Common Stock').slug,
                }
            ],
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        journal_entry = JournalEntry.objects.get(slug=response.data['slug'])
        self.assertTrue(journal_entry.is_adjusting_entry)
        self.assertFalse(journal_entry.is_closing_entry)



    def test_user_cant_create_entry_with_diplicate_account(self):
        """ Test that a user cannot create an entry that uses the same account more than once.
        """
        Account.objects.create_default_accounts(self.company)
        url = reverse('je-new')
        data = {
            'date':"2020-01-15",
            'memo':'investing in biz with common stock',
            'period':self.period.slug,
            'is_adjusting_entry':True,
            'journal_entry_lines':[
                {
                    "type":JournalEntryLine.TYPE_DEBIT,
                    "amount":45000,
                    "account":Account.objects.get(name='Cash').slug,
                }, {
                    "type":JournalEntryLine.TYPE_DEBIT,
                    "amount":500,
                    "account":Account.objects.get(name='Common Stock').slug,
                }, {
                    "type":JournalEntryLine.TYPE_CREDIT,
                    "amount":50000,
                    "account":Account.objects.get(name='Common Stock').slug,
                }
            ],
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'account': 'cannot use more than once'})


    def test_user_can_create_closing_entry(self):
        """ Test that a user can create a closing journal entry with 1 DR account and 1 CR account
        """
        Account.objects.create_default_accounts(self.company)
        url = reverse('je-new')
        data = {
            'date':"2020-01-15",
            'memo':'investing in biz with common stock',
            'period':self.period.slug,
            'is_closing_entry':True,
            'journal_entry_lines':[
                {
                    "type":JournalEntryLine.TYPE_DEBIT,
                    "amount":50000,
                    "account":Account.objects.get(name='Cash').slug,
                }, {
                    "type":JournalEntryLine.TYPE_CREDIT,
                    "amount":50000,
                    "account":Account.objects.get(name='Common Stock').slug,
                }
            ],
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        journal_entry = JournalEntry.objects.get(slug=response.data['slug'])
        self.assertFalse(journal_entry.is_adjusting_entry)
        self.assertTrue(journal_entry.is_closing_entry)


    def test_user_can_create_entry_multiple_dr_and_cr_accounts(self):
        """ Test that a user can create journal entry with 2+ DR account and 2+ CR account
        """
        Account.objects.create_default_accounts(self.company)
        url = reverse('je-new')
        data = {
            'date':"2020-01-15",
            'memo':'investing in biz with common stock and prepaid services',
            'period':self.period.slug,
            'journal_entry_lines':[
                {
                    "type":JournalEntryLine.TYPE_DEBIT,
                    "amount":40000,
                    "account":Account.objects.get(name='Cash').slug,
                }, {
                    "type":JournalEntryLine.TYPE_DEBIT,
                    "amount":20000,
                    "account":Account.objects.get(name='Prepaid Expenses').slug,
                }, {
                    "type":JournalEntryLine.TYPE_CREDIT,
                    "amount":50000,
                    "account":Account.objects.get(name='Common Stock').slug,
                }, {
                    "type":JournalEntryLine.TYPE_CREDIT,
                    "amount":10000,
                    "account":Account.objects.get(name='APIC').slug,
                }
            ],
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        journal_entry = JournalEntry.objects.get(slug=response.data['slug'])
        
        self.assertEqual(journal_entry.date, dt.date(2020, 1, 15))
        self.assertEqual(journal_entry.memo, 'investing in biz with common stock and prepaid services')
        self.assertEqual(journal_entry.period, self.period)
        self.assertFalse(journal_entry.is_adjusting_entry)
        self.assertFalse(journal_entry.is_closing_entry)
        self.assertEqual(journal_entry.dr_total, 60000)
        self.assertEqual(journal_entry.cr_total, 60000)  

        self.assertEqual(journal_entry.lines.count(), 4)
        cr_line_1 = journal_entry.lines.get(type=JournalEntryLine.TYPE_CREDIT, amount=50000)
        cr_line_2 = journal_entry.lines.get(type=JournalEntryLine.TYPE_CREDIT, amount=10000)
        dr_line_1 = journal_entry.lines.get(type=JournalEntryLine.TYPE_DEBIT, amount=40000)
        dr_line_2 = journal_entry.lines.get(type=JournalEntryLine.TYPE_DEBIT, amount=20000)

        self.assertEqual(cr_line_1.account, Account.objects.get(name='Common Stock'))
        self.assertEqual(cr_line_2.account, Account.objects.get(name='APIC'))
        self.assertEqual(dr_line_1.account, Account.objects.get(name='Cash'))
        self.assertEqual(dr_line_2.account, Account.objects.get(name='Prepaid Expenses'))


    def test_user_cant_create_an_entry_using_another_users_period(self):
        """ Test that a user cannot create an entry using another user's period
        """
        Account.objects.create_default_accounts(self.company)
        url = reverse('je-new')
        data = {
            'date':"2020-01-15",
            'memo':'investing in biz with common stock',
            'period':self.other_period.slug,
            'is_closing_entry':True,
            'journal_entry_lines':[
                {
                    "type":JournalEntryLine.TYPE_DEBIT,
                    "amount":50000,
                    "account":Account.objects.get(name='Cash').slug,
                }, {
                    "type":JournalEntryLine.TYPE_CREDIT,
                    "amount":50000,
                    "account":Account.objects.get(name='Common Stock').slug,
                }
            ],
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'period': 'period not found'})


    def test_user_cant_create_an_entry_using_another_users_account(self):
        """ Test that a user cannot create an entry using another user's account
        """
        Account.objects.create_default_accounts(self.other_company)
        url = reverse('je-new')
        data = {
            'date':"2020-01-15",
            'memo':'investing in biz with common stock',
            'period':self.period.slug,
            'is_closing_entry':True,
            'journal_entry_lines':[
                {
                    "type":JournalEntryLine.TYPE_DEBIT,
                    "amount":50000,
                    "account":Account.objects.get(name='Cash').slug,
                }, {
                    "type":JournalEntryLine.TYPE_CREDIT,
                    "amount":50000,
                    "account":Account.objects.get(name='Common Stock').slug,
                }
            ],
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'account': 'account not found'})

    def test_user_cant_create_an_entry_using_another_companys_account(self):
        """ Test that a user cannot create an entry using accounts associated with a different company
        """
        another_company = self.factory.create_company(self.user)
        Account.objects.create_default_accounts(another_company)

        url = reverse('je-new')
        data = {
            'date':"2020-01-15",
            'memo':'investing in biz with common stock',
            'period':self.period.slug,
            'is_closing_entry':True,
            'journal_entry_lines':[
                {
                    "type":JournalEntryLine.TYPE_DEBIT,
                    "amount":50000,
                    "account":Account.objects.get(name='Cash').slug,
                }, {
                    "type":JournalEntryLine.TYPE_CREDIT,
                    "amount":50000,
                    "account":Account.objects.get(name='Common Stock').slug,
                }
            ],
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'account': 'account belongs to another company'})


    def test_user_cant_create_entry_with_0_dollar_amounts(self):
        """ Test that a user cant create journal entries with 0 changes
        """
        Account.objects.create_default_accounts(self.company)
        url = reverse('je-new')
        data = {
            'date':"2020-01-15",
            'memo':'investing in biz with common stock',
            'period':self.period.slug,
            'journal_entry_lines':[
                {
                    "type":JournalEntryLine.TYPE_DEBIT,
                    "amount":0,
                    "account":Account.objects.get(name='Cash').slug,
                }, {
                    "type":JournalEntryLine.TYPE_CREDIT,
                    "amount":0,
                    "account":Account.objects.get(name='Common Stock').slug,
                }
            ],
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'dr/cr balance': 'zero changes in balance'})


    def test_user_cant_create_entry_with_negative_dollar_amounts(self):
        """ Test that a user cant create journal entries with negative values
        """
        Account.objects.create_default_accounts(self.company)
        url = reverse('je-new')
        data = {
            'date':"2020-01-15",
            'memo':'investing in biz with common stock',
            'period':self.period.slug,
            'journal_entry_lines':[
                {
                    "type":JournalEntryLine.TYPE_DEBIT,
                    "amount":-5000,
                    "account":Account.objects.get(name='Cash').slug,
                }, {
                    "type":JournalEntryLine.TYPE_CREDIT,
                    "amount":-5000,
                    "account":Account.objects.get(name='Common Stock').slug,
                }
            ],
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_user_cant_create_entry_with_unequal_dr_cr_amounts(self):
        """ Test that a user cant create journal entries with unequal dr/cr amounts
        """
        Account.objects.create_default_accounts(self.company)
        url = reverse('je-new')
        data = {
            'date':"2020-01-15",
            'memo':'investing in biz with common stock',
            'period':self.period.slug,
            'journal_entry_lines':[
                {
                    "type":JournalEntryLine.TYPE_DEBIT,
                    "amount":5000,
                    "account":Account.objects.get(name='Cash').slug,
                }, {
                    "type":JournalEntryLine.TYPE_CREDIT,
                    "amount":6000,
                    "account":Account.objects.get(name='Common Stock').slug,
                }
            ],
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'dr/cr balance': 'debits dont match credits'})


    def test_user_cant_create_entry_with_date_outside_period(self):
        """ Test that a user cant create journal entries with dates outside the period boundary
        """
        Account.objects.create_default_accounts(self.company)
        url = reverse('je-new')
        data = {
            'date':"2020-04-15",
            'memo':'investing in biz with common stock',
            'period':self.period.slug,
            'journal_entry_lines':[
                {
                    "type":JournalEntryLine.TYPE_DEBIT,
                    "amount":5000,
                    "account":Account.objects.get(name='Cash').slug,
                }, {
                    "type":JournalEntryLine.TYPE_CREDIT,
                    "amount":5000,
                    "account":Account.objects.get(name='Common Stock').slug,
                }
            ],
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"date":"entry date does not fall within period"})


    def test_user_cant_create_entry_if_user_is_at_journal_entry_object_limit(self):
        """ Test that a user cant create journal entries of doing so would violate their
            object limit.
        """
        self.user_profile.object_limit_entries_per_period = 0
        self.user_profile.save(update_fields=['object_limit_entries_per_period'])

        Account.objects.create_default_accounts(self.company)
        url = reverse('je-new')
        data = {
            'date':"2020-01-15",
            'memo':'investing in biz with common stock',
            'period':self.period.slug,
            'journal_entry_lines':[
                {
                    "type":JournalEntryLine.TYPE_DEBIT,
                    "amount":5000,
                    "account":Account.objects.get(name='Cash').slug,
                }, {
                    "type":JournalEntryLine.TYPE_CREDIT,
                    "amount":5000,
                    "account":Account.objects.get(name='Common Stock').slug,
                }
            ],
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"object limit":"cannot create additional entries for this period"})


    def test_user_can_delete_own_journal_entries(self):
        """ Test that a user can delete their own journal entries
        """
        Account.objects.create_default_accounts(self.company)
        je = self.factory.create_journal_entry(self.period, dt.date(2020, 1, 15))
        self.factory.create_journal_entry_line(
            je, Account.objects.get(name='Cash'), 'd', 5000)
        self.factory.create_journal_entry_line(
            je, Account.objects.get(name='Common Stock'), JournalEntryLine.TYPE_CREDIT, 5000)
        
        self.assertEqual(JournalEntry.objects.count(), 1)
        self.assertEqual(JournalEntryLine.objects.count(), 2)

        url = reverse("je-delete", kwargs={'slug':je.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(JournalEntry.objects.count(), 0)
        self.assertEqual(JournalEntryLine.objects.count(), 0)


    def test_user_cant_delete_another_users_journal_entry(self):
        """ Test that a user cant delete another user's journal entry
        """
        Account.objects.create_default_accounts(self.other_company)
        je = self.factory.create_journal_entry(self.other_period, dt.date(2020, 1, 15))
        self.factory.create_journal_entry_line(
            je, Account.objects.get(name='Cash'), 'd', 5000)
        self.factory.create_journal_entry_line(
            je, Account.objects.get(name='Common Stock'), JournalEntryLine.TYPE_CREDIT, 5000)
        
        self.assertEqual(JournalEntry.objects.count(), 1)
        self.assertEqual(JournalEntryLine.objects.count(), 2)

        url = reverse("je-delete", kwargs={'slug':je.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(JournalEntry.objects.count(), 1)
        self.assertEqual(JournalEntryLine.objects.count(), 2)


    def test_user_cant_cant_list_journal_entries_for_another_users_period(self):
        """ Test that a user cant view a list of journal entries associated with another user's period
        """
        url = reverse("je-list", kwargs={'slug':self.other_period.slug})
        # can't see other user's entries
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # owner can see own entries
        self.client.force_login(self.other_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
