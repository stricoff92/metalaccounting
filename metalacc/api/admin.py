from django.contrib import admin
from api.models import (
    Company,
    Period,
    Account,
    JournalEntry,
    JournalEntryLine,
    UserProfile,
    CashFlowWorksheet,
    ContactUsSubmission,
)

admin.site.register(Company)
admin.site.register(Period)
admin.site.register(Account)
admin.site.register(JournalEntry)
admin.site.register(JournalEntryLine)
admin.site.register(UserProfile)
admin.site.register(CashFlowWorksheet)
admin.site.register(ContactUsSubmission)
