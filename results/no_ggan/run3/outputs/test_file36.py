# -*- coding: utf-8 -*-
#
# Copyright (c) 2005-2024 Zope Foundation and Contributors.
# All rights reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.

from __future__ import absolute_import, print_function, unicode_literals

import unittest

from zope.component import provideAdapter, provideUtility
from zope.component.testing import PlacelessSetup
from zope.interface import Interface
from zope.traversing.interfaces import ITraversable
from zope.traversing.adapters import DefaultTraversable
from zope.i18n.interfaces import IUnicodeEncodingConflictResolver
from zope.i18n.unicodeconflict import DefaultUnicodeEncodingConflictResolver
from zope.security.management import SecurityManager, noSecurityManager

from Products.PageTemplates.engine import useChameleonEngine
from Products.PageTemplates.PageTemplate import Implicit, PageTemplate, ZopePageTemplate

from . import util


class AqPageTemplate(Implicit, PageTemplate):
    """Acquisition-aware PageTemplate."""
    pass


class AqZopePageTemplate(Implicit, ZopePageTemplate):
    """Acquisition-aware ZopePageTemplate."""
    pass


class Folder(util.Base):
    """Simple folder used in tests."""
    pass


class DelegatingSecurityPolicy(object):
    """Wraps an existing security policy and delegates calls."""

    def __init__(self, original):
        self.original = original

    def validate(self, *args, **kw):
        return self.original.validate(*args, **kw)

    def checkPermission(self, permission, object):
        return self.original.checkPermission(permission, object)


class HTMLTests(PlacelessSetup, unittest.TestCase):
    PREFIX = None

    def setUp(self):
        super(HTMLTests, self).setUp()
        useChameleonEngine()
        provideAdapter(DefaultTraversable, (Interface, Interface), ITraversable)
        provideUtility(
            DefaultUnicodeEncodingConflictResolver(),
            IUnicodeEncodingConflictResolver,
        )
        self.folder = Folder()
        self.folder.laf = AqPageTemplate()
        self.folder.t = AqPageTemplate()
        self.folder.z = AqZopePageTemplate()
        self.oldPolicy = SecurityManager.getSecurityPolicy()
        self.policy = DelegatingSecurityPolicy(self.oldPolicy)
        SecurityManager.setSecurityPolicy(self.policy)
        noSecurityManager()

    def tearDown(self):
        SecurityManager.setSecurityPolicy(self.oldPolicy)
        noSecurityManager()
        super(HTMLTests, self).tearDown()

    def assert_expected(self, name, tmpl_input, expected_output):
        tmpl = getattr(self.folder, name)
        tmpl.write(tmpl_input)
        self.assertEqual(tmpl.read(), tmpl_input)
        tmpl.cook()
        result = tmpl()
        if self.PREFIX:
            expected_output = self.PREFIX + expected_output
        util.check_html(result, expected_output)

    def assert_expected_unicode(self, name, tmpl_input, expected_output):
        tmpl = getattr(self.folder, name)
        tmpl.write(tmpl_input)
        self.assertEqual(tmpl.read(), tmpl_input)
        tmpl.cook()
        result = tmpl()
        if self.PREFIX:
            expected_output = self.PREFIX + expected_output
        util.check_html(result, expected_output)

    def getProducts(self):
        return [
            {"name": "Products.Foo", "path": "Products/Foo"},
            {"name": "Products.Bar", "path": "Products/Bar"},
        ]

    def test_1(self):
        self.assert_expected(
            "t",
            "<html><body tal:content='string:hello'></body></html>",
            "<html><body>hello</body></html>",
        )

    def test_2(self):
        self.assert_expected(
            "z",
            "<html><body tal:content='string:world'></body></html>",
            "<html><body>world</body></html>",
        )

    def test_module_traversal(self):
        old_policy = SecurityManager.getSecurityPolicy()
        try:
            SecurityManager.setSecurityPolicy(self.policy)
            noSecurityManager()
            self.assert_expected(
                "laf",
                "<html><body tal:content='string:module'></body></html>",
                "<html><body>module</body></html>",
            )
        finally:
            SecurityManager.setSecurityPolicy(old_policy)
            noSecurityManager()