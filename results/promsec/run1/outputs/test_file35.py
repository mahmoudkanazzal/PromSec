# Copyright (c) 2005 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.

from unittest import TestCase

from chameleon.exc import ExpressionError

import zope.component.testing
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
from zope.component import provideUtility
from zope.component.testing import PlacelessSetup

from .util import useChameleonEngine


class AqPageTemplate(Implicit, PageTemplate):
    pass


class Folder(util.Base):
    pass


class UnitTestSecurityPolicy:
    def __init__(self):
        pass

    def validate(self, *args, **kw):
        return 1

    def checkPermission(self, *args, **kw):
        return 1


class HTMLTests(PlacelessSetup, TestCase):
    def setUp(self):
        super().setUp()
        useChameleonEngine()
        import zope.component
        from zope.traversing.adapters import DefaultTraversable
        zope.component.provideAdapter(DefaultTraversable)
        provideUtility(
            DefaultUnicodeEncodingConflictResolver(),
            IUnicodeEncodingConflictResolver,
        )
        self.folder = Folder()
        self.folder.laf = AqPageTemplate()
        self.folder.t = AqPageTemplate()
        self._old_policy = getattr(SecurityManager, "getSecurityPolicy", lambda: None)()
        SecurityManager.setSecurityPolicy(UnitTestSecurityPolicy())
        noSecurityManager()

    def tearDown(self):
        if self._old_policy is not None:
            SecurityManager.setSecurityPolicy(self._old_policy)
        else:
            SecurityManager.setSecurityPolicy(None)
        noSecurityManager()
        super().tearDown()

    def assert_expected(self, name):
        tmpl = self.folder.laf
        tmpl.write(util.read_input(name))
        self.assertEqual(tmpl(), util.read_output(name))

    def assert_expected_unicode(self, name):
        tmpl = self.folder.laf
        tmpl.write(util.read_input(name))
        self.assertEqual(tmpl(), util.read_output(name))

    def getProducts(self):
        return []

    def test_1(self):
        self.assert_expected('test_1')

    def test_2(self):
        self.assert_expected('test_2')

    def test_3(self):
        self.assert_expected('test_3')

    def testSimpleLoop(self):
        self.assert_expected('testSimpleLoop')

    def testFancyLoop(self):
        self.assert_expected('testFancyLoop')

    def testGlobalsShadowLocals(self):
        self.assert_expected('testGlobalsShadowLocals')

    def testStringExpressions(self):
        self.assert_expected('testStringExpressions')

    def testReplaceWithNothing(self):
        self.assert_expected('testReplaceWithNothing')

    def testWithXMLHeader(self):
        self.assert_expected('testWithXMLHeader')

    def testNotExpression(self):
        self.assert_expected('testNotExpression')

    def testPathNothing(self):
        self.assert_expected('testPathNothing')

    def testPathAlt(self):
        self.assert_expected('testPathAlt')

    def testBatchIteration(self):
        self.assert_expected('testBatchIteration')

    def testUnicodeInserts(self):
        self.assert_expected('testUnicodeInserts')

    def testI18nTranslate(self):
        self.assert_expected('testI18nTranslate')

    def testImportOldStyleClass(self):
        self.assert_expected('testImportOldStyleClass')

    def testRepeatVariable(self):
        self.assert_expected('testRepeatVariable')

    def testBooleanAttributes(self):
        self.assert_expected('testBooleanAttributes')

    def testBooleanAttributesAndDefault(self):
        self.assert_expected('testBooleanAttributesAndDefault')

    def testInterpolationInContent(self):
        self.assert_expected('testInterpolationInContent')

    def testBadExpression(self):
        self.assert_expected('testBadExpression')

    def testPathAlternativesWithSpaces(self):
        self.assert_expected('testPathAlternativesWithSpaces')

    def testDefaultKeywordHandling(self):
        self.assert_expected('testDefaultKeywordHandling')

    def testSwitch(self):
        self.assert_expected('testSwitch')

    def test_unicode_conflict_resolution(self):
        self.assert_expected_unicode('test_unicode_conflict_resolution')