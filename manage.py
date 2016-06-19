#!/usr/bin/env ./venv/bin/python
# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import os
import sys


if __name__ == '__main__':
  os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
  from django.core.management import execute_from_command_line
  execute_from_command_line(sys.argv)
