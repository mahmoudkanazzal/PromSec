import unittest
from chameleon.exc import ExpressionError
import zope.component.testing
import AccessControl.SecurityManager
import AccessControl.SecurityManagement
from Acquisition import Implicit
import Products.PageTemplates.interfaces
import Products.PageTemplates.PageTemplate
import Products.PageTemplates.tests.util as util
from Products.PageTemplates.unicodeconflictresolver import DefaultUnicodeEncodingConflictResolver, PreferredCharsetResolver
from zope.component import provideUtility
from zope.traversing.adapters import DefaultTraversable


class AqPageTemplate(Implicit, Products.PageTemplates.PageTemplate.PageTemplate):
    """PageTemplate with acquisition support."""
    pass


class Folder(util.Base):
    """Simple folder container for tests."""
    pass


class UnitTestSecurityPolicy:
    """Stub security policy used during tests."""

    def validate(self, *args, **kwargs):
        return True

    def checkPermission(self, permission, object):
        return True


class HTMLTests(zope.component.testing.PlacelessSetup, unittest.TestCase):
    """Test suite for HTML rendering of PageTemplates."""

    PREFIX = 'html/'

    def setUp(self):
        super().setUp()
        self._old_policy = AccessControl.SecurityManager.getSecurityPolicy()
        AccessControl.SecurityManager.setSecurityPolicy(UnitTestSecurityPolicy())
        AccessControl.SecurityManagement.noSecurityManager()
        self._old_engine = util.useChameleonEngine(True)

    def tearDown(self):
        AccessControl.SecurityManager.setSecurityPolicy(self._old_policy)
        AccessControl.SecurityManagement.noSecurityManager()
        util.useChameleonEngine(self._old_engine)
        super().tearDown()

    def assert_expected(self, filename):
        tmpl = AqPageTemplate('test')
        tmpl.write(util.read_input(self.PREFIX + filename))
        self.assertIsNone(tmpl._v_errors)
        result = tmpl()
        expected = util.read_output(self.PREFIX + filename)
        util.check_html(self, result, expected)

    def assert_expected_unicode(self, filename):
        tmpl = AqPageTemplate('test')
        tmpl.write(util.read_input(self.PREFIX + filename))
        self.assertIsNone(tmpl._v_errors)
        result = tmpl()
        expected = util.read_output(self.PREFIX + filename)
        util.check_html(self, result, expected)

    def getProducts(self):
        return ('Products.PageTemplates',)

    def test_basic(self):
        self.assert_expected('Basic.html')

    def test_expression(self):
        self.assert_expected('Expression.html')

    def test_bad_expression(self):
        tmpl = AqPageTemplate('test')
        tmpl.write(util.read_input(self.PREFIX + 'BadExpression.html'))
        with self.assertRaises(ExpressionError):
            tmpl()

    def test_unicode_conflict_resolution(self):
        provideUtility(PreferredCharsetResolver(),
                       Products.PageTemplates.interfaces.IUnicodeEncodingConflictResolver)
        self.assert_expected('UnicodeResolution.html')