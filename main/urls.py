# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic import RedirectView, TemplateView

import debug_toolbar

from dicpick import urls as dicpick_urls
from main.custom_auth_forms import CustomAuthenticationForm


urlpatterns = [
  url(r'^admin/', admin.site.urls),
  url(r'^accounts/login/$', auth_views.login, {'authentication_form': CustomAuthenticationForm}),
  url('^accounts/', include('django.contrib.auth.urls')),

  url(r'^faq/$', TemplateView.as_view(template_name='dicpick/faq.html'), name='faq'),
  url(r'^contact_us/$', TemplateView.as_view(template_name='dicpick/contact_us.html'), name='contact_us'),
  url(r'^privacy/$', TemplateView.as_view(template_name='dicpick/privacy.html'), name='privacy'),
  url(r'^terms/$', TemplateView.as_view(template_name='dicpick/terms.html'), name='terms'),
  url(r'^favicon.ico$', RedirectView.as_view(url=staticfiles_storage.url('favicon.ico'), permanent=False)),

  url(r'^__debug__/', include(debug_toolbar.urls)),
  url(r'^', include(dicpick_urls, namespace='dicpick')),
]
