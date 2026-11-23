import unittest
from chameleon.exc import ExpressionError
from zope.component.testing import PlacelessSetup
from AccessControl.SecurityManager import SecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from Acquisition import Implicit
from Products.PageTemplates.interfaces import IUnicodeEncodingConflictResolver
from Products.PageTemplates.PageTemplate import PageTemplate
from Products.PageTemplates.tests import util
from Products.PageTemplates.unicodeconflictresolver import DefaultUnicodeEncodingConflictResolver, PreferredCharsetResolver
from zExceptions import NotFound
from zope.component import provideUtility
from zope.traversing.adapters import DefaultTraversable
from .util import useChameleonEngine


class AqPageTemplate(Implicit, PageTemplate):
    pass


class Folder(util.Base):
    pass


class UnitTestSecurityPolicy:
    def validate(self, *args, **kw):
        return True

    def checkPermission(self, *args, **kw):
        return True


class HTMLTests(PlacelessSetup, unittest.TestCase):
    PREFIX = None

    def setUp(self):
        super().setUp()
        useChameleonEngine()
        provideUtility(DefaultTraversable)
        provideUtility(DefaultUnicodeEncodingConflictResolver(),
                       IUnicodeEncodingConflictResolver)
        self.folder = Folder()
        self.folder.laf = AqPageTemplate('laf')
        self.folder.t = AqPageTemplate('t')
        self._old_policy = SecurityManager.getSecurityPolicy()
        SecurityManager.setSecurityPolicy(UnitTestSecurityPolicy())
        noSecurityManager()

    def tearDown(self):
        SecurityManager.setSecurityPolicy(self._old_policy)
        noSecurityManager()
        super().tearDown()

    def assert_expected(self, t, fname, *args, **kwargs):
        source = util.read_input(fname)
        t.write(source)
        self.assertFalse(t.errors, f"Template errors: {t.errors}")
        expected = util.read_output(fname)
        if self.PREFIX:
            expected = self.PREFIX + expected
        result = t(*args, **kwargs)
        util.check_html(expected, result)

    def assert_expected_unicode(self, t, fname, *args, **kwargs):
        source = util.read_input(fname)
        t.write(source)
        self.assertFalse(t.errors, f"Template errors: {t.errors}")
        expected = util.read_output(fname)
        if self.PREFIX:
            expected = self.PREFIX + expected
        result = t(*args, **kwargs)
        util.check_html(expected, result)

    def getProducts(self):
        return [
            {"title": "Foo", "price": 10},
            {"title": "Bar", "price": 20},
        ]

    def test_loop(self):
        self.assert_expected(self.folder.laf, "loop.pt", getProducts=self.getProducts)

    def test_globals(self):
        self.assert_expected(self.folder.laf, "globals.pt")

    def test_string_expression(self):
        self.assert_expected(self.folder.laf, "string_expression.pt")

    def test_path(self):
        self.assert_expected(self.folder.laf, "path.pt")

    def test_batch(self):
        self.assert_expected(self.folder.laf, "batch.pt", getProducts=self.getProducts)

    def test_unicode_insert(self):
        self.assert_expected_unicode(self.folder.laf, "unicode_insert.pt")

    def test_i18n(self):
        self.assert_expected(self.folder.laf, "i18n.pt")

    def test_old_style_class_import(self):
        self.assert_expected(self.folder.laf, "old_style_class_import.pt")

    def test_repeat(self):
        self.assert_expected(self.folder.laf, "repeat.pt", getProducts=self.getProducts)

    def test_boolean_attribute(self):
        self.assert_expected(self.folder.laf, "boolean_attribute.pt")

    def test_interpolation(self):
        self.assert_expected(self.folder.laf, "interpolation.pt")

    def test_bad_expression(self):
        with self.assertRaises(ExpressionError):
            self.assert_expected(self.folder.laf, "bad_expression.pt")

    def test_path_alternatives_spaces(self):
        self.assert_expected(self.folder.laf, "path_alternatives_spaces.pt")

    def test_default_keyword(self):
        self.assert_expected(self.folder.laf, "default_keyword.pt")

    def test_switch(self):
        self.assert_expected(self.folder.laf, "switch.pt")

    def test_unicode_conflict_resolution(self):
        self.assert_expected(self.folder.laf, "unicode_conflict.pt")

    def test_underscore_traversal(self):
        with self.assertRaises(NotFound):
            self.assert_expected(self.folder.laf, "underscore_traversal.pt")