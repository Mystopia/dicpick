# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import re

import requests
from django.contrib.auth.models import User
from django.forms import ModelForm, ValidationError, Form, FileField, URLField, TextInput, CharField, MultiValueField, \
  MultiWidget, HiddenInput, DateInput, BaseInlineFormSet, BaseModelFormSet, Field
from django.forms.utils import pretty_name
from django.shortcuts import get_object_or_404

from dicpick.models import Event, Tag, TaskType, Participant, Task
from dicpick.util import create_user


class DicPickModelForm(ModelForm):
  def __init__(self, *args, **kwargs):
    super(DicPickModelForm, self).__init__(*args, **kwargs)
    for field in self.fields.values():
      field.error_messages = {'required': 'Required'}

  def has_designator(self):
    return hasattr(self.Meta, 'designator_field')

  def designator_name(self):
    return pretty_name(self.Meta.designator_field)

  def designator(self):
    return getattr(self.instance, self.Meta.designator_field)


class EventForm(DicPickModelForm):
  class Meta:
    model = Event
    fields = ['name', 'slug', 'start_date', 'end_date']
    help_texts = {
      'start_date': 'First day of event',
      'end_date': 'Last day of event',
    }

  def clean(self):
    data = super(EventForm, self).clean()
    if data.get('start_date') > data.get('end_date'):
      raise ValidationError('Start date must precede end date.')
    return data


class FormWithTags(DicPickModelForm):
  """Form base that accepts tag_choices instead of attempting to compute them.

  Computing them would involve re-evaluating the same queryset for every form in a formset.
  """
  def __init__(self, *args, **kwargs):
    tags = kwargs.pop('tag_choices')
    super(FormWithTags, self).__init__(*args, **kwargs)
    tags_field = self.fields['tags']
    tags_field.choices = [(tags_field.prepare_value(obj), tags_field.label_from_instance(obj)) for obj in tags]


class TagForm(DicPickModelForm):
  class Meta:
    model = Tag
    fields = ['name']
    qualifier = 'tag'


class TaskTypeForm(FormWithTags):
  class Meta:
    model = TaskType
    fields = ['name', 'start_date', 'end_date', 'num_people', 'score', 'tags']
    qualifier = 'tasktype'
    labels = {
      'num_people': '# people'
    }
    help_texts = {
      'name': 'E.g., Dinner Sous Chef',
      'start_date': 'First day on which tasks of this type must be performed',
      'end_date': 'Last day on which tasks of this type must be performed',
      'num_people': 'Number of people needed to perform tasks of this type each day',
      'score': 'Score each person performing this task earns for doing so',
      'tags': 'Only people with at least one of these tags can be assigned tasks of this type'
    }


class TaskByTypeForm(FormWithTags):
  class Meta:
    model = Task
    fields = ['date', 'num_people', 'score', 'tags']
    qualifier = 'task'
    widgets = {
      'date': DateInput(attrs={'disabled': True})
    }
    help_texts = {
      'num_people': 'Number of people needed to perform this task on this day',
      'score': 'Score each person performing this task on this day earns for doing so',
      'tags': 'Only people with at least one of these tags can be assigned this task on this day'
    }


class TaskByDateForm(FormWithTags):
  class Meta:
    model = Task
    fields = ['num_people', 'score', 'tags']
    qualifier = 'task'
    help_texts = {
      'num_people': 'Number of people needed to perform this task on this day',
      'score': 'Score each person performing this task on this day earns for doing so',
      'tags': 'Only people with at least one of these tags can be assigned this task on this day'
    }
    designator_field = 'task_type'


class UserWidget(MultiWidget):
  placeholder = 'Jane Doe (jane.doe@email.com)'
  def __init__(self, attrs=None):
    self.users_by_id = None  # Will be set when the form is created.
    super(UserWidget, self).__init__((HiddenInput, TextInput(attrs={'class': 'user-widget',
                                                                    'placeholder': self.placeholder})), attrs)

  def decompress(self, user_id):
    if user_id is None:
      return [None, '']
    user = self.users_by_id[user_id]
    return [user.id, '{} {} ({})'.format(user.first_name, user.last_name, user.email)]


class UserField(MultiValueField):
  user_re = re.compile(r'^\s*(?P<first_name>[A-Za-z\- ]+)\s+(?P<last_name>[A-Za-z\-]+)\s+\(\s*(?P<email>\S+)\s*\)\s*$')

  def __init__(self, *args, **kwargs):
    super(UserField, self).__init__((CharField(required=False), CharField()),
                                    *args,
                                    widget=UserWidget(),
                                    require_all_fields=False,
                                    **kwargs)

  def compress(self, data_list):
    user_id, data_str = data_list
    m = self.user_re.match(data_str)
    if m is None:
      raise ValidationError('User field must be of the form: First Last (Email)')
    email = m.group('email')
    first_name = m.group('first_name').strip()
    last_name = m.group('last_name')

    if not user_id:
      # See if we know the email address.  Note that this only happens for the extra forms.
      try:
        user = User.objects.filter(email=email).get()
      except User.DoesNotExist:
        # We must create the new user here, not in the view, because standard ModelForm validation on ParticipantForm
        # will require a non-empty user_id in the user field (as it's not nullable in the Participant model).
        user = create_user(email, first_name, last_name)
    else:
      # Update the fields if needed.
      # TODO: A more elegant way to only save if there are changes.
      user = get_object_or_404(User, pk=user_id)

    save = False
    if user.email != email:
      user.email = email
      save = True
    if user.first_name != first_name:
      user.first_name = first_name
      save = True
    if user.last_name != last_name:
      user.last_name = last_name
      save = True
    if save:
      user.save()

    return user


class ParticipantForm(FormWithTags):
  class Meta:
    model = Participant
    fields = ['user', 'start_date', 'end_date', 'tags', 'initial_score']
    qualifier = 'participant'
    labels = {
      'initial_score': 'Score'
    }
    help_texts = {
      'start_date': 'First day person is available for tasks',
      'end_date': 'Last day person is available for tasks',
      'initial_score': 'Score person has already earned from out-of-band contributions',
      'tags': 'Tags describing this person',
    }

  user = UserField(help_text="Identify new or existing users as Firstname Lastname (email)")

  def __init__(self, *args, **kwargs):
    # Apply the hack to pass the id -> user map into the widget.
    # See ParticipantInlineFormset below for details.
    users_by_id = kwargs.pop('users_by_id')
    super(ParticipantForm, self).__init__(*args, **kwargs)
    self.fields['user'].widget.users_by_id = users_by_id


class ParticipantImportForm(Form):
  file = FileField(label='Upload file', required=False)
  url = URLField(label='Fetch from URL', required=False)

  def clean(self):
    super(ParticipantImportForm, self).clean()
    has_file = self.cleaned_data['file'] is not None
    has_url = self.cleaned_data['url'] != ''
    if not has_file and not has_url:
      raise ValidationError('Either a file or a URL must be provided.')
    elif has_file and has_url:
      raise ValidationError('Do not specify both a file and a URL.')

    if has_url:
      url = self.cleaned_data.get('url')
      try:
        r = requests.get(url)
      except IOError:
        raise ValidationError('Failed to fetch data from {}'.format(url))
      if r.status_code != 200:
        raise ValidationError('Failed to fetch data from {} (received status {} {})'.format(url, r.status_code, r.reason))
      try:
        self.cleaned_data['data_from_url'] = r.json()
      except ValueError:
        raise ValidationError('Invalid JSON at {}'.format(url))


class TagChoicesFormsetMixin(object):
  def __init__(self, *args, **kwargs):
    event = kwargs.pop('event')
    super(TagChoicesFormsetMixin, self).__init__(*args, **kwargs)
    self._tag_choices = Tag.objects.filter(event=event)

  def get_form_kwargs(self, index):
    kwargs = super(TagChoicesFormsetMixin, self).get_form_kwargs(index)
    if 'tags' in self.form.base_fields:
      kwargs['tag_choices'] = self._tag_choices
    return kwargs


class InlineFormsetWithTagChoices(TagChoicesFormsetMixin, BaseInlineFormSet):
  """InlineFormset base with a hack to pass the set of tag choices into each form.

  Otherwise the standard django code will re-evaluate the queryset (and hit the database) once per form.
  """
  pass


class ModelFormsetWithTagChoices(TagChoicesFormsetMixin, BaseModelFormSet):
  """Formset base with a hack to pass the set of tag choices into each form.

  Otherwise the standard django code will re-evaluate the queryset (and hit the database) once per form.
  """
  pass


class ParticipantInlineFormset(InlineFormsetWithTagChoices):
  def __init__(self, *args, **kwargs):
    super(ParticipantInlineFormset, self).__init__(*args, **kwargs)
    # Hack to pass in the id -> user mapping to the custom widget, so that its decompress method doesn't
    # have to hit the database once per form in the formset.
    self._users_by_id = {}
    for form in self.forms:
      participant = form.instance
      if participant and participant.user_id:
        self._users_by_id[participant.user.id] = participant.user

  def get_form_kwargs(self, index):
    kwargs = super(ParticipantInlineFormset, self).get_form_kwargs(index)
    kwargs['users_by_id'] = self._users_by_id
    return kwargs
