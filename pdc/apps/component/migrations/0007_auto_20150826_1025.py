# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('component', '0006_auto_20150818_0614'),
        ('contact', '0002_auto_20150826_1025'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='globalcomponent',
            name='contacts',
        ),
        migrations.RemoveField(
            model_name='releasecomponent',
            name='contacts',
        ),
        migrations.AddField(
            model_name='globalcomponent',
            name='contacts',
            field=models.ManyToManyField(to='contact.Contact', through='contact.RoleContact', blank=True),
        ),
        migrations.AddField(
            model_name='releasecomponent',
            name='contacts',
            field=models.ManyToManyField(to='contact.Contact', through='contact.RoleContact', blank=True),
        ),
    ]
