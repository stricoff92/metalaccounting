
import json

from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from freezegun import freeze_time

from .base import BaseTestBase
from api.models import Company, Account, JournalEntryLine, JournalEntry, Period, UserProfile, CashFlowWorksheet
from api.models.account import DEFAULT_ACCOUNTS


class ExportGraderViewTests(BaseTestBase):

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

        