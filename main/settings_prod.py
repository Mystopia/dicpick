# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (absolute_import, division, generators, nested_scopes,
                        print_function, unicode_literals, with_statement)

import os

import dj_database_url

# SECURITY WARNING: don't run with debug turned on in production!
if 'TEMPORARY_PROD_DEBUG_MODE_REMOVE_ME' in os.environ:
  DEBUG = True
else:
  DEBUG = False


# Get local settings from heroku environment.
SECRET_KEY = os.environ['SECRET_KEY']
TWITTER_APP_ID = os.environ['TWITTER_APP_ID']
TWITTER_APP_SECRET = os.environ['TWITTER_APP_SECRET']

SECURE_SSL_REDIRECT = True

# Honor the 'X-Forwarded-Proto' header for request.is_secure().
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Enable HSTS.
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Parse database configuration from $DATABASE_URL.
DATABASES = {
  'default': dj_database_url.config()
}

DATABASES['default']['CONN_MAX_AGE'] = 3600

ALLOWED_HOSTS = ['.funky-appname-1234.herokuapp.com', '.dicpick.com']

STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'

def maybe_cache_templates(loaders):
  return (
    ('django.template.loaders.cached.Loader', loaders),
  )
