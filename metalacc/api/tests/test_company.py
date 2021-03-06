
from django.urls import reverse
from rest_framework import status

from .base import BaseTestBase
from api.models import Company


class CompanyViewTests(BaseTestBase):

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)
    
    def tearDown(self):
        super().tearDown()


    def test_user_can_create_a_company(self):
        """ Test that a user can create a new company.
        """
        self.assertEqual(Company.objects.count(), 0)
        url = reverse("company-new")
        data = {'name':'foobar'}
        response = self.client.post(url, data, formt="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.assertEqual(Company.objects.count(), 1)
        company = Company.objects.first()
        self.assertEqual(company.user, self.user)
        self.assertEqual(company.name, "foobar")
        self.assertIsNone(company.user_finger_print_str)
        self.assertIsNotNone(company.slug)


    def test_user_cannot_create_a_company_if_they_hit_company_object_limit(self):
        """ Test that a user cannot add a company if they are at the object limit.
        """
        userprofile = self.user.userprofile
        userprofile.object_limit_companies = 0
        userprofile.save(update_fields=['object_limit_companies'])

        self.assertEqual(Company.objects.count(), 0)
        url = reverse("company-new")
        data = {'name':'foobar'}
        response = self.client.post(url, data, formt="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Company.objects.count(), 0)

        userprofile.object_limit_companies = 1
        userprofile.save(update_fields=['object_limit_companies'])
        response = self.client.post(url, data, formt="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Company.objects.count(), 1)


    def test_user_cannot_create_a_company_with_the_same_name_as_another_of_their_companies(self):
        """ Test that a user cannot create a company with the exact same name of one of their
            other companies
        """
        duplicate_name = "xyz corp"
        company = self.factory.create_company(self.user, name=duplicate_name)
        url = reverse("company-new")
        data = {'name':duplicate_name}
        response = self.client.post(url, data, formt="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "a company with that name already exists")


    def test_user_can_create_a_company_with_the_same_name_as_another_company_owned_by_another_user(self):
        """ Test that a user can create a company with the exact same name as another user's
            company
        """
        duplicate_name = "xyz corp"
        company = self.factory.create_company(self.other_user, name=duplicate_name)
        url = reverse("company-new")
        data = {'name':duplicate_name}
        response = self.client.post(url, data, formt="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


    def test_user_cannot_edit_a_company_to_have_the_same_name_as_another_of_their_companies(self):
        """ Test that a user cannot edit a company to have the exact same name of one of their
            other companies
        """
        duplicate_name = "xyz corp2"
        company1 = self.factory.create_company(self.user, name="xyz corp1")
        company2 = self.factory.create_company(self.user, name=duplicate_name)
        url = reverse("company-edit", kwargs={'slug':company1.slug})
        data = {'name':duplicate_name}
        response = self.client.post(url, data, formt="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "a company with that name already exists")


    def test_user_can_edit_a_company_to_have_the_same_name_as_another_company_owned_by_another_user(self):
        """ Test that a user can edit a company with the exact same name as another user's
            company
        """
        duplicate_name = "xyz corp2"
        company1 = self.factory.create_company(self.user, name="xyz corp1")
        company2 = self.factory.create_company(self.other_user, name=duplicate_name)
        url = reverse("company-edit", kwargs={'slug':company1.slug})
        data = {'name':duplicate_name}
        response = self.client.post(url, data, formt="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_user_can_edit_own_company(self):
        """ Test that a user can edit their own company.
        """
        company = self.factory.create_company(self.user)
        url = reverse("company-edit", kwargs={'slug':company.slug})
        data = {'name':'xyz corp'}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        company.refresh_from_db()
        self.assertEqual(company.name, 'xyz corp')


    def test_user_cannot_edit_another_users_company(self):
        """ Test that a user cannot edit another user's company.
        """
        company = self.factory.create_company(self.other_user)
        url = reverse("company-edit", kwargs={'slug':company.slug})
        data = {'name':'xyz corp'}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.client.force_login(self.other_user)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_user_can_delete_own_company(self):
        """ Test that a user can delete their own company.
        """
        company = self.factory.create_company(self.user)
        self.assertEqual(Company.objects.count(), 1)

        url = reverse("company-delete", kwargs={'slug':company.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Company.objects.count(), 0)
    

    def test_user_cannot_delete_other_users_company(self):
        """ Test that a user cannot delete another user's company.
        """
        company = self.factory.create_company(self.other_user)
        company_id = company.id
        self.assertEqual(Company.objects.count(), 1)

        url = reverse("company-delete", kwargs={'slug':company.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Company.objects.count(), 1)
        
        self.client.force_login(self.other_user)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Company.objects.count(), 0)
