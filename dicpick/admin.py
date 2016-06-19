# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

from django.contrib import admin

from dicpick.models import Camp, Event, Tag, Participant, Task, TaskType

admin.site.register(Camp)
admin.site.register(Event)
admin.site.register(Tag)
admin.site.register(Participant)
admin.site.register(Task)
admin.site.register(TaskType)
