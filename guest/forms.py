from django import forms
from django.forms import ModelForm
from django.forms.widgets import PasswordInput
from django.utils.translation import ugettext_lazy as _

from guest.models import Guest

class RegisterMail(forms.Form):
    mail = forms.EmailField()

class GuestForm(forms.Form):
    uid = forms.CharField(label=_('Username'))
    mail = forms.EmailField(label=_('Mail'))
    userPassword = forms.CharField(label=_('Password'), widget=PasswordInput(attrs={'placeholder':_('old password')}))
    givenName = forms.CharField(label=_('Given name'))
    sn = forms.CharField(label=_('Surname'))

class RecoveryForm(forms.Form):
    ident = forms.CharField(label=_('Username or mail'))

class PasswordForm(forms.Form):
    userPassword = forms.CharField(label=_('New password'), widget=PasswordInput)
