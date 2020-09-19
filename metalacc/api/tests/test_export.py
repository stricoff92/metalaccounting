
from django.urls import reverse
from rest_framework import status

from .base import BaseTestBase
from api.models import Company, Account, JournalEntryLine, JournalEntry, Period
from api.models.account import DEFAULT_ACCOUNTS


class ObjectExportViewTests(BaseTestBase):

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

        self.company = self.factory.create_company(self.user)
        self.accounts = Account.objects.create_default_accounts(self.company)
        self.period = self.factory.create_period(self.company, "2020-01-01", "2020-03-31")
    
        self.journal_entry = self.factory.create_journal_entry(self.period, "2020-01-01")
        self.jel1 = self.factory.create_journal_entry_line(
            self.journal_entry,
            Account.objects.get(name="Cash", user=self.user),
            JournalEntryLine.TYPE_DEBIT,
            1000000)
        self.jel2 = self.factory.create_journal_entry_line(
            self.journal_entry,
            Account.objects.get(name="Common Stock", user=self.user),
            JournalEntryLine.TYPE_CREDIT,
            1000000)
    
    def tearDown(self):
        super().tearDown()
    

    def test_a_company_and_its_objects_can_be_exported_and_imported_by_another_user(self):
        """ Test that a company can be exported by the owner, and reimported by any user
        """
        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(Period.objects.count(), 1)
        self.assertEqual(Account.objects.count(), len(DEFAULT_ACCOUNTS))
        self.assertEqual(JournalEntry.objects.count(), 1)
        self.assertEqual(JournalEntryLine.objects.count(), 2)

        # export company info to serialized data
        url = reverse("app-company-export", kwargs={"slug":self.company.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        signed_jwt = response.content.decode()
        self.assertTrue(len(signed_jwt) > 0)

        # authenticate as another user and import data
        self.client.force_login(self.other_user)
        url = reverse("company-import")
        data = {
            'data':signed_jwt,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Object counts doubled
        self.assertEqual(Company.objects.count(), 2)
        self.assertEqual(Period.objects.count(), 2)
        self.assertEqual(Account.objects.count(), 2 * len(DEFAULT_ACCOUNTS))
        self.assertEqual(JournalEntry.objects.count(), 2)
        self.assertEqual(JournalEntryLine.objects.count(), 4)

        # other_user now has a copy of the company
        new_company = Company.objects.get(slug=response.data['slug'])
        self.assertEqual(new_company.user, self.other_user)
        self.assertNotEqual(new_company.id, self.company.id)
        self.assertEqual(new_company.name, self.company.name)

        # other user has copy of accounts
        self.assertEqual(Account.objects.filter(user=self.other_user, company=new_company).count(), len(DEFAULT_ACCOUNTS))
        for account in Account.objects.filter(user=self.user):
            self.assertTrue(Account.objects.filter(
                user=self.other_user, 
                name=account.name, number=account.number,
                is_contra=account.is_contra, is_current=account.is_current, 
                is_operating=account.is_operating).exists())
        
        # other user has copy of periods
        self.assertEqual(Period.objects.filter(company=new_company).count(), 1)
        new_period = Period.objects.get(company=new_company)
        self.assertNotEqual(new_period.id, self.period.id)
        self.assertEqual(str(new_period.start), self.period.start)
        self.assertEqual(str(new_period.end), self.period.end)

        # other_user has a copy of journal entries
        self.assertEqual(JournalEntry.objects.filter(period=new_period).count(), 1)
        new_je = JournalEntry.objects.get(period=new_period)
        self.assertNotEqual(new_je.id, self.journal_entry.id)
        self.assertEqual(str(new_je.date), str(self.journal_entry.date))
        self.assertEqual(new_je.memo, self.journal_entry.memo)

        # Other_user has copy of journal entry lines
        jel_cash = JournalEntryLine.objects.get(journal_entry=new_je, type=JournalEntryLine.TYPE_DEBIT)
        jel_cs = JournalEntryLine.objects.get(journal_entry=new_je, type=JournalEntryLine.TYPE_CREDIT)

        self.assertNotEqual(jel_cash.id, self.jel1.id)
        self.assertEqual(jel_cash.amount, self.jel1.amount)
        self.assertNotEqual(jel_cs.id, self.jel2.id)
        self.assertEqual(jel_cs.amount, self.jel2.amount)


    def test_a_company_and_its_objects_can_be_exported_and_imported_by_same_user(self):
        """ Test that a company can be exported by the owner, and reimported by the same user
        """
        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(Period.objects.count(), 1)
        self.assertEqual(Account.objects.count(), len(DEFAULT_ACCOUNTS))
        self.assertEqual(JournalEntry.objects.count(), 1)
        self.assertEqual(JournalEntryLine.objects.count(), 2)

        # export company info to serialized data
        url = reverse("app-company-export", kwargs={"slug":self.company.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        signed_jwt = response.content.decode()
        self.assertTrue(len(signed_jwt) > 0)

        # reimport the company as a copy
        url = reverse("company-import")
        data = {
            'data':signed_jwt,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Object counts doubled
        self.assertEqual(Company.objects.count(), 2)
        self.assertEqual(Period.objects.count(), 2)
        self.assertEqual(Account.objects.count(), 2 * len(DEFAULT_ACCOUNTS))
        self.assertEqual(JournalEntry.objects.count(), 2)
        self.assertEqual(JournalEntryLine.objects.count(), 4)

        # user now has a copy of the company, with a different name
        new_company = Company.objects.get(slug=response.data['slug'])
        self.assertEqual(new_company.user, self.user)
        self.assertNotEqual(new_company.id, self.company.id)
        self.assertNotEqual(new_company.name, self.company.name)


    def test_a_user_cannot_export_another_users_company(self):
        """ Test that a user cannot export another user's company
        """
        self.client.force_login(self.other_user)
        url = reverse("app-company-export", kwargs={"slug":self.company.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_a_user_cannot_import_a_company_if_at_the_object_limit(self):
        """ Test that a user cannot import a company if they are already at the object limit for companies.
        """
        userprofile = self.other_user.userprofile
        userprofile.object_limit_companies = 0
        userprofile.save(update_fields=['object_limit_companies'])

        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(Period.objects.count(), 1)
        self.assertEqual(Account.objects.count(), len(DEFAULT_ACCOUNTS))
        self.assertEqual(JournalEntry.objects.count(), 1)
        self.assertEqual(JournalEntryLine.objects.count(), 2)

        # export company info to serialized data
        url = reverse("app-company-export", kwargs={"slug":self.company.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        signed_jwt = response.content.decode()
        self.assertTrue(len(signed_jwt) > 0)

        # authenticate as another user and import data
        self.client.force_login(self.other_user)
        url = reverse("company-import")
        data = {
            'data':signed_jwt,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("user cannot add additional companies" in str(response.data))
    