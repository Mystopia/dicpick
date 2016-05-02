# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

from django.contrib.auth.models import Group, User
from django.db import models


class Camp(models.Model):
  """An organization that runs an event, e.g., Mystopia."""
  # Human-readable camp name.
  name = models.CharField(max_length=40, unique=True)

  # Members of this group are admins for this camp.
  admin_group = models.OneToOneField(Group, unique=True)

  def __str__(self):
    return self.name


class Event(models.Model):
  """A 'universe' of tasks for some camp, e.g., Mystopia at Burning Man 2016."""
  class Meta:
    unique_together = ('camp', 'name')

  # The camp this event belongs to.
  camp = models.ForeignKey(Camp)
  # Human-readable event name.
  name = models.CharField(max_length=40)
  # First date of the event.
  start_date = models.DateField()
  # Last date of the event.
  end_date = models.DateField()

  def __str__(self):
    return self.name


class Label(models.Model):
  """A label that can be assigned to participants, such as 'Returner', 'Early Arriver', 'Camp Manager'."""
  event = models.ForeignKey(Event)
  name = models.CharField(max_length=20)

  def __str__(self):
    return self.name


class Participant(models.Model):
  """Someone eligible to perform tasks in an event, e.g., a Mystopian going to Burning Man 2016."""
  # The underlying user.
  user = models.ForeignKey(User)
  # The event.
  event = models.ForeignKey(Event)
  # Labels assigned to this participant.
  labels = models.ManyToManyField(Label, related_name='participants', blank=True)


class TaskType(models.Model):
  """A type of task, e.g., Dinner Cook."""
  event = models.ForeignKey(Event)
  # Human-readable name of the task type.
  name = models.CharField(max_length=40)
  # The score you get for completing tasks of this type.
  score = models.IntegerField()
  # Tasks of this type can only be assigned to participants with at least one of these labels.
  labels = models.ManyToManyField(Label, related_name='task_types', blank=True)

  def __str__(self):
    return self.name


class Task(models.Model):
  """An instance of a particular task type on a particular date, e.g., Dinner Cook on 8/30/2016."""
  class Meta:
    unique_together = ('task_type', 'date')

  # The type of this task.
  task_type = models.ForeignKey(TaskType)
  # The date on which this task is to be performed.
  date = models.DateField(db_index=True)
  # Number of people needed for this task on this date.
  num_people = models.IntegerField()
  # The score you get for completing this task on this date.
  # Optional - if specified, overrides task_type.score.
  score = models.IntegerField(null=True, blank=True)
  # This task can only be assigned to participants with at least one of these labels.
  # Optional - if specified, overrides task_type.labels.
  labels = models.ManyToManyField(Label, related_name='tasks', blank=True)
  # The participants assigned to this task.
  assignees = models.ManyToManyField(Participant, related_name='tasks')
