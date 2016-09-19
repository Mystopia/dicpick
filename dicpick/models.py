# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (absolute_import, division, generators, nested_scopes,
                        print_function, unicode_literals, with_statement)

from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import F, Sum
from django.utils.functional import cached_property


# NOTE: The models purposely use vanilla terminology (e.g., Task, Participant) instead of the more
# evocative terms used by Mystopia (DIC, Camper), as other camps may not share those terms, or
# may want to use their own.  We use the Django i18n mechanisms to spice up the language for Mystopia.


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
  """A superclass for any model that applies to a date range (e.g., an Event)."""
  class Meta:
    abstract = True

  # First date of the range.
  start_date = models.DateField()

  # Last date of the range.
  end_date = models.DateField()

  def date_range(self):
    """A generator that yields every date in the range, in ascending order."""
    date = self.start_date
    while date <= self.end_date:
      yield date
      date += timedelta(days=1)

  def is_in_date_range(self, dt):
    """Returns true iff dt is in the date range."""
    return self.start_date <= dt <= self.end_date


class Event(ModelWithDateRange):
  """An event for some camp, e.g., Mystopia at Burning Man 2016.

  The date range specifies the days on which the event occurs.
  """
  class Meta:
    unique_together = [('camp', 'name'), ('camp', 'slug')]

  # The camp this event belongs to.
  camp = models.ForeignKey(Camp, related_name='events')

  # Human-readable event name.
  name = models.CharField(max_length=40, help_text='E.g., "Burning Man 2016".')

  # Short name for use as a slug in URLs.
  slug = models.SlugField(max_length=10, db_index=True, help_text='A short string to use in URLs.  E.g., "2016".')

  def participants_sorted_by_score(self):
    """Returns a list of all participants in this event, sorted by descending assigned task scores."""
    return sorted(self.participants.all().prefetch_related('user', 'tasks', 'tasks__task_type'),
                  key=lambda p: p.assigned_score, reverse=True)

  @cached_property
  def total_score(self):
    """The sum of the scores of all tasks in this event."""
    return Task.objects.filter(task_type__event=self).aggregate(
        total_score=Sum(F('num_people')*F('score')))['total_score'] or 0

  @cached_property
  def total_assigned_score(self):
    """The sum of the scores of all assigned tasks in this event."""
    return Task.assignees.through.objects.filter(task__task_type__event=self).aggregate(
        total_assigned_score=Sum('task__score'))['total_assigned_score'] or 0

  @cached_property
  def num_participants(self):
    """The number of participants in this event."""
    return self.participants.count()

  @cached_property
  def num_tasks(self):
    """The number of tasks in this event."""
    return Task.objects.filter(task_type__event=self).count()

  @cached_property
  def score_per_participant(self):
    """Returns the total score divided by the number of participants, rounded to the nearest integer.

    This is the average number of points a participant will have if all tasks are assigned, and is
    a useful "fairness" metric (although it does not take a participant's initial score into account).
    """
    if self.num_participants == 0:
      return 0
    return int(self.total_score / self.num_participants + 0.5)

  def get_absolute_url(self):
    return reverse('dicpick:event_detail', kwargs={'camp_slug': self.camp.slug, 'event_slug': self.slug })

  def __str__(self):
    return self.name


class Tag(models.Model):
  """A tag that can be assigned to participants, such as 'Returner', 'Early Arriver', 'Camp Manager'."""
  class Meta:
    unique_together = [('event', 'name')]

  # The event this tag is relevant to.  If multiple events have the same taggable concepts, the
  # tags must be recreated for each event.
  event = models.ForeignKey(Event, related_name='tags')

  # The tag text.
  name = models.CharField(max_length=20)

  def __str__(self):
    return self.name


class Participant(ModelWithDateRange):
  """Someone eligible to perform tasks in an event, e.g., a Mystopian going to Burning Man 2016.

  The date range specifies when the participant is available to perform tasks.
  """
  class Meta:
    unique_together = [('event', 'user')]

  # The event.
  event = models.ForeignKey(Event, related_name='participants')

  # The underlying user.
  user = models.ForeignKey(User)

  # Tags assigned to this participant.
  tags = models.ManyToManyField(Tag, related_name='participants', blank=True)

  # Initial score that this participant has already earned through out-of-band contributions to the camp.
  # Assumed to be zero if unspecified.
  initial_score = models.IntegerField(blank=True, default=0)

  # Do not assign this participant to tasks alongside these other participants.
  # Useful if we know that two people don't get along...
  do_not_assign_with = models.ManyToManyField('self', blank=True)

  @cached_property
  def assigned_score(self):
    """The total score of tasks assigned to this participant, including the initial score."""
    return self.initial_score + sum(t.score for t in self.tasks.all())

  def short_name(self):
    """A useful display name for this participant.

    Note: Will cause the user to be fetched, so if calling on multiple participants be sure
    that the users have been prefetched efficiently using select_related().
    """
    return '{} {}.'.format(self.user.first_name.split()[0], self.user.last_name[:1])

  # Cached querysets, so they aren't re-created (and therefore re-evaluated) on every call.

  @cached_property
  def cached_tags(self):
    return self.tags.all()

  @cached_property
  def cached_do_not_assign_with(self):
    return self.do_not_assign_with.all()

  @cached_property
  def cached_tasks(self):
    return self.tasks.all()

  @cached_property
  def cached_task_dates(self):
    return set(t.date for t in self.cached_tasks)

  def __str__(self):
    return self.user.get_full_name()


class TaskType(ModelWithDateRange):
  """A type of task, e.g., Dinner Head Chef.

  The date range specifies the dates on which this task is needed.  We assume that this is specifiable
  with a range.  The model doesn't currently support 'gaps' (such as tasks that are needed every other day).
  """
  class Meta:
    unique_together = [('event', 'name')]

  event = models.ForeignKey(Event, related_name='task_types')

  # Human-readable name of the task type.
  name = models.CharField(max_length=40)

  # These can be overridden for individual task instances (e.g., we may need fewer people for dinner preparation
  # on burn night).

  # Number of people needed for this task, per day.
  num_people = models.IntegerField()

  # Score each person gets for completing tasks of this type.
  score = models.IntegerField()

  # Tasks of this type can only be assigned to participants with at least one of these tags.
  tags = models.ManyToManyField(Tag, related_name='task_types', blank=True)

  # Cached querysets, so they aren't re-created (and therefore re-evaluated) on every call.

  @cached_property
  def cached_tags(self):
    return self.tags.all()

  def __str__(self):
    return self.name


class Task(models.Model):
  """An instance of a particular task type on a particular date, e.g., Dinner Head Chef on 8/30/2016."""
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
  assignees = models.ManyToManyField(Participant, through='Assignment', related_name='tasks', blank=True)

  # Participants that must not be assigned to this task.
  # E.g., because we know they have another commitment on this date.
  do_not_assign_to = models.ManyToManyField(Participant, related_name='unassignable_tasks', blank=True)

  # Cached querysets, so they aren't re-created (and therefore re-evaluated) on every call.

  @cached_property
  def cached_tags(self):
    return self.tags.all()

  @cached_property
  def cached_assignees(self):
    return self.assignees.all()

  @cached_property
  def cached_do_not_assign_to(self):
    return self.do_not_assign_to.all()

  def __str__(self):
    return '{} on {}'.format(self.task_type.name, self.date)


class Assignment(models.Model):
  """The through table for task <-> participant assignments.

  We use this instead of Django's implicit through table, so we can record whether
  the assigment was automatic or manual.
  """
  participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
  task = models.ForeignKey(Task, on_delete=models.CASCADE)
  # Was this auto-assigned (if not, it was manually assigned).
  automatic = models.BooleanField()
