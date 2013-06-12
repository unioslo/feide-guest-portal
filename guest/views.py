# -*- coding: utf-8 -*-

from django.core.urlresolvers import reverse
from django.core import signing
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib import messages
from django.forms.models import model_to_dict
from django.db.models import Q
from django.utils.translation import ugettext as _

from guest.models import Guest
from guest.forms import GuestForm, RegisterMail, RecoveryForm, PasswordForm
from guest.tools import ssha, bind


import time
import copy


def only_admin(fun):
    def closure(request, *args, **kwargs):
        if 'REMOTE_USER' in request.META and request.META['REMOTE_USER'] in settings.FEIDE_ADMIN_ACCOUNTS:
            if 'uid' in kwargs:
                guest = get_object_or_404(Guest, uid=kwargs['uid'])
                del kwargs['uid']
                kwargs['guest'] = guest
                request.is_admin = True
            return fun(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return closure

def logged_in(fun):
    def closure(request, *args, **kwargs):
        if 'uid' in request.session:
            uid = request.session['uid']
            try:
                g = Guest.objects.get(uid=uid)
                return fun(request, *args, guest=g, **kwargs)
            except Guest.DoesNotExist:
                pass
        return redirect('guest.views.logout')
    return closure

def change_locale(request, locale=None):
    request.session['django_language'] = locale
    response = redirect(request.GET.get('next','guest.views.home'))
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, locale)
    return response

def home(request):
    return render(request, 'guest/home.html', {
        'title': _('Feide Guest Account System')
        })

def login(request):
    if request.POST:
        try:
            g = Guest.objects.get(uid=request.POST['uid'])
            if g and bind(g.dn, request.POST['userPassword']):
                request.session['uid'] = g.uid
                messages.add_message(request, messages.SUCCESS, _('Logged in as %(uid) (%(mail))') % {'uid':g.uid, 'mail':g.mail})
                return redirect('guest.views.me')
            else:
                messages.add_message(request, messages.ERROR, _('Wrong username and/or password'))
        except Guest.DoesNotExist:
            messages.add_message(request, messages.ERROR, _('Wrong username and/or password'))
    return render(request, 'guest/home.html', {
        'title': _('Login'),
        })

def logout(request):
    if 'uid' in request.session:
        del request.session['uid']
        messages.add_message(request, messages.SUCCESS, _('Logged out.'))
    else:
        messages.add_message(request, messages.ERROR, _('Not logged in.'))
    return redirect('guest.views.home')


def show(request, guest=None):
    return render(request, 'guest/show.html', {
        'fg': guest,
        'title': _('Showing %(name)') % {'name': guest.displayName},
        })
me = logged_in(show)
admin_show = only_admin(show)

def edit(request, guest=None):
    if request.POST:
        gf = GuestForm(request.POST)
        if request.is_admin:
            guest.uid = gf['uid'].value()
            guest.mail = gf['mail'].value()
            guest.givenName = gf['givenName'].value()
            guest.sn = gf['sn'].value()
            if gf['userPassword'].value(): # password changed
                guest.userPassword = ssha(gf['userPassword'].value()) # ssha the new password
            guest.save()
            return redirect('guest.views.admin_show', uid=guest.uid)

        else:
            if gf.is_valid():
                guest.uid = gf.cleaned_data['uid']
                guest.givenName = gf.cleaned_data['givenName']
                guest.sn = gf.cleaned_data['sn']
                if gf.cleaned_data['userPassword']: # password changed
                    guest.userPassword = ssha(gf.cleaned_data['userPassword']) # ssha the new password
                guest.save()

                if gf.cleaned_data['mail'] != guest.mail: # mail changed
                    obj = {'uid':guest.uid, 'mail':gf.cleaned_data['mail'], 'time':time.time()}
                    send_activation_mail(request, obj)
                return redirect('guest.views.me')
    else:
        gf = GuestForm(initial=model_to_dict(guest))
        if not request.is_admin:
            gf.fields['uid'].widget.attrs['readonly'] = True
    return render(request, 'guest/edit.html', {
        'form':gf,
        'title': _('Edit %(name)') % {'name': guest.displayName},
        })
edit_me = logged_in(edit)
admin_edit = only_admin(edit)

def delete(request, guest=None):
    guest.delete()
    messages.add_message(request, messages.SUCCESS, _('Account deleted.'))
    return redirect('guest.views.home')
delete_me = logged_in(delete)
admin_delete = only_admin(delete)

def new(request):
    if request.POST:
        f = RegisterMail(request.POST)
        if f.is_valid():
            obj = {'time':time.time(), 'mail':f.cleaned_data['mail']}
            send_activation_mail(request, obj)
    else:
        f = RegisterMail()
    return render(request, 'guest/edit.html', {
        'form': f,
        'title': _('New Guest Account'),
        })

def send_activation_mail(request, obj):
    code = signing.dumps(obj)
    send_mail(_('Activation of Guest account on Feide'),
              render_to_string('guest/activation_mail.txt', {'code':code}),
              settings.ACTIVATION_FROM_MAIL,
              [obj['mail']],
              fail_silently=False)
    messages.add_message(request, messages.SUCCESS, _("We've sent an activation mail to your address, %(mail). Follow it for further instructions.") % {'mail': obj['mail']})

def activate(request, code=None):
    if request.POST:
        gf = GuestForm(request.POST)
        if gf.is_valid():
            if gf.cleaned_data['mail'] == request.session['validated_mail']:
                g = gf.save(commit=False)
                g.userPassword = ssha(g.userPassword) # ssha the new password
                g.save()
                del request.session['validated_mail']
                messages.add_message(request, messages.SUCCESS, _('Account %(uid) created.') % {'uid': g.uid})
                request.session['uid'] = g.uid
                return redirect('guest.views.me')
            else:
                messages.add_message(request, messages.ERROR, _('Mail %(mail) not validated.') % {'mail': gf.cleaned_data['mail']})
                return redirect('guest.views.home')

    else:
        obj = signing.loads(code)
        if time.time() - obj['time'] > 60*60*2: # 2 hour TTL on activation links
            messages.add_message(request, messages.ERROR, _('The activation link has expired. Please register again to recieve a new one.'))
            return redirect('guest.views.home')
        else:
            if 'uid' in obj:
                g = get_object_or_404(Guest, uid=obj['uid'])
                g.mail = obj['mail']
                g.save()
                request.session['uid'] = g.uid
                messages.add_message(request, messages.SUCCESS, _('Mail updated.'))
                return redirect('guest.views.me')
            else:
                request.session['validated_mail'] = obj['mail']
                gf = GuestForm(initial={'mail':obj['mail']})
                gf.fields['mail'].widget.attrs['readonly'] = True
    return render(request, 'guest/edit.html', {
        'form': gf,
        'title': _('Activate account'),
        })

def send_recovery_mail(request, guest):
    obj = {'uid':guest.uid, 'time':time.time()}
    code = signing.dumps(obj)
    send_mail(_('Password recovery for Guest account on Feide'),
              render_to_string('guest/recovery_mail.txt', {'guest':guest, 'code':code}),
              settings.ACTIVATION_FROM_MAIL,
              [guest.mail],
              fail_silently=False)
    messages.add_message(request, messages.SUCCESS, _("We've sent recovery mail to your mail address, %(mail). Follow it for further instructions.") % {'mail': guest.mail})
    return redirect('guest.views.home')

def recover(request):
    if request.POST:
        f = RecoveryForm(request.POST)
        if f.is_valid():
            i = f.cleaned_data['ident']
            if '@' in i:
                try:
                    g = Guest.objects.get(mail=i)
                    return send_recovery_mail(request, g)
                except Guest.DoesNotExist:
                    pass
            else:
                try:
                    g = Guest.objects.get(uid=i)
                    return send_recovery_mail(request, g)
                except Guest.DoesNotExist:
                    pass
        f.fields['ident'].error = _('Username or mail not found.')
    else:
        f = RecoveryForm()
    return render(request, 'guest/edit.html',{
        'form': f,
        'title': _('Recover account'),
        })

def reset_password(request, code):
    if request.POST:
        pf = PasswordForm(request.POST)
        if pf.is_valid():
            g = get_object_or_404(Guest, uid=request.session['recovery_uid'])
            del request.session['recovery_uid']
            g.userPassword = ssha(pf.cleaned_data['userPassword']) # ssha the new password
            g.save()
            messages.add_message(request, messages.SUCCESS, 'New password set.')
            return redirect('guest.views.home')
    else:
        obj = signing.loads(code)
        if time.time() - obj['time'] > 60*60*2: # 2 hour TTL on password reset links
            messages.add_message(request, messages.ERROR, _('The password reset link has expired. Please do recovery again for a new one.'))
            return redirect('guest.views.recover')
        else:
            g = get_object_or_404(Guest, uid=obj['uid'])
            pf = PasswordForm()
            request.session['recovery_uid'] = g.uid
    return render(request, 'guest/edit.html', {
        'form': pf,
        'title': _('Reset password'),
        })

def admin_list(request):
    q = request.GET.get('q', None)
    if q:
        query = Q(uid__icontains=q) | Q(mail__icontains=q) | Q(displayName__icontains=q)
        guests = Guest.objects.filter(query)
    else:
        guests = Guest.objects.all()
    return render(request, 'guest/admin_list.html', {
        'guests': guests,
        'title': _('Admin List'),
        })
