
import datetime as dt

from django.urls import reverse
from django.core.exceptions import ValidationError
from rest_framework import status

from .base import BaseTestBase
from api.models import Company, Account
from api.models.account import DEFAULT_ACCOUNTS


class AccountViewTests(BaseTestBase):

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

        self.company = self.factory.create_company(self.user)
        self.other_company = self.factory.create_company(self.other_user)
    
    def tearDown(self):
        super().tearDown()
    

    def test_user_can_create_an_account(self):
        """ Test user can create a current account
        """
        self.assertEqual(Account.objects.count(), 0)
        url = reverse("account-new")
        data = {
            'company':self.company.slug,
            'name':'foobar',
            'type':Account.TYPE_ASSET,
            'is_contra':False,
            'is_current':True,
            'number':1500,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Account.objects.count(), 1)

        account = Account.objects.first()
        self.assertEqual(account.name, "foobar")
        self.assertEqual(account.number, 1500)
        self.assertEqual(account.type, Account.TYPE_ASSET)
        self.assertEqual(account.company, self.company)
        self.assertEqual(account.user, self.user)
        self.assertFalse(account.is_contra)
        self.assertTrue(account.is_current)


    def test_user_can_create_an_non_current_account(self):
        """ Test user can create a non current account
        """
        self.assertEqual(Account.objects.count(), 0)
        url = reverse("account-new")
        data = {
            'company':self.company.slug,
            'name':'foobar',
            'type':Account.TYPE_ASSET,
            'is_contra':False,
            'is_current':False,
            'number':1500,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Account.objects.count(), 1)

        account = Account.objects.first()
        self.assertFalse(account.is_current)
        self.assertFalse(account.is_contra)


    def test_user_can_create_a_temporary_revenue_account(self):
        """ Test user can create a temporary revenue account
        """
        self.assertEqual(Account.objects.count(), 0)
        url = reverse("account-new")
        data = {
            'company':self.company.slug,
            'name':'foobar',
            'type':Account.TYPE_REVENUE,
            'is_contra':False,
            'number':4500,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Account.objects.count(), 1)

        account = Account.objects.first()
        self.assertEqual(account.type, Account.TYPE_REVENUE)
        self.assertFalse(account.is_contra)


    def test_user_can_create_a_temporary_expense_account(self):
        """ Test user can create a temporary expense account.
        """
        self.assertEqual(Account.objects.count(), 0)
        url = reverse("account-new")
        data = {
            'company':self.company.slug,
            'name':'foobar',
            'type':Account.TYPE_EXPENSE,
            'is_contra':False,
            'number':4500,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Account.objects.count(), 1)

        account = Account.objects.first()
        self.assertEqual(account.type, Account.TYPE_EXPENSE)
        self.assertFalse(account.is_contra)


    def test_user_can_create_a_temporary_contra_revenue_account(self):
        """ Test user can create a temporary contra revenue account
        """
        self.assertEqual(Account.objects.count(), 0)
        url = reverse("account-new")
        data = {
            'company':self.company.slug,
            'name':'foobar',
            'type':Account.TYPE_REVENUE,
            'is_contra':True,
            'number':4500,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Account.objects.count(), 1)

        account = Account.objects.first()
        self.assertEqual(account.type, Account.TYPE_REVENUE)
        self.assertTrue(account.is_contra)


    def test_user_can_create_a_temporary_contra_expense_account(self):
        """ Test user can create a temporary contra expense account
        """
        self.assertEqual(Account.objects.count(), 0)
        url = reverse("account-new")
        data = {
            'company':self.company.slug,
            'name':'foobar',
            'type':Account.TYPE_EXPENSE,
            'is_contra':True,
            'number':4500,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Account.objects.count(), 1)

        account = Account.objects.first()
        self.assertEqual(account.type, Account.TYPE_EXPENSE)
        self.assertTrue(account.is_contra)


    def test_user_cannot_assign_is_current_to_temporary_revenue_account(self):
        """ Test user cannot attach a is_current value to a temporary account
        """
        self.assertEqual(Account.objects.count(), 0)
        url = reverse("account-new")
        data = {
            'company':self.company.slug,
            'name':'foobar',
            'type':Account.TYPE_REVENUE,
            'is_contra':True,
            'is_current':True,
            'number':4500,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data['is_current'] = False    
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        del data['is_current']
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


    def test_user_cannot_assign_is_current_to_temporary_expense_account(self):
        """ Test user cannot attach a is_current value to a temporary account
        """
        self.assertEqual(Account.objects.count(), 0)
        url = reverse("account-new")
        data = {
            'company':self.company.slug,
            'name':'foobar',
            'type':Account.TYPE_EXPENSE,
            'is_contra':True,
            'is_current':True,
            'number':4500,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data['is_current'] = False    
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        del data['is_current']
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


    def test_user_cannot_create_an_account_if_user_hit_object_limit(self):
        """ Test user cannot create an account if they are at the object limit
        """
        userprofile = self.user.userprofile
        userprofile.object_limit_accounts = 0
        userprofile.save()

        self.assertEqual(Account.objects.count(), 0)
        url = reverse("account-new")
        data = {
            'company':self.company.slug,
            'name':'foobar',
            'type':Account.TYPE_ASSET,
            'is_contra':False,
            'is_current':True,
            'number':1500,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Account.objects.count(), 0)

        userprofile.object_limit_accounts = 1
        userprofile.save()
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Account.objects.count(), 1)
    

    def test_user_cannot_create_an_account_attached_to_another_users_company(self):
        """ Test a user cannot use another user's company to attach to their account.
        """
        self.assertEqual(Account.objects.count(), 0)
        url = reverse("account-new")
        data = {
            'company':self.other_company.slug,
            'name':'foobar',
            'type':Account.TYPE_ASSET,
            'is_contra':False,
            'is_current':True,
            'number':1500,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Account.objects.count(), 0)

        self.client.force_login(self.other_user)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Account.objects.count(), 1)


    def test_user_cannot_create_duplicate_named_accounts(self):
        """ Test that a user cannot create an account with the exact same
            name and company
        """
        self.assertEqual(Account.objects.count(), 0)
        url = reverse("account-new")
        data = {
            'company':self.company.slug,
            'name':'foobar',
            'type':Account.TYPE_ASSET,
            'is_contra':False,
            'is_current':True,
            'number':1500,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Account.objects.count(), 1)

        data['number'] += 1
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(Account.objects.count(), 1)
        self.assertEqual(response.data, "An account with that name already exists")


    def test_user_cannot_create_duplicate_numbered_accounts(self):
        """ Test that a user cannot create an account with the exact same
            number and company
        """
        self.assertEqual(Account.objects.count(), 0)
        url = reverse("account-new")
        data = {
            'company':self.company.slug,
            'name':'foobar',
            'type':Account.TYPE_ASSET,
            'is_contra':False,
            'is_current':True,
            'number':1500,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Account.objects.count(), 1)

        data['name'] = "foobar2"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(Account.objects.count(), 1)
        self.assertEqual(response.data, "An account with that number already exists")


    def test_that_a_user_can_edit_their_own_account(self):
        """ Test that a user can edit their own account
        """
        account = self.factory.create_account(
            self.company, 'foobar', Account.TYPE_ASSET, 1500,
            is_current=True, is_contra=False)
        
        url = reverse("account-edit", kwargs={'slug':account.slug})
        data = {
            "name":"cold hard cash",
            "number":1900,
            "is_current":False
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        account.refresh_from_db()
        self.assertEqual(account.name, "cold hard cash")
        self.assertEqual(account.number, 1900)
        self.assertFalse(account.is_current)


    def test_that_a_user_can_edit_their_own_temporary_account(self):
        """ Test that a user can edit their own account
        """
        account = self.factory.create_account(
            self.company, 'foobar', Account.TYPE_REVENUE, 1500,
            is_current=None, is_contra=False)
        
        url = reverse("account-edit", kwargs={'slug':account.slug})
        data = {
            "name":"cold hard cash",
            "number":1900,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        account.refresh_from_db()
        self.assertEqual(account.name, "cold hard cash")
        self.assertEqual(account.number, 1900)
        self.assertIsNone(account.is_current)


    def test_that_a_user_cant_attach_is_current_value_to_temporary_accounts(self):
        """ Test that a user cant attach an is_current value to a non current account
        """
        account = self.factory.create_account(
            self.company, 'foobar', Account.TYPE_REVENUE, 1500,
            is_current=None, is_contra=False)
        
        url = reverse("account-edit", kwargs={'slug':account.slug})
        data = {
            "name":"cold hard cash",
            "number":1900,
            "is_current":False,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data['is_current'] = False
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_that_a_user_cant_edit_others_account(self):
        """ Test that a user cant edit another users account
        """
        account = self.factory.create_account(
            self.other_company, 'foobar', Account.TYPE_ASSET, 1500,
            is_current=True, is_contra=False)
        
        url = reverse("account-edit", kwargs={'slug':account.slug})
        data = {
            "name":"cold hard cash",
            "number":1900,
            "is_current":False
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.client.force_login(self.other_user)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_that_a_user_can_delete_their_own_account(self):
        """ Test that a user can delete their own account
        """
        account = self.factory.create_account(
            self.company, 'foobar', Account.TYPE_ASSET, 1500,
            is_current=True, is_contra=False)
        self.assertEqual(Account.objects.count(), 1)
        
        url = reverse("account-delete", kwargs={'slug':account.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Account.objects.count(), 0)


    def test_that_a_user_cant_delete_their_own_account_if_its_used_by_a_journal_entry(self):
        """ Test that a user cant delete their own account if the account
            is being used by an existing journal entry.
        """
        period = self.factory.create_period(
            self.company, dt.date(2020, 1 , 1), dt.date(2020, 3 , 31))
        account1 = self.factory.create_account(
            self.company, 'cash', Account.TYPE_ASSET, 1500,
            is_current=True, is_contra=False)
        account2 = self.factory.create_account(
            self.company, 'A/P', Account.TYPE_LIABILITY, 2500,
            is_current=True, is_contra=False)
        je = self.factory.create_journal_entry(
            period, dt.date(2020, 1, 30), memo="foobar")
        self.factory.create_journal_entry_line(
            je, account1, 'd', 50000)
        self.factory.create_journal_entry_line(
            je, account2, 'c', 50000)
    
        self.assertEqual(Account.objects.count(), 2)
        url = reverse("account-delete", kwargs={'slug':account1.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Account.objects.count(), 2)
        self.assertEqual(response.data, "Cannot Delete. This account is referenced by a journal entry.")


    def test_that_a_user_cant_delete_other_users_account(self):
        """ Test that a user cant delete another users account
        """
        account = self.factory.create_account(
            self.other_company, 'foobar', Account.TYPE_ASSET, 1500,
            is_current=True, is_contra=False)
        self.assertEqual(Account.objects.count(), 1)
        
        url = reverse("account-delete", kwargs={'slug':account.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Account.objects.count(), 1)


    def test_user_can_add_default_accounts(self):
        """ Test that a user can add default accounts to their own company if they dont
            already have any accounts associated with the company
        """
        self.assertEqual(self.company.account_set.count(), 0)
        url = reverse("account-add-default-accounts")
        data = {
            'company':self.company.slug
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.company.account_set.count(), len(DEFAULT_ACCOUNTS))


    def test_user_cant_add_default_accounts_to_a_company_if_the_company_already_has_accounts(self):
        """ Test that a user cant add default accounts to their own company if the company
            already has accounts associated
        """
        self.factory.create_account(
            self.company, 'cash', 'asset', 1000, is_current=True, is_contra=False)
        self.assertEqual(self.company.account_set.count(), 1)
    
        url = reverse("account-add-default-accounts")
        data = {
            'company':self.company.slug
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "this company already has accounts associated")


    def test_user_cant_add_default_accounts_to_another_users_company(self):
        """ Test that a user cant add default accounts to another user's company
        """
        self.assertEqual(self.other_company.account_set.count(), 0)
        url = reverse("account-add-default-accounts")
        data = {
            'company':self.other_company.slug
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_default_account_names_and_numbers_are_unique(self):
        numbers = [r[3] for r in DEFAULT_ACCOUNTS]
        names = [r[4] for r in DEFAULT_ACCOUNTS]
        self.assertEqual(len(numbers), len(set(numbers)))
        self.assertEqual(len(names), len(set(names)))
