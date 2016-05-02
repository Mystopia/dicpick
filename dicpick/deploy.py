# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

from materiality.util.deploy import Deployer


class DicPickDeployer(Deployer):
  def __init__(self):
    super(DicPickDeployer, self).__init__('cardigan')

  def compile_js(self):
    return []


if __name__ == '__main__':
  DicPickDeployer().deploy()
