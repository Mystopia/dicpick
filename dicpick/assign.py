# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (absolute_import, division, generators, nested_scopes,
                        print_function, unicode_literals, with_statement)

from collections import defaultdict

from django.db.models import Count, F

from dicpick.models import Task


class NoEligibleParticipant(Exception):
  def __init__(self, task):
    super(NoEligibleParticipant, self).__init__(
        'No eligible participant to assign to task {} on date {}'.format(task.task_type.name, task.date))
    self.task = task


def is_eligible(task, participant):
  task_tags = set(task.tags.all())
  return (participant.is_in_date_range(task.date) and
          (len(task_tags) == 0 or task_tags.intersection(participant.tags.all()) > 0) and
          participant not in task.assignees.all())


def assign(event, task_type_id, dt):
  task_filter = {'task_type__event': event}
  if task_type_id is not None:
    # Note that the event filter is important even if we have a task_type_id,
    # to verify that the task_type does actually belong to the event.
    task_filter['task_type'] = task_type_id
  if dt is not None:
    task_filter['date'] = dt

  tasks = list(
      Task.objects
        .annotate(assignee_count=Count('assignees'))
        .filter(assignee_count__lt=F('num_people'), **task_filter)
        .select_related('task_type')
        .prefetch_related('tags', 'assignees')
        .order_by()  # Clear the default ordering to avoid superfluous grouping.
  )
  participants = list(
      event.participants
        .select_related('user')
        .prefetch_related('tags')
        .all()
  )

  # All task_types we're dealing with.
  task_types = set()

  # Participant -> score achieved by that participant so far.
  # Allows us to sort participants from lowest to highest score.
  participant_scores = {}

  # particpants -> task_type -> count of tasks of this type assigned to this participant.
  # Allows us to prefer diversity of task types for each participant.
  #participant_task_type_counts = defaultdict(lambda: defaultdict(int))

  for participant in participants:
    participant_scores[participant] = participant.initial_score
  for task in tasks:
    task_types.add(task.task_type)
    for assignee in task.assignees.all():
      participant_scores[assignee] += task.score
      #participant_task_type_counts[assignee][task.task_type] += 1

  participants = sorted(participants, key=lambda p: participant_scores[p])
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
    task_type_count_participants[task_type_id][0].remove(participants_by_id[participant_id])
    task_type_count_participants[task_type_id][count].add(participants_by_id[participant_id])

  for task in tasks:
    for i in range(len(task.assignees.all()), task.num_people):
      # First try candidates with 0 tasks of this type, then 1, etc.  This ensures the best spread of task diversity.
      count_participant_pairs = sorted(task_type_count_participants[task.task_type_id].items())
      for count, participants in count_participant_pairs:
        assign_to = next((p for p in participants if is_eligible(task, p)), None)
        if assign_to is not None:
          break
      else:
        raise NoEligibleParticipant(task)

      task_type_count_participants[task.task_type.id][count].remove(assign_to)
      task_type_count_participants[task.task_type.id][count + 1].add(assign_to)
      task.assignees.add(assign_to)
