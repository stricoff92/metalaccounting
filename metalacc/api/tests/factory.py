
import json

from api.models import (
    Account,
    Company,
    Period,
    JournalEntry,
    JournalEntryLine,
    CashFlowWorksheet,
)

class TestObjectFactory:

    def create_company(self, user, name="foobar"):
        return Company.objects.create(user=user, name=name)

    def create_period(self, company, start, end):
        return Period.objects.create(company=company, start=start, end=end)

    def create_journal_entry(self, period, date, memo="foobar", is_adjusting_entry=False, is_closing_entry=False):
        return JournalEntry.objects.create(
            period=period,
            date=date,
            memo=memo,
            is_adjusting_entry=is_adjusting_entry,
            is_closing_entry=is_closing_entry)
    
    def create_journal_entry_line(self, journal_entry, account, type, amount):
        return JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            account=account,
            type=type,
            amount=amount)

    def create_account(self, company, name, acctype, number, is_current=None, is_operating=None, is_contra=False, tag=None):
        return Account.objects.create(
            company=company, user=company.user, name=name, type=acctype, number=number,
            is_current=is_current, is_contra=is_contra, is_operating=is_operating, tag=tag)

    def create_cashflow_worksheet(self, period, data={}):
        return CashFlowWorksheet.objects.create(
            period=period, version_hash=period.version_hash,
            data=json.dumps(data))
