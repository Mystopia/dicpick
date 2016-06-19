# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction


def create_user(email, first_name, last_name, num_attempts=10):
  for attempt in range(num_attempts):
    user = User()
    user.email = email
    user.first_name = first_name
    user.last_name = last_name

    if attempt == 0:
      user.username = first_name.lower()
    elif attempt == 1:
      user.username = '{}{}'.format(first_name, last_name)
    else:
      user.username = '{}{}{}'.format(first_name, last_name, attempt)

    try:
      # Since we catch an IntegrityError, we must wrap this block in a transaction.
      # See "Avoid catching exceptions inside atomic!" in https://docs.djangoproject.com/en/1.9/topics/db/transactions/.
      with transaction.atomic():
        user.save()
    except IntegrityError:
      if attempt == num_attempts - 1:
        raise
      else:
        continue
    return user
