# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

import guest.views
dir(guest.views)

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'guest.views.home', name='home'),
    # url(r'^guest/', include('guest.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    url(r'^guest/$', 'guest.views.home'),
    url(r'^guest/login$', 'guest.views.login'),
    url(r'^guest/logout$', 'guest.views.logout'),
    url(r'^guest/new$', 'guest.views.new'),
    url(r'^guest/me$', 'guest.views.me'),
    url(r'^guest/me/edit$', 'guest.views.edit_me'),
    url(r'^guest/me/delete$', 'guest.views.delete_me'),
    url(r'^guest/activate/(?P<code>.+)$', 'guest.views.activate'),
    url(r'^guest/recover$', 'guest.views.recover'),
    url(r'^guest/reset/(?P<code>.+)$', 'guest.views.reset_password'),
)
