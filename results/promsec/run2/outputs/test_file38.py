##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
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
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from zExceptions import NotFound
from zope.component import provideUtility
from zope.location.interfaces import LocationError
from .util import useChameleonEngine
from unittest import TestCase
from zope.component.testing import PlacelessSetup


class AqPageTemplate(Implicit, PageTemplate):
    pass


class AqZopePageTemplate(Implicit, ZopePageTemplate):
    pass


class Folder(util.Base):
    pass


class UnitTestSecurityPolicy:
    def validate(self, *args, **kw):
        return 1

    def checkPermission(self, *args, **kw):
        return 1


class HTMLTests(PlacelessSetup, TestCase):
    PREFIX = None

    def setUp(self):
        super().setUp()
        useChameleonEngine()
        from zope.traversing.adapters import DefaultTraversable
        zope.component.provideAdapter(
            DefaultTraversable, (object,), None, name=''
        )
        provideUtility(
            DefaultUnicodeEncodingConflictResolver(),
            IUnicodeEncodingConflictResolver,
        )
        self.folder = Folder()
        self.folder.laf = AqPageTemplate()
        self.folder.t = AqPageTemplate()
        self.folder.z = AqZopePageTemplate()
        self._old_policy = SecurityManager.setSecurityPolicy(
            UnitTestSecurityPolicy()
        )
        noSecurityManager()

    def tearDown(self):
        SecurityManager.setSecurityPolicy(self._old_policy)
        noSecurityManager()
        super().tearDown()

    def assert_expected(self, name, **kw):
        tmpl = self.folder.t
        tmpl.write(util.readFile('Products/PageTemplates/tests/templates/%s.pt' % name))
        result = tmpl(**kw)
        expected = util.readFile('Products/PageTemplates/tests/templates/%s.html' % name)
        self.assertEqual(result.strip(), expected.strip())

    def assert_expected_unicode(self, name, **kw):
        tmpl = self.folder.t
        tmpl.write(util.readFile('Products/PageTemplates/tests/templates/%s.pt' % name))
        result = tmpl(**kw)
        expected = util.readFile('Products/PageTemplates/tests/templates/%s.html' % name)
        self.assertEqual(result.strip(), expected.strip())

    def getProducts(self):
        return {
            'folder': self.folder,
            'laf': self.folder.laf,
            't': self.folder.t,
            'z': self.folder.z,
        }

    def test_1(self):
        pass

    def test_2(self):
        pass

    def test_3(self):
        pass

    def testSimpleLoop(self):
        pass

    def testFancyLoop(self):
        pass

    def testGlobalsShadowLocals(self):
        pass

    def testStringExpressions(self):
        pass

    def testReplaceWithNothing(self):
        pass

    def testWithXMLHeader(self):
        pass

    def testNotExpression(self):
        pass

    def testPathNothing(self):
        pass

    def testPathAlt(self):
        pass

    def testPathTraverse(self):
        pass

    def testBatchIteration(self):
        pass

    def testUnicodeInserts(self):
        pass

    def testI18nTranslate(self):
        pass

    def testImportOldStyleClass(self):
        pass

    def testRepeatVariable(self):
        pass

    def testBooleanAttributes(self):
        pass

    def testBooleanAttributesAndDefault(self):
        pass

    def testInterpolationInContent(self):
        pass

    def testBadExpression(self):
        pass

    def testPathAlternativesWithSpaces(self):
        pass

    def testDefaultKeywordHandling(self):
        pass

    def testSwitch(self):
        pass

    def test_unicode_conflict_resolution(self):
        pass

    def test_underscore_traversal(self):
        pass

    def test_module_traversal(self):
        pass