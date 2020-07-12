
from api.models import (
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
