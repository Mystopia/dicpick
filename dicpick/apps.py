# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (absolute_import, division, generators, nested_scopes,
                        print_function, unicode_literals, with_statement)

from django.apps import AppConfig


class DicPickConfig(AppConfig):
  name = 'dicpick'

  def ready(self):
    import dicpick.signals
