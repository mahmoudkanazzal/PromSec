from __future__ import absolute_import, print_function

import unittest

from chameleon.exc import ExpressionError
from zope.component.testing import PlacelessSetup
from AccessControl.SecurityManager import setSecurityPolicy
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


class AqPageTemplate(Implicit, PageTemplate):
    pass


class Folder(util.Base):
    pass


class UnitTestSecurityPolicy(object):
    def __init__(self):
        pass

    def validate(self, *args, **kwargs):
        return True

    def checkPermission(self, permission, object):
        return True

    def getUser(self):
        return None


class HTMLTests(PlacelessSetup, unittest.TestCase):
    PREFIX = None

    def setUp(self):
        super(HTMLTests, self).setUp()
        util.useChameleonEngine()
        provideUtility(DefaultTraversable())
        provideUtility(
            DefaultUnicodeEncodingConflictResolver(),
            IUnicodeEncodingConflictResolver,
        )
        self.folder = Folder()
        self.laf = AqPageTemplate('laf')
        self.t = AqPageTemplate('t')
        self.folder._setObject('laf', self.laf)
        self.folder._setObject('t', self.t)
        self.laf = self.folder.laf
        self.t = self.folder.t
        self._old_policy = setSecurityPolicy(UnitTestSecurityPolicy())
        noSecurityManager()

    def tearDown(self):
        setSecurityPolicy(self._old_policy)
        noSecurityManager()
        super(HTMLTests, self).tearDown()

    def assert_expected(self, tmpl, expected, **kwargs):
        self.t.pt_edit(tmpl)
        result = self.t.pt_render(**kwargs)
        util.check_html(self, result, expected)

    def assert_expected_unicode(self, tmpl, expected, **kwargs):
        self.t.pt_edit(tmpl)
        result = self.t.pt_render(**kwargs)
        util.check_html(self, result, expected)

    def getProducts(self):
        return [
            {"product": "Products.PageTemplates"},
            {"product": "Products.FooBar"},
        ]

    def test_1(self):
        tmpl = "<html><body>Hello World</body></html>"
        expected = "<html><body>Hello World</body></html>"
        self.assert_expected(tmpl, expected)

    def test_2(self):
        tmpl = "<html><body tal:content='string:Hello World'></body></html>"
        expected = "<html><body>Hello World</body></html>"
        self.assert_expected(tmpl, expected)

    def test_3(self):
        tmpl = "<html><body tal:repeat='item items'>${item}</body></html>"
        expected = "<html><body>1 2 3 </body></html>"
        self.assert_expected(tmpl, expected, items=[1, 2, 3])

    def testSimpleLoop(self):
        tmpl = "<ul tal:repeat='i items'><li tal:content='i'></li></ul>"
        expected = "<ul><li>1</li><li>2</li><li>3</li></ul>"
        self.assert_expected(tmpl, expected, items=[1, 2, 3])

    def testFancyLoop(self):
        tmpl = (
            "<ul tal:repeat='i items'>"
            "<li tal:condition='i%2'>${i}</li>"
            "</ul>"
        )
        expected = "<ul><li>1</li><li>3</li></ul>"
        self.assert_expected(tmpl, expected, items=[1, 2, 3])

    def testGlobalsShadowLocals(self):
        tmpl = (
            "<div tal:define='x 1' tal:content='python: x + globals().get(\"x\",0)'></div>"
        )
        expected = "<div>1</div>"
        self.assert_expected(tmpl, expected, x=0)

    def testStringExpressions(self):
        tmpl = "<div tal:content='string:${name}'></div>"
        expected = "<div>Bob</div>"
        self.assert_expected(tmpl, expected, name="Bob")

    def testReplaceWithNothing(self):
        tmpl = "<div tal:replace='nothing'></div>"
        expected = ""
        self.assert_expected(tmpl, expected)

    def testWithXMLHeader(self):
        tmpl = "<?xml version='1.0'?><root></root>"
        expected = "<?xml version='1.0'?><root></root>"
        self.assert_expected(tmpl, expected)

    def testNotExpression(self):
        tmpl = "<div tal:condition='not:False'></div>"
        expected = "<div></div>"
        self.assert_expected(tmpl, expected)

    def testPathNothing(self):
        tmpl = "<div tal:content='nothing'></div>"
        expected = "<div></div>"
        self.assert_expected(tmpl, expected)

    def testPathAlt(self):
        tmpl = "<div tal:content='path:missing|nothing'></div>"
        expected = "<div></div>"
        self.assert_expected(tmpl, expected)

    def testBatchIteration(self):
        tmpl = (
            "<ul tal:repeat='item batch'>"
            "<li tal:content='item'></li>"
            "</ul>"
        )
        expected = "<ul><li>1</li><li>2</li></ul>"
        self.assert_expected(tmpl, expected, batch=[1, 2])

    def testUnicodeInserts(self):
        tmpl = "<div tal:content='unicode:ü'></div>"
        expected = "<div>ü</div>"
        self.assert_expected_unicode(tmpl, expected)

    def testI18nTranslate(self):
        tmpl = "<div i18n:translate='Hello'></div>"
        expected = "<div>Hello</div>"
        self.assert_expected(tmpl, expected)

    def testImportOldStyleClass(self):
        tmpl = "<div tal:define='c:module:OldClass' tal:content='c'></div>"
        expected = "<div>OldClass</div>"
        self.assert_expected(tmpl, expected)

    def testRepeatVariable(self):
        tmpl = "<div tal:repeat='i items' tal:content='repeat.i'></div>"
        expected = "<div>1</div>"
        self.assert_expected(tmpl, expected, items=[1])

    def testBooleanAttributes(self):
        tmpl = "<input type='checkbox' tal:attributes='checked python:True'/>"
        expected = "<input type='checkbox' checked='checked'/>"
        self.assert_expected(tmpl, expected)

    def testBooleanAttributesAndDefault(self):
        tmpl = (
            "<input type='checkbox' tal:attributes='checked python:True; "
            "disabled python:False'/>"
        )
        expected = "<input type='checkbox' checked='checked'/>"
        self.assert_expected(tmpl, expected)

    def testInterpolationInContent(self):
        tmpl = "<div tal:content='string:${name} ${surname}'></div>"
        expected = "<div>John Doe</div>"
        self.assert_expected(tmpl, expected, name="John", surname="Doe")

    def testBadExpression(self):
        tmpl = "<div tal:content='bad:expression'></div>"
        with self.assertRaises(ExpressionError):
            self.t.pt_edit(tmpl)
            self.t.pt_render()

    def testPathAlternativesWithSpaces(self):
        tmpl = "<div tal:content='path:missing | nothing'></div>"
        expected = "<div></div>"
        self.assert_expected(tmpl, expected)

    def testDefaultKeywordHandling(self):
        tmpl = "<div tal:define='default default_value' tal:content='default'></div>"
        expected = "<div>default_value</div>"
        self.assert_expected(tmpl, expected)

    def testSwitch(self):
        tmpl = (
            "<div tal:switch='value'>"
            "<span tal:case='1'>One</span>"
            "<span tal:case='2'>Two</span>"
            "<span tal:default>Other</span>"
            "</div>"
        )
        expected = "<div><span>Two</span></div>"
        self.assert_expected(tmpl, expected, value=2)

    def test_unicode_conflict_resolution(self):
        provideUtility(PreferredCharsetResolver())
        tmpl = "<div tal:content='unicode:ü'></div>"
        expected = "<div>ü</div>"
        self.assert_expected_unicode(tmpl, expected)