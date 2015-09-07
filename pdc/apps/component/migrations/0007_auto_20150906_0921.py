# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


id_release_component_id = {}
id_global_component_id = {}


def save_info(apps, schema_editor):
    contact_roles = apps.get_model("contact", "RoleContact")
    for contact in contact_roles.objects.all():
        for rc in contact.releasecomponent_set.all():
            id_release_component_id.setdefault(contact.id, []).append(rc.id)
        for gc in contact.globalcomponent_set.all():
            id_global_component_id.setdefault(contact.id, []).append(gc.id)


def migrate_contact_role_for_component(apps, schema_editor):
    contact_roles = apps.get_model("contact", "RoleContact")
    GlobalComponent = apps.get_model("component", "GlobalComponent")
    ReleaseComponent = apps.get_model("component", "ReleaseComponent")
    for contact in contact_roles.objects.all():
        if contact.id in id_release_component_id:
            for rc_id in id_release_component_id[contact.id]:
                contact.release_components.add(ReleaseComponent.objects.get(id=rc_id))
        if contact.id in id_global_component_id:
            for gc_id in id_global_component_id[contact.id]:
                contact.global_components.add(GlobalComponent.objects.get(id=gc_id))


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0001_initial'),
        ('component', '0006_auto_20150818_0614'),
    ]

    operations = [
        migrations.RunPython(save_info),
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
            name='role_contacts',
            field=models.ManyToManyField(related_name='global_components', to='contact.RoleContact', blank=True),
        ),
        migrations.AddField(
            model_name='releasecomponent',
            name='role_contacts',
            field=models.ManyToManyField(related_name='release_components', to='contact.RoleContact', blank=True),
        ),
        migrations.RunPython(migrate_contact_role_for_component)
    ]
