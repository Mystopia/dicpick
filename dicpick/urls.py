# coding=utf-8
# Copyright 2016 Mystopia.
from django.urls import include, path

from dicpick import views

app_name = "dicpick"
urlpatterns = [
  path("", views.user_home, name="user_home"),

  path("<slug:camp_slug>/", views.CampDetail.as_view(), name="camp_detail"),

  path("<slug:camp_slug>/create_event/", views.EventCreate.as_view(),name="event_create"),
  path("<slug:camp_slug>/<slug:event_slug>/", views.EventDetail.as_view(), name="event_detail"),
  path("<slug:camp_slug>/<slug:event_slug>/update/", views.EventUpdate.as_view(), name="event_update"),
  path("<slug:camp_slug>/<slug:event_slug>/delete/", views.EventDelete.as_view(), name="event_delete"),

  path("<slug:camp_slug>/<slug:event_slug>/tags/", views.TagsUpdate.as_view(), name="tags_update"),
  path("<slug:camp_slug>/<slug:event_slug>/tags/autocomplete/", views.TagAutocomplete.as_view(), name="tag_autocomplete"),

  path("<slug:camp_slug>/<slug:event_slug>/participants/", views.ParticipantsUpdate.as_view(), name="participants_update"),
  path("<slug:camp_slug>/<slug:event_slug>/participants/import/", views.ParticipantsImport.as_view(), name="participants_import"),
  path("<slug:camp_slug>/<slug:event_slug>/participants/scores/", views.ParticipantScores.as_view(), name="participants_scores"),
  path("<slug:camp_slug>/<slug:event_slug>/participants/autocomplete/", views.ParticipantAutocomplete.as_view(), name="participant_autocomplete"),

  path("<slug:camp_slug>/<slug:event_slug>/task_types/", views.TaskTypesUpdate.as_view(), name="task_types_update"),
  path("<slug:camp_slug>/<slug:event_slug>/tasks_by_type/", views.TasksByType.as_view(), name="tasks_by_type"),
  path("<slug:camp_slug>/<slug:event_slug>/tasks_by_type/<int:task_type_pk>", views.TasksByTypeUpdate.as_view(), name="tasks_by_type_update"),
  path("<slug:camp_slug>/<slug:event_slug>/tasks_by_date/", views.TasksByDate.as_view(), name="tasks_by_date"),
  path("<slug:camp_slug>/<slug:event_slug>/tasks_by_date/<str:date>", views.TasksByDateUpdate.as_view(), name="tasks_by_date_update"),

  path("<slug:camp_slug>/<slug:event_slug>/tasks/all", views.AllTasks.as_view(), name="all_tasks"),
  path("<slug:camp_slug>/<slug:event_slug>/tasks/all.csv", views.AllTasks.as_view(), {"emit_csv": True}, name="all_tasks_csv"),
]
