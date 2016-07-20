# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (absolute_import, division, generators, nested_scopes,
                        print_function, unicode_literals, with_statement)

import logging.config
import os

SITE_ID = 1

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PASSWORD_HASHERS = [
  # Require bcrypt.
  'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]


# Set up logging without allowing Django to add its defaults, as they are notoriously difficult to override properly.

LOGGING_CONFIG = None

LOGGING = {
  'version': 1,
  'formatters': {
    'default': {
      'format': '[%(asctime)s %(levelname)s %(pathname)s:%(lineno)s] %(message)s',
      'datefmt': '%Y-%m-%d %H:%M:%S'
    }
  },
  'handlers': {
    'console': {
      'class': 'logging.StreamHandler',
      'level': 'DEBUG',
      'formatter': 'default'
    },
    'file': {
      'class': 'logging.FileHandler',
      'level': 'INFO',
      'filename': '/tmp/sql_debug.log',
      'formatter': 'default'
    },
  },
  'loggers': {
    # Everything will propagate to the root logger.  Note that the special name 'root' represents the logger at
    # the root of the dotted-string hierarchy, and which you'd logically expect to be represented by an empty string.
    'root': {
      'handlers': ['console'],
      'level': 'WARNING'
    },
    'django': {
      'handlers': ['console'],
      'level': 'INFO'
    },
    'dicpick': {
      'handlers': ['console'],
      'level': 'INFO'
    },
    'django.db.backends': {
      'handlers': ['file', 'console'],
      'level': 'INFO',  # Set to DEBUG to see live SQL queries.
      'propagate': False,
    },
  }
}

logging.config.dictConfig(LOGGING)


ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
  # First in the list, so it can overide the standard collectstatic command.
  'materiality.django.static',

  'django.contrib.admin',
  'django.contrib.auth',
  'django.contrib.contenttypes',
  'django.contrib.sessions',
  'django.contrib.sites',
  'django.contrib.messages',
  'django.contrib.staticfiles',

  #'debug_toolbar',

  'dicpick.apps.DicPickConfig',
)

MIDDLEWARE_CLASSES = (
  #'debug_toolbar.middleware.DebugToolbarMiddleware',
  'django.contrib.sessions.middleware.SessionMiddleware',
  'django.middleware.locale.LocaleMiddleware',
  'django.middleware.common.CommonMiddleware',
  'django.middleware.csrf.CsrfViewMiddleware',
  'django.contrib.auth.middleware.AuthenticationMiddleware',
  'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
  'django.contrib.messages.middleware.MessageMiddleware',
  'django.middleware.clickjacking.XFrameOptionsMiddleware',
  'django.middleware.security.SecurityMiddleware',
)

AUTHENTICATION_BACKENDS = (
  'django.contrib.auth.backends.ModelBackend',
)

LOGIN_REDIRECT_URL = 'main'

ROOT_URLCONF = 'main.urls'

WSGI_APPLICATION = 'main.wsgi.application'


LANGUAGE_CODE = 'de'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = False
USE_TZ = True


LANGUAGES = [
  ('en', 'English'),
  ('en-mystopia', 'Mystopia'),
]


STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(SITE_ROOT, 'staticfiles')

STATICFILES_FINDERS = (
  'django.contrib.staticfiles.finders.FileSystemFinder',
  'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)


DICPICK_ENV = os.environ.get('DICPICK_ENV', 'dicpick_dev')

if DICPICK_ENV == 'dicpick_dev':
  from main.settings_dev import *
elif DICPICK_ENV == 'dicpick_prod':
  from main.settings_prod import *

INTERNAL_IPS = [
  '127.0.0.1'
]

template_loaders = (
  'django.template.loaders.filesystem.Loader',
  'django.template.loaders.app_directories.Loader',
)

TEMPLATES = [
  {
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [
      # Overrides of templates loaded by other apps, if any.
      # These paths should use forward slashes even on Windows.
      '{}/dicpick/templates'.format(SITE_ROOT)
    ],
    'OPTIONS': {
    'context_processors': [
      'django.template.context_processors.debug',
      'django.template.context_processors.request',
      'django.contrib.auth.context_processors.auth',
      'django.contrib.messages.context_processors.messages',
    ],
    'loaders': maybe_cache_templates(template_loaders),
    'debug': DEBUG,
    },
  },
]

DEFAULT_FROM_EMAIL = 'no-reply@mystopia.camp'

MATERIALITY_DJANGO_STATIC_IGNORE_FILE = 'main/ignore_patterns.txt'

DATE_INPUT_FORMATS = [
  '%m/%d/%Y'
]

DEBUG_TOOLBAR_PATCH_SETTINGS = False
