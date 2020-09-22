
import datetime as dt
import json

from django.urls import reverse
from rest_framework import status

from .base import BaseTestBase
from api.models import Period, CashFlowWorksheet, Account, JournalEntryLine


class CashFlowWorksheetTests(BaseTestBase):

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

        self.company = self.factory.create_company(self.user)
        self.period = self.factory.create_period(self.company, "2020-01-01", "2020-03-31")
        Account.objects.create_default_accounts(self.company)

        # Create journal Entries.

        # Cash for Common Stock.
        self.jounral_entry_1 = self.factory.create_journal_entry(self.period, "2020-01-02")
        self.je1_jel1 = self.factory.create_journal_entry_line(
            self.jounral_entry_1,
            Account.objects.get(name="Cash"), JournalEntryLine.TYPE_DEBIT, 50000)
        self.je1_jel2 = self.factory.create_journal_entry_line(
            self.jounral_entry_1,
            Account.objects.get(name="Common Stock"), JournalEntryLine.TYPE_CREDIT, 50000)

        # Inventory for Cash and credit.
        self.jounral_entry_2 = self.factory.create_journal_entry(self.period, "2020-01-03")
        self.je2_jel1 = self.factory.create_journal_entry_line(
            self.jounral_entry_2,
            Account.objects.get(name="Inventory"), JournalEntryLine.TYPE_DEBIT, 20000)
        self.je2_jel2 = self.factory.create_journal_entry_line(
            self.jounral_entry_2,
            Account.objects.get(name="Cash"), JournalEntryLine.TYPE_CREDIT, 5000)
        self.je2_jel3 = self.factory.create_journal_entry_line(
            self.jounral_entry_2,
            Account.objects.get(name="A/P"), JournalEntryLine.TYPE_CREDIT, 15000)

        # Bought a Truck.
        self.jounral_entry_3 = self.factory.create_journal_entry(self.period, "2020-01-04")
        self.je3_jel1 = self.factory.create_journal_entry_line(
            self.jounral_entry_3,
            Account.objects.get(name="PPE"), JournalEntryLine.TYPE_DEBIT, 125000)
        self.je3_jel2 = self.factory.create_journal_entry_line(
            self.jounral_entry_3,
            Account.objects.get(name="Debt: Long Term"), JournalEntryLine.TYPE_CREDIT, 120000)
        self.je3_jel3 = self.factory.create_journal_entry_line(
            self.jounral_entry_3,
            Account.objects.get(name="Cash"), JournalEntryLine.TYPE_CREDIT, 5000)

        # Sold some inventory for a profit
        self.jounral_entry_4 = self.factory.create_journal_entry(self.period, "2020-01-05")
        self.je4_jel1 = self.factory.create_journal_entry_line(
            self.jounral_entry_4,
            Account.objects.get(name="Cash"), JournalEntryLine.TYPE_DEBIT, 6500)
        self.je4_jel2 = self.factory.create_journal_entry_line(
            self.jounral_entry_4,
            Account.objects.get(name="CoGS"), JournalEntryLine.TYPE_DEBIT, 12500)
        self.je4_jel3 = self.factory.create_journal_entry_line(
            self.jounral_entry_4,
            Account.objects.get(name="A/R"), JournalEntryLine.TYPE_DEBIT, 10000)

        self.je4_jel4 = self.factory.create_journal_entry_line(
            self.jounral_entry_4,
            Account.objects.get(name="Sales Revenue"), JournalEntryLine.TYPE_CREDIT, 16500)
        self.je4_jel5 = self.factory.create_journal_entry_line(
            self.jounral_entry_4,
            Account.objects.get(name="Inventory"), JournalEntryLine.TYPE_CREDIT, 12500)

        # Pay off some part of the truck
        self.jounral_entry_5 = self.factory.create_journal_entry(self.period, "2020-01-06")
        self.je5_jel1 = self.factory.create_journal_entry_line(
            self.jounral_entry_5,
            Account.objects.get(name="Debt: Long Term"), JournalEntryLine.TYPE_DEBIT, 2000)
        self.je5_jel2 = self.factory.create_journal_entry_line(
            self.jounral_entry_5,
            Account.objects.get(name="Interest Expenses"), JournalEntryLine.TYPE_DEBIT, 200)
        self.je5_jel3 = self.factory.create_journal_entry_line(
            self.jounral_entry_5,
            Account.objects.get(name="Cash"), JournalEntryLine.TYPE_CREDIT, 2200)

        # Sold some inventory on credit
        self.jounral_entry_6 = self.factory.create_journal_entry(self.period, "2020-01-07")
        self.je6_jel1 = self.factory.create_journal_entry_line(
            self.jounral_entry_6,
            Account.objects.get(name="CoGS"), JournalEntryLine.TYPE_DEBIT, 5000)
        self.je6_jel2 = self.factory.create_journal_entry_line(
            self.jounral_entry_6,
            Account.objects.get(name="A/R"), JournalEntryLine.TYPE_DEBIT, 7500)
        self.je6_jel3 = self.factory.create_journal_entry_line(
            self.jounral_entry_6,
            Account.objects.get(name="Sales Revenue"), JournalEntryLine.TYPE_CREDIT, 7500)
        self.je6_jel4 = self.factory.create_journal_entry_line(
            self.jounral_entry_6,
            Account.objects.get(name="Inventory"), JournalEntryLine.TYPE_CREDIT, 5000)

        # record depreciation on truck
        self.jounral_entry_7 = self.factory.create_journal_entry(
            self.period, "2020-01-08", is_adjusting_entry=True)
        self.je7_jel1 = self.factory.create_journal_entry_line(
            self.jounral_entry_7,
            Account.objects.get(name="Depreciation Expenses"), JournalEntryLine.TYPE_DEBIT, 4000)
        self.je7_jel1 = self.factory.create_journal_entry_line(
            self.jounral_entry_7,
            Account.objects.get(name="Accumulated Depreciation"), JournalEntryLine.TYPE_CREDIT, 4000)

    
    def tearDown(self):
        super().tearDown()


    def test_user_cant_create_a_cashflow_worksheet_for_a_period_if_one_already_exists_and_is_in_sync(self):
        """ Test that a user cant create a cashflow worksheet if one already exists and is in sync
        """
        existing_cash_flow_worksheet = self.factory.create_cashflow_worksheet(self.period)
        url = reverse("period-create-cashflow-worksheet", kwargs={"slug":self.period.slug})

        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)


    def test_user_can_create_a_cashflow_worksheet_for_a_period_if_one_already_exists_and_is_not_in_sync(self):
        """ Test that a out of sync worksheets are deleted when the user tries to create a new cashflow worksheet
            (successfully or not)
        """
        existing_cash_flow_worksheet = self.factory.create_cashflow_worksheet(self.period)
        existing_cash_flow_worksheet.version_hash = "asdasdasdasd"
        existing_cash_flow_worksheet.save()
        original_cfw_id = existing_cash_flow_worksheet.id

        url = reverse("period-create-cashflow-worksheet", kwargs={"slug":self.period.slug})

        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Out of sync cash flow worksheet was deleted.
        self.assertFalse(CashFlowWorksheet.objects.filter(id=original_cfw_id).exists())


    def test_user_can_create_a_cashflow_worksheet_with_valid_data(self):
        """ Test that a user can create a worksheet by submitting valid worksheet data.
        """

        url = reverse("period-create-cashflow-worksheet", kwargs={"slug":self.period.slug})
        data = [
            {
                # Cash for Common Stock.
                'journal_entry_slug':self.jounral_entry_1.slug,
                'operations':0,
                'investments':0,
                'finances':50000,
            },{
                # Inventory for Cash and credit.
                'journal_entry_slug':self.jounral_entry_2.slug,
                'operations':5000,
                'investments':0,
                'finances':0,
            },{
                # Bought a Truck.
                'journal_entry_slug':self.jounral_entry_3.slug,
                'operations':0,
                'investments':5000,
                'finances':0,
            },{
                # Sold some inventory for a profit
                'journal_entry_slug':self.jounral_entry_4.slug,
                'operations':6500,
                'investments':0,
                'finances':0,
            },{
                # Pay off some part of the truck
                'journal_entry_slug':self.jounral_entry_5.slug,
                'operations':200,
                'investments':0,
                'finances':2000,
            },
            # NON CASH TRANSACTIONS
            # {
            #     'journal_entry_slug':self.jounral_entry_6.slug,
            #     'operations':0,
            #     'investments':0,
            #     'finances':0,
            # },
            # {
            #     'journal_entry_slug':self.jounral_entry_7.slug,
            #     'operations':0,
            #     'investments':0,
            #     'finances':0,
            # },
        ]

        self.assertEqual(CashFlowWorksheet.objects.count(), 0)
        response = self.client.post(
            url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CashFlowWorksheet.objects.count(), 1)

        cfws = CashFlowWorksheet.objects.first()
        self.assertEqual(cfws.period, self.period)
        self.assertEqual(cfws.version_hash, self.period.version_hash)

        cfws_data = cfws.worksheet_data
        cfws_data = {row['journal_entry']:row for row in cfws_data}
        self.assertEqual(len(cfws_data), 5)

        self.assertEqual(
            cfws_data[self.jounral_entry_1.slug],
            {
                'journal_entry':self.jounral_entry_1.slug,
                'operations':0,
                'investments':0,
                'finances':50000,
            })
        self.assertEqual(
            cfws_data[self.jounral_entry_2.slug],
            {
                'journal_entry':self.jounral_entry_2.slug,
                'operations':5000,
                'investments':0,
                'finances':0,
            })
        self.assertEqual(
            cfws_data[self.jounral_entry_3.slug],
            {
                'journal_entry':self.jounral_entry_3.slug,
                'operations':0,
                'investments':5000,
                'finances':0,
            })
        self.assertEqual(
            cfws_data[self.jounral_entry_4.slug],
            {
                'journal_entry':self.jounral_entry_4.slug,
                'operations':6500,
                'investments':0,
                'finances':0,
            })
        self.assertEqual(
            cfws_data[self.jounral_entry_5.slug],
            {
                'journal_entry':self.jounral_entry_5.slug,
                'operations':200,
                'investments':0,
                'finances':2000,
            })


    def test_user_cant_create_a_cashflow_worksheet_with_extra_journal_entry_data(self):
        """ Test that a user cant create a worksheet by submitted a non cash journal entry.
        """
        url = reverse("period-create-cashflow-worksheet", kwargs={"slug":self.period.slug})
        data = [
            {
                # Cash for Common Stock.
                'journal_entry_slug':self.jounral_entry_1.slug,
                'operations':0,
                'investments':0,
                'finances':50000,
            },{
                # Inventory for Cash and credit.
                'journal_entry_slug':self.jounral_entry_2.slug,
                'operations':5000,
                'investments':0,
                'finances':0,
            },{
                # Bought a Truck.
                'journal_entry_slug':self.jounral_entry_3.slug,
                'operations':0,
                'investments':5000,
                'finances':0,
            },{
                # Sold some inventory for a profit
                'journal_entry_slug':self.jounral_entry_4.slug,
                'operations':6500,
                'investments':0,
                'finances':0,
            },{
                # Pay off some part of the truck
                'journal_entry_slug':self.jounral_entry_5.slug,
                'operations':200,
                'investments':0,
                'finances':2000,
            },
            # (Erroneously including a NON CASH TRANSACTIONS
            {
                'journal_entry_slug':self.jounral_entry_6.slug,
                'operations':0,
                'investments':0,
                'finances':0,
            },
            # {
            #     'journal_entry_slug':self.jounral_entry_7.slug,
            #     'operations':0,
            #     'investments':0,
            #     'finances':0,
            # },
        ]

        self.assertEqual(CashFlowWorksheet.objects.count(), 0)
        response = self.client.post(
            url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CashFlowWorksheet.objects.count(), 0)

        self.assertTrue(f"journal entry slug missing:{self.jounral_entry_6.slug}" in response.data)


    def test_user_cant_create_a_cashflow_worksheet_when_they_leave_off_a_cash_journal_entry(self):
        """ Test that a user cant create a worksheet when excluding a cash journal entry.
        """
        url = reverse("period-create-cashflow-worksheet", kwargs={"slug":self.period.slug})
        data = [
            {
                # Cash for Common Stock.
                'journal_entry_slug':self.jounral_entry_1.slug,
                'operations':0,
                'investments':0,
                'finances':50000,
            },
            # {
            #     # Inventory for Cash and credit. Erroneously EXCLUDE THIS ENTRY
            #     'journal_entry_slug':self.jounral_entry_2.slug,
            #     'operations':5000,
            #     'investments':0,
            #     'finances':0,
            # },
            {
                # Bought a Truck.
                'journal_entry_slug':self.jounral_entry_3.slug,
                'operations':0,
                'investments':5000,
                'finances':0,
            },{
                # Sold some inventory for a profit
                'journal_entry_slug':self.jounral_entry_4.slug,
                'operations':6500,
                'investments':0,
                'finances':0,
            },{
                # Pay off some part of the truck
                'journal_entry_slug':self.jounral_entry_5.slug,
                'operations':200,
                'investments':0,
                'finances':2000,
            },
            #  NON CASH TRANSACTIONS
            # {
            #     'journal_entry_slug':self.jounral_entry_6.slug,
            #     'operations':0,
            #     'investments':0,
            #     'finances':0,
            # },
            # {
            #     'journal_entry_slug':self.jounral_entry_7.slug,
            #     'operations':0,
            #     'investments':0,
            #     'finances':0,
            # },
        ]

        self.assertEqual(CashFlowWorksheet.objects.count(), 0)
        response = self.client.post(
            url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CashFlowWorksheet.objects.count(), 0)
        self.assertTrue(f"Journal Entries missing: {self.jounral_entry_2.slug}" in response.data)


    def test_user_cant_create_a_cashflow_worksheet_if_allocated_cash_is_too_low(self):
        """ Test that a user cant create a worksheet when they didnt allocate enough cash for an entry
        """
        url = reverse("period-create-cashflow-worksheet", kwargs={"slug":self.period.slug})
        data = [
            {
                # Cash for Common Stock.
                'journal_entry_slug':self.jounral_entry_1.slug,
                'operations':0,
                'investments':0,
                'finances':50000,
            },
            {
                # Inventory for Cash and credit.
                'journal_entry_slug':self.jounral_entry_2.slug,
                'operations':5000,
                'investments':0,
                'finances':0,
            },
            {
                # Bought a Truck.
                'journal_entry_slug':self.jounral_entry_3.slug,
                'operations':1,
                'investments':0, # NOT ENOUGH CASH ALLOCATED (1 dollar short)
                'finances':4998,
            },{
                # Sold some inventory for a profit
                'journal_entry_slug':self.jounral_entry_4.slug,
                'operations':6500,
                'investments':0,
                'finances':0,
            },{
                # Pay off some part of the truck
                'journal_entry_slug':self.jounral_entry_5.slug,
                'operations':200,
                'investments':0,
                'finances':2000,
            },
            #  NON CASH TRANSACTIONS
            # {
            #     'journal_entry_slug':self.jounral_entry_6.slug,
            #     'operations':0,
            #     'investments':0,
            #     'finances':0,
            # },
            # {
            #     'journal_entry_slug':self.jounral_entry_7.slug,
            #     'operations':0,
            #     'investments':0,
            #     'finances':0,
            # },
        ]

        self.assertEqual(CashFlowWorksheet.objects.count(), 0)
        response = self.client.post(
            url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CashFlowWorksheet.objects.count(), 0)
        self.assertTrue(f"journal entry {self.jounral_entry_3.slug} has been allocated cash incorrectly" in response.data)


    def test_user_cant_create_a_cashflow_worksheet_if_allocated_cash_is_too_high(self):
        """ Test that a user cant create a worksheet when they allocated too much cash for an entry
        """
        url = reverse("period-create-cashflow-worksheet", kwargs={"slug":self.period.slug})
        data = [
            {
                # Cash for Common Stock.
                'journal_entry_slug':self.jounral_entry_1.slug,
                'operations':0,
                'investments':0,
                'finances':50000,
            },
            {
                # Inventory for Cash and credit.
                'journal_entry_slug':self.jounral_entry_2.slug,
                'operations':5000,
                'investments':0,
                'finances':0,
            },
            {
                # Bought a Truck.
                'journal_entry_slug':self.jounral_entry_3.slug,
                'operations':1,
                'investments':5000, # TOO MUCH CASH ALLOCATED (1 dollar over)
                'finances':0,
            },{
                # Sold some inventory for a profit
                'journal_entry_slug':self.jounral_entry_4.slug,
                'operations':6500,
                'investments':0,
                'finances':0,
            },{
                # Pay off some part of the truck
                'journal_entry_slug':self.jounral_entry_5.slug,
                'operations':200,
                'investments':0,
                'finances':2000,
            },
            #  NON CASH TRANSACTIONS
            # {
            #     'journal_entry_slug':self.jounral_entry_6.slug,
            #     'operations':0,
            #     'investments':0,
            #     'finances':0,
            # },
            # {
            #     'journal_entry_slug':self.jounral_entry_7.slug,
            #     'operations':0,
            #     'investments':0,
            #     'finances':0,
            # },
        ]

        self.assertEqual(CashFlowWorksheet.objects.count(), 0)
        response = self.client.post(
            url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CashFlowWorksheet.objects.count(), 0)
        self.assertTrue(f"journal entry {self.jounral_entry_3.slug} has been allocated cash incorrectly" in response.data)


    def test_user_cant_create_a_cashflow_worksheet_for_another_users_period(self):
        """ Test that a user can create a worksheet by submitting valid worksheet data.
        """
        self.client.force_login(self.other_user)

        url = reverse("period-create-cashflow-worksheet", kwargs={"slug":self.period.slug})
        data = [
            {
                # Cash for Common Stock.
                'journal_entry_slug':self.jounral_entry_1.slug,
                'operations':0,
                'investments':0,
                'finances':50000,
            },{
                # Inventory for Cash and credit.
                'journal_entry_slug':self.jounral_entry_2.slug,
                'operations':5000,
                'investments':0,
                'finances':0,
            },{
                # Bought a Truck.
                'journal_entry_slug':self.jounral_entry_3.slug,
                'operations':0,
                'investments':5000,
                'finances':0,
            },{
                # Sold some inventory for a profit
                'journal_entry_slug':self.jounral_entry_4.slug,
                'operations':6500,
                'investments':0,
                'finances':0,
            },{
                # Pay off some part of the truck
                'journal_entry_slug':self.jounral_entry_5.slug,
                'operations':200,
                'investments':0,
                'finances':2000,
            },
            # NON CASH TRANSACTIONS
            # {
            #     'journal_entry_slug':self.jounral_entry_6.slug,
            #     'operations':0,
            #     'investments':0,
            #     'finances':0,
            # },
            # {
            #     'journal_entry_slug':self.jounral_entry_7.slug,
            #     'operations':0,
            #     'investments':0,
            #     'finances':0,
            # },
        ]

        # other user has no access
        self.assertEqual(CashFlowWorksheet.objects.count(), 0)
        response = self.client.post(
            url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # owner can create
        self.client.force_login(self.user)
        response = self.client.post(
            url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)



    def test_user_cant_create_a_cashflow_worksheet_with_journal_entries_from_another_period(self):
        """ Test that a user cant create a worksheet for period A by submitting Journal entries from period B.
        """
        
        # Pay off some part of the truck in another period
        other_period = self.factory.create_period(self.company, "2020-04-01", "2020-06-30")
        other_jounral_entry = self.factory.create_journal_entry(other_period, "2020-04-06")
        other_jel_1 = self.factory.create_journal_entry_line(
            other_jounral_entry,
            Account.objects.get(name="Debt: Long Term"), JournalEntryLine.TYPE_DEBIT, 1000)
        other_jel_2 = self.factory.create_journal_entry_line(
            other_jounral_entry,
            Account.objects.get(name="Interest Expenses"), JournalEntryLine.TYPE_DEBIT, 100)
        other_jel_3 = self.factory.create_journal_entry_line(
            other_jounral_entry,
            Account.objects.get(name="Cash"), JournalEntryLine.TYPE_CREDIT, 1100)

        url = reverse("period-create-cashflow-worksheet", kwargs={"slug":self.period.slug})
        data = [
            {
                # Paid off part of the truck # EXTRA ENTRY FROM WRONG PERIOD
                'journal_entry_slug':other_jounral_entry.slug,
                'operations':0,
                'investments':0,
                'finances':1100,
            }, {
                # Cash for Common Stock.
                'journal_entry_slug':self.jounral_entry_1.slug,
                'operations':0,
                'investments':0,
                'finances':50000,
            },{
                # Inventory for Cash and credit.
                'journal_entry_slug':self.jounral_entry_2.slug,
                'operations':5000,
                'investments':0,
                'finances':0,
            },{
                # Bought a Truck.
                'journal_entry_slug':self.jounral_entry_3.slug,
                'operations':0,
                'investments':5000,
                'finances':0,
            },{
                # Sold some inventory for a profit
                'journal_entry_slug':self.jounral_entry_4.slug,
                'operations':6500,
                'investments':0,
                'finances':0,
            },{
                # Pay off some part of the truck
                'journal_entry_slug':self.jounral_entry_5.slug,
                'operations':200,
                'investments':0,
                'finances':2000,
            },
            # NON CASH TRANSACTIONS
            # {
            #     'journal_entry_slug':self.jounral_entry_6.slug,
            #     'operations':0,
            #     'investments':0,
            #     'finances':0,
            # },
            # {
            #     'journal_entry_slug':self.jounral_entry_7.slug,
            #     'operations':0,
            #     'investments':0,
            #     'finances':0,
            # },
        ]

        self.assertEqual(CashFlowWorksheet.objects.count(), 0)
        response = self.client.post(
            url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Drop that extra entry and try again.
        data = data[1:]
        response = self.client.post(
            url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CashFlowWorksheet.objects.count(), 1)


    def test_user_cant_create_a_cashflow_worksheet_with_netagive_numbers(self):
        """ Test that a user can create a worksheet by submitting valid worksheet data.
        """

        url = reverse("period-create-cashflow-worksheet", kwargs={"slug":self.period.slug})
        data = [
            {
                # Cash for Common Stock.
                'journal_entry_slug':self.jounral_entry_1.slug,
                'operations':0,
                'investments':0,
                'finances':50000,
            },{
                # Inventory for Cash and credit.
                'journal_entry_slug':self.jounral_entry_2.slug,
                'operations':5000,
                'investments':0,
                'finances':0,
            },{
                # Bought a Truck.
                'journal_entry_slug':self.jounral_entry_3.slug,
                'operations':0,
                'investments':5000,
                'finances':0,
            },{
                # Sold some inventory for a profit
                'journal_entry_slug':self.jounral_entry_4.slug,
                'operations':6500,
                'investments':0,
                'finances':0,
            },{
                # Pay off some part of the truck
                'journal_entry_slug':self.jounral_entry_5.slug,
                'operations':-200, # NEGATIVE NUMBER
                'investments':0,
                'finances':2000,
            },
            # NON CASH TRANSACTIONS
            # {
            #     'journal_entry_slug':self.jounral_entry_6.slug,
            #     'operations':0,
            #     'investments':0,
            #     'finances':0,
            # },
            # {
            #     'journal_entry_slug':self.jounral_entry_7.slug,
            #     'operations':0,
            #     'investments':0,
            #     'finances':0,
            # },
        ]

        self.assertEqual(CashFlowWorksheet.objects.count(), 0)
        response = self.client.post(
            url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("operations must be greater than 0" in str(response.data))
