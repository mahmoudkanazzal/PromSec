from __future__ import absolute_import

import unittest

from chameleon.exc import ExpressionError
from zope.component.testing import PlacelessSetup
from AccessControl.SecurityManager import setSecurityPolicy, SecurityManager
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
from zope.component import provideUtility, provideAdapter
from zope.traversing.adapters import DefaultTraversable
from .util import useChameleonEngine


class AqPageTemplate(Implicit, PageTemplate):
    pass


class Folder(util.Base):
    pass


class UnitTestSecurityPolicy:
    def validate(self, *args, **kwargs):
        return 1

    def checkPermission(self, permission, object):
        return 1


class HTMLTests(PlacelessSetup, unittest.TestCase):
    PREFIX = "test_html_"

    def setUp(self):
        super(HTMLTests, self).setUp()
        setSecurityPolicy(UnitTestSecurityPolicy())
        SecurityManager(None)
        provideAdapter(DefaultTraversable, (object,), None, name="default")
        provideUtility(
            DefaultUnicodeEncodingConflictResolver(),
            IUnicodeEncodingConflictResolver,
        )
        useChameleonEngine()
        self.folder = Folder()
        self.folder.__allow_groups__ = ()
        self.folder.__allow_roles__ = ()
        self.folder.__allow_users__ = ()
        self.folder.__ac_local_roles__ = {}
        self.folder.__ac_roles__ = ()
        self.folder.__ac_permissions__ = {}

    def tearDown(self):
        noSecurityManager()
        super(HTMLTests, self).tearDown()

    def assert_expected(self, name):
        pt = AqPageTemplate()
        pt.write(util.read_input(name + ".pt"))
        self.folder[name] = pt
        output = self.folder[name]()
        expected = util.read_output(name + ".html")
        self.assertEqual(output.strip(), expected.strip())
        self.assertTrue(util.check_html(output))

    def assert_expected_unicode(self, name):
        pt = AqPageTemplate()
        pt.write(util.read_input(name + ".pt"))
        self.folder[name] = pt
        output = self.folder[name]()
        expected = util.read_output(name + ".html")
        self.assertEqual(output, expected)
        self.assertTrue(util.check_html(output))

    def getProducts(self):
        return [
            ("test_html_1", self.assert_expected),
            ("test_html_2", self.assert_expected),
            ("test_html_3", self.assert_expected),
            ("test_html_4", self.assert_expected),
            ("test_html_5", self.assert_expected_unicode),
            ("test_html_6", self.assert_expected),
            ("test_html_7", self.assert_expected),
            ("test_html_8", self.assert_expected),
            ("test_html_9", self.assert_expected),
            ("test_html_10", self.assert_expected),
            ("test_html_11", self.assert_expected),
            ("test_html_12", self.assert_expected),
        ]

    def test_1(self):
        self.assert_expected(self.PREFIX + "1")

    def test_2(self):
        self.assert_expected(self.PREFIX + "2")

    def test_3(self):
        self.assert_expected(self.PREFIX + "3")

    def test_4(self):
        self.assert_expected(self.PREFIX + "4")

    def test_5(self):
        self.assert_expected_unicode(self.PREFIX + "5")

    def test_6(self):
        self.assert_expected(self.PREFIX + "6")

    def test_7(self):
        self.assert_expected(self.PREFIX + "7")

    def test_8(self):
        self.assert_expected(self.PREFIX + "8")

    def test_9(self):
        self.assert_expected(self.PREFIX + "9")

    def test_10(self):
        self.assert_expected(self.PREFIX + "10")

    def test_11(self):
        self.assert_expected(self.PREFIX + "11")

    def test_12(self):
        self.assert_expected(self.PREFIX + "12")

    def test_expression_error(self):
        pt = AqPageTemplate()
        pt.write(util.read_input("expression_error.pt"))
        self.folder["expression_error"] = pt
        with self.assertRaises(ExpressionError):
            self.folder["expression_error"]()

    def test_not_found(self):
        pt = AqPageTemplate()
        pt.write(util.read_input("not_found.pt"))
        self.folder["not_found"] = pt
        with self.assertRaises(NotFound):
            self.folder["not_found"]()

    def test_underscore_traversal(self):
        pt = AqPageTemplate()
        pt.write(util.read_input("_underscore.pt"))
        self.folder["_underscore"] = pt
        with self.assertRaises(NotFound):
            self.folder["_underscore"]()