# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import datetime
import json
import textwrap

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User
from django.db import transaction
from django.forms import inlineformset_factory, modelformset_factory
from django.shortcuts import get_object_or_404, render
from django.views.generic import CreateView, UpdateView, DetailView, DeleteView, FormView, TemplateView

from dicpick.forms import EventForm, TagForm, TaskTypeForm, ParticipantForm, \
  ParticipantImportForm, TaskByTypeForm, TaskByDateForm, ParticipantInlineFormset, InlineFormsetWithTagChoices, \
  ModelFormsetWithTagChoices
from dicpick.models import Event, Camp, Participant, TaskType, Task

# Helper mixin.
from dicpick.util import create_user


class CampRelatedMixin(object):
  """Mixin for views relating to data on or under a certain camp."""
  @property
  def camp(self):
    return get_object_or_404(Camp, slug=self.kwargs['camp_slug'])


class IsCampAdminMixin(UserPassesTestMixin, CampRelatedMixin):
  def test_func(self):
    return self.request.user.is_superuser or self.request.user.groups.filter(pk=self.camp.admin_group_id).exists()


# Home page.

@login_required
def user_home(request):
  camps = Camp.objects.filter(admin_group__in=list(request.user.groups.all()))
  context = {
    'camps': camps
  }
  return render(request, 'dicpick/user_home.html', context=context)


# Camp views.

class CampDetail(IsCampAdminMixin, DetailView):
  model = Camp
  slug_url_kwarg = 'camp_slug'
  context_object_name = 'camp'


# Event views.

class EventRelatedMixin(IsCampAdminMixin):
  """Mixin for views relating to data on or under a single event."""
  def __init__(self, *args, **kwargs):
    super(EventRelatedMixin, self).__init__(*args, **kwargs)
    self._event = None

  @property
  def event(self):
    if self._event is None:
      self._event = get_object_or_404(Event.objects.prefetch_related('tags'),
                                      camp__slug=self.kwargs['camp_slug'], slug=self.kwargs['event_slug'])
    return self._event


class EventRelatedTemplateMixin(EventRelatedMixin):
  """Mixin for template views relating to data on or under a single event."""
  def get_context_data(self, **kwargs):
    data = super(EventRelatedTemplateMixin, self).get_context_data(**kwargs)
    data['event'] = self.event
    return data


class EventMixin(EventRelatedMixin):
  """Mixin for views relating to the direct properties of a single event."""
  model = Event

  def get_object(self):
    return self.event


class EventRelatedFormMixin(EventRelatedTemplateMixin):
  """Mixin for views that modify data on or under a single event."""
  help_text = ''

  def get_context_data(self, **kwargs):
    data = super(EventRelatedFormMixin, self).get_context_data(**kwargs)
    data['legend'] = self.legend
    data['help_text'] = self.help_text
    return data

  def get_success_url(self):
    return self.event.get_absolute_url()


class EventRelatedSingleFormMixin(EventRelatedFormMixin):
  template_name = 'dicpick/event_related_single_form.html'


class EventRelatedFormsetMixin(EventRelatedFormMixin):
  template_name = 'dicpick/event_related_formset.html'


class EventFormMixin(EventMixin, EventRelatedSingleFormMixin):
  """Mixin for views that modify the direct properties of a single event.

  Note the diamond multiple inheritance of EventRelatedMixin.
  """
  form_class = EventForm
  legend = 'Edit event'

  def form_valid(self, form):
    form.instance.camp_id = self.camp.pk
    return super(EventFormMixin, self).form_valid(form)


class EventCreate(EventFormMixin, CreateView):
  @property
  def event(self):
    return self.object


class EventUpdate(EventFormMixin, UpdateView):
  pass


class EventDelete(EventMixin, DeleteView):
  def get_success_url(self):
    return self.camp.get_absolute_url()


class EventDetail(EventMixin, DetailView):
  pass


# Event-related formset views.

class EventRelatedFormsetUpdate(EventRelatedFormsetMixin, FormView):
  """Base class for views that update 1:many data belonging to a single event via foreign key."""

  @staticmethod
  def create_form_class(single_model_form_class, formset_base_class=InlineFormsetWithTagChoices):
    return inlineformset_factory(Event, single_model_form_class.Meta.model,
                                 form=single_model_form_class, extra=4,
                                 formset=formset_base_class)

  def get_form_kwargs(self):
    kwargs = super(EventRelatedFormsetUpdate, self).get_form_kwargs()
    kwargs['instance'] = self.event
    kwargs['event'] = self.event
    return kwargs

  def form_valid(self, form):
    if form.is_valid():
      form.save()
    return super(EventRelatedFormsetUpdate, self).form_valid(form)


class TagsUpdate(EventRelatedFormsetUpdate):
  form_class = EventRelatedFormsetUpdate.create_form_class(TagForm)
  legend = 'Enter Tags'
  help_text = "Short tags describing people and possibly restricting the tasks they're allowed to do.\n" \
              "E.g., \"early arriver\", \"returner\", \"camp manager\""


class ParticipantsUpdate(EventRelatedFormsetUpdate):
  form_class = EventRelatedFormsetUpdate.create_form_class(ParticipantForm, formset_base_class=ParticipantInlineFormset)
  legend = 'Enter Participants'
  help_text = ("Details of a user's participation in this event.\n"
               "Existing users are identified via email address.  New users are created as needed.")

  def get_form(self, form_class=None):
    formset = super(EventRelatedFormsetUpdate, self).get_form(form_class)
    for form in formset.extra_forms:
      form.initial['start_date'] = self.event.start_date
      form.initial['end_date'] = self.event.end_date
    return formset

  def get_form_kwargs(self):
    kwargs = super(ParticipantsUpdate, self).get_form_kwargs()
    kwargs['queryset'] = (
      Participant.objects
        .filter(event=self.event)
        .select_related('user')
        .prefetch_related('tags')
        .order_by('user__first_name', 'user__last_name')
    )
    return kwargs

  def form_valid(self, formset):
    with transaction.atomic():
      for form in formset:
        if form.cleaned_data and not form.initial.get('user'):
          # This is a user we just added, so add them to the camp's group.
          user = form.cleaned_data['user']
          user.groups.add(self.camp.member_group)

      return super(ParticipantsUpdate, self).form_valid(formset)


class ParticipantsImport(EventRelatedSingleFormMixin, FormView):
  form_class = ParticipantImportForm
  legend = 'Upload Participant JSON'
  help_text = textwrap.dedent("""
    Provide a file containing JSON with the following format:
    ```{
      firstName: Jane,
      lastName: Doe,
      email: jane.doe@email.com
    }```
  """)

  def form_valid(self, form):
    if 'file' in self.request.FILES:
      participant_data = json.load(self.request.FILES['file'])
    else:
      participant_data = json.load(form.cleaned_data['data_from_url'])

    for record in participant_data:
      email = record['email'].strip()
      first_name = record['firstName'].strip()
      last_name = record['lastName'].strip()

      user = User.objects.filter(email=email).first()
      with transaction.atomic():
        if user:
          # Update existing user.
          user.first_name = first_name
          user.last_name = last_name
          user.email = email
          user.save()
        else:
          user = create_user(email, first_name, last_name)
        user.groups.add(self.camp.member_group)

        if not Participant.objects.filter(event=self.event, user=user).exists():
          participant = Participant(event=self.event, user=user,
                                    start_date=self.event.start_date, end_date=self.event.end_date, initial_score=0)
          participant.save()

    return super(ParticipantsImport, self).form_valid(form)


class TaskTypesUpdate(EventRelatedFormsetUpdate):
  form_class = EventRelatedFormsetUpdate.create_form_class(TaskTypeForm)
  legend = 'Enter Task Types'
  help_text = 'These are categories of tasks, each of which must be performed on ' \
              'multiple days, possibly by multiple people.\nE.g., Morning MOOP Sweep, Dinner Sous Chef.'

  def get_form_kwargs(self):
    kwargs = super(TaskTypesUpdate, self).get_form_kwargs()
    kwargs['queryset'] = (
      TaskType.objects
        .filter(event=self.event)
        .prefetch_related('tags')
        .order_by('name')
    )
    return kwargs


class TasksByType(EventRelatedTemplateMixin, TemplateView):
  template_name = 'dicpick/tasks_by_type.html'


class TasksByTypeUpdate(EventRelatedFormsetMixin, FormView):
  @property
  def legend(self):
    return 'Tweak data for {} tasks'.format(self.task_type.name)

  @property
  def task_type(self):
    # Note that we filter by camp and event even though the pk is enough for uniqueness, to ensure that
    # the current user is allowed to access the task type.
    return get_object_or_404(TaskType.objects.prefetch_related('tags'),
                             event__camp__slug=self.kwargs['camp_slug'],
                             event__slug=self.kwargs['event_slug'],
                             pk=self.kwargs['task_type_pk'])

  def get_form_class(self):
    return inlineformset_factory(TaskType, Task, form=TaskByTypeForm, extra=0, can_delete=False,
                                 formset=InlineFormsetWithTagChoices)

  def get_form_kwargs(self):
    kwargs = super(TasksByTypeUpdate, self).get_form_kwargs()
    kwargs['instance'] = self.task_type
    kwargs['event'] = self.event
    kwargs['queryset'] = (
      Task.objects
        .filter(task_type=self.task_type)
        .prefetch_related('tags')
        .order_by('date')
    )
    return kwargs

  def form_valid(self, form):
    if form.is_valid():
      form.save()
    return super(TasksByTypeUpdate, self).form_valid(form)


class TasksByDate(EventRelatedTemplateMixin, TemplateView):
  template_name = 'dicpick/tasks_by_date.html'


class TasksByDateUpdate(EventRelatedFormsetMixin, FormView):
  @property
  def legend(self):
    return 'Tweak data for tasks on {}'.format(self.date)

  @property
  def date(self):
    return datetime.datetime.strptime(self.kwargs['date'], '%Y_%m_%d').date()

  def get_form_class(self):
    return modelformset_factory(Task, TaskByDateForm, extra=0, can_delete=False,
                                formset=ModelFormsetWithTagChoices)

  def get_form_kwargs(self):
    kwargs = super(TasksByDateUpdate, self).get_form_kwargs()
    kwargs['queryset'] = (
      Task.objects
        .filter(task_type__event=self.event, date=self.date)
        .select_related('task_type')
        .prefetch_related('tags')
        .order_by('task_type__name')
    )
    kwargs['event'] = self.event
    return kwargs

  def form_valid(self, form):
    if form.is_valid():
      form.save()
    return super(TasksByDateUpdate, self).form_valid(form)
