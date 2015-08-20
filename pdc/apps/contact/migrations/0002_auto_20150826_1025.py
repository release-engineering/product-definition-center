# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


id_release_component_id = {}
id_global_component_id = {}


def save_info(apps, schema_editor):
    contact_roles = apps.get_model("contact", "RoleContact")
    for contact in contact_roles.objects.all():
        for rc in contact.releasecomponent_set.all():
            id_release_component_id[contact.id] = rc.id
        for gc in contact.globalcomponent_set.all():
            id_global_component_id[contact.id] = gc.id


def migrate_contact_role_for_component(apps, schema_editor):
    contact_roles = apps.get_model("contact", "RoleContact")
    GlobalComponent = apps.get_model("component", "GlobalComponent")
    ReleaseComponent = apps.get_model("component", "ReleaseComponent")
    for contact in contact_roles.objects.all():
        if contact.id in id_release_component_id:
            contact.release_component = ReleaseComponent.objects.get(id=id_release_component_id[contact.id])
        if contact.id in id_global_component_id:
            contact.global_component = GlobalComponent.objects.get(id=id_global_component_id[contact.id])
        contact.save()


class Migration(migrations.Migration):

    dependencies = [
        #('component', '0007_auto_20150826_1025'),
        ('component', '0006_auto_20150818_0614'),
        ('contact', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(save_info),
        migrations.AddField(
            model_name='rolecontact',
            name='global_component',
            field=models.ForeignKey(related_name='role_contacts', blank=True, to='component.GlobalComponent', null=True),
        ),
        migrations.AddField(
            model_name='rolecontact',
            name='release_component',
            field=models.ForeignKey(related_name='role_contacts', blank=True, to='component.ReleaseComponent', null=True),
        ),
        migrations.RunPython(migrate_contact_role_for_component),
    ]
