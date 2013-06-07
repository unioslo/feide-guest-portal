from django import forms
from django.forms import ModelForm
from django.forms.widgets import PasswordInput

from guest.models import Guest

class RegisterMail(forms.Form):
    mail = forms.EmailField()

class GuestForm(ModelForm):
    class Meta:
        model = Guest
        fields = ['uid', 'mail', 'userPassword', 'givenName', 'sn']
        widgets = {'userPassword': PasswordInput, }

class RecoveryForm(forms.Form):
    ident = forms.CharField()

class PasswordForm(forms.Form):
    userPassword = forms.CharField(widget=PasswordInput)
