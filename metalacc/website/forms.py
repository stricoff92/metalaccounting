
from django import forms

class LoginForm(forms.Form):
    email = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class RegisterNewUser(forms.Form):
    email = forms.CharField(required=True)
    password1 = forms.CharField(required=True)
    password2 = forms.CharField(required=True)

class ContactUsForm(forms.Form):
    email = forms.CharField(required=False)
    message = forms.CharField(required=True, max_length=2048)
    