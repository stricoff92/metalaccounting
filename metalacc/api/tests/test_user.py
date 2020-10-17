
import datetime as dt
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from freezegun import freeze_time

from .base import BaseTestBase
from api.models import Period, CashFlowWorksheet
from api.lib import email as email_lib
from api.utils import get_account_activation_token


@freeze_time("2012-01-14 03:21:34")
class UserViewTests(BaseTestBase):

    def setUp(self):
        super().setUp()
        self.mock_send_account_activation_email = patch.object(email_lib, "send_account_activation_email").start()
    
    def tearDown(self):
        self.mock_send_account_activation_email.stop()
        super().tearDown()
    

    def test_new_user_can_register_and_activate_their_account(self):
        url = reverse("register")
        data = {
            "email":"derpy@derp.oi",
            "password1":"password",
            "password2":"password",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_user = get_user_model().objects.get(email="derpy@derp.oi")
        self.assertFalse(new_user.is_active)
        self.mock_send_account_activation_email.assert_called_once_with(
            new_user,
            get_account_activation_token(new_user.userprofile.slug))

        
        activate_url = (
            reverse("app-activate-user", kwargs={'slug':new_user.userprofile.slug})
            + "?token="
            + get_account_activation_token(new_user.userprofile.slug))
        response = self.client.get(activate_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        new_user.refresh_from_db()
        self.assertTrue(new_user.is_active)


    def test_new_user_cant_register_if_email_in_use(self):
        url = reverse("register")
        data = {
            "email":self.user.email,
            "password1":"password",
            "password2":"password",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("email is already in use" in str(response.data))
        self.mock_send_account_activation_email.assert_not_called()


    def test_new_user_cant_register_if_passwords_dont_match(self):
        url = reverse("register")
        data = {
            "email":'derp@derp.io',
            "password1":"password1",
            "password2":"password2",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("Passwords do not match." in str(response.data))
        self.mock_send_account_activation_email.assert_not_called()


    def test_activation_link_is_resent_if_existing_email_is_not_active(self):
        url = reverse("register")
        data = {
            "email":self.user.email,
            "password1":"password",
            "password2":"password",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("email is already in use" in str(response.data))
        # Activation email does not send because account is active.
        self.mock_send_account_activation_email.assert_not_called()

        # Activation email does send because account is not active.
        self.user.is_active = False
        self.user.save()
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("email is already in use" in str(response.data))
        self.mock_send_account_activation_email.assert_called_once()
