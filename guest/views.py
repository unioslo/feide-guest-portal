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
from guest.forms import GuestFormCreate, GuestFormEdit, GuestFormAdmin, RegisterMail, RecoveryForm, PasswordForm
from guest.tools import ssha, bind


import time
import logging

logger = logging.getLogger(__name__)

def only_admin(fun):
    def closure(request, *args, **kwargs):
        if 'REMOTE_USER' in request.META and request.META['REMOTE_USER'] in settings.FEIDE_ADMIN_ACCOUNTS:
            request.is_admin = True
            if 'uid' in kwargs:
                guest = get_object_or_404(Guest, uid=kwargs['uid'])
                del kwargs['uid']
                kwargs['guest'] = guest
            return fun(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return closure

def logged_in(fun):
    def closure(request, *args, **kwargs):
        request.is_admin = False
        if 'uid' in request.session:
            uid = request.session['uid']
            try:
                g = Guest.objects.get(uid=uid)
                return fun(request, *args, guest=g, **kwargs)
            except Guest.DoesNotExist:
                return redirect('guest.views.logout')
        else:
            redir = redirect('guest.views.login')
            redir['LOCATION'] += '?next='+request.path
            return redir
    return closure

def change_locale(request):
    if 'locale' in request.GET:
        locale = request.GET['locale']
        request.session['django_language'] = locale
        if 'next' in request.GET:
            response = redirect(request.GET.get('next','guest.views.home'))
        else:
           response = redirect('guest.views.home')
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, locale)
        return response
    else:
        return redirect('guest.views.home')

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
                messages.add_message(request, messages.SUCCESS, _('Logged in as %(uid)s (%(mail)s)') % {'uid':g.uid, 'mail':g.mail})
                return redirect('guest.views.me')
            else:
                messages.add_message(request, messages.ERROR, _('Wrong username and/or password'))
                logger.warning('User entered wrong username/password')
        except Guest.DoesNotExist:
            messages.add_message(request, messages.ERROR, _('Wrong username and/or password'))
            logger.warning('User entered wrong username/password')
    next = request.GET.get('next','/')
    return render(request, 'guest/login.html', {
        'title': _('Login'),
        'next': next,
        })

def logout(request):
    if 'uid' in request.session:
        del request.session['uid']
        messages.add_message(request, messages.SUCCESS, _('Logged out.'))
    else:
        messages.add_message(request, messages.ERROR, _('Not logged in.'))
        logger.warning("User tried to log out although he wasn't logged in.")
    return redirect('guest.views.home')


def show(request, guest=None):
    return render(request, 'guest/show.html', {
        'fg': guest,
        'title': _('Showing %(name)s') % {'name': guest.displayName},
        })
me = logged_in(show)
admin_show = only_admin(show)

@logged_in
def edit_me(request, guest=None):
    if request.POST:
        gf = GuestFormEdit(request.POST)
        if gf.is_valid():
            guest.givenName = gf.cleaned_data['givenName']
            guest.sn = gf.cleaned_data['sn']
            if gf.cleaned_data['userPassword']: # password changed
                guest.userPassword = ssha(gf.cleaned_data['userPassword']) # ssha the new password
            guest.save()

            f_mail = gf.cleaned_data['mail']
            if f_mail and f_mail != guest.mail: # mail changed
                obj = {'uid':guest.uid, 'mail':f_mail, 'time':time.time()}
                send_activation_mail(request, obj)
            return redirect('guest.views.me')
    else:
        m = model_to_dict(guest)
        m.pop('mail')
        gf = GuestFormEdit(initial=m)
    return render(request, 'guest/edit.html', {
        'form':gf,
        'guest':guest,
        'title': _('Edit %(name)s') % {'name': guest.displayName},
        })

@only_admin
def admin_edit(request, guest=None):
    if request.POST:
        gf = GuestFormAdmin(request.POST)
        guest.uid = gf['uid'].value()
        guest.mail = gf['mail'].value()
        guest.givenName = gf['givenName'].value()
        guest.sn = gf['sn'].value()
        if gf['userPassword'].value(): # password changed
            guest.userPassword = ssha(gf['userPassword'].value()) # ssha the new password
        guest.save()
        return redirect('guest.views.admin_show', uid=guest.uid)
    else:
        gf = GuestFormAdmin(initial=model_to_dict(guest))
    return render(request, 'guest/edit.html', {
        'form':gf,
        'guest':guest,
        'title': _('Edit %(name)s') % {'name': guest.displayName},
        })

def delete(request, guest=None):
    guest.delete()
    messages.add_message(request, messages.SUCCESS, _('Account deleted.'))
    if request.is_admin:
        return redirect('guest.views.admin_list')
    else:
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
    return render(request, 'guest/form.html', {
        'form': f,
        'title': _('New Guest Account'),
        })

def send_activation_mail(request, obj):
    code = signing.dumps(obj)
    url = request.build_absolute_uri(reverse('guest.views.activate', kwargs={'code':code}))
    send_mail(_('Activation of Guest account on Feide'),
              render_to_string('guest/activation_mail.txt', {'url':url}),
              settings.ACTIVATION_FROM_MAIL,
              [obj['mail']],
              fail_silently=False)
    messages.add_message(request, messages.SUCCESS, _("We've sent an activation mail to your address, %(mail)s. Follow it for further instructions.") % {'mail': obj['mail']})

def activate(request, code=None):
    if request.POST:
        gf = GuestFormCreate(request.POST)
        if gf.is_valid():
            g = Guest()
            g.uid = gf.cleaned_data['uid']
            g.mail = request.session['validated_mail']
            g.givenName = gf.cleaned_data['givenName']
            g.sn = gf.cleaned_data['sn']
            g.userPassword = ssha(gf.cleaned_data['userPassword']) # ssha the new password
            g.save()
            del request.session['validated_mail']
            messages.add_message(request, messages.SUCCESS, _('Account %(uid)s created.') % {'uid': g.uid})
            request.session['uid'] = g.uid
            return redirect('guest.views.me')
    else:
        try:
            obj = signing.loads(code)
        except signing.BadSignature:
            messages.add_message(request, messages.ERROR, _("The activation link is broken. Are you shure you've entered it correctly?"))
            logger.error('User entered broken activation link. Possible user copy/paste error.')
            return redirect('guest.views.home')
        if time.time() - obj['time'] > 60*60*settings.LINK_EXPIRY:
            messages.add_message(request, messages.ERROR, _('The activation link has expired. Please register again to recieve a new one.'))
            logger.error('User entered expired activation link. Possible server clock error. If not, consider increasing the LINK_EXPIRY setting.')
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
                gf = GuestFormCreate()
    return render(request, 'guest/form.html', {
        'form': gf,
        'title': _('Activate account'),
        })

def send_recovery_mail(request, guest):
    obj = {'uid':guest.uid, 'time':time.time()}
    code = signing.dumps(obj)
    url = request.build_absolute_uri(reverse('guest.views.reset_password', kwargs={'code':code}))

    send_mail(_('Password recovery for Guest account on Feide'),
              render_to_string('guest/recovery_mail.txt', {'guest':guest, 'url':url}),
              settings.ACTIVATION_FROM_MAIL,
              [guest.mail],
              fail_silently=False)
    messages.add_message(request, messages.SUCCESS, _("We've sent recovery mail to your mail address, %(mail)s. Follow it for further instructions.") % {'mail': guest.mail})
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
    return render(request, 'guest/form.html',{
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
        if time.time() - obj['time'] > 60*60*settings.LINK_EXPIRY:
            messages.add_message(request, messages.ERROR, _('The password reset link has expired. Please do recovery again for a new one.'))
            logger.error('User entered expired password reset link. Possible server clock error. If not, consider increasing the LINK_EXPIRY setting.')
            return redirect('guest.views.recover')
        else:
            g = get_object_or_404(Guest, uid=obj['uid'])
            pf = PasswordForm()
            request.session['recovery_uid'] = g.uid
    return render(request, 'guest/form.html', {
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
