# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (absolute_import, division, generators, nested_scopes,
                        print_function, unicode_literals, with_statement)

from django.contrib.auth.management.commands.createsuperuser import Command as CreateSuperUserCommand

from dicpick.monkeypatch import auth_with_email

# Note that this lives under dicpick.monkeypatch.management, instead of under dicpick.management,
# so that we can put it above django.contrib.auth in INSTALLED_APPS, thus overriding the standard createsuperuser.

auth_with_email.patch()


Command = CreateSuperUserCommand
