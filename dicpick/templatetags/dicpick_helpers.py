# coding=utf-8
# Copyright 2016 Mystopia.
import datetime

from django import template
from django.forms import BaseForm
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter('any')
def any_(iterable):
  return any(iterable)

@register.filter
def date_to_slug(date):
  return date.strftime('%Y_%m_%d')


# The dates of the burn for the next few years.  Update this before 2020.
burns = {datetime.date(2016, 9, 3), datetime.date(2017, 9, 2), datetime.date(2018, 9, 1),
         datetime.date(2019, 8, 31), datetime.date(2020, 9, 5)}


burn_logo = ")'("


@register.filter
def is_burn(dt):
  return dt in burns


@register.filter
def date_to_pretty_str(dt):
  return dt.strftime('%A, %B %d %Y')


@register.filter
def date_to_short_str(dt):
  ret = dt.strftime('%a %m/%d')
  if is_burn(dt):
    ret = '{} {}'.format(burn_logo, ret)
  return ret


@register.filter
def date_to_shortest_str(dt):
  return dt.strftime('%m/%d')


@register.filter
def format_designator(form):
  v = form.designator()
  if isinstance(v, datetime.date):
    return date_to_short_str(v)
  else:
    return v


@register.filter
def add_standard_classes(bound_field):
  widget_name = type(bound_field.field.widget).__name__.lower()
  form_control_class = '' if widget_name == 'checkboxinput' else 'form-control'
  css_class = '{} field-{} widget-{}'.format(form_control_class, bound_field.name, widget_name)
  return bound_field.as_widget(attrs={'class':css_class})


@register.filter(needs_autoescape=True)
def lightweight_formatting(text, autoescape=True):
  if autoescape:
    esc = conditional_escape
  else:
    esc = lambda x: x

  def indents(line):
    i = 0
    ret = ''
    while i < len(line) and line[i] == ' ':
      ret += '&nbsp;'
      i += 1
    ret += line[i:]
    return ret

  def newlines(block):
    return '<br>'.join([indents(esc(s)) for s in block.split('\n')])

  blocks = text.split('```')
  codified = ''
  for i in range(0, len(blocks) - 1):
    codified += newlines(blocks[i])
    if i % 2 == 0:
      codified += '<code>'
    else:
      codified += '</code>'
  codified += newlines(blocks[-1])

  return mark_safe(codified)


@register.filter(needs_autoescape=True)
def nbspify(text, autoescape=True):
  if autoescape:
    esc = conditional_escape
  else:
    esc = lambda x: x
  return mark_safe('&nbsp;'.join([esc(s) for s in text.split(' ')]))


@register.filter
def get_item(dictionary, key):
  return dictionary[key]


@register.filter
def has_required_fields(form):
  return _has_field_with_property(form, lambda field: field.required)


def _has_field_with_property(form, predicate):
  if isinstance(form, BaseForm):
    return any(predicate(x) for x in list(form.fields.values()))
  else:  # Assume it's a FormSet.
    return any(predicate(x) for x in list(form.forms[0].fields.values()))
