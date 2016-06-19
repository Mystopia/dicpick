# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

from django.apps import AppConfig


class DicPickConfig(AppConfig):
  name = 'dicpick'

  def ready(self):
    import dicpick.signals
