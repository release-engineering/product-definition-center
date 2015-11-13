# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from __future__ import print_function

import sys
import argparse
import beanbag
import os
import os.path
import logging
import imp

# The client supports Bash completion if argcomplete Python package is
# installed. To enable it, run this in your terminal (assuming pdc is somewhere
# on path).
#
#     eval "$(register-python-argcomplete pdc)"
#
# This is only a temporary solution, when the client is packaged, a completion
# file should be shipped with it and installed to /etc/bash_completion.d/.
try:
    import argcomplete
except ImportError:
    class argcomplete(object):
        @classmethod
        def autocomplete(*args):
            pass

import pdc_client
from pdc_client.utils import pretty_print


# A list of paths to directories where plugins should be loaded from.
# The purpose of the plugins is to extend the default behaviour.
PLUGIN_DIRS = [
    os.path.join(os.path.dirname(__file__), 'plugins')
]


class Runner(object):
    def __init__(self):
        self.raw_plugins = []
        self.plugins = []
        self.logger = logging.getLogger('pdc')

    def load_plugins(self):
        for dir in PLUGIN_DIRS:
            self.logger.debug('Loading plugins from {}'.format(dir))
            for name in os.listdir(dir):
                if not name.endswith('.py'):
                    continue
                file, pathname, description = imp.find_module(name[:-3], [dir])
                plugin = imp.load_module(name[:-3], file, pathname, description)
                self.logger.debug('Loaded plugin {}'.format(name[:-3]))
                self.raw_plugins.append(plugin)
                if hasattr(plugin, 'PLUGIN_CLASSES'):
                    for p in plugin.PLUGIN_CLASSES:
                        self.logger.debug('Instantiating {}'.format(p.__name__))
                        self.plugins.append(p(self))

    def run_hook(self, hook, *args, **kwargs):
        """
        Loop over all plugins and invoke function `hook` with `args` and
        `kwargs` in each of them. If the plugin does not have the function, it
        is skipped.
        """
        for plugin in self.raw_plugins:
            if hasattr(plugin, hook):
                self.logger.debug('Calling hook {} in plugin {}'.format(hook, plugin.__name__))
                getattr(plugin, hook)(*args, **kwargs)

    def setup(self):
        self.load_plugins()

        self.parser = argparse.ArgumentParser(description='PDC Client')
        self.parser.add_argument('-s', '--server', default='stage',
                                 help='API URL or shortcut from config file')
        self.parser.add_argument('--debug', action='store_true', help=argparse.SUPPRESS)
        self.parser.add_argument('--json', action='store_true',
                                 help='display output as JSON')

        subparsers = self.parser.add_subparsers(metavar='COMMAND')

        for plugin in self.plugins:
            plugin._before_register(subparsers)
            plugin.register()

        argcomplete.autocomplete(self.parser)

    def run(self, args=None):
        self.args = self.parser.parse_args(args=args)
        self.client = pdc_client.PDCClient(self.args.server)
        try:
            self.args.func(self.args)
        except beanbag.BeanBagException as exc:
            self.print_error_header(exc)
            json = None
            try:
                json = exc.response.json()
                pretty_print(json, file=sys.stderr)
            except ValueError:
                # Response was not JSON
                print('Failed to parse error response.', file=sys.stderr)
            except TypeError as e:
                # Failed to pretty print.
                print('Failed to correctly display error message. Please file a bug.',
                      file=sys.stderr)
                self.logger.info(json, exc_info=e)
            sys.exit(1)

    def print_error_header(self, exc):
        if exc.response.status_code > 500:
            print('Internal server error. Please consider reporting a bug.',
                  file=sys.stderr)
        else:
            headers = {
                400: 'bad request data',
                401: 'unauthorized',
                404: 'not found',
                409: 'conflict',
            }
            print('Client error: {}.'.format(headers.get(exc.response.status_code, 'unknown')),
                  file=sys.stderr)
