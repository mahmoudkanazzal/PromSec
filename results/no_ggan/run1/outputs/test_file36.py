import unittest

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
from zope.traversing.adapters import DefaultTraversable

from .util import useChameleonEngine


class AqPageTemplate(Implicit, PageTemplate):
    pass


class AqZopePageTemplate(Implicit, ZopePageTemplate):
    pass


class Folder(util.Base):
    pass


class UnitTestSecurityPolicy:
    def validate(self, accessed=None, container=None, name=None, value=None, context=None, roles=None, *args, **kw):
        return 1

    def checkPermission(self, permission, object, context):
        return 1


class HTMLTests(zope.component.testing.PlacelessSetup, unittest.TestCase):
    PREFIX = None

    def setUp(self):
        super().setUp()
        useChameleonEngine()
        provideUtility(DefaultTraversable, name='default')
        provideUtility(DefaultUnicodeEncodingConflictResolver, IUnicodeEncodingConflictResolver)
        self.folder = Folder()
        self.folder.laf = AqPageTemplate()
        self.folder.t = AqPageTemplate()
        self.folder.z = AqZopePageTemplate("testing")
        self.oldPolicy = SecurityManager.getSecurityPolicy()
        SecurityManager.setSecurityPolicy(UnitTestSecurityPolicy())
        noSecurityManager()

    def tearDown(self):
        SecurityManager.setSecurityPolicy(self.oldPolicy)
        noSecurityManager()
        super().tearDown()

    def assert_expected(self, t, fname, *args, **kwargs):
        util.write_input_file(fname, *args, **kwargs)
        self.assertFalse(t._v_errors, f"Template errors: {t._v_errors}")
        if self.PREFIX:
            fname = self.PREFIX + fname
        expected = util.read_expected_output(fname)
        result = t()
        util.check_html(self, result, expected)

    def assert_expected_unicode(self, t, fname, *args, **kwargs):
        util.write_input_file(fname, *args, **kwargs)
        self.assertFalse(t._v_errors, f"Template errors: {t._v_errors}")
        if self.PREFIX:
            fname = self.PREFIX + fname
        expected = util.read_expected_output(fname)
        if not isinstance(expected, str):
            expected = expected.decode('utf-8')
        result = t()
        if not isinstance(result, str):
            result = result.decode('utf-8')
        util.check_html(self, result, expected)

    def getProducts(self):
        return [
            {
                'id': 'testproduct',
                'title': 'Test Product',
                'description': 'A product for testing.',
                'price': 9.99,
                'available': True,
            },
            {
                'id': 'anotherproduct',
                'title': 'Another Product',
                'description': 'Another product for testing.',
                'price': 19.99,
                'available': False,
            },
        ]

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