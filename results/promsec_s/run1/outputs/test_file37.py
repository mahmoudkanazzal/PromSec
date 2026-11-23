# Zope Public License (ZPL) 2.1
# Copyright (c) Zope Corporation and Contributors.
# All rights reserved.

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from unittest import TestCase

from zope.component import provideAdapter, provideUtility, getUtility
from zope.interface import Interface
from zope.traversing.interfaces import ITraversable
from zope.security.management import setSecurityPolicy, noSecurityManager
from zope.securitypolicy.interfaces import IPrincipalPermissionManager

from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PageTemplates.tests import util
from Products.PageTemplates.tests.util import check_html, get_test_path
from Products.PageTemplates.tests.util import read_template, read_expected

from AccessControl.SecurityManagement import newSecurityManager, getSecurityManager
from AccessControl.SecurityPolicy import SecurityPolicy

from zope.i18n.unicodeconflict import DefaultUnicodeEncodingConflictResolver


class AqPageTemplate(PageTemplateFile):
    """A page template that supports acquisition."""

    def __init__(self, filename: str, path: str) -> None:
        super().__init__(filename, path)


class Folder:
    """Simple container for page templates."""

    def __init__(self) -> None:
        self.__dict__: Dict[str, Any] = {}

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


class UnitTestSecurityPolicy(SecurityPolicy):
    """Stub security policy for unit tests."""

    def __init__(self) -> None:
        self._allowed: List[Tuple[str, str]] = []

    def checkPermission(self, permission: str, object: Any) -> bool:
        return True

    def validate(self, *args: Any, **kwargs: Any) -> None:
        pass


class HTMLTests(util.PlacelessSetup, TestCase):
    """Test suite for HTML rendering of page templates."""

    PREFIX: str | None = None

    def setUp(self) -> None:
        super().setUp()
        from Products.PageTemplates.engine import Engine

        Engine.activate('chameleon')
        provideAdapter(util.DefaultTraversable, (Interface, Interface), ITraversable)
        provideUtility(DefaultUnicodeEncodingConflictResolver())
        self.folder = Folder()
        self.folder.laf = AqPageTemplate('laf.pt', get_test_path())
        self.folder.t = AqPageTemplate('t.pt', get_test_path())
        setSecurityPolicy(UnitTestSecurityPolicy())
        noSecurityManager()

    def tearDown(self) -> None:
        setSecurityPolicy(SecurityPolicy())
        noSecurityManager()
        super().tearDown()

    def assert_expected(self, name: str) -> None:
        tmpl = read_template(name)
        self.assertIsNotNone(tmpl)
        expected = read_expected(name)
        result = tmpl()
        check_html(expected, result)

    def assert_expected_unicode(self, name: str) -> None:
        tmpl = read_template(name)
        self.assertIsNotNone(tmpl)
        expected = read_expected(name, unicode=True)
        result = tmpl()
        check_html(expected, result)

    def getProducts(self) -> List[Dict[str, Any]]:
        return [
            {'id': 'Products.Foo', 'title': 'Foo'},
            {'id': 'Products.Bar', 'title': 'Bar'},
        ]

    def test_1(self) -> None:
        self.assert_expected('test_1')

    def test_2(self) -> None:
        self.assert_expected('test_2')

    def test_3(self) -> None:
        self.assert_expected('test_3')

    def testSimpleLoop(self) -> None:
        self.assert_expected('testSimpleLoop')

    def testFancyLoop(self) -> None:
        self.assert_expected('testFancyLoop')

    def testGlobalsShadowLocals(self) -> None:
        self.assert_expected('testGlobalsShadowLocals')

    def testStringExpressions(self) -> None:
        self.assert_expected('testStringExpressions')

    def testReplaceWithNothing(self) -> None:
        self.assert_expected('testReplaceWithNothing')

    def testWithXMLHeader(self) -> None:
        self.assert_expected('testWithXMLHeader')

    def testNotExpression(self) -> None:
        self.assert_expected('testNotExpression')

    def testPathNothing(self) -> None:
        self.assert_expected('testPathNothing')

    def testPathAlt(self) -> None:
        self.assert_expected('testPathAlt')

    def testPathTraverse(self) -> None:
        self.assert_expected('testPathTraverse')

    def testBatchIteration(self) -> None:
        self.assert_expected('testBatchIteration')

    def testUnicodeInserts(self) -> None:
        self.assert_expected_unicode('testUnicodeInserts')

    def testI18nTranslate(self) -> None:
        self.assert_expected('testI18nTranslate')

    def testImportOldStyleClass(self) -> None:
        self.assert_expected('testImportOldStyleClass')

    def testRepeatVariable(self) -> None:
        self.assert_expected('testRepeatVariable')

    def testBooleanAttributes(self) -> None:
        self.assert_expected('testBooleanAttributes')

    def testBooleanAttributesAndDefault(self) -> None:
        self.assert_expected('testBooleanAttributesAndDefault')

    def testInterpolationInContent(self) -> None:
        self.assert_expected('testInterpolationInContent')

    def testBadExpression(self) -> None:
        with self.assertRaises(util.ExpressionError):
            self.assert_expected('testBadExpression')

    def testPathAlternativesWithSpaces(self) -> None:
        self.assert_expected('testPathAlternativesWithSpaces')

    def testDefaultKeywordHandling(self) -> None:
        self.assert_expected('testDefaultKeywordHandling')

    def testSwitch(self) -> None:
        self.assert_expected('testSwitch')

    def test_unicode_conflict_resolution(self) -> None:
        self.assert_expected('test_unicode_conflict_resolution')

    def test_underscore_traversal(self) -> None:
        self.assert_expected('test_underscore_traversal')