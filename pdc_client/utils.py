# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from __future__ import print_function

import sys


def _pprint_str(file, s, indent, lead=''):
    """Print indented string with optional leading text."""
    print(' ' * indent + lead + s, file=file)


def _pprint_list(file, items, indent):
    """Print an indented bullet point list."""
    for item in items:
        _pprint_str(file, item, indent, lead='* ')


def _pprint_dict(file, data, indent):
    """Print a dict as an indented definition list."""
    for key, value in data.iteritems():
        _pprint_str(file, key + ':', indent)
        pretty_print(value, indent + 1, file)


def pretty_print(data, indent=0, file=sys.stdout):
    """Pretty print a data structure."""
    if isinstance(data, basestring):
        _pprint_list(file, [data], indent)
    elif isinstance(data, list):
        _pprint_list(file, data, indent)
    elif isinstance(data, dict):
        _pprint_dict(file, data, indent)
    else:
        raise TypeError('Can not handle {}'.format(type(data)))
