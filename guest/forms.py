from django import forms
from django.forms import ModelForm
from django.forms.widgets import PasswordInput, TextInput
from django.utils.translation import ugettext_lazy as _

from guest.models import Guest

import re

class NotBlankCharField(forms.CharField):
    def clean(self, data):
        return super(NotBlankCharField, self).clean(data.strip())

class RegisterMail(forms.Form):
    mail = forms.EmailField()

class GuestFormEdit(forms.Form):
    givenName = NotBlankCharField(label=_('Given name'))
    sn = NotBlankCharField(label=_('Surname'))
    mail = forms.EmailField(label=_('Mail'), widget=TextInput(attrs={'placeholder':_('old mail')}), required=False, help_text=_('Leave mail blank to keep the old one.'))
    userPassword = forms.CharField(label=_('Password'), min_length=6, widget=PasswordInput(attrs={'placeholder':_('old password')}), required=False, help_text=_('Leave password blank to keep the old one.'))

    def clean_mail(self):
        data = self.cleaned_data['mail']
        try: # check if new mail aleady exist and return early if so.
            Guest.objects.get(mail=data)
            raise forms.ValidationError(_("Mail already in use."))
        except Guest.DoesNotExist:
            return data

class GuestFormCreate(forms.Form):
    uid = NotBlankCharField(label=_('Username'))
    userPassword = forms.CharField(label=_('New password'), min_length=6, widget=PasswordInput())
    givenName = NotBlankCharField(label=_('Given name'))
    sn = NotBlankCharField(label=_('Surname'))

    def  clean_uid(self):
        data = self.cleaned_data['uid']
        data = data.lower()
        data = data.strip()
        rule = re.compile('[a-z0-9\._-]+')
        if not rule.match(data):
            raise forms.ValidationError(_('Username can only contain lower case letters, digits, ".", "-" and "_".'))
        try: # check if uid aleady exist and return early if so.
            Guest.objects.get(uid=data)
            raise forms.ValidationError(_("Username already in use."))
        except Guest.DoesNotExist:
            return data

class GuestFormAdmin(forms.Form):
    uid = forms.CharField(label=_('Username'))
    mail = forms.EmailField(label=_('Mail'))
    userPassword = forms.CharField(label=_('Password'), widget=PasswordInput(attrs={'placeholder':_('old password')}), help_text=_('Leave password blank to keep the old one.'))
    givenName = forms.CharField(label=_('Given name'))
    sn = forms.CharField(label=_('Surname'))

class RecoveryForm(forms.Form):
    ident = forms.CharField(label=_('Username or mail'))

class PasswordForm(forms.Form):
    userPassword = forms.CharField(label=_('New password'), widget=PasswordInput)
