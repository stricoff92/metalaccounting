
from django.urls import reverse
from rest_framework import status

from .base import BaseTestBase
from api.models import Company, Account


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


    def test_user_cannot_create_duplicate_accounts(self):
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

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Account.objects.count(), 1)
