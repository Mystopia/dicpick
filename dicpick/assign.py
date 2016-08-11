# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (absolute_import, division, generators, nested_scopes,
                        print_function, unicode_literals, with_statement)

import random
from collections import defaultdict

import datetime
from django.db.models import Count, F

from dicpick.models import Task, Assignment


class NoEligibleParticipant(Exception):
  def __init__(self, task):
    super(NoEligibleParticipant, self).__init__(
        'No eligible participant to assign to task {} on date {}'.format(task.task_type.name, task.date))
    self.task = task


def _is_eligible(task, participant):
  if participant in task.do_not_assign_to.all():
    return False
  for a in task.assignees.all():
    if participant == a or participant in a.do_not_assign_with.all():
      return False

  task_tags = set(task.tags.all())
  return (participant.is_in_date_range(task.date) and
          (not task_tags or task_tags.intersection(participant.tags.all())))


def assign_from_request(event, request):
  task_type_str = request.POST.get('task_type')
  date_str = request.POST.get('date')
  task_type_id = int(task_type_str) if task_type_str else None
  dt = datetime.datetime.strptime(date_str, '%Y_%m_%d') if date_str else None
  return assign_for_task_type_and_date(event, task_type_id, dt)


def assign_for_task_type_and_date(event, task_type_id, dt):
  task_filter = {}
  if task_type_id is not None:
    task_filter['task_type'] = task_type_id
  if dt is not None:
    task_filter['date'] = dt

  return assign_for_filter(event, **task_filter)


def assign_for_task_ids(event, task_ids):
  return assign_for_filter(event, id__in=task_ids)


def assign_for_filter(event, **task_filter):
  # Note that the event filter is important even if we have a task_type_id,
  # to verify that the task_type does actually belong to the event.
  tasks = list(
      Task.objects
        .annotate(assignee_count=Count('assignees'))
        .filter(assignee_count__lt=F('num_people'), task_type__event=event, **task_filter)
        .select_related('task_type')
        .prefetch_related('tags', 'assignees', 'assignees__do_not_assign_with')
        .order_by()  # Clear the default ordering to avoid superfluous grouping.
  )
  participants = list(
      event.participants
        .select_related('user')
        .prefetch_related('tags', 'tasks')
        .all()
  )

  # All task_types we're dealing with.
  task_types = set()

  for task in tasks:
    task_types.add(task.task_type)

  participants_by_id = dict((p.id, p) for p in participants)

  participant_task_type_counts = (
    event.participants
      .values('id', 'tasks__task_type')
      .annotate(count=Count('tasks__task_type'))
      .filter(tasks__task_type__in=task_types, count__gt=0)
      .all()
  )

  # task_type -> count -> participants already assigned this number of tasks of that task_type.
  task_type_count_participants = defaultdict(lambda: defaultdict(set))

  # Start by assuming participants are assigned to 0 tasks of each type.
  for task_type in task_types:
    for participant in participants:
      task_type_count_participants[task_type.id][0].add(participant)

  # Then update based on actual data.
  for x in participant_task_type_counts:
    task_type_id = x['tasks__task_type']
    participant_id = x['id']
    count = x['count']
    task_type_count_participants[task_type_id][0].discard(participants_by_id[participant_id])
    task_type_count_participants[task_type_id][count].add(participants_by_id[participant_id])

  unassignable_tasks = set()
  for task in tasks:
    try:
      for i in range(len(task.assignees.all()), task.num_people):
        # First try candidates with 0 tasks of this type, then 1, etc.  This ensures the best spread of task diversity.
        count_participant_pairs = sorted(task_type_count_participants[task.task_type_id].items())
        for count, candidates in count_participant_pairs:
          eligible = [p for p in candidates if _is_eligible(task, p)]
          if eligible:  # Pick some random candidate from among those with the lowest score.
            lowest_score = min(p.assigned_score for p in eligible)
            assign_to = random.choice([p for p in eligible if p.assigned_score == lowest_score])
            break
        else:
          unassignable_tasks.add(task.id)
          raise NoEligibleParticipant(task)

        task_type_count_participants[task.task_type.id][count].remove(assign_to)
        task_type_count_participants[task.task_type.id][count + 1].add(assign_to)
        # TODO: Bulk-create these.
        Assignment.objects.create(participant=assign_to, task=task, automatic=True)
        assign_to.assigned_score += task.score
    except NoEligibleParticipant:
      pass

  return unassignable_tasks
