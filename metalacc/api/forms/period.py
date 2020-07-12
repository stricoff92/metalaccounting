
from django import forms

from api.models import Period

class PeriodForm(forms.ModelForm):
    class Meta:
        model = Period
        fields = ('start', 'end', )

