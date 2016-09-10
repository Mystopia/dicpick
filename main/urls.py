# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (absolute_import, division, generators, nested_scopes,
                        print_function, unicode_literals, with_statement)

import debug_toolbar
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic import RedirectView, TemplateView

from dicpick.monkeypatch import auth_with_email
from dicpick import urls as dicpick_urls


urlpatterns = [
  url(r'^admin/', admin.site.urls),
  url(r'^accounts/login/$', auth_views.login),
  url('^accounts/', include('django.contrib.auth.urls')),

  url(r'^faq/$', TemplateView.as_view(template_name='dicpick/faq.html'), name='faq'),
  url(r'^contact_us/$', TemplateView.as_view(template_name='dicpick/contact_us.html'), name='contact_us'),
  url(r'^privacy/$', TemplateView.as_view(template_name='dicpick/privacy.html'), name='privacy'),
  url(r'^terms/$', TemplateView.as_view(template_name='dicpick/terms.html'), name='terms'),
  url(r'^favicon.ico$', RedirectView.as_view(url=staticfiles_storage.url('favicon.ico'), permanent=False)),

  url(r'^__debug__/', include(debug_toolbar.urls)),
  url(r'^', include(dicpick_urls, namespace='dicpick')),
]


# Monkeypatching goes here because this file is guaranteed to execute before any requests are handled.
auth_with_email.patch()
