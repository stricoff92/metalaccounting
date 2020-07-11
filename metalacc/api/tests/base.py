

from django.test import TestCase
from django.test import Client as TestClient
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser, User

from api.models import UserProfile
from .factory import TestObjectFactory


class BaseTestBase(TestCase):


    PASSWORD_FACTORY = "password-yo"
    ADMIN_USER_NAME = "foobar-admin"
    USER_NAME = "foobar"
    OTHER_USER_NAME = "foobar2"

    factory = TestObjectFactory()


    def setUp(self):
        self.client = TestClient()

        self.user = User.objects.create_user(
            username=self.USER_NAME,
            email=f'{self.USER_NAME}@mail.com',
            password=self.PASSWORD_FACTORY)
        self.user_profile = UserProfile.objects.create(user=self.user)

        self.other_user = User.objects.create_user(
            username=self.OTHER_USER_NAME,
            email=f'{self.OTHER_USER_NAME}@mail.com',
            password=self.PASSWORD_FACTORY)
        self.other_user_profile = UserProfile.objects.create(user=self.other_user)

    def tearDown(self):
        self.client.logout()

