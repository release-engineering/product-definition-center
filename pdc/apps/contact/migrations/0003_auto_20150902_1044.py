# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0002_auto_20150826_1025'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='rolecontact',
            unique_together=set([('contact', 'contact_role', 'release_component'), ('contact', 'contact_role', 'global_component')]),
        ),
    ]
