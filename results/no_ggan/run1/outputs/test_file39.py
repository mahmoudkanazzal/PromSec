from __future__ import absolute_import

import unittest

from zope.component.testing import PlacelessSetup
from zope.traversing.interfaces import ITraversable
from zope.traversing.adapters import DefaultTraversable
from zope.interface import alsoProvides
from zope.component import provideAdapter, provideUtility

from chameleon import useChameleonEngine

from AccessControl import SecurityManagement
from AccessControl.SecurityManagement import setSecurityPolicy, noSecurityManager, getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager

from Products.PageTemplates.PageTemplate import PageTemplate
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from Products.PageTemplates.unicode import DefaultUnicodeEncodingConflictResolver
from Products.PageTemplates.interfaces import IUnicodeEncodingConflictResolver

from Acquisition import Implicit

from Products.PageTemplates.tests import util
from Products.PageTemplates.tests.test_html import HTMLTests as _BaseHTMLTests


class UnitTestSecurityPolicy(object):
    def checkPermission(self, permission, object):
        return True

    def validate(self, *args, **kw):
        return True

    def getUser(self):
        class DummyUser(object):
            def getRoles(self):
                return ['Manager']

            def getId(self):
                return 'test_user'

        return DummyUser()


class AqPageTemplate(Implicit, PageTemplate):
    pass


class AqZopePageTemplate(Implicit, ZopePageTemplate):
    pass


class Folder(util.Base):
    pass


class HTMLTests(_BaseHTMLTests, PlacelessSetup, unittest.TestCase):
    def setUp(self):
        super(HTMLTests, self).setUp()
        useChameleonEngine()
        provideAdapter(DefaultTraversable, (object,), ITraversable)
        provideUtility(DefaultUnicodeEncodingConflictResolver(),
                       IUnicodeEncodingConflictResolver)
        self.folder = Folder()
        self.folder.laf = AqPageTemplate()
        self.folder.t = PageTemplate()
        self.folder.z = ZopePageTemplate()
        self._old_policy = getSecurityManager()
        setSecurityPolicy(UnitTestSecurityPolicy())
        newSecurityManager(None, self._old_policy.getUser())

    def tearDown(self):
        noSecurityManager()
        setSecurityPolicy(self._old_policy)
        super(HTMLTests, self).tearDown()

    def assert_expected(self, name, prefix=''):
        tmpl = util.read_input(name)
        self.assertFalse(tmpl._v_errors, tmpl._v_errors)
        expected = util.read_input(name + '.html')
        if prefix:
            expected = prefix + expected
        util.check_html(self, tmpl(), expected)

    def assert_expected_unicode(self, name, prefix=''):
        tmpl = util.read_input(name, unicode=True)
        self.assertFalse(tmpl._v_errors, tmpl._v_errors)
        expected = util.read_input(name + '.html', unicode=True)
        if prefix:
            expected = prefix + expected
        util.check_html(self, tmpl(), expected)

    def getProducts(self):
        return [
            {'id': 'Products.Foo', 'title': 'Foo Product'},
            {'id': 'Products.Bar', 'title': 'Bar Product'}
        ]


if __name__ == '__main__':
    unittest.main()