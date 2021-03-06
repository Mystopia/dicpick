# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (absolute_import, division, generators, nested_scopes,
                        print_function, unicode_literals, with_statement)

from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from dicpick.models import Task, TaskType


# The signal handlers below ensure that certain changes to TaskType are reflected onto all the tasks of that type.
# Note that the signal handlers run in the same transaction as the event that triggered the signal.

@receiver(post_save, sender=TaskType)
def create_task_instances(sender, instance, **kwargs):
  """Ensure that there is a task instance for each date in the range specified by the task type.

  Necessary to support date range changes.
  """
  task_type = instance
  existing_dates = set([task.date for task in task_type.tasks.all()])
  required_dates = set(task_type.date_range())
  missing_dates = required_dates - existing_dates
  superfluous_dates = existing_dates - required_dates
  Task.objects.filter(task_type=task_type, date__in=superfluous_dates).delete()
  for missing_date in missing_dates:
    task = Task(task_type=task_type, date=missing_date, num_people=task_type.num_people, score=task_type.score)
    task.save()

  Task.objects.filter(task_type=task_type).update(num_people=task_type.num_people, score=task_type.score)


@receiver(m2m_changed, sender=TaskType.tags.through)
def tags_updated(sender, instance, action, **kwargs):
  """If tags were added to or removed from a TaskType, add/remove them from all tasks of that type."""
  task_type = instance
  pk_set = kwargs.pop('pk_set')
  if action == 'post_add':
    for task in task_type.tasks.all():
      task.tags.add(*pk_set)
  elif action == 'post_remove':
    for task in task_type.tasks.all():
      task.tags.remove(*pk_set)
