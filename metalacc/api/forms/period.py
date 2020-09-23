
from django import forms

from api.models import Period
from api.utils import is_valid_slug

class PeriodForm(forms.ModelForm):
    class Meta:
        model = Period
        fields = ('start', 'end', )
    
    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data['start'] >= cleaned_data['end']:
            raise forms.ValidationError("start must be before end")
        return cleaned_data


class CashFlowWorkSheetRowForm(forms.Form):
    journal_entry_slug = forms.CharField(max_length=20, required=True)

    operations = forms.IntegerField(required=True)
    investments = forms.IntegerField(required=True)
    finances = forms.IntegerField(required=True)

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data['operations'] < 0:
            raise forms.ValidationError("operations must be greater than 0")
        if cleaned_data['investments'] < 0:
            raise forms.ValidationError("investments must be greater than 0")
        if cleaned_data['finances'] < 0:
            raise forms.ValidationError("finances must be greater than 0")
        
        if not is_valid_slug(cleaned_data['journal_entry_slug']):
            raise forms.ValidationError("field journal_entry_slug is not valid")

        return cleaned_data
