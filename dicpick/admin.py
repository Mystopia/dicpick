# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

from itertools import ifilter

from django.contrib import admin
from django.db import models
from django.forms import TextInput

from dicpick.models import Camp, Event, Label, Participant, Task, TaskType


# Disallow bulk deletes by default.  Individual ModelAdmin subclasses may re-enable this selectively.
admin.site.disable_action('delete_selected')


def _safe_int(s):
  try:
    return int(s)
  except TypeError:
    return -1


def _camp_filter(request, qs):
  if request.user.is_superuser:
    return qs
  else:
    return qs.filter(admin_group__in=request.user.groups.all())

class CampFKModelAdminBase(admin.ModelAdmin):
  def get_queryset(self, request):
    return _camp_filter(request, super(CampFKModelAdminBase, self).get_queryset(request))

  def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
    if db_field.name == 'camp':
      qs = _camp_filter(request, Camp.objects.all())
      camps = list(qs)
      kwargs['queryset'] = qs
      kwargs['initial'] = camps[0] if len(camps) == 1 else None
    return super(CampFKModelAdminBase, self).formfield_for_foreignkey(db_field, request, **kwargs)


class EventFKModelAdminBase(admin.ModelAdmin):
  def get_queryset(self, request):
    ret = super(EventFKModelAdminBase, self).get_queryset(request)
    if not request.user.is_superuser:
      ret = ret.filter(event__camp__admin_group__in=request.user.groups.all())
    return ret

  def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
    if db_field.name == 'event' and not request.user.is_superuser:
      qs = Event.objects.filter(camp__admin_group__in=request.user.groups.all())
      events = list(qs)
      current_event_id = request.session.get('current_event_id', None)
      kwargs['queryset'] = qs
      # Make the most recently used event the default selection.
      kwargs['initial'] = next(ifilter(lambda e: e.id == current_event_id, events), None)
    return super(EventFKModelAdminBase, self).formfield_for_foreignkey(db_field, request, **kwargs)

  def save_model(self, request, obj, form, change):
    super(EventFKModelAdminBase, self).save_model(request, obj, form, change)
    # Update the most recently used event.
    request.session['current_event_id'] = obj.event.id


class TaskTypeFKModelAdminBase(admin.ModelAdmin):
  def get_queryset(self, request):
    ret = super(TaskTypeFKModelAdminBase, self).get_queryset(request)
    if not request.user.is_superuser:
      ret = ret.filter(task_type__event__camp__admin_group__in=request.user.groups.all())
    return ret

  def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
    if db_field.name == 'task_type' and not request.user.is_superuser:
      qs = TaskType.objects.filter(event__camp__admin_group__in=request.user.groups.all())
      task_types = list(qs)
      current_task_type_id = request.session.get('current_task_type_id', None)
      kwargs['queryset'] = qs
      # Make the most recently used task type the default selection.
      kwargs['initial'] = next(ifilter(lambda e: e.id == current_task_type_id, task_types), None)
    return super(TaskTypeFKModelAdminBase, self).formfield_for_foreignkey(db_field, request, **kwargs)

  def save_model(self, request, obj, form, change):
    super(TaskTypeFKModelAdminBase, self).save_model(request, obj, form, change)
    # Update the most recently used task type.
    request.session['current_task_type_id'] = obj.task_type.event.id


class CampAdmin(admin.ModelAdmin):
  def get_queryset(self, request):
    # We don't anticipate giving admins permissions to edit even their own camps, but this
    # is here in case that ever changes.
    if request.user.is_superuser:
      return super(CampAdmin, self).get_queryset(request)
    else:
      return Camp.objects.filter(admin_group__in=request.user.groups.all())


class EventAdmin(CampFKModelAdminBase):
  formfield_overrides = {
    models.CharField: {'widget': TextInput(attrs={'placeholder': 'E.g., Burning Man 2016'})},
  }


class LabelAdmin(EventFKModelAdminBase):
  formfield_overrides = {
    models.CharField: {'widget': TextInput(attrs={'placeholder': 'E.g., Returner'})},
  }


class TaskInline(admin.TabularInline):
  model = Task
  fields = ('date', 'num_people', 'score')
  max_num = 20


class TaskTypeAdmin(EventFKModelAdminBase):
  inlines = [TaskInline]

  formfield_overrides = {
    models.CharField: {'widget': TextInput(attrs={'placeholder': 'E.g., Dinner Chef'})},
  }


class DpAdminSite(admin.AdminSite):
  site_header = 'DicPick Administration'
  site_title = site_header

  def each_context(self, request):
    ret = super(DpAdminSite, self).each_context(request)
    ret['dicpick_camps'] = _camp_filter(request, Camp.objects.all())
    ret['dicpick_selected_camp_id'] = _safe_int(request.GET.get('c'))
    return ret



dpadmin_site = DpAdminSite(name='dpadmin')

dpadmin_site.register(Camp, CampAdmin)
dpadmin_site.register(Event, EventAdmin)
dpadmin_site.register(Label, LabelAdmin)
dpadmin_site.register(TaskType, TaskTypeAdmin)
dpadmin_site.register(Participant)
