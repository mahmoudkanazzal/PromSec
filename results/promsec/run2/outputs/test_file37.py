from __future__ import absolute_import, division, print_function, unicode_literals

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
from zope.component import provideUtility
from zope.component.testing import PlacelessSetup

from .util import useChameleonEngine


class AqPageTemplate(Implicit, PageTemplate):
    pass


class Folder(util.Base):
    pass


class UnitTestSecurityPolicy:
    def validate(self, *args, **kwargs):
        return 1

    def checkPermission(self, *args, **kwargs):
        return 1


class HTMLTests(PlacelessSetup, unittest.TestCase):
    PREFIX = None

    def setUp(self):
        super(HTMLTests, self).setUp()
        useChameleonEngine()
        from Products.PageTemplates.traversable import DefaultTraversable
        provideUtility(DefaultTraversable, name='DefaultTraversable')
        provideUtility(
            DefaultUnicodeEncodingConflictResolver(),
            IUnicodeEncodingConflictResolver,
        )
        self.folder = Folder()
        self.folder.laf = AqPageTemplate()
        self.folder.t = AqPageTemplate()
        self._original_policy = SecurityManager.getSecurityPolicy()
        SecurityManager.setSecurityPolicy(UnitTestSecurityPolicy())
        noSecurityManager()

    def tearDown(self):
        SecurityManager.setSecurityPolicy(self._original_policy)
        noSecurityManager()
        super(HTMLTests, self).tearDown()

    def assert_expected(self, name, **kw):
        tmpl = self.folder.t
        tmpl.write(util.read_input(name + '.pt'))
        if getattr(tmpl, '_v_errors', None):
            raise AssertionError(tmpl._v_errors)
        expected = util.read_output(name + '.html')
        result = tmpl()
        util.check_html(expected, result, **kw)

    def assert_expected_unicode(self, name, **kw):
        tmpl = self.folder.t
        tmpl.write(util.read_input(name + '.pt'))
        if getattr(tmpl, '_v_errors', None):
            raise AssertionError(tmpl._v_errors)
        expected = util.read_output(name + '.html')
        result = tmpl()
        util.check_html(expected, result, **kw)

    def getProducts(self):
        return [
            {'title': 'Product 1', 'price': 10},
            {'title': 'Product 2', 'price': 20},
        ]

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

    def testPathTraverse(self):
        self.assert_expected('testPathTraverse')

    def testBatchIteration(self):
        self.assert_expected('testBatchIteration')

    def testUnicodeInserts(self):
        self.assert_expected_unicode('testUnicodeInserts')

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
        with self.assertRaises(ExpressionError):
            self.assert_expected('testBadExpression')

    def testPathAlternativesWithSpaces(self):
        self.assert_expected('testPathAlternativesWithSpaces')

    def testDefaultKeywordHandling(self):
        self.assert_expected('testDefaultKeywordHandling')

    def testSwitch(self):
        self.assert_expected('testSwitch')

    def test_unicode_conflict_resolution(self):
        provideUtility(PreferredCharsetResolver())
        self.assert_expected('test_unicode_conflict_resolution')

    def test_underscore_traversal(self):
        with self.assertRaises(NotFound):
            self.assert_expected('test_underscore_traversal')