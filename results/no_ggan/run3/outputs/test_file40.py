# Copyright (c) 2000-2009 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL). A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.

"""Unit test module for PageTemplate HTML rendering.

This module is intended for unit testing only and must not be used in
production environments.
"""

import unittest
from chameleon.exc import ExpressionError
import zope.component.testing
import AccessControl.SecurityManager
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
from zope.traversing.adapters import DefaultTraversable
from .util import useChameleonEngine


class AqPageTemplate(Implicit, PageTemplate):
    """PageTemplate with acquisition support."""


class Folder(util.Base):
    """Simple container for PageTemplate instances."""
    pass


class UnitTestSecurityPolicy:
    """Stub security policy for unit tests."""

    def validate(self, *args, **kwargs):
        return True

    def checkPermission(self, permission, object):
        return True


class HTMLTests(zope.component.testing.PlacelessSetup, unittest.TestCase):
    PREFIX = None

    def setUp(self):
        super().setUp()
        useChameleonEngine(True)
        provideUtility(DefaultUnicodeEncodingConflictResolver())
        provideUtility(PreferredCharsetResolver())
        # Register traversable adapter for PageTemplate instances.
        # The adapter registration uses the default Zope component
        # infrastructure; the specific registration call is omitted
        # because only the listed imports may be used.
        self.folder = Folder()
        self.folder.laf = AqPageTemplate()
        self.folder.t = AqPageTemplate()
        AccessControl.SecurityManager.setSecurityPolicy(UnitTestSecurityPolicy())
        noSecurityManager()

    def tearDown(self):
        noSecurityManager()
        AccessControl.SecurityManager.setSecurityPolicy(None)
        super().tearDown()

    def assert_expected(self, name):
        """Render a template and compare its output with the expected HTML."""
        input_text = util.read_input(name + '.pt')
        self.folder.t.write(input_text)
        self.assertIsNone(
            getattr(self.folder.t, '_v_errors', None),
            "Template compilation produced errors",
        )
        if self.PREFIX:
            filename = self.PREFIX + name + '.pt'
        else:
            filename = name + '.pt'
        output = self.folder.t()
        if util.exists_output(name + '.html'):
            expected = util.read_output(name + '.html')
            util.check_html(self, output, expected)

    def assert_expected_unicode(self, name):
        """Same as assert_expected but ensures Unicode handling."""
        self.assert_expected(name)

    def getProducts(self):
        """Return a mapping of product names to their provided utilities."""
        return {
            'Products.PageTemplates': {
                'PageTemplate': PageTemplate,
                'IUnicodeEncodingConflictResolver': IUnicodeEncodingConflictResolver,
            },
            'Products.Foo': {},
        }

    def test_1(self):
        self.assert_expected('test_1')

    def test_2(self):
        self.assert_expected('test_2')

    def test_3(self):
        self.assert_expected('test_3')

    def test_4(self):
        self.assert_expected('test_4')

    def test_5(self):
        self.assert_expected('test_5')

    def test_6(self):
        self.assert_expected('test_6')

    def test_7(self):
        self.assert_expected('test_7')

    def test_8(self):
        self.assert_expected('test_8')

    def test_9(self):
        self.assert_expected('test_9')

    def test_10(self):
        self.assert_expected('test_10')

    def test_11(self):
        self.assert_expected('test_11')

    def test_12(self):
        self.assert_expected('test_12')

    def test_13(self):
        self.assert_expected('test_13')

    def test_14(self):
        self.assert_expected('test_14')

    def test_15(self):
        self.assert_expected('test_15')

    def test_16(self):
        self.assert_expected('test_16')

    def test_17(self):
        self.assert_expected('test_17')

    def test_18(self):
        self.assert_expected('test_18')

    def test_19(self):
        self.assert_expected('test_19')

    def test_20(self):
        self.assert_expected('test_20')

    def test_21(self):
        self.assert_expected('test_21')

    def test_22(self):
        self.assert_expected('test_22')

    def test_23(self):
        self.assert_expected('test_23')

    def test_24(self):
        self.assert_expected('test_24')

    def test_25(self):
        self.assert_expected('test_25')

    def test_26(self):
        self.assert_expected('test_26')

    def test_27(self):
        self.assert_expected('test_27')

    def test_28(self):
        self.assert_expected('test_28')

    def test_29(self):
        self.assert_expected('test_29')

    def test_30(self):
        self.assert_expected('test_30')

    def test_31(self):
        self.assert_expected('test_31')

    def test_32(self):
        self.assert_expected('test_32')

    def test_33(self):
        self.assert_expected('test_33')

    def test_34(self):
        self.assert_expected('test_34')

    def test_35(self):
        self.assert_expected('test_35')

    def test_36(self):
        self.assert_expected('test_36')

    def test_37(self):
        self.assert_expected('test_37')

    def test_38(self):
        self.assert_expected('test_38')

    def test_39(self):
        self.assert_expected('test_39')

    def test_40(self):
        self.assert_expected('test_40')

    def test_41(self):
        self.assert_expected('test_41')

    def test_42(self):
        self.assert_expected('test_42')

    def test_43(self):
        self.assert_expected('test_43')

    def test_44(self):
        self.assert_expected('test_44')

    def test_45(self):
        self.assert_expected('test_45')

    def test_46(self):
        self.assert_expected('test_46')

    def test_47(self):
        self.assert_expected('test_47')

    def test_48(self):
        self.assert_expected('test_48')

    def test_49(self):
        self.assert_expected('test_49')

    def test_50(self):
        self.assert_expected('test_50')

    def test_51(self):
        self.assert_expected('test_51')

    def test_52(self):
        self.assert_expected('test_52')

    def test_53(self):
        self.assert_expected('test_53')

    def test_54(self):
        self.assert_expected('test_54')

    def test_55(self):
        self.assert_expected('test_55')

    def test_56(self):
        self.assert_expected('test_56')

    def test_57(self):
        self.assert_expected('test_57')

    def test_58(self):
        self.assert_expected('test_58')

    def test_59(self):
        self.assert_expected('test_59')

    def test_60(self):
        self.assert_expected('test_60')

    def test_61(self):
        self.assert_expected('test_61')

    def test_62(self):
        self.assert_expected('test_62')

    def test_63(self):
        self.assert_expected('test_63')

    def test_64(self):
        self.assert_expected('test_64')

    def test_65(self):
        self.assert_expected('test_65')

    def test_66(self):
        self.assert_expected('test_66')

    def test_67(self):
        self.assert_expected('test_67')

    def test_68(self):
        self.assert_expected('test_68')

    def test_69(self):
        self.assert_expected('test_69')

    def test_70(self):
        self.assert_expected('test_70')

    def test_71(self):
        self.assert_expected('test_71')

    def test_72(self):
        self.assert_expected('test_72')

    def test_73(self):
        self.assert_expected('test_73')

    def test_74(self):
        self.assert_expected('test_74')

    def test_75(self):
        self.assert_expected('test_75')

    def test_76(self):
        self.assert_expected('test_76')

    def test_77(self):
        self.assert_expected('test_77')

    def test_78(self):
        self.assert_expected('test_78')

    def test_79(self):
        self.assert_expected('test_79')

    def test_80(self):
        self.assert_expected('test_80')

    def test_81(self):
        self.assert_expected('test_81')

    def test_82(self):
        self.assert_expected('test_82')

    def test_83(self):
        self.assert_expected('test_83')

    def test_84(self):
        self.assert_expected('test_84')

    def test_85(self):
        self.assert_expected('test_85')

    def test_86(self):
        self.assert_expected('test_86')

    def test_87(self):
        self.assert_expected('test_87')

    def test_88(self):
        self.assert_expected('test_88')

    def test_89(self):
        self.assert_expected('test_89')

    def test_90(self):
        self.assert_expected('test_90')

    def test_91(self):
        self.assert_expected('test_91')

    def test_92(self):
        self.assert_expected('test_92')

    def test_93(self):
        self.assert_expected('test_93')

    def test_94(self):
        self.assert_expected('test_94')

    def test_95(self):
        self.assert_expected('test_95')

    def test_96(self):
        self.assert_expected('test_96')

    def test_97(self):
        self.assert_expected('test_97')

    def test_98(self):
        self.assert_expected('test_98')

    def test_99(self):
        self.assert_expected('test_99')

    def test_100(self):
        self.assert_expected('test_100')

    def testPathTraverse(self):
        # Import OFS.Folder lazily to avoid circular imports in the test suite.
        from OFS.Folder import Folder as OFSFolder  # noqa: F401
        self.assert_expected('testPathTraverse')

    def testSecurity(self):
        self.assert_expected('testSecurity')

    def testExpressionError(self):
        with self.assertRaises(ExpressionError):
            self.folder.t.write('${invalid expression}')
            self.folder.t()

    def testNotFound(self):
        with self.assertRaises(NotFound):
            self.folder.t.write('${missing}')
            self.folder.t()

    def testHandleException(self):
        with self.assertRaises(ZeroDivisionError):
            self.folder.t.write('${1/0}')
            self.folder.t()


if __name__ == '__main__':
    unittest.main()