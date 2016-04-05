# coding=utf-8
# Copyright 2016 Materiality Labs.

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

from materiality.util.setup_prod import SetupProd


class DicPickSetupProd(SetupProd):
  @classmethod
  def create(cls):
    return super(DicPickSetupProd, cls).create(app_name='dicpick')


if __name__ == '__main__':
  DicPickSetupProd.create().setup()
