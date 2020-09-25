
from django import forms
from django.core.signing import BadSignature
from django.conf import settings
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
    company_text_data = forms.CharField(required=True)

    def clean(self):
        cleaned_data = super().clean()
        try:
            cleaned_data['decoded_data'] = company_export.decode_signed_jwt(cleaned_data['company_text_data'])
        except (BadSignature, jwt.InvalidSignatureError):
            raise forms.ValidationError("Invalid Data")
        
        version = cleaned_data['decoded_data']['meta']['version']
        if version not in settings.OBJECT_SERIALIZATION_SUPPORTED_VERSIONS:
            raise forms.ValidationError("Unsupported Version")

        return cleaned_data
