
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

    def __init__(self, data, *args, **kwargs):
        if data.get('company_text_file'):
            uploaded_file = data['company_text_file']
            if uploaded_file.content_type.lower() != "text/plain":
                return Response("Invalid File Format. Expected text/plain", status.HTTP_400_BAD_REQUEST)
            form_data = {
                "company_text_data": uploaded_file.file.read().decode()
            }
        else:
            form_data = data

        return super().__init__(form_data, *args, **kwargs)


    def clean(self):
        cleaned_data = super().clean()
        try:
            cleaned_data['decoded_data'] = company_export.decode_signed_jwt(
                cleaned_data['company_text_data'])
        except (BadSignature, jwt.InvalidSignatureError):
            raise forms.ValidationError("Invalid Data")
            
        try:
            version = cleaned_data['decoded_data']['meta']['version']
        except KeyError:
            raise forms.ValidationError("Unsupported Version. Invalid Data.")

        if version not in settings.OBJECT_SERIALIZATION_SUPPORTED_VERSIONS:
            raise forms.ValidationError("Unsupported Version")
            

        return cleaned_data
