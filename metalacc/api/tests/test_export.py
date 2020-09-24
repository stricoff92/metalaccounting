
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from freezegun import freeze_time

from .base import BaseTestBase
from api.models import Company, Account, JournalEntryLine, JournalEntry, Period, UserProfile
from api.models.account import DEFAULT_ACCOUNTS


class ObjectExportViewTests(BaseTestBase):

    def setUp(self):
        super().setUp()

        self.third_user = User.objects.create_user(
            username="foobarrrrr",
            email=f'fooooorbbbbbaaaahhhhr@mail.com',
            password=self.PASSWORD_FACTORY)
        self.third_user_user_profile = UserProfile.objects.create(user=self.third_user)

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
    
    @freeze_time("2012-01-14 03:21:34")
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

        # other_user now has a copy of the company, with user history
        new_company = Company.objects.get(slug=response.data['slug'])
        self.assertEqual(new_company.user, self.other_user)
        self.assertNotEqual(new_company.id, self.company.id)
        self.assertEqual(new_company.name, self.company.name)
        self.assertEqual(
            new_company.user_fingerprints,
            [
                {'user_hash':self.user.userprofile.slug,'event':'export', 'timestamp': '1326511294'},
                {'user_hash':self.other_user.userprofile.slug, 'event':'import', 'timestamp': '1326511294'}
            ])

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


    def test_a_companys_previous_export_history_is_included_when_an_imported_company_is_exported(self):
        """ Test that if a user exports a company they had originally imported the original export and import are included
            in the history
        """
        # 1st user exports company info to serialized data
        url = reverse("app-company-export", kwargs={"slug":self.company.slug})
        with freeze_time("2012-01-14 03:21:34"):
            response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        signed_jwt = response.content.decode()
        self.assertTrue(len(signed_jwt) > 0)

        # 2nd user imports the company
        self.client.force_login(self.other_user)
        url = reverse("company-import")
        data = {
            'data':signed_jwt,
        }
        with freeze_time("2012-01-14 03:25:34"):
            response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        second_company = Company.objects.get(slug=response.data['slug'])

        # second user exports the company
        url = reverse("app-company-export", kwargs={"slug":second_company.slug})
        with freeze_time("2012-01-14 03:28:34"):
            response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        signed_jwt = response.content.decode()
        self.assertTrue(len(signed_jwt) > 0)


        # 3nd user imports the company
        self.client.force_login(self.third_user)
        url = reverse("company-import")
        data = {
            'data':signed_jwt,
        }
        with freeze_time("2012-01-14 03:32:34"):
            response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        third_company = Company.objects.get(slug=response.data['slug'])

        self.assertEqual(len(third_company.user_fingerprints), 4)
        self.assertEqual(len(set(r['user_hash'] for r in third_company.user_fingerprints)), 3)

        # 3rd user exports the company
        url = reverse("app-company-export", kwargs={"slug":third_company.slug})
        with freeze_time("2012-01-14 03:46:34"):
            response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        signed_jwt = response.content.decode()
        self.assertTrue(len(signed_jwt) > 0)


        # View company history
        data = {
            'data':signed_jwt,
        }
        url = reverse("company-export-history")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            [
                {'user_hash': self.user.userprofile.slug, 'timestamp': '1326511294', 'event': 'export'},
                {'user_hash': self.other_user.userprofile.slug, 'timestamp': '1326511534', 'event': 'import'},
                {'user_hash': self.other_user.userprofile.slug, 'timestamp': '1326511714', 'event': 'export'},
                {'user_hash': self.third_user.userprofile.slug, 'timestamp': '1326511954', 'event': 'import'},
                {'user_hash': self.third_user.userprofile.slug, 'timestamp': '1326512794', 'event': 'export'}
            ])
