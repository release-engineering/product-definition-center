#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from . import models
from pdc.apps.common.fields import ChoiceSlugField
from pdc.apps.common.serializers import StrictSerializerMixin
from pdc.apps.component.models import GlobalComponent
from pdc.apps.contact.models import Person
from pdc.apps.release import models as release_models


class RepoSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    release_id       = serializers.CharField(source='variant_arch.variant.release.release_id')
    variant_uid      = serializers.CharField(source='variant_arch.variant.variant_uid')
    arch             = serializers.CharField(source='variant_arch.arch.name')
    service          = ChoiceSlugField(slug_field='name',
                                       queryset=models.Service.objects.all())
    repo_family      = ChoiceSlugField(slug_field='name',
                                       queryset=models.RepoFamily.objects.all())
    content_format   = ChoiceSlugField(slug_field='name',
                                       queryset=models.ContentFormat.objects.all())
    content_category = ChoiceSlugField(slug_field='name',
                                       queryset=models.ContentCategory.objects.all())
    name             = serializers.CharField()
    shadow           = serializers.BooleanField(required=False, default=False)
    product_id       = serializers.IntegerField(required=False, default=None, allow_null=True)

    class Meta:
        model = models.Repo
        fields = ('id', 'release_id', 'variant_uid', 'arch', 'service', 'repo_family',
                  'content_format', 'content_category', 'name', 'shadow', 'product_id')

    def validate(self, attrs):
        try:
            variant_arch = attrs.get('variant_arch', {})
            release_id  = variant_arch.get('variant', {}).get('release', {}).get('release_id', '')
            variant_uid = variant_arch.get('variant', {}).get('variant_uid', '')
            arch        = variant_arch.get('arch', {}).get('name', '')
            if self.instance and self.partial:
                variantarch = self.instance.variant_arch
                release_id = release_id or variantarch.variant.release.release_id
                variant_uid = variant_uid or variantarch.variant.variant_uid
                arch = arch or variantarch.arch.name
            attrs['variant_arch'] = release_models.VariantArch.objects.get(
                variant__release__release_id=release_id,
                variant__variant_uid=variant_uid,
                arch__name=arch
            )
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                'No VariantArch for release_id=%s, variant_uid=%s, arch=%s'
                % (release_id, variant_uid, arch)
            )
        if not self.instance:
            # Validate repo name.
            instance = models.Repo(**attrs)
            instance.clean()
            # Validate repo is unique.
            try:
                models.Repo.objects.get(**attrs)
                raise serializers.ValidationError(
                    'Repo with this Variant arch, Service, Repo family, Content format, '
                    'Content category, Name and Shadow already exists.'
                )
            except models.Repo.DoesNotExist:
                pass
        return super(RepoSerializer, self).validate(attrs)


class RepoFamilySerializer(StrictSerializerMixin, serializers.ModelSerializer):
    name          = serializers.CharField()
    description   = serializers.CharField()

    class Meta:
        model = models.RepoFamily
        fields = ("name", "description")


class ContentCategorySerializer(StrictSerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = models.ContentCategory
        fields = ('name', 'description',)


class ContentFormatSerializer(StrictSerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = models.ContentFormat
        fields = ('name', 'description',)


class ServiceSerializer(StrictSerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = models.Service
        fields = ('name', 'description',)


class PushTargetSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    name = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    host = serializers.CharField(allow_blank=True, required=False)
    service = ChoiceSlugField(slug_field='name', queryset=models.Service.objects.all())

    class Meta:
        model = models.PushTarget
        fields = ('id', 'name', 'description', 'service', 'host')


class MultiDestinationSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    global_component = ChoiceSlugField(slug_field='name', queryset=GlobalComponent.objects.all())
    origin_repo_id = serializers.PrimaryKeyRelatedField(
        source='origin_repo', write_only=True, queryset=models.Repo.objects.all())
    destination_repo_id = serializers.PrimaryKeyRelatedField(
        source='destination_repo', write_only=True, queryset=models.Repo.objects.all())
    origin_repo = RepoSerializer(read_only=True)
    destination_repo = RepoSerializer(read_only=True)
    subscribers = ChoiceSlugField(slug_field='username', many=True, queryset=Person.objects.filter(active=True))
    active = serializers.BooleanField(default=True)

    class Meta:
        model = models.MultiDestination
        fields = (
            'id',
            'global_component',
            'origin_repo_id',
            'destination_repo_id',
            'origin_repo',
            'destination_repo',
            'subscribers',
            'active',
        )
