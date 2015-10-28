# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import sys
import json

from pdc_client import get_paged
from pdc_client.plugin_helpers import (PDCClientPlugin,
                                       add_parser_arguments,
                                       extract_arguments,
                                       add_create_update_args)


class RPMPlugin(PDCClientPlugin):
    def register(self):
        self.set_command('rpm', help='rpm')

        list_parser = self.add_subcommand('list', help='list all rpms')
        filters = ('name version release arch compose conflicts obsoletes provides '
                   'suggests recommends requires'.split())
        for arg in filters:
            list_parser.add_argument('--' + arg, dest='filter_' + arg)
        list_parser.set_defaults(func=self.rpm_list)

        info_parser = self.add_subcommand('info', help='display details of an RPM')
        info_parser.add_argument('rpmid', metavar='ID')
        info_parser.set_defaults(func=self.rpm_info)

        create_parser = self.add_admin_subcommand('create', help='create new RPM')
        self.add_rpm_arguments(create_parser, required=True)
        create_parser.set_defaults(func=self.rpm_create)

        update_parser = self.add_admin_subcommand('update', help='update existing RPM')
        update_parser.add_argument('rpmid', metavar='ID')
        self.add_rpm_arguments(update_parser)
        update_parser.set_defaults(func=self.rpm_update)

    def add_rpm_arguments(self, parser, required=False):
        required_args = {
            'arch': {},
            'epoch': {'type': int},
            'name': {},
            'release': {},
            'srpm_name': {},
            'version': {}}
        optional_args = {
            'filename': {},
            'srpm_nevra': {},
            'linked_releases': {'nargs': '*', 'metavar': 'RELEASE_ID'}}
        add_create_update_args(parser, required_args, optional_args, required)

        add_parser_arguments(parser, {
            'dependencies__requires': {'nargs': '*', 'metavar': 'DEPENDENCY', 'arg': 'requires'},
            'dependencies__provides': {'nargs': '*', 'metavar': 'DEPENDENCY', 'arg': 'provides'},
            'dependencies__suggests': {'nargs': '*', 'metavar': 'DEPENDENCY', 'arg': 'suggests'},
            'dependencies__obsoletes': {'nargs': '*', 'metavar': 'DEPENDENCY', 'arg': 'obsoletes'},
            'dependencies__recommends': {'nargs': '*', 'metavar': 'DEPENDENCY', 'arg': 'recommends'},
            'dependencies__conflicts': {'nargs': '*', 'metavar': 'DEPENDENCY', 'arg': 'conflicts'}},
            group='Dependencies (optional)')

    def rpm_list(self, args):
        filters = extract_arguments(args, prefix='filter_')
        if not filters:
            sys.stderr.write('At least some filter must be used.\n')
            sys.exit(1)
        rpms = get_paged(self.client.rpms._, **filters)
        if args.json:
            print json.dumps(list(rpms))
            return

        for rpm in rpms:
            print '{id:10} {name:45} {epoch}:{version}-{release}.{arch}'.format(**rpm)

    def rpm_info(self, args, rpm_id=None):
        response = self.client.rpms[rpm_id or args.rpmid]._()
        if args.json:
            print json.dumps(response)
            return
        fmt = '{:20} {}'
        print fmt.format('ID', response['id'])
        print fmt.format('Name', response['name'])
        print fmt.format('Epoch', response['epoch'])
        print fmt.format('Version', response['version'])
        print fmt.format('Release', response['release'])
        print fmt.format('Arch', response['arch'])
        print fmt.format('SRPM Name', response['srpm_name'])
        print fmt.format('SRPM NEVRA', response['srpm_nevra'] or '')
        print fmt.format('Filename', response['filename'])

        if response['linked_composes']:
            print '\nIncluded in composes:'
            for compose in sorted(response['linked_composes']):
                print compose

        if response['linked_releases']:
            print '\nLinked to releases:'
            for release in sorted(response['linked_releases']):
                print release

        for type in ('recommends', 'suggests', 'obsoletes', 'provides', 'conflicts', 'requires'):
            if response['dependencies'][type]:
                print '\n{}:'.format(type.capitalize())
                for dep in response['dependencies'][type]:
                    print dep

    def rpm_create(self, args):
        data = extract_arguments(args)
        self.logger.debug('Creating rpm with data %r', data)
        response = self.client.rpms._(data)
        self.rpm_info(args, response['id'])

    def rpm_update(self, args):
        data = extract_arguments(args)
        if data:
            self.logger.debug('Updating rpm %s with data %r', args.rpmid, data)
            self.client.rpms[args.rpmid]._ += data
        else:
            self.logger.debug('Empty data, skipping request')
        self.rpm_info(args)


PLUGIN_CLASSES = [RPMPlugin]
