
from django import forms

from api.models import Account


class NewAccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ('name', 'type', 'number', 'is_contra', 'is_current', 'is_operating',)


class EditAccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ('name', 'number', 'is_current', 'is_operating',)
