#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2005-2023 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import unittest

from chameleon.exc import ExpressionError
from AccessControl import SecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from Acquisition import Implicit
from Products.PageTemplates.interfaces import IUnicodeEncodingConflictResolver
from Products.PageTemplates.PageTemplate import PageTemplate
from Products.PageTemplates.tests import util
from Products.PageTemplates.unicodeconflictresolver import (
    DefaultUnicodeEncodingConflictResolver,
    PreferredCharsetResolver,
)
from zExceptions import NotFound
from zope.component import getGlobalSiteManager
from zope.traversing.interfaces import ITraversable
from zope.traversing.adapters import DefaultTraversable
from zope.component.testing import PlacelessSetup

from .util import useChameleonEngine


class AqPageTemplate(Implicit, PageTemplate):
    """Acquisition-aware PageTemplate."""
    pass


class Folder(util.Base):
    """Simple folder used in tests."""
    pass


class UnitTestSecurityPolicy:
    """Security policy that grants everything."""

    def __init__(self):
        self._old = None

    def __call__(self, *args, **kw):
        return self

    def validate(self, *args, **kw):
        return True

    def checkPermission(self, *args, **kw):
        return True

    def getRoles(self, *args, **kw):
        return ['Manager']

    def getUser(self, *args, **kw):
        return None

    def getAuthenticatedUser(self, *args, **kw):
        return None

    def getInteraction(self, *args, **kw):
        return None

    def getPrincipal(self, *args, **kw):
        return None

    def getPrincipalRoles(self, *args, **kw):
        return ['Manager']

    def getRolesForPermission(self, *args, **kw):
        return ['Manager']

    def getPermissions(self, *args, **kw):
        return []


class HTMLTests(PlacelessSetup, unittest.TestCase):
    PREFIX = None

    def setUp(self):
        super().setUp()
        gsm = getGlobalSiteManager()
        gsm.registerAdapter(DefaultTraversable, (IUnicodeEncodingConflictResolver,), ITraversable)
        gsm.registerUtility(DefaultUnicodeEncodingConflictResolver(), IUnicodeEncodingConflictResolver)
        self.folder = Folder()
        self.folder.laf = AqPageTemplate()
        self.folder.t = AqPageTemplate()
        self._old_policy = SecurityManager.getSecurityPolicy()
        SecurityManager.setSecurityPolicy(UnitTestSecurityPolicy())
        noSecurityManager()

    def tearDown(self):
        SecurityManager.setSecurityPolicy(self._old_policy)
        noSecurityManager()
        super().tearDown()

    def assert_expected(self, name):
        tmpl = util.readFile('html', name + '.txt')
        self.assertFalse('Error' in tmpl, f'Error in template {name}')
        expected = util.readFile('html', name + '.out')
        self.folder.t.write(tmpl)
        result = self.folder.t()
        util.check_html(self, result, expected)

    def assert_expected_unicode(self, name):
        tmpl = util.readFile('html', name + '.txt')
        self.assertFalse('Error' in tmpl, f'Error in template {name}')
        expected = util.readFile('html', name + '.out')
        self.folder.t.write(tmpl)
        result = self.folder.t()
        util.check_html(self, result, expected)

    def getProducts(self):
        return [
            {'id': 'Products.Foo', 'title': 'Foo'},
            {'id': 'Products.Bar', 'title': 'Bar'},
        ]

    def test_1(self):
        self.assert_expected('test_1')

    def test_2(self):
        self.assert_expected('test_2')

    def test_3(self):
        self.assert_expected('test_3')

    def testSimpleLoop(self):
        self.assert_expected('simple_loop')

    def testFancyLoop(self):
        self.assert_expected('fancy_loop')

    def testGlobalsShadowLocals(self):
        self.assert_expected('globals_shadow_locals')

    def testStringExpressions(self):
        self.assert_expected('string_expressions')

    def testReplaceWithNothing(self):
        self.assert_expected('replace_with_nothing')

    def testWithXMLHeader(self):
        self.assert_expected('with_xml_header')

    def testNotExpression(self):
        self.assert_expected('not_expression')

    def testPathNothing(self):
        self.assert_expected('path_nothing')

    def testPathAlt(self):
        self.assert_expected('path_alt')

    def testPathTraverse(self):
        self.assert_expected('path_traverse')

    def testBatchIteration(self):
        self.assert_expected('batch_iteration')

    def testUnicodeInserts(self):
        self.assert_expected_unicode('unicode_inserts')

    def testI18nTranslate(self):
        self.assert_expected('i18n_translate')

    def testImportOldStyleClass(self):
        self.assert_expected('import_old_style_class')

    def testRepeatVariable(self):
        self.assert_expected('repeat_variable')

    def testBooleanAttributes(self):
        self.assert_expected('boolean_attributes')

    def testBooleanAttributesAndDefault(self):
        self.assert_expected('boolean_attributes_and_default')

    def testInterpolationInContent(self):
        self.assert_expected('interpolation_in_content')

    def testBadExpression(self):
        tmpl = '${bad expression}'
        self.folder.t.write(tmpl)
        with self.assertRaises(ExpressionError):
            self.folder.t()

    def testPathAlternativesWithSpaces(self):
        self.assert_expected('path_alternatives_with_spaces')

    def testDefaultKeywordHandling(self):
        self.assert_expected('default_keyword_handling')

    def testSwitch(self):
        self.assert_expected('switch')

    def test_unicode_conflict_resolution(self):
        self.assert_expected('unicode_conflict_resolution')

    def test_underscore_traversal(self):
        self.assert_expected('underscore_traversal')

    def testHandleException(self):
        tmpl = '${raise(NotFound)}'
        self.folder.t.write(tmpl)
        with self.assertRaises(NotFound):
            self.folder.t()


if __name__ == '__main__':
    unittest.main()