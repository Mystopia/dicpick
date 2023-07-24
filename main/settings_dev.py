# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (absolute_import, division, generators, nested_scopes,
                        print_function, unicode_literals, with_statement)

import sys

# SECURITY WARNING: don't run with debug turned on in production!

DEBUG = True

# Uncomment these to test locally with no debug info (e.g., to see what a real user would see when an error occurs).
# You will also need to add the --insecure flag to run_dev_server.sh.
# DEBUG = False
# ALLOWED_HOSTS = ['localhost']

# Get local settings from file.
try:
  from main.settings_local import *
except ImportError as e:
  print('ERROR: No local settings file at settings_local.py! Exiting.')
  sys.exit(1)


#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.postgresql_psycopg2',
#        'NAME': 'dicpick',
#        'USER': 'dicpick',
#        'PASSWORD': DEFAULT_DATABASE_PASSWORD,
#        'HOST': '127.0.0.1',
#        'PORT': '5432',
#    }
#}


WITH_CACHING = False
def maybe_cache_templates(loaders):
  if WITH_CACHING:
    return (
      ('django.template.loaders.cached.Loader', loaders),
    )
  else:
    return loaders  # No caching.


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
