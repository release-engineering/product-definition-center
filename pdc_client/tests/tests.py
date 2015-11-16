# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import unittest
from StringIO import StringIO

from .. import plugin_helpers
from .. import utils


class PluginHelperTestCase(unittest.TestCase):
    def test_extract_arguments(self):
        class Temp(object):
            pass
        args = Temp()
        setattr(args, 'prf__foo__bar__baz', 1)
        setattr(args, 'prf__foo__bar__quux', 2)
        data = plugin_helpers.extract_arguments(args, prefix='prf__')
        self.assertDictEqual(data,
                             {'foo': {'bar': {'baz': 1, 'quux': 2}}})


class PrettyPrinterTestCase(unittest.TestCase):
    def setUp(self):
        self.out = StringIO()

    def tearDown(self):
        self.out.close()

    def test_print_list(self):
        utils.pretty_print(['foo', 'bar', 'baz'], file=self.out)
        self.assertEqual(self.out.getvalue(),
                         '* foo\n* bar\n* baz\n')

    def test_print_dict(self):
        utils.pretty_print({'foo': 'bar'}, file=self.out)
        self.assertEqual(self.out.getvalue(),
                         'foo:\n * bar\n')

    def test_print_nested_dict(self):
        utils.pretty_print({'foo': {'bar': ['baz', 'quux']}}, file=self.out)
        self.assertEqual(self.out.getvalue(),
                         'foo:\n bar:\n  * baz\n  * quux\n')
