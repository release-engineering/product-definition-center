# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json

from pdc_client.plugins import PDCClientPlugin, get_permissions


class PermissionPlugin(PDCClientPlugin):
    def register(self):
        subcmd = self.add_command('list-my-permissions', help='list my permissions')
        subcmd.set_defaults(func=self.permission_list)

    def permission_list(self, args):
        permissions = get_permissions(self.client.auth['current-user'])
        if args.json:
            print json.dumps(list(permissions))
            return

        for permission in sorted(permissions):
            print permission


PLUGIN_CLASSES = [PermissionPlugin]
