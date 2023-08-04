# coding=utf-8
# Copyright 2016 Mystopia.
from django.contrib import admin

from dicpick.models import Camp, Event, Participant, Tag, Task, TaskType

admin.site.register(Camp)
admin.site.register(Event)
admin.site.register(Tag)
admin.site.register(Participant)
admin.site.register(Task)
admin.site.register(TaskType)
