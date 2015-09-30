# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.query import QuerySet
from django.forms.models import model_to_dict

__all__ = [
    'Person',
    'Maillist',
    'ContactRole',
    'Contact',
    'RoleContact',
]


class ContactRole(models.Model):

    name = models.CharField(max_length=128, unique=True)

    def __unicode__(self):
        return u"%s" % self.name

    def export(self, fields=None):
        _fields = ['name'] if fields is None else fields
        return model_to_dict(self, fields=_fields)


# https://djangosnippets.org/snippets/1034/
class SubclassingQuerySet(QuerySet):
    def __getitem__(self, k):
        result = super(SubclassingQuerySet, self).__getitem__(k)
        if isinstance(result, models.Model):
            return result.as_leaf_class()
        else:
            return result

    def __iter__(self):
        for item in super(SubclassingQuerySet, self).__iter__():
            yield item.as_leaf_class()


class ContactManager(models.Manager):
    def get_queryset(self):
        return SubclassingQuerySet(self.model)


class Contact(models.Model):
    content_type = models.ForeignKey(ContentType, editable=False, null=True)
    active       = models.BooleanField(default=True)

    objects = ContactManager()

    def __unicode__(self):
        return u"%s" % self.as_leaf_class()

    def export(self, *args, **kwargs):
        return self.as_leaf_class().export()

    def save(self, *args, **kwargs):
        if not self.content_type:
            self.content_type = ContentType.objects.get_for_model(self.__class__)
        super(Contact, self).save(*args, **kwargs)

    def as_leaf_class(self):
        content_type = self.content_type
        model = content_type.model_class()
        if model == Contact:
            return self
        return model.objects.get(id=self.id)


class Person(Contact):
    """
    Person as Contact.
    """
    contact     = models.OneToOneField(Contact, related_name="person", parent_link=True)
    username = models.CharField(max_length=128, db_index=True, unique=True)
    email       = models.EmailField()

    objects = ContactManager()

    def __unicode__(self):
        return u"%s(%s)" % (self.username, self.email)

    def export(self, fields=None):
        _fields = ['username', 'email'] if fields is None else fields
        return model_to_dict(self, fields=_fields)


class Maillist(Contact):
    """
    Maillist as Contact.
    """
    contact   = models.OneToOneField(Contact, related_name="maillist", parent_link=True)
    mail_name = models.CharField(max_length=128, db_index=True, unique=True)
    email     = models.EmailField()

    objects = ContactManager()

    def __unicode__(self):
        return u"%s(%s)" % (self.mail_name, self.email)

    def export(self, fields=None):
        _fields = ['mail_name', 'email'] if fields is None else fields
        return model_to_dict(self, fields=_fields)


class RoleContactSpecificManager(models.Manager):
    def get(self, **kwargs):
        if kwargs.get('username', None) is not None:
            obj = Contact.objects.get(person__username=kwargs.get('username'),
                                      person__email=kwargs.get('email'))
        elif kwargs.get('mail_name', None) is not None:
            obj = Contact.objects.get(maillist__mail_name=kwargs.get('mail_name'),
                                      maillist__email=kwargs.get('email'))
        else:
            raise KeyError("Unsupported key for RoleContactSpecificManager.")
        get_kwargs = {
            "contact_id": obj.pk,
        }
        if kwargs.get('contact_role', None) is not None:
            contact_role_obj = ContactRole.objects.get(name=kwargs.get('contact_role'))
            get_kwargs["contact_role"] = contact_role_obj
        else:
            raise KeyError("'contact_role' is needed for RoleContactSpecificManager.")
        return self.get_queryset().get(**get_kwargs)

    def create(self, **kwargs):
        if kwargs.get('username', None) is not None:
            obj, _ = Person.objects.get_or_create(username=kwargs.get('username'),
                                                  email=kwargs.get('email'))
        elif kwargs.get('mail_name', None) is not None:
            obj, _ = Maillist.objects.get_or_create(mail_name=kwargs.get('mail_name'),
                                                    email=kwargs.get('email'))
        else:
            raise KeyError("Unsupported key for RoleContactSpecificManager.")
        create_kwargs = {
            "contact_id": obj.pk,
        }
        if kwargs.get('contact_role', None) is not None:
            contact_role_obj, _ = ContactRole.objects.get_or_create(name=kwargs.get('contact_role'))
            create_kwargs["contact_role"] = contact_role_obj
        else:
            raise KeyError("'contact_role' is needed for RoleContactSpecificManager.")
        return self.get_queryset().create(**create_kwargs)


class GlobalComponentRoleContact(models.Model):

    contact_role = models.ForeignKey(ContactRole, related_name='global_component_role_contacts',
                                     on_delete=models.PROTECT)
    contact      = models.ForeignKey(Contact, related_name='global_component_role_contacts',
                                     on_delete=models.PROTECT)
    component = models.ForeignKey('component.GlobalComponent', related_name='global_component_role_contacts',
                                  on_delete=models.PROTECT)

    def __unicode__(self):
        return u"%s: %s: %s" % (unicode(self.component), self.contact_role, unicode(self.contact))

    class Meta:
        unique_together = (
            ("contact", "contact_role", "component"),
        )

    def export(self, fields=None):
        result = {'contact': self.contact.export(fields=fields)}
        result['contact_role'] = self.contact_role.name
        result['component'] = self.component.name
        return result


class ReleaseComponentRoleContact(models.Model):

    contact_role = models.ForeignKey(ContactRole, related_name='release_component_role_contacts',
                                     on_delete=models.PROTECT)
    contact      = models.ForeignKey(Contact, related_name='release_component_role_contacts',
                                     on_delete=models.PROTECT)
    component = models.ForeignKey('component.ReleaseComponent', related_name='release_component_role_contacts',
                                  on_delete=models.PROTECT)

    def __unicode__(self):
        return u"%s: %s: %s" % (unicode(self.component), self.contact_role, unicode(self.contact))

    class Meta:
        unique_together = (
            ("contact", "contact_role", "component"),
        )

    def export(self, fields=None):
        result = {'contact': self.contact.export(fields=fields)}
        result['contact_role'] = self.contact_role.name
        result['component'] = self.component.name
        return result


class RoleContact(models.Model):

    contact_role = models.ForeignKey(ContactRole, related_name='role_contacts',
                                     on_delete=models.PROTECT)
    contact      = models.ForeignKey(Contact, related_name='role_contacts',
                                     on_delete=models.PROTECT)

    objects = models.Manager()
    specific_objects = RoleContactSpecificManager()

    def __unicode__(self):
        return u"%s: %s" % (self.contact_role,
                            unicode(self.contact))

    class Meta:
        unique_together = (
            ("contact", "contact_role"),
        )

    def export(self, fields=None):
        result = {'contact': self.contact.export(fields=fields)}
        result['contact_role'] = self.contact_role.name
        return result
