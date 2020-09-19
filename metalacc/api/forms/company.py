
from django import forms
from django.core.signing import BadSignature
import jwt

from api.models import Company
from api.lib import company_export


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ('name', )


class CompanySelectionForm(forms.Form):
    company = forms.ModelChoiceField(
        queryset=Company.objects.all(), required=True, to_field_name="slug")


class ImportCompanyForm(forms.Form):
    data = forms.CharField(required=True)

    def clean(self):
        cleaned_data = super().clean()
        try:
            cleaned_data['decoded_data'] = company_export.decode_signed_jwt(cleaned_data['data'])
        except (BadSignature, jwt.InvalidSignatureError):
            raise forms.ValidationError("invalid data")
        
        return cleaned_data
