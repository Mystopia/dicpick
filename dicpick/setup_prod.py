# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (absolute_import, division, generators, nested_scopes,
                        print_function, unicode_literals, with_statement)

from materiality.util.setup_prod import SetupProd


class DicPickSetupProd(SetupProd):
  @classmethod
  def create(cls):
    return super(DicPickSetupProd, cls).create(app_name='dicpick', twitter_api=False)


if __name__ == '__main__':
  DicPickSetupProd.create().setup()
