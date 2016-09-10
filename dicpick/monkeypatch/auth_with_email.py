# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (absolute_import, division, generators, nested_scopes,
                        print_function, unicode_literals, with_statement)

from django.contrib.auth.models import User


def patch():
  # Monkeypatch uniqueness for email addresses.
  User._meta.get_field('email')._unique = True

  # Monkeypatch to use email for authentication.
  # Note that REQUIRED_FIELDS (the extra field names that will be prompted for when creating a user via the
  # createsuperuser management command) is ['email'] by default.  However django does not allow it to contain
  # the USERNAME_FIELD (as that field is always prompted for, and so is not 'extra').
  # Therefore in order to set USERNAME_FIELD to 'email' we must remove 'email' from REQUIRED_FIELDS.
  # On the other hand, we must add 'username' to REQUIRED_FIELDS, because it is in fact required on the model
  # (i.e., it does not have blank=True).  For details see:
  # https://docs.djangoproject.com/en/1.9/topics/auth/customizing/#django.contrib.auth.models.CustomUser.REQUIRED_FIELDS.
  User.REQUIRED_FIELDS = ['username']
  User.USERNAME_FIELD = 'email'
