# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (absolute_import, division, generators, nested_scopes,
                        print_function, unicode_literals, with_statement)

import re

import requests
from django.db import transaction
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.forms import (BaseInlineFormSet, BaseModelFormSet, CharField, FileField, Form, HiddenInput,
                          ModelForm, MultiValueField, MultiWidget, SelectMultiple, TextInput, URLField,
                          ValidationError, FileInput, ModelMultipleChoiceField, Field)
from django.forms.utils import pretty_name
from django.utils.html import format_html
from django.utils.translation import ugettext as _

from dicpick.models import Event, Participant, Tag, Task, TaskType, Assignment
from dicpick.templatetags.dicpick_helpers import date_to_slug
from dicpick.util import create_user


# Note: This file contains many performance hacks to work around Django's naive handling of inline formsets.


class DicPickModelFormBase(ModelForm):
  """Base class for forms that edit a single model instance."""
  def __init__(self, *args, **kwargs):
    super(DicPickModelFormBase, self).__init__(*args, **kwargs)
    for field in self.fields.values():
      field.error_messages = {'required': 'Required'}

  # A 'designator' is a property of the model that should not be edited by a given form,
  # but should still be displayed.  For example, when editing all tasks on a certain date,
  # we want to display their type, but we do not want to allow users to change the type.
  # Similarly, when editing all tasks of a certain type, we want to display each task's date,
  # but not allow users to change the date.
  # This is primarily useful when the form is used in a formset.
  #
  # Note that using disabled or read-only form fields for this kind of thing is a bad idea:
  # the update view still expects a value from those fields, and a malicious client can send the
  # wrong value.  Our 'designator' mechanism avoids this, as the designator is not a form field at all.

  def has_designator(self):
    return hasattr(self.Meta, 'designator_field')

  def designator_name(self):
    return pretty_name(self.Meta.designator_field)

  def designator(self):
    return getattr(self.instance, self.Meta.designator_field)

  # The designator link, if any, is the url to visit when the designator is clicked on.

  def has_designator_link(self):
    return self.designator_link() is not None

  def designator_link(self):
    return None


class EventForm(DicPickModelFormBase):
  """A form to edit an event's direct properties."""
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


class FormWithTagsBase(DicPickModelFormBase):
  """A base class for forms with many-to-many field, named 'tags', to the Tag model.

  A form with such a many-to-many field will use a multi-select widget, and will generate <option> elements for each
  possible tag by querying the database for all possible tags. If you have N forms in a formset, this will cause
  N identical database queries.

  To avoid this, this base class takes a precomputed set of tags, as a performance hack.
  """
  def __init__(self, *args, **kwargs):
    tags_by_id = kwargs.pop('tags_by_id')
    super(FormWithTagsBase, self).__init__(*args, **kwargs)
    # Create <option> elements for the currently selected values in this form, so that the initial data displays
    # correctly. We don't create <option> elements for all other possible tag choices. They will come from select2's
    # autocomplete mechanism.
    field = self.fields['tags']
    field.choices = [(field.prepare_value(tags_by_id[x]), field.label_from_instance(tags_by_id[x]))
                     for x in self.initial.get('tags', [])]


class TagForm(DicPickModelFormBase):
  """A form to add/edit tags."""
  class Meta:
    model = Tag
    fields = ['name']
    qualifier = 'tag'

  def __init__(self, *args, **kwargs):
    kwargs.pop('tags_by_id')  # Our superclass provides this. We don't need it but we must discard it anyway.
    super(TagForm, self).__init__(*args, **kwargs)


class TaskTypeForm(FormWithTagsBase):
  """A form to add/edit a single task type."""
  class Meta:
    model = TaskType
    fields = ['name', 'start_date', 'end_date', 'num_people', 'score', 'tags']
    qualifier = 'tasktype'
    labels = {
      'num_people': '# people',
      'score': 'Points'
    }
    help_texts = {
      'name': 'E.g., Dinner Sous Chef',
      'start_date': 'First day on which tasks of this type must be performed',
      'end_date': 'Last day on which tasks of this type must be performed',
      'num_people': 'Number of people needed to perform tasks of this type each day',
      'score': 'Points each person performing this task earns for doing so',
      'tags': 'Only people with at least one of these tags can be assigned tasks of this type'
    }


class AssigneesSelect(SelectMultiple):
  """A custom widget to render assignees efficiently."""
  def render_option(self, selected_choices, option_value, option_label):
    ret = super(AssigneesSelect, self).render_option(selected_choices, option_value, option_label)
    # Note that the task's assignment_set is prefetched, but we can't filter on it directly as that
    # would create a new queryset and database query.
    assignment = [a for a in self.task.assignment_set.all() if a.participant_id == option_value][0]
    cls = 'assignment-automatic' if assignment.automatic else 'assignment-manual'
    # Assumes that ret starts with '<option '.
    return '<option class="{}" {}'.format(cls, ret[8:])


class ParticipantMultipleChoiceField(ModelMultipleChoiceField):
  """A field for selecting multiple participants, with performance hacks."""
  participants_by_id = None  # Set by the form on each instance, on creation.

  def clean(self, value):
    # Copied from the superclass clean() method.
    if self.required and not value:
      raise ValidationError(self.error_messages['required'], code='required')
    elif not self.required and not value:
      return self.queryset.none()
    if not isinstance(value, (list, tuple)):
      raise ValidationError(self.error_messages['list'], code='list')

    # Here the superclass creates a queryset and triggers a new db query every time.
    # However we know we can satisfy the lookup in memory, so we do so here instead.
    ret = []
    for participant_id in value:
      try:
        ret.append(self.participants_by_id[int(participant_id)])
      except KeyError:
        raise ValidationError('Invalid participant id: {}'.format(participant_id))

    # Back to the superclass clean() method's implementation.
    self.run_validators(value)
    return ret


class TaskFormBase(FormWithTagsBase):
  """A base class for forms for editing tasks.

  Tasks have many-to-many fields to the Participant model.  A form with such a many-to-many field will use a
  multi-select widget, and will generate <option> elements for each possible participant by querying the database for
  all possible participant. If you have N forms in a formset, this will cause N identical database queries, each
  with a result set the size of the number of total participants in the event.

  To avoid this, this base class takes a precomputed set of participants, as a performance hack.
  """
  class Meta:
    model = Task
    # Subclasses must copy the fields list, because it gets modified by the framework.
    fields = ['num_people', 'assignees', 'score', 'tags', 'do_not_assign_to']
    qualifier = 'task'
    labels = {
      'num_people': '# people',
      'assignees': 'Assigned to',
      'score': 'Points',
      'do_not_assign_to': 'Unassignable',
    }
    field_classes = {
      'assignees': ParticipantMultipleChoiceField,
      'do_not_assign_to': ParticipantMultipleChoiceField,
    }
    widgets = {
      'assignees': AssigneesSelect,
    }
    help_texts = {
      'num_people': 'Number of people needed to perform this task on this day',
      'assignees': 'People currently assigned to this task',
      'score': 'Points each person performing this task on this day earns for doing so',
      'tags': 'Only people with at least one of these tags can be assigned this task on this day',
      'do_not_assign_to': 'These people cannot be assigned to this task',
    }
    designator_field = None

  def __init__(self, *args, **kwargs):
    # Pop extra data provided by the views that use us.
    participants_by_id = kwargs.pop('participants_by_id')
    kwargs.pop('users_by_id')
    super(TaskFormBase, self).__init__(*args, **kwargs)

    # Set up a many-to-many field to the Participant model.
    # Note that the dp-for-date and dp-for-tags custom HTML attributes are used by our
    # javascript to render the options specially if the participant is ineligible to be
    # selected due to date or tag mismatch with a task.
    def setup_participants_m2m_field(field_name):
      field = self.fields[field_name]
      # Create <option> elements for the currently selected values in this form, so that the initial data displays
      # correctly. We don't create <option> elements for all other possible participant choices. They will come from
      # select2's autocomplete mechanism.
      field.choices = [(field.prepare_value(participants_by_id[x]), field.label_from_instance(participants_by_id[x]))
                       for x in self.initial.get(field_name, [])]
      field.participants_by_id = participants_by_id
      field.widget.attrs['dp-for-date'] = self.instance.date
      field.widget.attrs['dp-for-tags'] = '|'.join([t.name for t in self.instance.tags.all()])
      field.widget.task = self.instance

    setup_participants_m2m_field('assignees')
    setup_participants_m2m_field('do_not_assign_to')

  def clean_assignees(self):
    """Custom validation logic.

    Disallows a participant from being assigned two tasks on the same date.
    """
    assignees = self.cleaned_data.get('assignees')
    for assignee in assignees:
      if (self.instance.date in assignee.cached_task_dates and
          self.instance.id not in [t.id for t in assignee.cached_tasks]):
        raise ValidationError('{} already assigned to a {} on this date.'.format(assignee, _('task')))
    return assignees

  def save(self, commit=True):
    # Pop off the asignees so that the super() call doesn't try to save them (which it can't do because
    # the through table isn't autocreated, and it won't know how to create instances of it).
    assignees = self.cleaned_data.pop('assignees')
    with transaction.atomic():
      # Save without the assignees.
      super(TaskFormBase, self).save(commit)
      # Manually save the assignees.
      existing_assignments = set(self.instance.assignment_set.all())
      self.instance.assignees.clear()
      to_create = []
      for assignee in assignees:
        automatic = False
        for ea in existing_assignments:
          if ea.participant == assignee and ea.task == self.instance:
            automatic = ea.automatic
            break
        to_create.append(Assignment(participant=assignee, task=self.instance, automatic=automatic))
      Assignment.objects.bulk_create(to_create)


class TaskByTypeForm(TaskFormBase):
  """Form for editing all tasks of a given type."""
  class Meta(TaskFormBase.Meta):
    fields = list(TaskFormBase.Meta.fields)
    designator_field = 'date'

  def designator_link(self):
    event = self.instance.task_type.event
    return reverse('dicpick:tasks_by_date_update', args=[event.camp.slug, event.slug, date_to_slug(self.instance.date)])


class TaskByDateForm(TaskFormBase):
  """Form for editing all tasks on a given date."""
  class Meta(TaskFormBase.Meta):
    fields = list(TaskFormBase.Meta.fields)
    designator_field = 'task_type'

  def designator_link(self):
    event = self.instance.task_type.event
    return reverse('dicpick:tasks_by_type_update', args=[event.camp.slug, event.slug, self.instance.task_type_id])


# A custom widget/field pair to bind together a user id and its data for use in the participants formset.
# This is how we bridge between our form, which lets you edit users as text, inline in the participant form,
# and Django's form handling mechanism, which needs to end up with a user id to put in the model field.

class UserWidget(TextInput):
  """Custom widget for editing a user inline, as 'FirstName LastName (email)'."""
  placeholder = 'Jane Doe (jane.doe@email.com)'

  def __init__(self, attrs=None):
    attrs = attrs or {}
    attrs['class'] = 'user-widget'
    attrs['placeholder'] = self.placeholder
    # A map of id -> user for all relevant users.
    # This saves us from doing database lookups one by one.
    self.users_by_id = None  # Will be set when the form is created.
    super(UserWidget, self).__init__(attrs)

  def render(self, name, user_id, attrs=None):
    if user_id is None:
      value = ''
    else:
      user = self.users_by_id[user_id]
      value ='{} {} ({})'.format(user.first_name, user.last_name, user.email)
    return super(UserWidget, self).render(name, value, attrs)


class UserField(Field):
  """A custom field for adding/editing a user inline, as 'FirstName LastName (email)'."""

  # A regex to match the 'FirstName LastName (email)' pattern.
  user_re = re.compile(r'^\s*(?P<first_name>[A-Za-z\- ]+)\s+(?P<last_name>[A-Za-z\-]+)\s+\(\s*(?P<email>\S+)\s*\)\s*$')

  def __init__(self, *args, **kwargs):
    kwargs['widget'] = UserWidget()
    super(UserField, self).__init__(*args, **kwargs)

  def clean(self, value):
    m = self.user_re.match(value)
    if m is None:
      raise ValidationError('User field must be of the form: First Last (Email)')
    email = m.group('email')
    first_name = m.group('first_name').strip()
    last_name = m.group('last_name')

    # See if we know the email address.
    try:
      user = User.objects.filter(email=email).get()
      # Update the fields if needed.
      if user.first_name != first_name or user.last_name != last_name:
        user.first_name = first_name
        user.last_name = last_name
        user.save()
    except User.DoesNotExist:
      # We must create the new user here, not in the view, because standard ModelForm validation on ParticipantForm
      # will require a non-empty user_id in the user field (as it's not nullable in the Participant model).
      user = create_user(email, first_name, last_name)
    return user

class ParticipantForm(FormWithTagsBase):
  """Form to add/edit a single participant."""
  class Meta:
    model = Participant
    fields = ['user', 'start_date', 'end_date', 'tags', 'initial_score', 'do_not_assign_with']
    qualifier = 'participant'
    labels = {
      'initial_score': 'Extra&nbsp;Pts'
    }
    help_texts = {
      'start_date': 'First day person is available for tasks',
      'end_date': 'Last day person is available for tasks',
      'tags': 'Tags describing this person',
      'initial_score': 'Points this person has already earned from other contributions',
      'do_not_assign_with': 'Do not assign this person to tasks alongside these other people',
    }

  user = UserField(help_text='Identify new or existing users as Firstname Lastname (email)')

  def __init__(self, *args, **kwargs):
    # Apply the hack to pass the id -> user map into the widget.
    # See ParticipantInlineFormset below for details.
    participants_by_id = kwargs.pop('participants_by_id')
    users_by_id = kwargs.pop('users_by_id')
    super(ParticipantForm, self).__init__(*args, **kwargs)
    self.fields['user'].widget.users_by_id = users_by_id

    do_not_assign_with_field = self.fields['do_not_assign_with']
    # Create <option> tags for the currently selected values in this form, so that the initial data displays
    # correctly. We don't create <option> tags for all other possible participant choices, as there may be many
    # participants X many forms in the formset.  The other choices will come from the remote autocomplete view.
    do_not_assign_with_field.choices = [(do_not_assign_with_field.prepare_value(participants_by_id[x]),
                                         do_not_assign_with_field.label_from_instance(participants_by_id[x]))
                                        for x in self.initial.get('do_not_assign_with', [])]

  def _get_validation_exclusions(self):
    # Don't validate the user field, because it will cause at least one db query per form in the formset.
    return super(ParticipantForm, self)._get_validation_exclusions() + ['user']


class FileUploadWidget(FileInput):
  """A custom file upload widget.

  The regular one is very ugly.  This is a known trick to get a file upload field that plays nicely with bootstrap.
  """
  def render(self, name, value, attrs=None):
    attrs['style'] = attrs.get('style', ' ') + 'display: none;'
    return format_html("""<label class="btn btn-default btn-file">Browse {}</label><span class="file-upload-path"></span>""",
                       super(FileUploadWidget, self).render(name, None, attrs=attrs))


class ParticipantImportForm(Form):
  """Form for providing an import data source for participant data."""
  file = FileField(label='Upload file', required=False, widget=FileUploadWidget)
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
      except IOError as e:
        raise ValidationError('Failed to fetch data from {} ({})'.format(url, e))
      if r.status_code != 200:
        raise ValidationError('Failed to fetch data from {} (received status {} {})'.format(url, r.status_code, r.reason))
      try:
        self.cleaned_data['data_from_url'] = r.json()
      except ValueError:
        raise ValidationError('Invalid JSON at {}'.format(url))


class TagChoicesFormsetMixin(object):
  """Formset mixin with hacks to pass the sets of tag choices into each form.

  Otherwise django will re-evaluate the querysets (and hit the database) for every form in the formset.

  Note that this is different from FormWithTagsBase above.  That is a base class for a form, this is
  a mixin for a formset.
  """
  def __init__(self, *args, **kwargs):
    event = kwargs.pop('event')
    super(TagChoicesFormsetMixin, self).__init__(*args, **kwargs)
    self._tags_by_id = {t.id: t for t in Tag.objects.filter(event=event).all()}

  def get_form_kwargs(self, index):
    kwargs = super(TagChoicesFormsetMixin, self).get_form_kwargs(index)
    kwargs['tags_by_id'] = self._tags_by_id
    return kwargs


class InlineFormsetWithTagChoicesBase(TagChoicesFormsetMixin, BaseInlineFormSet):
  """InlineFormset base with a hack to pass the set of tag choices into each form.

  Otherwise django will re-evaluate the queryset (and hit the database) for every form in the formset.
  """
  pass


class ParticipantAndTagChoicesFormsetMixin(TagChoicesFormsetMixin):
  """Formset mixin with hacks to pass the sets of tag and participant choices into each form.

  Otherwise django will re-evaluate the querysets (and hit the database) for every form in the formset.
  """

  def __init__(self, *args, **kwargs):
    event = kwargs.get('event')  # Superclass needs this kwarg, and will pop it off before passing the kwargs up.
    super(ParticipantAndTagChoicesFormsetMixin, self).__init__(*args, **kwargs)
    participant_choices = Participant.objects.filter(event=event).select_related('user').prefetch_related('tasks').all()
    self._participants_by_id = {p.id: p for p in participant_choices}
    self._users_by_id = {p.user_id: p.user for p in participant_choices}

  def get_form_kwargs(self, index):
    kwargs = super(ParticipantAndTagChoicesFormsetMixin, self).get_form_kwargs(index)
    kwargs['participants_by_id'] = self._participants_by_id
    kwargs['users_by_id'] = self._users_by_id
    return kwargs

  def participant_id_to_python(self, participant_id):
    if participant_id is None or participant_id == '':
      return None
    try:
      return self._participants_by_id[int(participant_id)]
    except KeyError:
      raise ValidationError('Invalid participant id: {}'.format(participant_id))


class TaskFormsetMixin(ParticipantAndTagChoicesFormsetMixin):
  """Formset mixin for editing tasks."""
  def __init__(self, *args, **kwargs):
    queryset = kwargs.get('queryset')
    super(TaskFormsetMixin, self).__init__(*args, **kwargs)
    self._tasks_by_id = {t.id: t for t in queryset.all()}

  def task_id_to_python(self, task_id):
    try:
      return self._tasks_by_id[int(task_id)]
    except KeyError:
      raise ValidationError('Invalid task id: {}'.format(task_id))

  def add_fields(self, form, index):
    super(TaskFormsetMixin, self).add_fields(form, index)
    # The naive to_python queries the database each time.  But we know we've already fetched
    # these for all possible ids, so we simply look them up in memory.
    form.fields['assignees'].to_python = self.participant_id_to_python
    form.fields['do_not_assign_to'].to_python = self.participant_id_to_python
    form.fields['id'].to_python = self.task_id_to_python


class TaskInlineFormset(TaskFormsetMixin, BaseInlineFormSet):
  """InlineFormset for editing tasks that all share a foreign key to a single TaskType."""
  pass


class TaskModelFormset(TaskFormsetMixin, BaseModelFormSet):
  """ModelFormset for editing tasks that don't share a foreign key to anything."""
  pass


class ParticipantInlineFormset(ParticipantAndTagChoicesFormsetMixin, BaseInlineFormSet):
  """Formset for editing participants inline."""
  def add_fields(self, form, index):
    super(ParticipantInlineFormset, self).add_fields(form, index)
    # The naive to_python queries the database each time.  But we know we've already fetched
    # these for all possible ids, so we simply look them up in memory.
    form.fields['id'].to_python = self.participant_id_to_python
