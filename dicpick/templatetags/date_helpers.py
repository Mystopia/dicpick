# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (absolute_import, division, generators, nested_scopes,
                        print_function, unicode_literals, with_statement)

from django import template

register = template.Library()


@register.filter
def to_slug(date):
  return date.strftime('%Y_%m_%d')


@register.filter
def to_pretty_str(date):
  return date.strftime('%d %b %Y')
