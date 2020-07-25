
from django import forms

from api.models import JournalEntry, JournalEntryLine, Period, Account

class NewJournalEntryForm(forms.ModelForm):

    period = forms.ModelChoiceField(
        queryset=Period.objects.all(), required=True, to_field_name="slug")

    class Meta:
        model = JournalEntry
        fields = (
            'period', 'date', 'memo', 
            'is_adjusting_entry', 'is_closing_entry',)


class NewJournalEntryLineForm(forms.ModelForm):

    account = forms.ModelChoiceField(
        queryset=Account.objects.all(), required=True, to_field_name="slug")

    class Meta:
        model = JournalEntryLine
        fields = ('account', 'type', 'amount',)
