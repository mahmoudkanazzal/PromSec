# -*- coding: utf-8 -*-
# Copyright (c) 2005 Zope Corporation and Contributors.
# All Rights Reserved.
# Zope Public License (ZPL) version 2.1

from __future__ import absolute_import, print_function

import unittest

from AccessControl.SecurityManagement import setSecurityPolicy, noSecurityManager, SecurityManager
from Products.PageTemplates.PageTemplate import PageTemplate, Implicit
from Products.PageTemplates.tests import util
from zope.component import provideUtility, provideAdapter
from zope.traversing.adapters import DefaultTraversable
from zope.i18n.unicodeconflict import DefaultUnicodeEncodingConflictResolver
from zope.i18n.charset import PreferredCharsetResolver
from zope.component.testing import PlacelessSetup


def useChameleonEngine():
    """Placeholder to activate the Chameleon engine."""
    pass


class UnitTestSecurityPolicy(object):
    """Permissive security policy stub for unit tests."""

    def validate(self, *args, **kwargs):
        return True

    def checkPermission(self, permission, object):
        return True


class AqPageTemplate(Implicit, PageTemplate):
    """PageTemplate subclass using Implicit rendering."""
    pass


class Folder(util.Base):
    """Simple folder class for tests."""
    pass


class HTMLTests(PlacelessSetup, unittest.TestCase):
    PREFIX = None

    def setUp(self):
        super(HTMLTests, self).setUp()
        self._old_policy = getattr(SecurityManager, 'getSecurityPolicy', lambda: None)()
        setSecurityPolicy(UnitTestSecurityPolicy())
        provideUtility(DefaultTraversable(), name='default')
        provideUtility(DefaultUnicodeEncodingConflictResolver(), name='default')
        provideUtility(PreferredCharsetResolver(), name='default')
        useChameleonEngine()

    def tearDown(self):
        noSecurityManager()
        setSecurityPolicy(self._old_policy)
        super(HTMLTests, self).tearDown()

    def assert_expected(self, filename):
        tmpl = util.read_input(filename)
        expected = util.read_output(filename)
        pt = AqPageTemplate(tmpl)
        result = pt()
        util.check_html(result, expected)

    def assert_expected_unicode(self, filename):
        tmpl = util.read_input(filename)
        expected = util.read_output(filename)
        pt = AqPageTemplate(tmpl)
        result = pt()
        util.check_html(result, expected)

    def getProducts(self):
        return [
            {'id': 'Products.PageTemplates', 'path': 'Products/PageTemplates'},
            {'id': 'Products.Five', 'path': 'Products/Five'}
        ]

    def test_1(self):
        self.assert_expected('test_1.pt')

    def test_2(self):
        self.assert_expected('test_2.pt')

    def test_3(self):
        self.assert_expected('test_3.pt')

    def test_4(self):
        self.assert_expected('test_4.pt')

    def test_5(self):
        self.assert_expected('test_5.pt')

    def testHandleException(self):
        tmpl = util.read_input('exception.pt')
        pt = AqPageTemplate(tmpl)
        try:
            pt()
        except ZeroDivisionError as e:
            # Re‑raise as a clearly documented exception to avoid swallowing.
            raise RuntimeError('ZeroDivisionError caught during template rendering') from e
        else:
            self.fail('ZeroDivisionError was not raised')


if __name__ == '__main__':
    unittest.TextTestRunner().run(
        unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__))
    )