# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (absolute_import, division, generators, nested_scopes,
                        print_function, unicode_literals, with_statement)

from django.conf.urls import url

from dicpick import views


urlpatterns = [
  url(r'^$', views.user_home, name='user_home'),

  url(r'^(?P<camp_slug>\w+)/$', views.CampDetail.as_view(), name='camp_detail'),

  url(r'^(?P<camp_slug>\w+)/create_event/$', views.EventCreate.as_view(), name='event_create'),
  url(r'^(?P<camp_slug>\w+)/(?P<event_slug>\w+)/$', views.EventDetail.as_view(), name='event_detail'),
  url(r'^(?P<camp_slug>\w+)/(?P<event_slug>\w+)/update/$', views.EventUpdate.as_view(), name='event_update'),
  url(r'^(?P<camp_slug>\w+)/(?P<event_slug>\w+)/delete/$', views.EventDelete.as_view(), name='event_delete'),

  url(r'^(?P<camp_slug>\w+)/(?P<event_slug>\w+)/tags/$', views.TagsUpdate.as_view(), name='tags_update'),
  url(r'^(?P<camp_slug>\w+)/(?P<event_slug>\w+)/participants/$', views.ParticipantsUpdate.as_view(), name='participants_update'),
  url(r'^(?P<camp_slug>\w+)/(?P<event_slug>\w+)/participants/import/$', views.ParticipantsImport.as_view(), name='participants_import'),
  url(r'^(?P<camp_slug>\w+)/(?P<event_slug>\w+)/participants/scores/$', views.ParticipantScores.as_view(), name='participants_scores'),
  url(r'^(?P<camp_slug>\w+)/(?P<event_slug>\w+)/participants/autocomplete/$', views.ParticipantAutocomplete.as_view(), name='participant_autocomplete'),

  url(r'^(?P<camp_slug>\w+)/(?P<event_slug>\w+)/task_types/$', views.TaskTypesUpdate.as_view(), name='task_types_update'),
  url(r'^(?P<camp_slug>\w+)/(?P<event_slug>\w+)/tasks_by_type/$', views.TasksByType.as_view(), name='tasks_by_type'),
  url(r'^(?P<camp_slug>\w+)/(?P<event_slug>\w+)/tasks_by_type/(?P<task_type_pk>\d+)$', views.TasksByTypeUpdate.as_view(), name='tasks_by_type_update'),
  url(r'^(?P<camp_slug>\w+)/(?P<event_slug>\w+)/tasks_by_date/$', views.TasksByDate.as_view(), name='tasks_by_date'),
  url(r'^(?P<camp_slug>\w+)/(?P<event_slug>\w+)/tasks_by_date/(?P<date>\w+)$', views.TasksByDateUpdate.as_view(), name='tasks_by_date_update'),
]
