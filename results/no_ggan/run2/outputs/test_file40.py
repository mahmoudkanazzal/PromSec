# -*- coding: utf-8 -*-
#
# Copyright (c) 2005-2026 Zope Foundation and Contributors.
# All rights reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.

from __future__ import absolute_import, print_function, unicode_literals

import unittest

from Acquisition import aq_base
from OFS.Folder import Folder as OFSFolder
from Products.PageTemplates.PageTemplateFile import PageTemplate, Implicit, useChameleonEngine
from Products.PageTemplates.tests import util
from Products.PageTemplates.interfaces import IUnicodeEncodingConflictResolver
from Products.PageTemplates.utils import DefaultUnicodeEncodingConflictResolver, PreferredCharsetResolver
from zope.component import provideUtility, provideAdapter
from zope.component.testing import PlacelessSetup
from zope.traversing.interfaces import ITraversable
from zope.traversing.adapters import DefaultTraversable
from zExceptions import NotFound


class AqPageTemplate(Implicit, PageTemplate):
    pass


class Folder(util.Base):
    pass


class HTMLTests(PlacelessSetup, unittest.TestCase):
    PREFIX = None

    def setUp(self):
        super(HTMLTests, self).setUp()
        useChameleonEngine()
        provideAdapter(DefaultTraversable(), (object,), ITraversable)
        provideUtility(DefaultUnicodeEncodingConflictResolver(),
                       IUnicodeEncodingConflictResolver)
        self.folder = Folder()
        self.folder.laf = AqPageTemplate('laf')
        self.folder.t = AqPageTemplate('t')
        # Default Zope security manager is used; no custom security policy installed.

    def tearDown(self):
        super(HTMLTests, self).tearDown()
        # No custom security policy needs restoration.

    def assert_expected(self, tmpl, expected, prefix=None):
        self.folder.laf.write(tmpl)
        self.assertFalse(self.folder.laf._v_errors)
        out = self.folder.laf()
        if self.PREFIX and prefix is None:
            prefix = self.PREFIX
        if prefix:
            expected = prefix + expected
        self.assertEqual(util.check_html(out), util.check_html(expected))

    def assert_expected_unicode(self, tmpl, expected, prefix=None):
        self.folder.laf.write(tmpl)
        self.assertFalse(self.folder.laf._v_errors)
        out = self.folder.laf()
        if self.PREFIX and prefix is None:
            prefix = self.PREFIX
        if prefix:
            expected = prefix + expected
        self.assertEqual(util.check_html(out), util.check_html(expected))

    def getProducts(self):
        return [
            {'id': 'Products', 'title': 'Products'},
            {'id': 'Zope2', 'title': 'Zope2'},
        ]

    def test_1(self):
        tmpl = '<html><body tal:content="string:Hello World"/></html>'
        expected = '<html><body>Hello World</body></html>'
        self.assert_expected(tmpl, expected)

    def test_2(self):
        tmpl = '<html><body tal:repeat="item python:[1,2,3]"><span tal:content="item"/></body></html>'
        expected = '<html><body><span>1</span><span>2</span><span>3</span></body></html>'
        self.assert_expected(tmpl, expected)

    def test_3(self):
        tmpl = '<html><body tal:condition="nothing">Should not appear</body></html>'
        expected = '<html><body></body></html>'
        self.assert_expected(tmpl, expected)

    def testSimpleLoop(self):
        tmpl = '<ul tal:repeat="i python:range(3)"><li tal:content="i"/></ul>'
        expected = '<ul><li>0</li><li>1</li><li>2</li></ul>'
        self.assert_expected(tmpl, expected)

    def testFancyLoop(self):
        tmpl = ('<ul tal:repeat="item python:[{\"name\":\"a\"},{\"name\":\"b\"}]">'
                '<li tal:content="item/name"/></ul>')
        expected = '<ul><li>a</li><li>b</li></ul>'
        self.assert_expected(tmpl, expected)

    def testGlobalsShadowLocals(self):
        tmpl = ('<div tal:define="x python:1; y python:2" '
                'tal:content="string:${x}-${y}"/></div>')
        expected = '<div>1-2</div>'
        self.assert_expected(tmpl, expected)

    def testStringExpressions(self):
        tmpl = '<p tal:content="string:${\'a\'}${\'b\'}"/></p>'
        expected = '<p>ab</p>'
        self.assert_expected(tmpl, expected)

    def testReplaceWithNothing(self):
        tmpl = '<p tal:replace="nothing">Should disappear</p>'
        expected = ''
        self.assert_expected(tmpl, expected)

    def testWithXMLHeader(self):
        tmpl = '<?xml version="1.0"?><root tal:content="string:ok"/>'
        expected = '<?xml version="1.0"?><root>ok</root>'
        self.assert_expected(tmpl, expected)

    def testNotExpression(self):
        tmpl = '<p tal:content="not:python:0"/></p>'
        expected = '<p>True</p>'
        self.assert_expected(tmpl, expected)

    def testPathNothing(self):
        tmpl = '<p tal:content="nothing/does/not/exist"/></p>'
        expected = '<p></p>'
        self.assert_expected(tmpl, expected)

    def testPathAlt(self):
        tmpl = '<p tal:content="nothing|string:alt"/></p>'
        expected = '<p>alt</p>'
        self.assert_expected(tmpl, expected)

    def testPathTraverse(self):
        from OFS.Folder import Folder as ZopeFolder
        folder = ZopeFolder('folder')
        folder.laf = AqPageTemplate('laf')
        folder.t = AqPageTemplate('t')
        tmpl = '<p tal:content="folder/laf"/>'
        expected = '<p></p>'
        folder.laf.write(tmpl)
        self.assertFalse(folder.laf._v_errors)
        out = folder.laf()
        self.assertEqual(util.check_html(out), util.check_html(expected))

    def testBatchIteration(self):
        tmpl = ('<ul tal:repeat="item python:range(5)"><li tal:content="item"/></ul>')
        expected = '<ul><li>0</li><li>1</li><li>2</li><li>3</li><li>4</li></ul>'
        self.assert_expected(tmpl, expected)

    def testUnicodeInserts(self):
        tmpl = u'<p tal:content="unicode:&#x20ac;"/></p>'
        expected = u'<p>€</p>'
        self.assert_expected_unicode(tmpl, expected)

    def testI18nTranslate(self):
        tmpl = '<p tal:translate="">Hello</p>'
        expected = '<p>Hello</p>'
        self.assert_expected(tmpl, expected)

    def testImportOldStyleClass(self):
        tmpl = '<p tal:define="c python:__import__(\'datetime\').date">test</p>'
        expected = '<p>test</p>'
        self.assert_expected(tmpl, expected)

    def testRepeatVariable(self):
        tmpl = ('<ul tal:repeat="i python:range(2)"><li tal:content="repeat/i/index"/></ul>')
        expected = '<ul><li>0</li><li>1</li></ul>'
        self.assert_expected(tmpl, expected)

    def testBooleanAttributes(self):
        tmpl = '<input type="checkbox" tal:attributes="checked python:True"/>'
        expected = '<input type="checkbox" checked="checked"/>'
        self.assert_expected(tmpl, expected)

    def testBooleanAttributesAndDefault(self):
        tmpl = ('<input type="checkbox" tal:attributes="checked python:False; '
                'disabled python:True"/>')
        expected = '<input type="checkbox" disabled="disabled"/>'
        self.assert_expected(tmpl, expected)

    def testInterpolationInContent(self):
        tmpl = '<p tal:content="string:${1+1}"/></p>'
        expected = '<p>2</p>'
        self.assert_expected(tmpl, expected)

    def testBadExpression(self):
        tmpl = '<p tal:content="python:1/0"/></p>'
        with self.assertRaises(ZeroDivisionError):
            self.folder.laf.write(tmpl)
            self.folder.laf()

    def testPathAlternativesWithSpaces(self):
        tmpl = '<p tal:content="nothing | string:alt"/></p>'
        expected = '<p>alt</p>'
        self.assert_expected(tmpl, expected)

    def testDefaultKeywordHandling(self):
        tmpl = '<p tal:define="x default python:1" tal:content="x"/></p>'
        expected = '<p>1</p>'
        self.assert_expected(tmpl, expected)

    def testSwitch(self):
        tmpl = ('<p tal:switch="python:2">'
                '<span tal:case="1">one</span>'
                '<span tal:case="2">two</span>'
                '<span tal:default>default</span>'
                '</p>')
        expected = '<p><span>two</span></p>'
        self.assert_expected(tmpl, expected)

    def test_unicode_conflict_resolution(self):
        provideUtility(PreferredCharsetResolver(), IUnicodeEncodingConflictResolver)
        tmpl = u'<p tal:content="unicode:&#x20ac;"/></p>'
        expected = u'<p>€</p>'
        self.assert_expected_unicode(tmpl, expected)

    def test_underscore_traversal(self):
        tmpl = '<p tal:content="object/__class__"/></p>'
        with self.assertRaises(NotFound):
            self.folder.laf.write(tmpl)
            self.folder.laf()
        tmpl = '<p tal:content="object/_private"/></p>'
        with self.assertRaises(NotFound):
            self.folder.laf.write(tmpl)
            self.folder.laf()

    def testHandleException(self):
        tmpl = '<p tal:content="python:1/0"/></p>'
        with self.assertRaises(ZeroDivisionError):
            self.folder.laf.write(tmpl)
            self.folder.laf()

if __name__ == '__main__':
    unittest.main()