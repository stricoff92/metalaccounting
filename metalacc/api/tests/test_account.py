
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


    def test_user_cant_create_account_with_invalid_use_of_cogs_tag(self):
        """ Test user cant create an account with invalid use of a CoGS tag 
        """
        url = reverse("account-new")
        for acc_type in [Account.TYPE_ASSET, Account.TYPE_LIABILITY]:
            data = {
                'company':self.company.slug,
                'name':'foobar',
                'type':acc_type,
                'is_contra':False,
                'is_current':False,
                'number':1500,
                'tag':Account.TAG_COST_OF_GOODS,
            }
            response = self.client.post(url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(str(response.data), "['Accounts with tag Cost of Goods Sold must be an expense account.']")

        data = {
            'company':self.company.slug,
            'name':'foobar',
            'type':Account.TYPE_EQUITY,
            'is_contra':False,
            'number':1500,
            'tag':Account.TAG_COST_OF_GOODS,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data), "['Accounts with tag Cost of Goods Sold must be an expense account.']")

        data = {
            'company':self.company.slug,
            'name':'foobar',
            'type':Account.TYPE_REVENUE,
            'is_contra':False,
            'number':1500,
            'tag':Account.TAG_COST_OF_GOODS,
            'is_operating':True,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data), "['Revenue account must be marked as a contra account to hold a Cost of Goods sold tag.']")

        data = {
            'company':self.company.slug,
            'name':'foobar',
            'type':Account.TYPE_EXPENSE,
            'is_contra':True,
            'number':1500,
            'tag':Account.TAG_COST_OF_GOODS,
            'is_operating':True,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data), "['Expense accounts cannot be marked as a contra account to hold a Cost of Goods sold tag.']")


    def test_user_cant_create_account_with_invalid_use_of_dividends_tag(self):
        """ Test user cant create an account with invalid use of a CoGS tag 
        """
        url = reverse("account-new")
        for acc_type in [Account.TYPE_ASSET, Account.TYPE_LIABILITY,]:
            data = {
                'company':self.company.slug,
                'name':'foobar',
                'type':acc_type,
                'is_contra':True,
                'is_current':False,
                'number':1500,
                'tag':Account.TAG_DIVIDENDS,
            }
            response = self.client.post(url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(str(response.data), "['Accounts with tag Dividends must be a contra equity account.']")

        for acc_type in [Account.TYPE_REVENUE, Account.TYPE_REVENUE,]:
            data = {
                'company':self.company.slug,
                'name':'foobar',
                'type':acc_type,
                'is_contra':True,
                'is_operating':True,
                'number':1500,
                'tag':Account.TAG_DIVIDENDS,
            }
            response = self.client.post(url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(str(response.data), "['Accounts with tag Dividends must be a contra equity account.']")

        data = {
            'company':self.company.slug,
            'name':'foobar',
            'type':Account.TYPE_EQUITY,
            'is_contra':False,
            'number':1500,
            'tag':Account.TAG_DIVIDENDS,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data), "['Accounts with tag Dividends must be a contra equity account.']")


    def test_user_can_create_account_with_using_cogs_tag(self):
        """ Test user cant create an account with invalid use of a CoGS tag 
        """
        url = reverse("account-new")
        data = {
            'company':self.company.slug,
            'name':'foobar',
            'type':Account.TYPE_EXPENSE,
            'is_contra':False,
            'number':1500,
            'tag':Account.TAG_COST_OF_GOODS,
            'is_operating':True,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Account.objects.get(slug=response.data['slug']).tag, Account.TAG_COST_OF_GOODS)

        data = {
            'company':self.company.slug,
            'name':'foobar2',
            'type':Account.TYPE_REVENUE,
            'is_contra':True,
            'number':1501,
            'tag':Account.TAG_COST_OF_GOODS,
            'is_operating':True,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Account.objects.get(slug=response.data['slug']).tag, Account.TAG_COST_OF_GOODS)


    def test_user_can_create_account_with_using_dividends_tag(self):
        """ Test user cant create an account with invalid use of a CoGS tag 
        """
        url = reverse("account-new")
        data = {
            'company':self.company.slug,
            'name':'foobar',
            'type':Account.TYPE_EQUITY,
            'is_contra':True,
            'number':1500,
            'tag':Account.TAG_DIVIDENDS,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Account.objects.get(slug=response.data['slug']).tag, Account.TAG_DIVIDENDS)


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
        self.assertIsNone(account.is_operating)


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
        self.assertIsNone(account.is_operating)


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
            'is_operating':True,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Account.objects.count(), 1)

        account = Account.objects.first()
        self.assertEqual(account.type, Account.TYPE_REVENUE)
        self.assertFalse(account.is_contra)
        self.assertTrue(account.is_operating)


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
            'is_operating':False,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Account.objects.count(), 1)

        account = Account.objects.first()
        self.assertEqual(account.type, Account.TYPE_EXPENSE)
        self.assertFalse(account.is_contra)
        self.assertFalse(account.is_operating)


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
            'is_operating':True,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Account.objects.count(), 1)

        account = Account.objects.first()
        self.assertEqual(account.type, Account.TYPE_REVENUE)
        self.assertTrue(account.is_contra)


    def test_user_cant_create_a_temporary_account_without_is_operational(self):
        """ Test user cant create a temporary account without is_operational info
        """
        url = reverse("account-new")
        data = {
            'company':self.company.slug,
            'name':'foobar',
            'type':Account.TYPE_REVENUE,
            'is_contra':True,
            'number':4500,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("is_operating cannot be null for type revenue" in str(response.data))
        data = {
            'company':self.company.slug,
            'name':'foobar',
            'type':Account.TYPE_EXPENSE,
            'is_contra':True,
            'number':4500,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("is_operating cannot be null for type expense" in str(response.data))


    def test_user_cant_create_a_non_temporary_account_with_is_operational(self):
        """ Test user cant create a non temporary account with is_operational info
        """
        url = reverse("account-new")
        data = {
            'company':self.company.slug,
            'name':'foobar',
            'type':Account.TYPE_ASSET,
            'is_current':True,
            'number':4500,
            "is_operating":True,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("is_operating must be null for type asset" in str(response.data))
        data = {
            'company':self.company.slug,
            'name':'foobar',
            'type':Account.TYPE_LIABILITY,
            'is_current':True,
            'number':4500,
            "is_operating":False,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("is_operating must be null for type liability" in str(response.data))
        data = {
            'company':self.company.slug,
            'name':'foobar',
            'type':Account.TYPE_EQUITY,
            'is_contra':True,
            'number':4500,
            "is_operating":False,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("is_operating must be null for type equity" in str(response.data))


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
            'is_operating':True,
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
            'is_operating':True,
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
            'is_operating':True,
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


    def test_that_is_current_is_required_for_asset_accounts(self):
        """ Test that is_current is required for asset accounts
        """
        account = self.factory.create_account(
            self.company, 'foobar', Account.TYPE_ASSET, 1500,
            is_current=True, is_contra=False)
        
        url = reverse("account-edit", kwargs={'slug':account.slug})
        data = {
            "name":"cold hard cash",
            "number":1900,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "is_current cannot be null for type asset")


    def test_that_is_current_is_required_for_liability_accounts(self):
        """ Test that is_current is required for asset accounts
        """
        account = self.factory.create_account(
            self.company, 'a/p', Account.TYPE_LIABILITY, 2500,
            is_current=True, is_contra=False)
        
        url = reverse("account-edit", kwargs={'slug':account.slug})
        data = {
            "name":"a/p",
            "number":2700,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "is_current cannot be null for type liability")


    def test_that_a_user_can_edit_their_own_temporary_account(self):
        """ Test that a user can edit their own account
        """
        account = self.factory.create_account(
            self.company, 'foobar', Account.TYPE_REVENUE, 1500,
            is_current=None, is_contra=False, is_operating=True)
        
        url = reverse("account-edit", kwargs={'slug':account.slug})
        data = {
            "name":"cold hard cash",
            "number":1900,
            "is_operating":False
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        account.refresh_from_db()
        self.assertEqual(account.name, "cold hard cash")
        self.assertEqual(account.number, 1900)
        self.assertIsNone(account.is_current)
        self.assertFalse(account.is_operating)


    def test_that_a_user_cant_attach_is_current_value_to_revenue_accounts(self):
        """ Test that a user cant attach an is_current value to revenue account
        """
        account = self.factory.create_account(
            self.company, 'foobar', Account.TYPE_REVENUE, 1500,
            is_current=None, is_contra=False, is_operating=True)
        
        url = reverse("account-edit", kwargs={'slug':account.slug})
        data = {
            "name":"cold hard cash",
            "number":1900,
            "is_current":False,
            "is_operating":True
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "is_current must be null for type revenue")


    def test_that_a_user_cant_attach_is_current_value_to_expense_accounts(self):
        """ Test that a user cant attach an is_current value to expense account
        """
        account = self.factory.create_account(
            self.company, 'foobar', Account.TYPE_EXPENSE, 1500,
            is_current=None, is_contra=False, is_operating=True)
        
        url = reverse("account-edit", kwargs={'slug':account.slug})
        data = {
            "name":"cold hard cash",
            "number":1900,
            "is_current":False,
            'is_operating':True,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "is_current must be null for type expense")


    def test_that_a_user_cant_attach_is_current_value_to_equity_accounts(self):
        """ Test that a user cant attach an is_current value to equity account
        """
        account = self.factory.create_account(
            self.company, 'foobar', Account.TYPE_EQUITY, 1500,
            is_current=None, is_contra=False)
        
        url = reverse("account-edit", kwargs={'slug':account.slug})
        data = {
            "name":"cold hard cash",
            "number":1900,
            "is_current":False,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "is_current must be null for type equity")


    def test_that_a_user_cant_edit_an_account_to_have_the_same_name_as_an_existing_account(self):
        """ Test that a user cant edit an account name to have the same name as an existing account
        """
        account1 = self.factory.create_account(
            self.company, 'foobar1', Account.TYPE_EQUITY, 1500,
            is_current=None, is_contra=False)
        account2 = self.factory.create_account(
            self.company, 'foobar2', Account.TYPE_EQUITY, 1600,
            is_current=None, is_contra=False)

        url = reverse("account-edit", kwargs={'slug':account1.slug})
        data = {
            "name":"foobar2",
            "number":1500,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data, "An account with that name already exists")


    def test_that_a_user_cant_edit_an_account_to_have_the_same_number_as_an_existing_account(self):
        """ Test that a user cant edit an account number to have the same number as an existing account
        """
        account1 = self.factory.create_account(
            self.company, 'foobar1', Account.TYPE_EQUITY, 1500,
            is_current=None, is_contra=False)
        account2 = self.factory.create_account(
            self.company, 'foobar2', Account.TYPE_EQUITY, 1600,
            is_current=None, is_contra=False)

        url = reverse("account-edit", kwargs={'slug':account1.slug})
        data = {
            "name":"foobar1",
            "number":1600,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data, "An account with that number already exists")


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


    def test_that_a_user_cant_edit_their_temporary_account_to_have_null_is_operating(self):
        """ Test that a user cant edit their temporary account such that it has an is_operating=Null
        """
        revenue_account = self.factory.create_account(
            self.company, 'foobar', Account.TYPE_REVENUE, 1500,
            is_current=None, is_contra=False, is_operating=True)
        
        url = reverse("account-edit", kwargs={'slug':revenue_account.slug})
        data = {
            "name":"cold hard cash",
            "number":1900,
            "is_contra":False,
            # is_operating is omitted
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("is_operating cannot be null for type revenue", str(response.data))

        expense_account = self.factory.create_account(
            self.company, 'foobar2', Account.TYPE_EXPENSE, 3500,
            is_current=None, is_contra=False, is_operating=True)
        
        url = reverse("account-edit", kwargs={'slug':expense_account.slug})
        data = {
            "name":"cold hard cash",
            "number":1900,
            "is_contra":False,
            # is_operating is omitted
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("is_operating cannot be null for type expense", str(response.data))


    def test_that_a_user_cant_edit_their_non_temporary_account_to_have_non_null_is_operating(self):
        """ Test that a user cant edit their non temporary account such that it has a non-null is_operating value
        """
        account = self.factory.create_account(
            self.company, 'foobar', Account.TYPE_ASSET, 1500,
            is_current=True, is_contra=False, is_operating=None)
        
        url = reverse("account-edit", kwargs={'slug':account.slug})
        data = {
            "name":"cold hard cash",
            "number":1900,
            "is_contra":False,
            "is_current":True,
            "is_operating":True,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("is_operating must be null for type asset", str(response.data))


    def test_that_a_user_cant_edit_their_account_to_have_an_invalid_use_of_the_cogs_tag(self):
        """ Test that a user cant edit their non temporary account such that it has a non-null is_operating value
        """
        asset_account = self.factory.create_account(
            self.company, 'foobar1', Account.TYPE_ASSET, 1500, is_contra=False, is_current=True)
        liability_account = self.factory.create_account(
            self.company, 'foobar2', Account.TYPE_LIABILITY, 1501, is_contra=True, is_current=True)
        equity_account = self.factory.create_account(
            self.company, 'foobar3', Account.TYPE_EQUITY, 1502)
        revenue_account = self.factory.create_account(
            self.company, 'foobar4', Account.TYPE_REVENUE, 1503, is_operating=True, is_contra=False)
        expense_account = self.factory.create_account(
            self.company, 'foobar5', Account.TYPE_EXPENSE, 1504, is_operating=True, is_contra=False)

        url = reverse("account-edit", kwargs={'slug':asset_account.slug})
        data = {
            "name":"cold hard cash",
            "number":1900,
            "is_contra":False,
            "is_current":True,
            'tag':Account.TAG_COST_OF_GOODS,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("['Accounts with tag Cost of Goods Sold must be an expense account.']", str(response.data))

        url = reverse("account-edit", kwargs={'slug':liability_account.slug})
        data = {
            "name":"cold hard cash",
            "number":1900,
            "is_contra":False,
            "is_current":True,
            'tag':Account.TAG_COST_OF_GOODS,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("['Accounts with tag Cost of Goods Sold must be an expense account.']", str(response.data))

        url = reverse("account-edit", kwargs={'slug':equity_account.slug})
        data = {
            "name":"cold hard cash",
            "number":1900,
            "is_contra":False,
            'tag':Account.TAG_COST_OF_GOODS,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("['Accounts with tag Cost of Goods Sold must be an expense account.']", str(response.data))

        url = reverse("account-edit", kwargs={'slug':revenue_account.slug})
        data = {
            "name":"cold hard cash",
            "number":1900,
            "is_contra":False,
            "is_operating":True,
            'tag':Account.TAG_COST_OF_GOODS,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            "['Revenue account must be marked as a contra account to hold a Cost of Goods sold tag.']",
            str(response.data))

        url = reverse("account-edit", kwargs={'slug':expense_account.slug})
        data = {
            "name":"cold hard cash",
            "number":1900,
            "is_operating":False,
            'tag':Account.TAG_COST_OF_GOODS,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            "['Accounts with the tag Cost of Goods Sold must be operating accounts.']",
            str(response.data))


    def test_that_a_user_cant_edit_their_account_to_have_an_invalid_use_of_the_dividends_tag(self):
        """ Test that a user cant edit their non temporary account such that it has a non-null is_operating value
        """
        asset_account = self.factory.create_account(
            self.company, 'foobar1', Account.TYPE_ASSET, 1500, is_contra=False, is_current=True)
        liability_account = self.factory.create_account(
            self.company, 'foobar2', Account.TYPE_LIABILITY, 1501, is_contra=True, is_current=True)
        equity_account = self.factory.create_account(
            self.company, 'foobar3', Account.TYPE_EQUITY, 1502)
        revenue_account = self.factory.create_account(
            self.company, 'foobar4', Account.TYPE_REVENUE, 1503, is_operating=True, is_contra=False)
        expense_account = self.factory.create_account(
            self.company, 'foobar5', Account.TYPE_EXPENSE, 1504, is_operating=True, is_contra=False)

        url = reverse("account-edit", kwargs={'slug':asset_account.slug})
        data = {
            "name":"cold hard cash",
            "number":1900,
            "is_contra":False,
            "is_current":True,
            'tag':Account.TAG_DIVIDENDS,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("['Accounts with tag Dividends must be a contra equity account.']", str(response.data))

        url = reverse("account-edit", kwargs={'slug':liability_account.slug})
        data = {
            "name":"cold hard cash",
            "number":1900,
            "is_contra":False,
            "is_current":True,
            'tag':Account.TAG_DIVIDENDS,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("['Accounts with tag Dividends must be a contra equity account.']", str(response.data))

        url = reverse("account-edit", kwargs={'slug':revenue_account.slug})
        data = {
            "name":"cold hard cash",
            "number":1900,
            "is_contra":False,
            "is_operating":True,
            'tag':Account.TAG_DIVIDENDS,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            "['Accounts with tag Dividends must be a contra equity account.']",
            str(response.data))

        url = reverse("account-edit", kwargs={'slug':expense_account.slug})
        data = {
            "name":"cold hard cash",
            "number":1900,
            "is_operating":False,
            'tag':Account.TAG_DIVIDENDS,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            "['Accounts with tag Dividends must be a contra equity account.']",
            str(response.data))

        url = reverse("account-edit", kwargs={'slug':equity_account.slug})
        data = {
            "name":"cold hard cash",
            "number":1900,
            "is_contra":False, # contra must be true
            'tag':Account.TAG_DIVIDENDS,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("['Accounts with tag Dividends must be a contra equity account.']", str(response.data))



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
        numbers = [r[4] for r in DEFAULT_ACCOUNTS]
        names = [r[5] for r in DEFAULT_ACCOUNTS]
        self.assertEqual(len(numbers), len(set(numbers)))
        self.assertEqual(len(names), len(set(names)))
