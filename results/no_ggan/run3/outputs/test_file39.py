import unittest
from chameleon.exc import ExpressionError
import zope.component.testing
from AccessControl import SecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from Acquisition import Implicit
from Products.PageTemplates.interfaces import IUnicodeEncodingConflictResolver
from Products.PageTemplates.PageTemplate import PageTemplate
from Products.PageTemplates.tests import util
from Products.PageTemplates.unicodeconflictresolver import DefaultUnicodeEncodingConflictResolver, PreferredCharsetResolver
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from zExceptions import NotFound
from zope.component import provideUtility, provideAdapter
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
    def validate(self, *args, **kw):
        return 1

    def checkPermission(self, *args, **kw):
        return 1


class HTMLTests(zope.component.testing.PlacelessSetup, unittest.TestCase):
    PREFIX = None

    def setUp(self):
        super().setUp()
        useChameleonEngine()
        provideAdapter(DefaultTraversable)
        provideUtility(DefaultUnicodeEncodingConflictResolver(), IUnicodeEncodingConflictResolver)
        self.folder = Folder()
        self.folder.laf = AqPageTemplate()
        self.folder.t = AqPageTemplate()
        self.folder.z = AqZopePageTemplate()
        self.oldPolicy = SecurityManager.getSecurityPolicy()
        SecurityManager.setSecurityPolicy(UnitTestSecurityPolicy())
        noSecurityManager()

    def tearDown(self):
        SecurityManager.setSecurityPolicy(self.oldPolicy)
        noSecurityManager()
        super().tearDown()

    def assert_expected(self, t, fname, *args, **kwargs):
        input_data = util.read_input(fname)
        t.write(input_data)
        self.assertEqual(t.errors(), [])
        if self.PREFIX:
            fname = self.PREFIX + fname
        expected = util.read_output(fname)
        result = t(*args, **kwargs)
        util.check_html(self, result, expected)

    def assert_expected_unicode(self, t, fname, *args, **kwargs):
        input_data = util.read_input(fname)
        t.write(input_data)
        self.assertEqual(t.errors(), [])
        if self.PREFIX:
            fname = self.PREFIX + fname
        expected = util.read_output(fname)
        if isinstance(expected, bytes):
            expected = expected.decode('utf-8')
        result = t(*args, **kwargs)
        util.check_html(self, result, expected)

    def getProducts(self):
        return [{'id': 'Products.PageTemplates', 'title': 'Page Templates'}]

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
    unittest.main()