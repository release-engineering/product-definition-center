# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from . import views
from pdc.apps.utils.SortedRouter import router


router.register(r'products', views.ProductViewSet)
router.register(r'product-versions', views.ProductVersionViewSet)
router.register(r'releases', views.ReleaseViewSet)
router.register(r'base-products', views.BaseProductViewSet)
router.register(r'release-types', views.ReleaseTypeViewSet, base_name='releasetype')
router.register('releases/(?P<release_id>[^/]+)/rpm-mapping',
                views.ReleaseRPMMappingView,
                base_name='releaserpmmapping')
router.register(r'rpc/release/import-from-composeinfo',
                views.ReleaseImportView,
                base_name='releaseimportcomposeinfo')
router.register(r'rpc/release/clone',
                views.ReleaseCloneViewSet,
                base_name='releaseclone')
router.register(r'release-variants',
                views.ReleaseVariantViewSet)
router.register(r'variant-types', views.VariantTypeViewSet,
                base_name='varianttype')
