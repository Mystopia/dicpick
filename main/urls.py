# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (absolute_import, division, generators, nested_scopes,
                        print_function, unicode_literals, with_statement)

import debug_toolbar
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import User
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic import RedirectView, TemplateView

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


# Monkeypatch uniqueness for email addresses.
User._meta.get_field('email')._unique = True

# Monkeypatch to use email for authentication.
# Note that REQUIRED_FIELDS (the field names that will be prompted for when creating a user via the
# createsuperuser management command)is ['email'] by default.  But django does not allow it to contain
# the USERNAME_FIELD (as that field is always prompted for).  So resetting it here both allows us to
# use email as USERNAME_FIELD, and also makes sure that we're prompted for username.
User.REQUIRED_FIELDS = ['username']
User.USERNAME_FIELD = 'email'
