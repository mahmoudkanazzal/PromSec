# -*- coding: utf-8 -*-
# Copyright (c) 2005-2026 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL). A copy of the ZPL should accompany this distribution.

from __future__ import absolute_import, division, print_function, unicode_literals

import importlib

# Lazy imports for unittest and PlacelessSetup
_unittest = importlib.import_module('unittest')
_PlacelessSetup = importlib.import_module('zope.component.testing').PlacelessSetup

from .util import useChameleonEngine, check_html, Base
from Products.PageTemplates.PageTemplate import PageTemplate, Implicit
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from zope.traversing.adapters import DefaultTraversable
from zope.traversing.interfaces import ITraversable
from zope.component import provideAdapter, provideUtility
from zope.security import checkPermission
from zope.security.management import SecurityManager, noSecurityManager
from zope.securitypolicy.interfaces import IPrincipalPermissionManager
from zope.interface import implementer
from Products.PageTemplates.tests.util import DefaultUnicodeEncodingConflictResolver


class AqPageTemplate(Implicit, PageTemplate):
    pass


class AqZopePageTemplate(Implicit, ZopePageTemplate):
    pass


class Folder(Base):
    pass


class UnitTestSecurityPolicy(object):
    def validate(self, *args, **kwargs):
        return 1

    def checkPermission(self, *args, **kwargs):
        return 1


class HTMLTests(_unittest.TestCase, _PlacelessSetup):
    PREFIX = None

    def setUp(self):
        super(HTMLTests, self).setUp()
        useChameleonEngine()
        provideAdapter(DefaultTraversable, (ITraversable,), ITraversable)
        provideUtility(DefaultUnicodeEncodingConflictResolver())
        self.f = Folder()
        self.f.laf = AqPageTemplate()
        self.f.t = AqPageTemplate()
        self.f.z = AqZopePageTemplate()
        self._old_policy = SecurityManager.getSecurityPolicy()
        SecurityManager.setSecurityPolicy(UnitTestSecurityPolicy())
        noSecurityManager()

    def tearDown(self):
        SecurityManager.setSecurityPolicy(self._old_policy)
        noSecurityManager()
        super(HTMLTests, self).tearDown()

    def assert_expected(self, tmpl_input, expected_output):
        self.f.laf.write(tmpl_input)
        self.assertEqual(self.f.laf.errors, [])
        result = self.f.laf()
        if self.PREFIX:
            expected_output = self.PREFIX + expected_output
        check_html(result, expected_output)

    def assert_expected_unicode(self, tmpl_input, expected_output):
        self.f.laf.write(tmpl_input)
        self.assertEqual(self.f.laf.errors, [])
        result = self.f.laf()
        if self.PREFIX:
            expected_output = self.PREFIX + expected_output
        check_html(result, expected_output)

    def getProducts(self):
        return [
            {
                'name': 'Products.Foo',
                'path': '/path/to/foo',
                'title': 'Foo Product',
                'description': 'A foo product.'
            },
            {
                'name': 'Products.Bar',
                'path': '/path/to/bar',
                'title': 'Bar Product',
                'description': 'A bar product.'
            }
        ]

    def test_1(self):
        tmpl = u'<html><body>Hello World</body></html>'
        self.assert_expected(tmpl, tmpl)

    def test_2(self):
        tmpl = u'<p>${"&amp;"}</p>'
        expected = u'<p>&amp;</p>'
        self.assert_expected(tmpl, expected)

    def test_module_traversal(self):
        tmpl = u'<p tal:content="module:os.path">fallback</p>'
        expected = u'<p>posixpath</p>'
        self.assert_expected(tmpl, expected)