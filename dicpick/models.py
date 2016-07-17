# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (absolute_import, division, generators, nested_scopes,
                        print_function, unicode_literals, with_statement)

from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Sum, F
from django.utils.functional import cached_property


class Camp(models.Model):
  """An organization that runs an event, e.g., Mystopia."""
  # Human-readable camp name.
  name = models.CharField(max_length=40, unique=True)

  # Short name for use as a slug in URLs.
  slug = models.SlugField(max_length=10, unique=True, db_index=True)

  # Members of this group are admins for this camp.
  admin_group = models.OneToOneField(Group, unique=True, related_name='+')

  # Members of this group are members of this camp.
  member_group = models.OneToOneField(Group, unique=True, related_name='+')

  def get_absolute_url(self):
    return reverse('dicpick:camp_detail', kwargs={'camp_slug': self.slug})

  def __str__(self):
    return self.name


class ModelWithDateRange(models.Model):
  class Meta:
    abstract = True

  # First date of the event.
  start_date = models.DateField()

  # Last date of the event.
  end_date = models.DateField()

  def date_range(self):
    date = self.start_date
    while date <= self.end_date:
      yield date
      date += timedelta(days=1)

  def is_in_date_range(self, dt):
    return self.start_date <= dt <= self.end_date


class Event(ModelWithDateRange):
  """A 'universe' of tasks for some camp, e.g., Mystopia at Burning Man 2016."""
  class Meta:
    unique_together = [('camp', 'name'), ('camp', 'slug')]

  # The camp this event belongs to.
  camp = models.ForeignKey(Camp, related_name='events')

  # Human-readable event name.
  name = models.CharField(max_length=40, help_text='E.g., "Burning Man 2016".')

  # Short name for use as a slug in URLs.
  slug = models.SlugField(max_length=10, db_index=True, help_text='A short string to use in URLs.  E.g., "2016".')

  def participants_sorted_by_score(self):
    return sorted(self.participants.all(), key=lambda p: p.assigned_score, reverse=True)

  @cached_property
  def total_score(self):
    return Task.objects.filter(task_type__event=self).aggregate(
        total_score=Sum(F('num_people')*F('score')))['total_score']

  @cached_property
  def total_assigned_score(self):
    return Task.assignees.through.objects.filter(task__task_type__event=self).aggregate(
        total_assigned_score=Sum('task__score'))['total_assigned_score']

  @cached_property
  def num_participants(self):
    return self.participants.count()

  @cached_property
  def num_tasks(self):
    return Task.objects.filter(task_type__event=self).count()

  @cached_property
  def score_per_participant(self):
    return int(self.total_score / self.num_participants + 0.5)

  def get_absolute_url(self):
    return reverse('dicpick:event_detail', kwargs={'camp_slug': self.camp.slug, 'event_slug': self.slug })

  def __str__(self):
    return self.name


class Tag(models.Model):
  """A tag that can be assigned to participants, such as 'Returner', 'Early Arriver', 'Camp Manager'."""
  class Meta:
    unique_together = [('event', 'name')]

  event = models.ForeignKey(Event, related_name='tags')
  name = models.CharField(max_length=20)

  def __str__(self):
    return self.name


class Participant(ModelWithDateRange):
  """Someone eligible to perform tasks in an event, e.g., a Mystopian going to Burning Man 2016."""
  class Meta:
    unique_together = [('event', 'user')]

  # The event.
  event = models.ForeignKey(Event, related_name='participants')

  # The underlying user.
  user = models.ForeignKey(User)

  # Tags assigned to this participant.
  tags = models.ManyToManyField(Tag, related_name='participants', blank=True)

  # Initial score that this participant has already earned through out-of-band contributions.
  # Assumed to be zero if unspecified.
  initial_score = models.IntegerField(blank=True, default=0)

  @cached_property
  def assigned_score(self):
    return self.initial_score + sum(t.score for t in self.tasks.all())

  def __str__(self):
    return self.user.get_full_name()


class TaskType(ModelWithDateRange):
  class Meta:
    unique_together = [('event', 'name')]

  """A type of task, e.g., Dinner Cook."""
  event = models.ForeignKey(Event, related_name='task_types')

  # Human-readable name of the task type.
  name = models.CharField(max_length=40)

  # These can be overridden for individual task instances of this type:

  # Default number of people needed for this task, per day.
  num_people = models.IntegerField()

  # Default score each person gets for completing tasks of this type.
  score = models.IntegerField()

  # Tasks of this type can only be assigned to participants with at least one of these tags, by default.
  tags = models.ManyToManyField(Tag, related_name='task_types', blank=True)

  def __str__(self):
    return self.name


class Task(models.Model):
  """An instance of a particular task type on a particular date, e.g., Dinner Cook on 8/30/2016."""
  class Meta:
    unique_together = ('task_type', 'date')
    ordering = ['task_type__name', 'date']

  # The type of this task.
  task_type = models.ForeignKey(TaskType, related_name='tasks')

  # The date on which this task is to be performed.
  date = models.DateField(db_index=True)

  # Number of people needed for this task on this date.
  # Initialized to task_type.num_people, but can be overridden here.
  num_people = models.IntegerField()

  # The score each person gets for completing this task on this date.
  # Initialized to task_type.score, but can be overridden here.
  score = models.IntegerField()

  # This task can only be assigned to participants with at least one of these tags.
  # Initialized to task_type.tags, but can be overridden here.
  tags = models.ManyToManyField(Tag, related_name='tasks', blank=True)

  # The participants assigned to this task.
  assignees = models.ManyToManyField(Participant, related_name='tasks', blank=True)

  def __str__(self):
    return '{} on {}'.format(self.task_type.name, self.date)
