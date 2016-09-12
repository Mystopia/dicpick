# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (absolute_import, division, generators, nested_scopes,
                        print_function, unicode_literals, with_statement)

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction


def create_user(email, first_name, last_name, num_attempts=10):
  """Helper function to create a User instance based on an email address, first name and last name.

  To successfully create a User we need to synthesize a unique username.  We try this num_attempts times
  before giving up.
  """
  for attempt in range(num_attempts):
    user = User()
    user.email = email
    user.first_name = first_name
    user.last_name = last_name
    # Various django auth flows assume (e.g., password reset) require a non-null password.
    # The user can do a password reset in the future to get a usable password.
    user.password = make_password(User.objects.make_random_password())

    if attempt == 0:
      user.username = first_name.lower()[:30]
    elif attempt == 1:
      user.username = '{}{}'.format(first_name, last_name)[:30]
    else:
      user.username = '{}{}'.format('{}{}'.format(first_name, last_name)[:29], attempt)

    try:
      # Since we catch an IntegrityError, we must wrap this block in a transaction.
      # See "Avoid catching exceptions inside atomic!" in https://docs.djangoproject.com/en/1.9/topics/db/transactions/.
      with transaction.atomic():
        user.save()
    except IntegrityError:
      if attempt >= num_attempts - 1:
        raise
      else:
        continue
    return user
