# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

from allauth.account.views import logout
from allauth.socialaccount.views import login_cancelled
from allauth.socialaccount.providers.twitter import urls as twitter_urls
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic import RedirectView, TemplateView

from dicpick.admin import dpadmin_site


urlpatterns = [
  url(r'^admin/', admin.site.urls),
  url(r'^dpadmin/', dpadmin_site.urls),

  # We selectively enable just the allauth urls we allow.
  url(r'^auth/', include(twitter_urls)),
  url(r'^logout/$', logout, name='logout'),
  url('^login/cancelled/$', login_cancelled, name='socialaccount_login_cancelled'),

  url(r'^$', TemplateView.as_view(template_name='dicpick/index.html'), name='main'),

  url(r'^faq/$', TemplateView.as_view(template_name='dicpick/faq.html'), name='faq'),
  url(r'^contact_us/$', TemplateView.as_view(template_name='dicpick/contact_us.html'), name='contact_us'),
  url(r'^privacy/$', TemplateView.as_view(template_name='dicpick/privacy.html'), name='privacy'),
  url(r'^terms/$', TemplateView.as_view(template_name='dicpick/terms.html'), name='terms'),
  url(r'^favicon.ico$', RedirectView.as_view(url=staticfiles_storage.url('favicon.ico'), permanent=False)),
]
