#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import re
import json

from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.core.exceptions import FieldError
from django.http import Http404
from django.conf import settings

from contrib import drf_introspection

from rest_framework import mixins, status, viewsets
from rest_framework.response import Response


class NoSetattrInPreSaveMixin(object):
    """
    Skip all `setattr`s in pre_save intentionally, as they modify the
    object to be saved by resetting all fields present in URL.
    """
    def pre_save(self, obj):
        if hasattr(obj, 'full_clean'):
            obj.full_clean()


class ChangeSetCreateModelMixin(mixins.CreateModelMixin):
    """
    Wrapper around CreateModelMixin that logs the change.
    """
    def perform_create(self, serializer):
        obj = serializer.save()
        self.object = obj
        if not isinstance(obj, list):
            obj = [obj]
        for item in obj:
            model_name = ContentType.objects.get_for_model(item).model
            self.request.changeset.add(model_name,
                                       item.id,
                                       'null',
                                       json.dumps(item.export()))


class NoEmptyPatchMixin(object):
    """
    This mixin checks request data on PATCH request and returns an error
    response if the body is empty. This is useful as some software (notable
    `python-requests`) may remove the request body on redirect, which would
    lead to successful update with no changes performed..
    """
    def update(self, request, *args, **kwargs):
        if kwargs.get('partial', False) and not request.data:
            return NoEmptyPatchMixin.make_response()
        return super(NoEmptyPatchMixin, self).update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not request.data:
            return NoEmptyPatchMixin.make_response()
        return super(NoEmptyPatchMixin, self).partial_update(request, *args, **kwargs)

    @classmethod
    def make_response(self):
        """
        Use this method to build a descriptive error response for the empty
        PATCH request situation.
        """
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data=settings.EMPTY_PATCH_ERROR_RESPONSE
        )


class ChangeSetUpdateModelMixin(NoSetattrInPreSaveMixin,
                                NoEmptyPatchMixin,
                                mixins.UpdateModelMixin):
    """
    Wrapper around UpdateModelMixin that logs the change.
    """
    # NOTE(xchu): As Lubomir Sedlar pointed out that saving the old value in
    #             pre_save is actually too late because there are some
    #             modifications done before this hook is fired.
    #             His solution was to save the object the first time
    #             `get_object()` was called.
    def get_object(self):
        obj = super(ChangeSetUpdateModelMixin, self).get_object()
        self.origin_obj = getattr(self, 'origin_obj', obj.export())
        return obj

    def perform_update(self, serializer):
        obj = serializer.save()
        self.object = obj

        model_name = ContentType.objects.get_for_model(obj).model
        self.request.changeset.add(model_name,
                                   obj.id,
                                   json.dumps(self.origin_obj),
                                   json.dumps(obj.export()))
        del self.origin_obj


class ChangeSetDestroyModelMixin(mixins.DestroyModelMixin):
    """
    Wrapper around DestroyModelMixin that logs the change.
    """
    def perform_destroy(self, obj):
        model_name = ContentType.objects.get_for_model(obj).model
        obj_id = obj.id
        obj_content = json.dumps(obj.export())
        super(ChangeSetDestroyModelMixin, self).perform_destroy(obj)
        self.request.changeset.add(model_name,
                                   obj_id,
                                   obj_content,
                                   'null')


class ChangeSetModelMixin(ChangeSetCreateModelMixin,
                          ChangeSetUpdateModelMixin,
                          ChangeSetDestroyModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.ListModelMixin):
    """
    Model viewset that provides default `list()`, `retrieve()`,
    with logging the changes in `create`, `update()`, `partial_update()`
    and `destroy()` actions.
    """
    pass


class StrictQueryParamMixin(object):
    """
    This mixin will make a viewset strict in what query string parameters it
    accepts. If an unknown parameter is used, a 400 BAD REQUEST response will
    be sent (through the global exception handler).

    The list of allowed parameters is obtained from multiple sources:
      * filter set class
      * filter_fields attribute
      * extra_query_params attribute (which should be a list/tuple of strings)
      * paginate_by_param attribute

    The serializer can define what query parameters it uses by defining a
    `query_params` class attribute on the serializer. Note that this should
    only include the parameters that are passed via URL query string, not
    request body fields.

    It also provides some helper functions for examining request.
    """
    def initial(self, request, *args, **kwargs):
        super(StrictQueryParamMixin, self).initial(request, *args, **kwargs)

        # We should not raise the exception if there is no handler for the
        # requested method, as it is better to return 405 METHOD NOT ALLOWED in
        # such case even if there are extra query parameters.
        if (request.method.lower() not in self.http_method_names or
                not hasattr(self, request.method.lower())):
            return

        allowed_keys = drf_introspection.get_allowed_query_params(self)
        extra_keys = set(request.query_params.keys()) - allowed_keys
        if extra_keys:
            raise FieldError('Unknown query params: %s.' % ', '.join(sorted(extra_keys)))

    def is_filtered_list(self):
        """Return True if the current action is list and pagination is enabled.

        This may be handy for adding prefetching of related models from
        database.
        """
        return self.action == 'list' and self.paginator.get_page_size(self.request)


class PDCModelViewSet(StrictQueryParamMixin,
                      ChangeSetModelMixin,
                      viewsets.GenericViewSet):
    """
    PDC common ModelViewSet.
    With `StrictQueryParam`, `ProtectOnDelete` and `ChangeSetModel`
    """
    pass


class MultiLookupFieldMixin(object):
    """
    This mixin allows using multiple lookup fields in URL. The viewset using
    this mixin must define `lookup_fields` class attribute as a list (or tuple)
    of two-tuples. Each element of the list corresponds to a single lookup
    field. First element in the inner tuple is the name of the field, second
    element is a regular expression describing what the value in URL should
    look like.

    The field names are used in `get_object` to retrieve the specified
    instance. They should be given in the format usable for `get` method on a
    queryset and all the fields together should be enough to uniquely identify
    a single object.
    """
    lookup_field = 'composite_field'

    def __init__(self, *args, **kwargs):
        if not hasattr(self, 'lookup_fields'):
            raise Exception('The "lookup_fields" attribute must be included."')
        super(MultiLookupFieldMixin, self).__init__(*args, **kwargs)

    def _populate_kwargs(self):
        """
        This methods makes sure kwargs contain the detailed fields. (This is
        necessary for bulk operations to function correctly.)
        """
        m = re.match(self.lookup_value_regex, self.kwargs[self.lookup_field])
        if not m:
            raise Http404('Provided identifier fields do not match expected format.')
        self.kwargs.update(m.groupdict())

    def get_object(self):
        queryset = self.get_queryset()
        self._populate_kwargs()
        filters = {}
        for field_name, _ in self.lookup_fields:
            filters[field_name] = self.kwargs[field_name]
        obj = get_object_or_404(queryset, **filters)
        self.check_object_permissions(self.request, obj)
        return obj
