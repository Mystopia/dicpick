# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (absolute_import, division, generators, nested_scopes,
                        print_function, unicode_literals, with_statement)

import datetime

from django.contrib.auth.models import Group, User
from django.core.management import BaseCommand
from django.db import IntegrityError

from dicpick.models import Camp, Event, Tag, TaskType


def _safe_save(obj):
  try:
    obj.save()
    print(('{} saved'.format(obj)))
    return True
  except IntegrityError:
    print(('{} already exists'.format(obj)))
    return False


class Command(BaseCommand):

  def handle(self, *args, **options):
    self.create_superuser()
    self.create_dev_data()
    self.create_other_camp_data()

  def create_superuser(self):
    god = User(username='god', email='god@heaven.com', is_superuser=True, is_staff=True)
    god.set_password('123456')
    _safe_save(god)

  def create_dev_data(self):
    member_group = Group(name='mystopia_member')
    _safe_save(member_group)
    member_group = Group.objects.filter(name='mystopia_member').get()

    admin_group = Group(name='mystopia_admin')
    _safe_save(admin_group)
    admin_group = Group.objects.filter(name='mystopia_admin').get()

    james = User(username='james', first_name='James', last_name='Landau', email='james.landau@gmail.com')
    james.set_password('123456')
    if _safe_save(james):
      james.groups.add(member_group)
      james.groups.add(admin_group)
    james = User.objects.filter(username='james').get()

    mystopia = Camp(name='Mystopia', slug='mystopia', admin_group=admin_group, member_group=member_group)
    _safe_save(mystopia)
    mystopia = Camp.objects.filter(slug='mystopia').get()

    bm2016 = Event(camp=mystopia, name='Burning Man 2016', slug='2016',
                   start_date=datetime.date(2016, 8, 24), end_date=datetime.date(2016, 9, 5))
    _safe_save(bm2016)
    bm2016 = Event.objects.filter(camp=mystopia, slug='2016').get()

    def add_tag(name):
      tag = Tag(event=bm2016, name=name)
      _safe_save(tag)
      return Tag.objects.filter(event=bm2016, name=name).get()

    camp_manager = add_tag('camp manager')
    returner = add_tag('returner')
    early_arriver = add_tag('early arriver')

    tt = TaskType(event=bm2016, name='Morning Camp Manager', num_people=1, score=10,
                  start_date=bm2016.start_date, end_date=bm2016.end_date)
    _safe_save(tt)
    tt = TaskType.objects.filter(event=bm2016, name='Morning Camp Manager').get()
    tt.tags.add(camp_manager)

    tt = TaskType(event=bm2016, name='Evening Camp Manager', num_people=1, score=10,
                  start_date=bm2016.start_date, end_date=bm2016.end_date)
    _safe_save(tt)
    tt = TaskType.objects.filter(event=bm2016, name='Evening Camp Manager').get()
    tt.tags.add(camp_manager)

    tt = TaskType(event=bm2016, name='Dinner Head Chef', num_people=1, score=20,
                  start_date=bm2016.start_date, end_date=bm2016.end_date)
    _safe_save(tt)
    tt = TaskType.objects.filter(event=bm2016, name='Dinner Head Chef').get()
    tt.tags.add(returner)

    tt = TaskType(event=bm2016, name='Dinner Sous Chef', num_people=3, score=20,
                  start_date=bm2016.start_date, end_date=bm2016.end_date)
    _safe_save(tt)
    tt = TaskType.objects.filter(event=bm2016, name='Dinner Sous Chef').get()

  def create_other_event_data(self):
    mystopia = Camp.objects.filter(slug='mystopia').get()
    yyy_event = Event(camp=mystopia, name='YYY Event', slug='yyy',
                      start_date=datetime.date(2017, 8, 24), end_date=datetime.date(2017, 9, 5))
    _safe_save(yyy_event)
    yyy_event = Event.objects.filter(camp=mystopia, slug='yyy').get()

    def add_yyy_tag(name):
      tag = Tag(event=yyy_event, name=name)
      _safe_save(tag)
      return Tag.objects.filter(event=yyy_event, name=name).get()

    yyy_tag0 = add_yyy_tag('camp manager')
    yyy_tag1 = add_yyy_tag('yyy tag1')
    yyy_tag2 = add_yyy_tag('yyy_tag2')

    tt = TaskType(event=yyy_event, name='YYY TaskType', num_people=7, score=101,
                  start_date=yyy_event.start_date, end_date=yyy_event.end_date)
    _safe_save(tt)
    tt = TaskType.objects.filter(event=yyy_event, name='YYY TaskType').get()
    tt.tags.add(yyy_tag0)
    tt.tags.add(yyy_tag1)

  def create_other_camp_data(self):
    member_group = Group(name='xxx_member')
    _safe_save(member_group)
    member_group = Group.objects.filter(name='xxx_member').get()

    admin_group = Group(name='xxx_admin')
    _safe_save(admin_group)
    admin_group = Group.objects.filter(name='xxx_admin').get()

    xxx_user = User(username='xxx', first_name='Xxx', last_name='Yyyy', email='xxx@yyy.com')
    xxx_user.set_password('123456')
    if _safe_save(xxx_user):
      xxx_user.groups.add(member_group)
      xxx_user.groups.add(admin_group)
    xxx_user = User.objects.filter(username='xxx').get()

    xxx_camp = Camp(name='Xxx', slug='xxx', admin_group=admin_group, member_group=member_group)
    _safe_save(xxx_camp)
    xxx_camp = Camp.objects.filter(slug='xxx').get()

    xxx_event = Event(camp=xxx_camp, name='XXX Event', slug='xxx_event',
                   start_date=datetime.date(2016, 8, 24), end_date=datetime.date(2016, 9, 5))
    _safe_save(xxx_event)
    xxx_event = Event.objects.filter(camp=xxx_camp, slug='xxx_event').get()

    def add_tag(name):
      tag = Tag(event=xxx_event, name=name)
      _safe_save(tag)
      return Tag.objects.filter(event=xxx_event, name=name).get()

    xxx_tag1 = add_tag('xxx 1')
    xxx_tag2 = add_tag('xxx 2')
    xxx_tag3 = add_tag('xxx 3')

    tt = TaskType(event=xxx_event, name='XXX TaskType 1', num_people=2, score=22,
                  start_date=xxx_event.start_date, end_date=xxx_event.end_date)
    _safe_save(tt)
    tt = TaskType.objects.filter(event=xxx_event, name='XXX TaskType 1').get()
    tt.tags.add(xxx_tag1)

    tt = TaskType(event=xxx_event, name='XXX TaskType 2', num_people=5, score=77,
                  start_date=xxx_event.start_date, end_date=xxx_event.end_date)
    _safe_save(tt)
    tt = TaskType.objects.filter(event=xxx_event, name='XXX TaskType 2').get()
    tt.tags.add(xxx_tag2)
    tt.tags.add(xxx_tag3)
