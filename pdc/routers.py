#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from pdc.apps.auth import views as pdc_auth_views
from pdc.apps.changeset import views as changeset_views
from pdc.apps.component import views as component_views
from pdc.apps.contact import views as contact_views
from pdc.apps.release import views as release_views
from pdc.apps.compose import views as compose_views
from pdc.apps.repository import views as repo_views
from pdc.apps.common import views as common_views
from pdc.apps.package import views as rpm_views
from pdc.apps.utils import SortedRouter
from pdc.apps.osbs import views as osbs_views
from pdc.apps.partners import views as partner_views


router = SortedRouter.PDCRouter()

# register api token auth view
router.register(r'auth/token', pdc_auth_views.TokenViewSet, base_name='token')
router.register(r'auth/groups', pdc_auth_views.GroupViewSet)
router.register(r'auth/permissions', pdc_auth_views.PermissionViewSet)
router.register(r'auth/current-user',
                pdc_auth_views.CurrentUserViewSet,
                base_name='currentuser')

# register changeset view sets
router.register(r'changesets', changeset_views.ChangesetViewSet)

# register release view sets
router.register(r'products', release_views.ProductViewSet)
router.register(r'product-versions', release_views.ProductVersionViewSet)
router.register(r'releases', release_views.ReleaseViewSet)
router.register(r'base-products', release_views.BaseProductViewSet)
router.register(r'release-types', release_views.ReleaseTypeViewSet, base_name='releasetype')

# TODO: these two end-points will be removed
router.register(r'persons', contact_views.PersonViewSet, base_name='persondeprecated')
router.register(r'maillists', contact_views.MaillistViewSet, base_name='maillistdeprecated')

# register contact view sets
router.register(r'contacts/people', contact_views.PersonViewSet, base_name='person')
router.register(r'contacts/mailing-lists', contact_views.MaillistViewSet, base_name='maillist')
router.register(r'contact-roles', contact_views.ContactRoleViewSet)
router.register(r'role-contacts', contact_views.RoleContactViewSet)

# register component view sets
router.register(r'labels', common_views.LabelViewSet, base_name='label')

router.register(r'global-components',
                component_views.GlobalComponentViewSet,
                base_name='globalcomponent')
router.register(r'global-components/(?P<instance_pk>[^/.]+)/contacts',
                component_views.GlobalComponentContactViewSet,
                base_name='globalcomponentcontact')
router.register(r'global-components/(?P<instance_pk>[^/.]+)/labels',
                component_views.GlobalComponentLabelViewSet,
                base_name='globalcomponentlabel')
router.register(r'release-components',
                component_views.ReleaseComponentViewSet,
                base_name='releasecomponent')
router.register(r'release-components/(?P<instance_pk>[^/.]+)/contacts',
                component_views.ReleaseComponentContactViewSet,
                base_name='releasecomponentcontact')
router.register(r'bugzilla-components',
                component_views.BugzillaComponentViewSet,
                base_name='bugzillacomponent')
router.register(r'component-groups', component_views.GroupViewSet, base_name='componentgroup')
router.register(r'component-group-types', component_views.GroupTypeViewSet, base_name='componentgrouptype')
router.register(r'component-relationship-types', component_views.ReleaseComponentRelationshipTypeViewSet,
                base_name='componentrelationshiptype')
router.register(r'release-component-relationships', component_views.ReleaseComponentRelationshipViewSet,
                base_name='rcrelationship')
router.register(r'release-component-types', component_views.ReleaseComponentTypeViewSet,
                base_name='releasecomponenttype')

# register compose view sets
router.register(r'composes', compose_views.ComposeViewSet)
router.register(r'composes/(?P<compose_id>[^/]+)/rpm-mapping',
                compose_views.ComposeRPMMappingView,
                base_name='composerpmmapping')
router.register(r'compose-rpms', compose_views.ComposeRPMView)
router.register(r'compose-images', compose_views.ComposeImageView)

router.register(r'rpc/release/import-from-composeinfo',
                release_views.ReleaseImportView,
                base_name='releaseimportcomposeinfo')
router.register(r'rpc/compose/import-images',
                compose_views.ComposeImportImagesView,
                base_name='composeimportimages')

router.register(r'repos', repo_views.RepoViewSet)
router.register(r'repo-families', repo_views.RepoFamilyViewSet,
                base_name='repofamily')
router.register(r'rpc/repos/clone',
                repo_views.RepoCloneViewSet,
                base_name='repoclone')

# This must be specified after deprecated repos so that automatic link
# generation picks this version.
router.register(r'content-delivery-repos', repo_views.RepoViewSet)
router.register(r'content-delivery-repo-families', repo_views.RepoFamilyViewSet,
                base_name='contentdeliveryrepofamily')
router.register(r'rpc/content-delivery-repos/clone',
                repo_views.RepoCloneViewSet,
                base_name='cdreposclone')

router.register('overrides/rpm',
                compose_views.ReleaseOverridesRPMViewSet,
                base_name='overridesrpm')

router.register(r'rpc/release/clone',
                release_views.ReleaseCloneViewSet,
                base_name='releaseclone')
router.register(r'rpc/where-to-file-bugs', compose_views.FilterBugzillaProductsAndComponents,
                base_name='bugzilla')

router.register('rpc/find-compose-by-release-rpm/(?P<release_id>[^/]+)/(?P<rpm_name>[^/]+)',
                compose_views.FindComposeByReleaseRPMViewSet,
                base_name='findcomposebyrr')

router.register('rpc/find-older-compose-by-compose-rpm/(?P<compose_id>[^/]+)/(?P<rpm_name>[^/]+)',
                compose_views.FindOlderComposeByComposeRPMViewSet,
                base_name='findoldercomposebycr')

router.register('rpc/find-composes-by-product-version-rpm/(?P<product_version>[^/]+)/(?P<rpm_name>[^/]+)',
                compose_views.FindComposeByProductVersionRPMViewSet,
                base_name='findcomposesbypvr')

# register common view sets
router.register(r'arches', common_views.ArchViewSet)
router.register(r'sigkeys', common_views.SigKeyViewSet)

router.register('releases/(?P<release_id>[^/]+)/rpm-mapping',
                release_views.ReleaseRPMMappingView,
                base_name='releaserpmmapping')

# register package view sets
router.register(r'rpms', rpm_views.RPMViewSet, base_name='rpms')
router.register(r'images', rpm_views.ImageViewSet)
router.register(r'build-images', rpm_views.BuildImageViewSet)

router.register(r'compose/package',
                compose_views.FindComposeWithOlderPackageViewSet,
                base_name='findcomposewitholderpackage')
router.register(r'release-variants',
                release_views.ReleaseVariantViewSet)
router.register(r'variant-types', release_views.VariantTypeViewSet,
                base_name='varianttype')

# TODO: these three end-points will be removed
router.register(r'content-delivery-content-category', repo_views.ContentCategoryViewSet,
                base_name='contentcategorydeprecated')
router.register(r'content-delivery-content-format', repo_views.ContentFormatViewSet,
                base_name='contentformatdeprecated')
router.register(r'content-delivery-service', repo_views.ServiceViewSet,
                base_name='contentservicedeprecated')

router.register(r'content-delivery-content-categories', repo_views.ContentCategoryViewSet,
                base_name='contentdeliverycontentcategory')
router.register(r'content-delivery-content-formats', repo_views.ContentFormatViewSet,
                base_name='contentdeliverycontentformat')
router.register(r'content-delivery-services', repo_views.ServiceViewSet,
                base_name='contentdeliveryservice')

router.register(r'osbs', osbs_views.OSBSViewSet,
                base_name='osbs')

router.register(r'global-component-contacts',
                component_views.GlobalComponentContactInfoViewSet,
                base_name='globalcomponentcontacts')
router.register(r'release-component-contacts',
                component_views.ReleaseComponentContactInfoViewSet,
                base_name='releasecomponentcontacts')

router.register(r'partner-types',
                partner_views.PartnerTypeViewSet)
router.register(r'partners',
                partner_views.PartnerViewSet)
router.register(r'partners-mapping',
                partner_views.PartnerMappingViewSet)
