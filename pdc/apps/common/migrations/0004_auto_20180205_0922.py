# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0003_auto_20180131_1318'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sigkey',
            name='name',
            field=models.CharField(unique=True, max_length=50),
        ),
    ]
