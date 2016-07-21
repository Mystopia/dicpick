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

ALLOWED_HOSTS = ['.dicpick.herokuapp.com', '.dicpick.com']

STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'

def maybe_cache_templates(loaders):
  return (
    ('django.template.loaders.cached.Loader', loaders),
  )

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = os.environ['SENDGRID_USERNAME']
EMAIL_HOST_PASSWORD = os.environ['SENDGRID_PASSWORD']
EMAIL_PORT = 587
EMAIL_USE_TLS = True
