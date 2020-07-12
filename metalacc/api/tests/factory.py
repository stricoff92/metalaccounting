
from api.models import (
    Account,
    Company,
    Period,
    JournalEntry,
)

class TestObjectFactory:

    def create_company(self, user, name="foobar"):
        return Company.objects.create(user=user, name=name)

    def create_period(self, company, start, end):
        return Period.objects.create(company=company, start=start, end=end)

    def create_journal_entry(self, period, date, memo="foobar", is_adjusting_entry=False):
        return JournalEntry.objects.create(
            period=period,
            date=date,
            memo=memo,
            is_adjusting_entry=is_adjusting_entry)

    def create_account(self, company, name, acctype, number, is_current=None, is_contra=False):
        return Account.objects.create(
            company=company, user=company.user, name=name, type=acctype, number=number,
            is_current=is_current, is_contra=is_contra)
