# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('release', '0006_auto_20160512_0515'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReleaseInteropFeatureCategories',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('description', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
    ]
