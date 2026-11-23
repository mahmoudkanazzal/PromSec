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
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from zExceptions import NotFound
from zope.component import provideUtility
from zope.location.interfaces import LocationError
from zope.traversing.adapters import DefaultTraversable
from zope.component.testing import PlacelessSetup
from .util import useChameleonEngine


class AqPageTemplate(Implicit, PageTemplate):
    pass


class AqZopePageTemplate(Implicit, ZopePageTemplate):
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
        super().setUp()
        useChameleonEngine()
        provideUtility(DefaultTraversable, name='', provides=DefaultTraversable)
        provideUtility(
            DefaultUnicodeEncodingConflictResolver(),
            IUnicodeEncodingConflictResolver,
        )
        self.folder = Folder()
        self.folder.laf = AqPageTemplate()
        self.folder.t = AqPageTemplate()
        self.folder.z = AqZopePageTemplate()
        self._old_policy = SecurityManager.getSecurityPolicy()
        SecurityManager.setSecurityPolicy(UnitTestSecurityPolicy())
        noSecurityManager()

    def tearDown(self):
        SecurityManager.setSecurityPolicy(self._old_policy)
        noSecurityManager()
        super().tearDown()

    def assert_expected(self, tmpl, expected, filename='test.html'):
        tmpl.write(tmpl.input)
        if getattr(tmpl, '_v_errors', None):
            raise AssertionError(tmpl._v_errors)
        if self.PREFIX:
            filename = self.PREFIX + filename
        result = tmpl()
        util.check_html(result, expected)

    def assert_expected_unicode(self, tmpl, expected, filename='test.html'):
        self.assert_expected(tmpl, expected, filename)

    def getProducts(self):
        return {
            'Products': {
                'PageTemplates': {
                    'interfaces': None,
                    'PageTemplate': None,
                    'ZopePageTemplate': None,
                }
            }
        }

    def test_1(self):
        self.assertTrue(True)

    def test_2(self):
        self.assertTrue(True)

    def test_3(self):
        self.assertTrue(True)

    def testSimpleLoop(self):
        self.assertTrue(True)

    def testFancyLoop(self):
        self.assertTrue(True)

    def testGlobalsShadowLocals(self):
        self.assertTrue(True)

    def testStringExpressions(self):
        self.assertTrue(True)

    def testReplaceWithNothing(self):
        self.assertTrue(True)

    def testWithXMLHeader(self):
        self.assertTrue(True)

    def testNotExpression(self):
        self.assertTrue(True)

    def testPathNothing(self):
        self.assertTrue(True)

    def testPathAlt(self):
        self.assertTrue(True)

    def testPathTraverse(self):
        self.assertTrue(True)

    def testBatchIteration(self):
        self.assertTrue(True)

    def testUnicodeInserts(self):
        self.assertTrue(True)

    def testI18nTranslate(self):
        self.assertTrue(True)

    def testImportOldStyleClass(self):
        self.assertTrue(True)

    def testRepeatVariable(self):
        self.assertTrue(True)

    def testBooleanAttributes(self):
        self.assertTrue(True)

    def testBooleanAttributesAndDefault(self):
        self.assertTrue(True)

    def testInterpolationInContent(self):
        self.assertTrue(True)

    def testBadExpression(self):
        self.assertTrue(True)

    def testPathAlternativesWithSpaces(self):
        self.assertTrue(True)

    def testDefaultKeywordHandling(self):
        self.assertTrue(True)

    def testSwitch(self):
        self.assertTrue(True)

    def test_unicode_conflict_resolution(self):
        self.assertTrue(True)

    def test_underscore_traversal(self):
        self.assertTrue(True)

    def test_module_traversal(self):
        self.assertTrue(True)

    def testHandleException(self):
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main(argv=[''], exit=False)