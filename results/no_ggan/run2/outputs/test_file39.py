import unittest

from chameleon.exc import ExpressionError

import zope.component.testing
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
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from zExceptions import NotFound
from zope.component import provideUtility
from zope.location.interfaces import LocationError
from zope.traversing.adapters import DefaultTraversable

from .util import useChameleonEngine


class AqPageTemplate(Implicit, PageTemplate):
    pass


class AqZopePageTemplate(Implicit, ZopePageTemplate):
    pass


class Folder(util.Base):
    pass


class UnitTestSecurityPolicy:
    def validate(self, *args, **kw):
        return 1

    def checkPermission(self, *args, **kw):
        return 1


class HTMLTests(unittest.TestCase, zope.component.testing.PlacelessSetup):
    PREFIX = None

    def setUp(self):
        super().setUp()
        useChameleonEngine()
        self._old_traversable = zope.component.getAdapter(
            None, zope.traversing.interfaces.ITraversable, name='default')
        zope.component.provideAdapter(
            DefaultTraversable, (object,), zope.traversing.interfaces.ITraversable)
        provideUtility(
            DefaultUnicodeEncodingConflictResolver(),
            IUnicodeEncodingConflictResolver)
        self.folder = Folder()
        self.laf = AqPageTemplate('laf')
        self.t = AqPageTemplate('t')
        self.z = AqZopePageTemplate('z')
        self.folder._setObject('laf', self.laf)
        self.folder._setObject('t', self.t)
        self.folder._setObject('z', self.z)
        self.folder.laf = self.laf
        self.folder.t = self.t
        self.folder.z = self.z
        self._old_policy = SecurityManager.getSecurityPolicy()
        SecurityManager.setSecurityPolicy(UnitTestSecurityPolicy())
        SecurityManager.setInteraction(SecurityManager.getInteraction())
        self._old_security_manager = SecurityManager.getSecurityManager()
        SecurityManager.setSecurityManager(self.folder)

    def tearDown(self):
        noSecurityManager()
        SecurityManager.setSecurityPolicy(self._old_policy)
        SecurityManager.setInteraction(None)
        SecurityManager.setSecurityManager(self._old_security_manager)
        zope.component.provideAdapter(
            self._old_traversable, (object,), zope.traversing.interfaces.ITraversable)
        super().tearDown()

    def assert_expected(self, name):
        tmpl = util.read_input(name)
        self.t.write(tmpl)
        self.t.pt_edit(tmpl, content_type='text/html')
        output = self.t()
        expected = util.read_output(name)
        self.assertEqual(output, expected)
        self.assertFalse(self.t._v_errors)

    def assert_expected_unicode(self, name):
        tmpl = util.read_input(name)
        self.t.write(tmpl)
        self.t.pt_edit(tmpl, content_type='text/html')
        output = self.t()
        expected = util.read_output(name)
        self.assertEqual(output, expected)
        self.assertFalse(self.t._v_errors)

    def getProducts(self):
        return {
            'Products.PageTemplates': {
                'ZopePageTemplate': self.z,
                'PageTemplate': self.t,
            },
            'Products.Foo': {},
        }

    def test_1(self):
        pass

    def test_2(self):
        pass

    def testHandleException(self):
        pass


if __name__ == '__main__':
    unittest.main()