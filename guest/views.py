# -*- coding: utf-8 -*-

from django.core.urlresolvers import reverse
from django.core import signing
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib import messages

from guest.models import Guest
from guest.forms import GuestForm, RegisterMail, RecoveryForm, PasswordForm
from guest.tools import ssha, bind


import time
import copy

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

def home(request):
    return render(request, 'guest/home.html')

def login(request):
    if request.POST:
        try:
            g = Guest.objects.get(uid=request.POST['uid'])
            if g and bind(g.dn, request.POST['userPassword']):
                request.session['uid'] = g.uid
                messages.add_message(request, messages.SUCCESS, 'Logged in as %s (%s)' % (g.uid, g.mail))
                return redirect('guest.views.me')
            else:
                messages.add_message(request, messages.ERROR, 'Wrong username and/or password')
        except Guest.DoesNotExist:
            messages.add_message(request, messages.ERROR, 'Wrong username and/or password')
    return render(request, 'guest/home.html')

def logout(request):
    if 'uid' in request.session:
        del request.session['uid']
        messages.add_message(request, messages.SUCCESS, 'Logged out.')
    else:
        messages.add_message(request, messages.ERROR, 'Not logged in.')
    return redirect('guest.views.home')


@logged_in
def me(request, guest=None):
    return render(request, 'guest/show.html', {
        'fg':guest,
        })

@logged_in
def edit_me(request, guest=None):
    if request.POST:
        old_mail = copy.copy(guest.mail)
        gf = GuestForm(request.POST, instance=guest)
        if gf.is_valid():
            if gf.cleaned_data['mail'] != old_mail:
                obj = {'uid':guest.uid, 'mail':gf.cleaned_data['mail'], 'time':time.time()}
                send_activation_mail(request, obj)
                gf.cleaned_data['mail'] = old_mail
                guest = gf.save(commit=False)
                guest.mail = old_mail
                guest.userPassword = ssha(guest.userPassword) # ssha the new password
                guest.save()
            return redirect('guest.views.me')
    else:
        gf = GuestForm(instance=guest)
    return render(request, 'guest/edit.html', {
        'form':gf,
        })

@logged_in
def delete_me(request, guest=None):
    guest.delete()
    messages.add_message(request, messages.SUCCESS, 'Account deleted.')
    return redirect('guest.views.home')

def new(request):
    if request.POST:
        f = RegisterMail(request.POST)
        if f.is_valid():
            obj = {'time':time.time(), 'mail':f.cleaned_data['mail']}
            send_activation_mail(request, obj)
    else:
        f = RegisterMail()
    return render(request, 'guest/edit.html', {
        'form':f,
        })

def send_activation_mail(request, obj):
    code = signing.dumps(obj)
    send_mail('Activation of Guest account on Feide',
              render_to_string('guest/activation_mail.txt', {'code':code}),
              settings.ACTIVATION_FROM_MAIL,
              [obj['mail']],
              fail_silently=False)
    messages.add_message(request, messages.SUCCESS, "We've sent an activation mail to your address, %s. Follow it for further instructions." % obj['mail'])

def activate(request, code=None):
    if request.POST:
        gf = GuestForm(request.POST)
        if gf.is_valid():
            if gf.cleaned_data['mail'] == request.session['validated_mail']:
                g = gf.save(commit=False)
                g.userPassword = ssha(g.userPassword) # ssha the new password
                g.save()
                del request.session['validated_mail']
                messages.add_message(request, messages.SUCCESS, 'Account %s created.' % g.uid)
                request.session['uid'] = g.uid
                return redirect('guest.views.me')
            else:
                messages.add_message(request, messages.ERROR, 'Mail %s not validated.' % gf.cleaned_data['mail'])
                return redirect('guest.views.home')

    else:
        obj = signing.loads(code)
        if time.time() - obj['time'] > 60*60*2: # 2 hour TTL on activation links
            messages.add_message(request, messages.ERROR, 'The activation link has expired. Please register again to recieve a new one.')
            return redirect('guest.views.home')
        else:
            if 'uid' in obj:
                g = get_object_or_404(Guest, uid=obj['uid'])
                g.mail = obj['mail']
                g.save()
                request.session['uid'] = g.uid
                messages.add_message(request, messages.SUCCESS, 'Mail updated.')
                return redirect('guest.views.me')
            else:
                request.session['validated_mail'] = obj['mail']
                gf = GuestForm(initial={'mail':obj['mail']})
                gf.fields['mail'].widget.attrs['readonly'] = True
    return render(request, 'guest/edit.html', {
        'form':gf,
        })

def send_recovery_mail(request, guest):
    obj = {'uid':guest.uid, 'time':time.time()}
    code = signing.dumps(obj)
    send_mail('Password recovery for Guest account on Feide',
              render_to_string('guest/recovery_mail.txt', {'guest':guest, 'code':code}),
              settings.ACTIVATION_FROM_MAIL,
              [guest.mail],
              fail_silently=False)
    messages.add_message(request, messages.SUCCESS, "We've sent recovery mail to your mail address, %s. Follow it for further instructions." % guest.mail)
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
        f.fields['ident'].error = 'Username or mail not found.'
    else:
        f = RecoveryForm()
    return render(request, 'guest/edit.html',{
        'form':f,
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
            messages.add_message(request, messages.ERROR, 'The password reset link has expired. Please do recovery again for a new one.')
            return redirect('guest.views.recover')
        else:
            g = get_object_or_404(Guest, uid=obj['uid'])
            pf = PasswordForm()
            request.session['recovery_uid'] = g.uid
    return render(request, 'guest/edit.html', {
        'form':pf,
        })
