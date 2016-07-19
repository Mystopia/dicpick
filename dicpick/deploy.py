# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (absolute_import, division, generators, nested_scopes,
                        print_function, unicode_literals, with_statement)

from materiality.util.deploy import Deployer


class DicPickDeployer(Deployer):
  def __init__(self):
    super(DicPickDeployer, self).__init__('dicpick')

  def compile_js(self):
    return []


if __name__ == '__main__':
  DicPickDeployer().deploy()
