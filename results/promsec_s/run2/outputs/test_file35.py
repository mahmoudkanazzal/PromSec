# Zope Public License (ZPL) Version 2.1
# Copyright (c) Zope Corporation and Contributors.
# All rights reserved.
#
# This software is subject to the provisions of the ZPL 2.1
# (http://zope.org/Products/ZPL/2.1/), a copy of which should
# accompany this distribution.

from unittest import TestCase
from chameleon.exc import ExpressionError
import zope.component
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
from zope.traversing.adapters import DefaultTraversable
from zope.component.testing import PlacelessSetup
from .util import useChameleonEngine


class AqPageTemplate(Implicit, PageTemplate):
    pass


class Folder(util.Base):
    pass


class UnitTestSecurityPolicy:
    """A security policy that allows everything for testing."""

    def validate(self, accessed=None, container=None, name=None, value=None,
                 context=None, roles=None, *args, **kw):
        return 1

    def checkPermission(self, permission, object, context):
        return 1


class HTMLTests(PlacelessSetup, TestCase):
    PREFIX = None

    def setUp(self):
        super().setUp()
        useChameleonEngine()
        zope.component.provideAdapter(DefaultTraversable)
        provideUtility(
            DefaultUnicodeEncodingConflictResolver(),
            IUnicodeEncodingConflictResolver,
        )
        self.folder = Folder()
        self.folder.laf = AqPageTemplate()
        self.folder.t = AqPageTemplate()
        self.oldPolicy = SecurityManager.getSecurityPolicy()
        SecurityManager.setSecurityPolicy(UnitTestSecurityPolicy())
        noSecurityManager()

    def tearDown(self):
        super().tearDown()
        SecurityManager.setSecurityPolicy(self.oldPolicy)
        noSecurityManager()

    def assert_expected(self, t, fname, *args, **kwargs):
        with open(fname, "rb") as f:
            source = f.read()
        t.write(source)
        self.assertEqual(t._v_errors, [])
        expected_name = fname
        if self.PREFIX:
            expected_name = self.PREFIX + expected_name
        with open(expected_name, "rb") as f:
            expected = f.read()
        result = t.render(*args, **kwargs)
        util.check_html(self, result, expected)

    def assert_expected_unicode(self, t, fname, *args, **kwargs):
        with open(fname, "r", encoding="utf-8") as f:
            source = f.read()
        t.write(source.encode("utf-8"))
        self.assertEqual(t._v_errors, [])
        expected_name = fname
        if self.PREFIX:
            expected_name = self.PREFIX + expected_name
        with open(expected_name, "r", encoding="utf-8") as f:
            expected = f.read()
        result = t.render(*args, **kwargs)
        util.check_html(self, result, expected)

    def getProducts(self):
        return [
            {"id": "product1", "title": "Product 1", "description": "Desc 1"},
            {"id": "product2", "title": "Product 2", "description": "Desc 2"},
        ]

    def test_1(self):
        self.assert_expected(self.folder.laf, "test_1.pt")

    def test_2(self):
        self.assert_expected(self.folder.laf, "test_2.pt")

    def test_3(self):
        self.assert_expected(self.folder.laf, "test_3.pt")

    def testSimpleLoop(self):
        self.assert_expected(self.folder.laf, "simple_loop.pt")

    def testFancyLoop(self):
        self.assert_expected(self.folder.laf, "fancy_loop.pt")

    def testGlobalsShadowLocals(self):
        self.assert_expected(self.folder.laf, "globals_shadow_locals.pt")

    def testStringExpressions(self):
        self.assert_expected(self.folder.laf, "string_expressions.pt")

    def testReplaceWithNothing(self):
        self.assert_expected(self.folder.laf, "replace_with_nothing.pt")

    def testWithXMLHeader(self):
        self.assert_expected(self.folder.laf, "with_xml_header.pt")

    def testNotExpression(self):
        self.assert_expected(self.folder.laf, "not_expression.pt")

    def testPathNothing(self):
        self.assert_expected(self.folder.laf, "path_nothing.pt")

    def testPathAlt(self):
        self.assert_expected(self.folder.laf, "path_alt.pt")

    def testBatchIteration(self):
        self.assert_expected(self.folder.laf, "batch_iteration.pt")

    def testUnicodeInserts(self):
        self.assert_expected_unicode(self.folder.laf, "unicode_inserts.pt")

    def testI18nTranslate(self):
        self.assert_expected(self.folder.laf, "i18n_translate.pt")

    def testImportOldStyleClass(self):
        self.assert_expected(self.folder.laf, "import_old_style_class.pt")

    def testRepeatVariable(self):
        self.assert_expected(self.folder.laf, "repeat_variable.pt")

    def testBooleanAttributes(self):
        self.assert_expected(self.folder.laf, "boolean_attributes.pt")

    def testBooleanAttributesAndDefault(self):
        self.assert_expected(self.folder.laf, "boolean_attributes_and_default.pt")

    def testInterpolationInContent(self):
        self.assert_expected(self.folder.laf, "interpolation_in_content.pt")

    def testBadExpression(self):
        t = self.folder.laf
        with self.assertRaises(ExpressionError):
            self.assert_expected(t, "bad_expression.pt")

    def testPathAlternativesWithSpaces(self):
        self.assert_expected(self.folder.laf, "path_alternatives_with_spaces.pt")

    def testDefaultKeywordHandling(self):
        self.assert_expected(self.folder.laf, "default_keyword_handling.pt")

    def testSwitch(self):
        self.assert_expected(self.folder.laf, "switch.pt")

    def test_unicode_conflict_resolution(self):
        provideUtility(PreferredCharsetResolver(), IUnicodeEncodingConflictResolver)
        t = PageTemplate()
        self.assert_expected_unicode(t, "unicode_conflict.pt")