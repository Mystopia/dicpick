# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (absolute_import, division, generators, nested_scopes,
                        print_function, unicode_literals, with_statement)

import csv
import datetime
import json
import re
import io
import textwrap
from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.forms import inlineformset_factory, modelformset_factory
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import translation
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, DetailView, FormView, TemplateView, UpdateView, View

from dicpick.assign import assign_for_task_ids
from dicpick.forms import (EventForm, InlineFormsetWithTagChoicesBase, ParticipantForm,
                           ParticipantImportForm, ParticipantInlineFormset, TagForm, TaskByDateForm,
                           TaskByTypeForm, TaskInlineFormset, TaskModelFormset, TaskTypeForm)
from dicpick.models import Assignment, Camp, Event, Participant, Tag, Task, TaskType
from dicpick.templatetags.dicpick_helpers import burn_logo, date_to_pretty_str, is_burn
from dicpick.util import create_user
from functools import reduce


# Many views share common functionality (such as converting camp and event slugs to objects).
# This commonality is implemented as mixins, which must have no `__init__` method, no state, and
#  must be the leftmost superclasses of their subclasss.
# The mixins act on members they don't themselves define.  They assume that they will be mixed in
# to classes that do have those members.  Dynamic dispatch FTW.  This does mean, however, that
# an IDE may see these as unresolved references and warn about them.

# TODO: This file is now quite long. Break it up into multiple files?


class CampRelatedMixin(object):
  """Mixin for views relating to data on or under a certain camp."""
  @cached_property
  def camp(self):
    return get_object_or_404(Camp, slug=self.kwargs['camp_slug'])


class IsCampAdminMixin(UserPassesTestMixin, CampRelatedMixin):
  """Mixin for camp-related views that are only viewable by the admins of the camp.

  We also use this to set any camp-specific language variants.

  Note that mixing this in has the side effect of requiring the user to be logged in,
  so views that do so shouldn't decorate themselves with @login_required.
  """
  def test_func(self):
    return self.request.user.is_superuser or self.request.user.groups.filter(pk=self.camp.admin_group_id).exists()

  def get(self, request, *args, **kwargs):
    # We hard-code some special casing for mystopia.  If other camps want their own special language
    # variant, we'll come up with a more dynamic approach.
    # Note that setting the language in the session here will only take effect on the next request.
    # if self.camp.slug == 'mystopia':
    #   request.session[translation.LANGUAGE_SESSION_KEY] = 'en-mystopia'
    # else:
    #   request.session[translation.LANGUAGE_SESSION_KEY] = 'en'
    return super(IsCampAdminMixin, self).get(request, *args, **kwargs)


# Home page.

@login_required
def user_home(request):
  """View to render the user's home page.

  Currently just a list of camps the user is an admin of.
  """
  camps = Camp.objects.filter(admin_group__in=list(request.user.groups.all()))
  context = {
    'camps': camps
  }
  return render(request, 'dicpick/user_home.html', context=context)


# Camp views.

class CampDetail(IsCampAdminMixin, DetailView):
  """View to edit a camp's direct properties (name etc.)."""
  model = Camp
  slug_url_kwarg = 'camp_slug'
  context_object_name = 'camp'


# Event views.

class EventRelatedMixin(IsCampAdminMixin):
  """Mixin for views relating to data on or under a single event."""
  @classmethod
  def prefetch_related(cls):
    return ['tags']

  @cached_property
  def event(self):
    return get_object_or_404(Event.objects.prefetch_related(*self.prefetch_related()),
                             camp__slug=self.kwargs['camp_slug'], slug=self.kwargs['event_slug'])



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
  """Mixin for views that modify a single model instance under a single event."""
  template_name = 'dicpick/event_related_single_form.html'


class EventRelatedFormsetMixin(EventRelatedFormMixin):
  """Mixin for views that modify multiple instances of a model under a single event."""
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


# Views to create/update/delete/view a single event's direct properties.

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
  def create_form_class(single_model_form_class, formset_base_class=InlineFormsetWithTagChoicesBase):
    return inlineformset_factory(Event, single_model_form_class.Meta.model,
                                 form=single_model_form_class, extra=1,
                                 formset=formset_base_class)

  def get_form_kwargs(self):
    kwargs = super(EventRelatedFormsetUpdate, self).get_form_kwargs()
    kwargs['instance'] = self.event
    kwargs['event'] = self.event
    return kwargs

  def form_valid(self, form):
    if form.is_valid():
      # Ensure that all forms in the formset (and all signal processing) are atomic.
      with transaction.atomic():
        form.save()
    return super(EventRelatedFormsetUpdate, self).form_valid(form)


class TagsUpdate(EventRelatedFormsetUpdate):
  """Create/update/delete an event's tags."""
  form_class = EventRelatedFormsetUpdate.create_form_class(TagForm)
  legend = 'Enter Tags'
  help_text = "Short tags describing people and possibly restricting the tasks they're allowed to do.\n" \
              "E.g., \"early arriver\", \"returner\", \"camp manager\""


class ParticipantScores(EventRelatedTemplateMixin, TemplateView):
  """Show all participants scores."""
  template_name = 'dicpick/participant_scores.html'

  @classmethod
  def prefetch_related(cls):
    return ['participants', 'participants__user', 'participants__tasks']


class ParticipantsUpdate(EventRelatedFormsetUpdate):
  """Create/update/delete an event's participants."""
  form_class = EventRelatedFormsetUpdate.create_form_class(ParticipantForm, formset_base_class=ParticipantInlineFormset)
  help_text = ("Details of a person's participation in this event.\n"
               "Existing users are identified via email address.  New users are created as needed.")

  @property
  def legend(self):
    return 'Edit {}'.format(_('Participants'))

  @property
  def help_text(self):
    return ("Details of a {person}'s participation in this event.\n"
            "Existing users are identified via email address.  New users are created as needed.".format(
            person=_('person')))

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
        .prefetch_related('tags', 'do_not_assign_with__user')
        .order_by('user__first_name', 'user__last_name')
    )
    return kwargs

  def form_valid(self, formset):
    with transaction.atomic():
      for form in formset:
        user = form.cleaned_data.get('user')
        if user:
          # We exclude the user field from validation (see forms.py for the reason), Django doesn't
          # set it on the instance either for some reason. So we set it manually here.
          form.instance.user = user
          if user != form.initial.get('user'):
            # This may be a new user, so add them to the camp's group.
            user.groups.add(self.camp.member_group)
      return super(ParticipantsUpdate, self).form_valid(formset)

  def get_success_url(self):
    return self.request.path   # Return to the same formset for further editing.


class ParticipantsImport(EventRelatedSingleFormMixin, FormView):
  """Import participant data from a JSON data source."""
  form_class = ParticipantImportForm

  help_text = textwrap.dedent("""
    Provide a file containing JSON with the following format:
    ```{
      firstName: "Jane",
      lastName: "Doe",
      email: "jane.doe@email.com",
      points: 25,
      firstFullDay: "YYYY-MM-DD",
      lastFullDay: "YYYY-MM-DD",
    }```

    Re-importing multiple times is safe: existing users will be modified if necessary, but not deleted.
  """)

  @property
  def legend(self):
    return 'Upload {} JSON'.format(_('Participants'))

  def form_valid(self, form):
    if 'file' in self.request.FILES:
      participant_data = json.load(self.request.FILES['file'])
    else:
      participant_data = form.cleaned_data['data_from_url']

    invalid_name_chars_re = re.compile(r'[^A-Za-z\- ]')
    def clean_name(s):
      return invalid_name_chars_re.sub('', s)

    for record in participant_data:
      email = record['email'].strip()
      first_name = clean_name(record['firstName'].strip())
      last_name = clean_name(record['lastName'].strip())

      def convert_date(key):
        date_str = record.get(key)  # May be None (if it's null in the JSON).
        if date_str:
          return datetime.datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
        return None

      start_date = convert_date('firstFullDay')
      end_date = convert_date('lastFullDay')
      initial_score = int(record.get('points') or 0)

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

        participants = list(Participant.objects.filter(event=self.event, user=user))
        if participants:
          # Update existing participant.
          participant = participants[0]
          if start_date:
            participant.start_date = start_date
          if end_date:
            participant.end_date = end_date
          participant.initial_score = initial_score
        else:
          participant = Participant(event=self.event,
                                    user=user,
                                    start_date=start_date or self.event.start_date,
                                    end_date=end_date or self.event.end_date,
                                    initial_score=initial_score)
        participant.save()

    return super(ParticipantsImport, self).form_valid(form)


class TaskTypesUpdate(EventRelatedFormsetUpdate):
  """Create/update/delete task types."""
  form_class = EventRelatedFormsetUpdate.create_form_class(TaskTypeForm)
  help_text = ('These are categories of tasks, each of which must be performed on '
               'multiple days, possibly by multiple people.\nE.g., Morning MOOP Sweep, Dinner Sous Chef.')

  @property
  def legend(self):
    return 'Edit {} Types'.format(_('Task'))

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
  """Browse tasks by type."""
  template_name = 'dicpick/tasks_by_type.html'


class TasksByDate(EventRelatedTemplateMixin, TemplateView):
  """Browse tasks by date."""
  template_name = 'dicpick/tasks_by_date.html'


class InlineTaskFormsetUpdateBase(EventRelatedFormMixin, FormView):
  """Base class for views that update multiple tasks (by type, or by date)."""
  template_name = 'dicpick/task_formset.html'

  def get_form_kwargs(self):
    kwargs = super(InlineTaskFormsetUpdateBase, self).get_form_kwargs()
    kwargs['event'] = self.event
    kwargs['queryset'] = (
      Task.objects
        .filter(task_type__event=self.event, **self.queryset_filter())
        .select_related('task_type', 'task_type__event', 'task_type__event__camp')
        .prefetch_related('tags', 'assignment_set',
                          'assignees', 'assignees__user', 'assignees__tasks',
                          'do_not_assign_to', 'do_not_assign_to__user')
        .order_by(self.queryset_order_by())
    )
    return kwargs

  def form_valid(self, form):
    if 'delete-auto-assignments' in self.request.POST:
      # Delete auto assignees, but don't save any other form data.
      task_ids = [t['id'].id for t in form.cleaned_data]
      # Note that we filter by event, to ensure that the current user has permission to modify these tasks.
      Assignment.objects.filter(task__task_type__event=self.event, task_id__in=task_ids, automatic=True).delete()
    elif 'delete-all-assignments' in self.request.POST:
      # Delete all assignees, but don't save any other form data.
      task_ids = [t['id'].id for t in form.cleaned_data]
      # Note that we filter by event, to ensure that the current user has permission to modify these tasks.
      Assignment.objects.filter(task__task_type__event=self.event, task_id__in=task_ids).delete()
    else:
      if form.is_valid():
        form.save()
      if 'assign' in self.request.POST:
        # Weirdly, t['id'] in form.cleaned_data is a full Task object, not an int.
        # Note that we must let the assign code re-fetch the Task objects, so it can prefetch
        # related objects, filter them etc.
        forms_by_task_id = {t['id'].id: f for (t, f) in zip(form.cleaned_data, form.forms)}
        unassignable_tasks = assign_for_task_ids(self.event, [t['id'].id for t in form.cleaned_data])
        if unassignable_tasks:
          for task_id in unassignable_tasks:
            forms_by_task_id[task_id].add_error(None,
                                                "Couldn't find an eligible {} to perform this {}.".format(
                                                    _('Participant'), _('Task')))
          return self.form_invalid(form)

    return super(InlineTaskFormsetUpdateBase, self).form_valid(form)

  def get_success_url(self):
    return self.request.path   # Return to the same formset for further editing.


class TasksByTypeUpdate(InlineTaskFormsetUpdateBase):
  """Update all tasks of a given type."""
  @property
  def legend(self):
    return 'Edit {} {}'.format(self.task_type.name, _('Tasks'))

  @cached_property
  def task_type(self):
    # Note that we filter by camp and event even though the pk is enough for uniqueness, to ensure that
    # the current user is allowed to access the task type.
    return get_object_or_404(TaskType.objects.prefetch_related('tags'),
                             event__camp__slug=self.kwargs['camp_slug'],
                             event__slug=self.kwargs['event_slug'],
                             pk=self.kwargs['task_type_pk'])

  def get_form_class(self):
    # Note that this is an inlineformset, because these tasks share a foreign key to the TaskType.
    return inlineformset_factory(TaskType, Task, form=TaskByTypeForm, extra=0, can_delete=False,
                                 formset=TaskInlineFormset)

  def queryset_filter(self):
    return {'task_type': self.task_type}

  @staticmethod
  def queryset_order_by():
    return 'date'

  def get_form_kwargs(self):
    kwargs = super(TasksByTypeUpdate, self).get_form_kwargs()
    kwargs['instance'] = self.task_type
    return kwargs


class TasksByDateUpdate(InlineTaskFormsetUpdateBase):
  """Update all tasks on a given date."""
  template_name = 'dicpick/task_by_date_update.html'

  @property
  def legend(self):
    return 'Edit {} on {} {}'.format(_('Tasks'), burn_logo if is_burn(self.date) else '', date_to_pretty_str(self.date))

  @property
  def date(self):
    return datetime.datetime.strptime(self.kwargs['date'], '%Y_%m_%d').date()

  def get_form_class(self):
    # Note that this is a modelformset, not an inlineformset, because these tasks don't share
    # a foreign key to anything.
    return modelformset_factory(Task, form=TaskByDateForm, extra=0, can_delete=False,
                                formset=TaskModelFormset)

  def queryset_filter(self):
    return {'date': self.date}

  @staticmethod
  def queryset_order_by():
    return 'task_type__name'

  def get_context_data(self, **kwargs):
    data = super(TasksByDateUpdate, self).get_context_data(**kwargs)
    day = datetime.timedelta(days=1)
    data['prev_date'] = self.date - day
    data['next_date'] = self.date + day
    return data


class AllTasks(EventRelatedTemplateMixin, TemplateView):
  """Show a matrix (or a csv stream) of all task assignments."""
  template_name = 'dicpick/all_tasks.html'

  @classmethod
  def prefetch_related(cls):
    return ['task_types', 'task_types__tasks', 'task_types__tasks__assignees', 'task_types__tasks__assignees__user']

  def get(self, request, emit_csv=False, *args, **kwargs):
    if emit_csv:
      assignments = self._get_assignments_dict()
      dates = list(self.event.date_range())
      data = io.StringIO()
      out = csv.writer(data)
      out.writerow([''] + [dt.strftime('%a. %m/%d') for dt in dates])
      for task_type in self.event.task_types.all():
        rows = []
        for i, dt in enumerate(dates):
          for j, assignee in enumerate(assignments[task_type.id][dt]):
            while len(rows) <= j:
              rows.append([task_type.name] + [''] * len(dates))
            rows[j][1 + i] = assignee
        for row in rows:
          out.writerow(row)
      return HttpResponse(data.getvalue(), content_type='application/csv')
    else:
      return super(AllTasks, self).get(request, *args, **kwargs)

  def get_context_data(self, **kwargs):
    data = super(AllTasks, self).get_context_data(**kwargs)
    data['assignments'] = self._get_assignments_dict()
    return data

  def _get_assignments_dict(self):
    # We put all the task assignments into a dict, so that we don't have to assume anything
    # about which task types and dates we have data for, what order we see them in, etc.
    assignments = defaultdict(lambda: defaultdict(list))

    for task_type in self.event.task_types.all():
      for task in task_type.tasks.all():
        assignments[task_type.id][task.date] = list(task.assignees.all())

    return assignments


class TagAutocomplete(EventRelatedMixin, View):
  """View to serve tag autocomplete ajax requests."""
  def get(self, request, camp_slug, event_slug):
    query = request.GET.get('q') or ''
    # Note that we return just the first 5 results.
    qs = Tag.objects.filter(event=self.event, name__istartswith=query)[:5]
    results = [{'id': t.id, 'text': t.name} for t in qs]
    ret = {
      'results': results,
    }
    return JsonResponse(ret, safe=False)


class ParticipantAutocomplete(EventRelatedMixin, View):
  """View to serve participant autocomplete ajax requests."""
  def get(self, request, camp_slug, event_slug):
    query = request.GET.get('q') or ''

    for_date_str = request.GET.get('d')
    for_date = datetime.datetime.strptime(for_date_str, "%Y-%m-%d").date() if for_date_str else None

    for_tags_str = request.GET.get('t')
    for_tags_strs = for_tags_str.split('|') if for_tags_str else []
    for_tags = set(Tag.objects.filter(event=self.event, name__in=for_tags_strs))

    filters = [Q(**{'user__{}__istartswith'.format(f): query}) for f in ['username', 'first_name', 'last_name', 'email']]
    combined_filter = Q(event=self.event) & reduce(lambda x, y: x | y, filters)
    # Note that we return just the first 5 results.
    qs = (
      Participant.objects.filter(combined_filter)
        .select_related('user')
        .prefetch_related('tags')
        .order_by('user__first_name', 'user__last_name')
    )[:5]

    def fmt_date(dt):
      return dt.strftime('%b %d')

    results = []
    for p in qs:
      result = {'id': p.id, 'text': '{} {}'.format(p.user.first_name, p.user.last_name)}
      if for_date and (for_date < p.start_date or for_date > p.end_date):
        result['disabled'] = True
        result['disqualified_for_date'] = True
        result['tooltip'] = 'Available {}-{}.'.format(fmt_date(p.start_date), fmt_date(p.end_date))
      if for_tags and not for_tags.intersection(p.tags.all()):
        result['disabled'] = True
        result['disqualified_for_tags'] = True
        result['tooltip'] = result.get('tooltip', '') + " No matching tags."
      results.append(result)

    ret = {
      'results': results,
    }
    return JsonResponse(ret, safe=False)
