# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (absolute_import, division, generators, nested_scopes,
                        print_function, unicode_literals, with_statement)

import random
from collections import defaultdict

from django.db import transaction
from django.db.models import Count, F

from dicpick.models import Assignment, Task

"""Helper functions to auto-assign participants to tasks."""


class NoEligibleParticipant(Exception):
  def __init__(self, task):
    super(NoEligibleParticipant, self).__init__(
        'No eligible participant to assign to task {} on date {}'.format(task.task_type.name, task.date))
    self.task = task


def assign_for_task_ids(event, task_ids):
  """Auto-assign the specified tasks.

  :param event: The event the tasks belong to.
  :param task_ids: The tasks to assign (which must belong to the given event).
  """
  return assign_for_filter(event, id__in=task_ids)


@transaction.atomic
def assign_for_filter(event, **task_filter):
  """The actual auto-assign logic.

  Attempts to assign participants to all tasks that are selected by the given filter.

  Note that we currently assign at most one task per participant per date, to avoid scheduling conflicts.
  If this turns out to be too restrictive (that is, if we do need to assign the same person two tasks on the
  same day) we'll have to have more fine-grained scheduling, e.g., a range of hours, or a simple
  morning/afternoon/evening distinction.

  :param event: Assign this event's tasks.
  :param task_filter: Assign only to the event's tasks that match this QuerySet filter.
  """
  # Note that the event filter is important even if we have a task_type_id in the task_filter,
  # to verify that the task_type does actually belong to the event.
  tasks = list(
      Task.objects
        .annotate(assignee_count=Count('assignees'))
        .filter(assignee_count__lt=F('num_people'), task_type__event=event, **task_filter)
        .select_related('task_type')
        .prefetch_related('tags', 'assignees', 'assignees__do_not_assign_with', 'do_not_assign_to')
        .order_by()  # Clear the default ordering to avoid superfluous grouping.
  )
  participants = list(
      event.participants
        .select_related('user')
        .prefetch_related('tags', 'tasks')
        .all()
  )

  # Map of participant id -> Participant object with that id.
  participants_by_id = {p.id: p for p in participants}

  # Map of participant id -> set of dates on which that participant already has assigned tasks.
  participant_busy_dates_by_id = {p.id: p.cached_task_dates for p in participants}

  def _is_eligible(task, p):
    """Returns True iff the participant is eligible to be assigned to the task."""
    if p in task.cached_do_not_assign_to:
      return False
    for a in task.cached_assignees:
      if p == a or p in a.cached_do_not_assign_with:
        return False

    task_tags = set(task.cached_tags)
    return (p.is_in_date_range(task.date) and
            task.date not in participant_busy_dates_by_id[p.id] and
            (not task_tags or task_tags.intersection(p.cached_tags)))

  # All task_types we're dealing with.
  task_types = set(task.task_type for task in tasks)

  # Triples of (participant id, tasks__task_type, count), where count is always > 0.
  # These state how many tasks of that type have been assigned to that participant.
  # This is useful for "task diversity" - attempting not to assign too many tasks of a single type to
  # a single participant.
  participant_task_type_counts = (
    event.participants
      .values('id', 'tasks__task_type')
      .annotate(count=Count('tasks__task_type'))
      .filter(tasks__task_type__in=task_types, count__gt=0)
      .all()
  )

  # Map of task_type -> (map of count -> participants already assigned this number of tasks of that task_type).
  task_type_count_participants = defaultdict(lambda: defaultdict(set))

  # Start by assuming participants are assigned to 0 tasks of each type.
  for task_type in task_types:
    for participant in participants:
      task_type_count_participants[task_type.id][0].add(participant)

  # Then update based on actual data.
  for x in participant_task_type_counts:
    task_type_id = x['tasks__task_type']
    participant_id = x['id']
    task_type_count_participants[task_type_id][0].discard(participants_by_id[participant_id])
    task_type_count_participants[task_type_id][x['count']].add(participants_by_id[participant_id])

  # Tasks we failed to assign anyone to.
  unassignable_tasks = set()

  # Assignment objects representing successful assignments that need to be stored in the database.
  to_create = []

  # Helper function to auto-assign a single task, if possible.
  def assign_task(task):
    # Assign the remaining empty assignment slots for this task.
    for i in range(task.cached_assignees.count(), task.num_people):
      # First try candidates with 0 tasks of this type, then 1, etc.  This provides a good spread of task diversity.
      count_participant_pairs = sorted(task_type_count_participants[task.task_type_id].items())
      for count, candidates in count_participant_pairs:
        eligible = [p for p in candidates if _is_eligible(task, p)]
        if eligible:  # Pick some random candidate from among those with the lowest score.
          lowest_score = min(p.assigned_score for p in eligible)
          assign_to = random.choice([p for p in eligible if p.assigned_score == lowest_score])
          break
      else:
        unassignable_tasks.add(task.id)
        return

      # Do the accounting to update our data structures.
      task_type_count_participants[task.task_type.id][count].remove(assign_to)
      task_type_count_participants[task.task_type.id][count + 1].add(assign_to)
      participant_busy_dates_by_id[assign_to.id].add(task.date)

      # Create the Assignment object representing the successful assignment.
      to_create.append(Assignment(participant=assign_to, task=task, automatic=True))
      assign_to.assigned_score += task.score

  # Now attempt to assign each task.
  for t in tasks:
    assign_task(t)

  Assignment.objects.bulk_create(to_create)
  return unassignable_tasks
