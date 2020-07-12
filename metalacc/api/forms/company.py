
from django import forms

from api.models import Company


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ('name', )


class CompanySelectionForm(forms.Form):
    company = forms.ModelChoiceField(
        queryset=Company.objects.all(), required=True, to_field_name="slug")
