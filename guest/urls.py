# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url

import guest.views
dir(guest.views)

urlpatterns = patterns('',
    url(r'^$', 'guest.views.home'),
    url(r'^login$', 'guest.views.login'),
    url(r'^logout$', 'guest.views.logout'),
    url(r'^new$', 'guest.views.new'),
    url(r'^me$', 'guest.views.me'),
    url(r'^me/edit$', 'guest.views.edit_me'),
    url(r'^me/delete$', 'guest.views.delete_me'),
    url(r'^activate/(?P<code>.+)$', 'guest.views.activate'),
    url(r'^recover$', 'guest.views.recover'),
    url(r'^reset/(?P<code>.+)$', 'guest.views.reset_password'),

    url(r'^change_locale$', 'guest.views.change_locale'),

    url(r'^admin/$', 'guest.views.admin_list'),
    url(r'^admin/(?P<uid>[^/]+)$', 'guest.views.admin_show', name='admin_show'),
    url(r'^admin/(?P<uid>[^/]+)/edit$', 'guest.views.admin_edit', name='admin_edit'),
    url(r'^admin/(?P<uid>[^/]+)/delete$', 'guest.views.admin_delete', name='admin_delete'),
)
