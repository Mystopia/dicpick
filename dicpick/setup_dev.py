# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

from materiality.util.setup_dev import SetupDev


class DicPickSetupDev(SetupDev):
  @classmethod
  def create(cls):
    return super(DicPickSetupDev, cls).create(app_name='dicpick')


if __name__ == '__main__':
  DicPickSetupDev.create().setup()
