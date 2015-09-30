# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


def migrate_contact_role_for_component(apps, schema_editor):
    contact_roles = apps.get_model("contact", "RoleContact")
    GlobalComponentRoleContact = apps.get_model("contact", "GlobalComponentRoleContact")
    ReleaseComponentRoleContact = apps.get_model("contact", "ReleaseComponentRoleContact")
    for contact in contact_roles.objects.all():
        for rc in contact.releasecomponent_set.all():
            ReleaseComponentRoleContact.objects.create(component=rc, contact_role=contact.contact_role,
                                                       contact=contact.contact)
        for gc in contact.globalcomponent_set.all():
            GlobalComponentRoleContact.objects.create(component=gc, contact_role=contact.contact_role,
                                                      contact=contact.contact)


class Migration(migrations.Migration):

    dependencies = [
        ('component', '0007_auto_20150821_0834'),
        ('contact', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GlobalComponentRoleContact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('component', models.ForeignKey(related_name='global_component_role_contacts', on_delete=django.db.models.deletion.PROTECT, to='component.GlobalComponent')),
                ('contact', models.ForeignKey(related_name='global_component_role_contacts', on_delete=django.db.models.deletion.PROTECT, to='contact.Contact')),
                ('contact_role', models.ForeignKey(related_name='global_component_role_contacts', on_delete=django.db.models.deletion.PROTECT, to='contact.ContactRole')),
            ],
        ),
        migrations.CreateModel(
            name='ReleaseComponentRoleContact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('component', models.ForeignKey(related_name='release_component_role_contacts', on_delete=django.db.models.deletion.PROTECT, to='component.ReleaseComponent')),
                ('contact', models.ForeignKey(related_name='release_component_role_contacts', on_delete=django.db.models.deletion.PROTECT, to='contact.Contact')),
                ('contact_role', models.ForeignKey(related_name='release_component_role_contacts', on_delete=django.db.models.deletion.PROTECT, to='contact.ContactRole')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='releasecomponentrolecontact',
            unique_together=set([('contact', 'contact_role', 'component')]),
        ),
        migrations.AlterUniqueTogether(
            name='globalcomponentrolecontact',
            unique_together=set([('contact', 'contact_role', 'component')]),
        ),
        migrations.RunPython(migrate_contact_role_for_component)
    ]
