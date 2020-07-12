
from django import forms

from api.models import Period

class PeriodForm(forms.ModelForm):
    class Meta:
        model = Period
        fields = ('start', 'end', )
    
    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data['start'] >= cleaned_data['end']:
            raise forms.ValidationError("start must be before end")
        return cleaned_data
