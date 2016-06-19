# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.contrib.auth.forms import AuthenticationForm


class CustomAuthenticationForm(AuthenticationForm):
  def __init__(self, request, *args, **kwargs):
    super(CustomAuthenticationForm, self).__init__(request, *args, **kwargs)
    self.helper = FormHelper(self)
    self.helper.form_class = 'form-horizontal'
    self.helper.label_class = 'col-lg-2'
    self.helper.field_class = 'col-lg-4'
    self.helper.add_input(Submit('login', 'Login'))
