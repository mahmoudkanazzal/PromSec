from __future__ import absolute_import, print_function, unicode_literals

import unittest

from zope.component.testing import PlacelessSetup
from zope.component import getGlobalSiteManager, provideAdapter, provideUtility
from zope.interface import Interface, implementer
from zope.security.management import setSecurityPolicy, noSecurityManager, getSecurityManager
from zope.security.policy import SecurityPolicy

from Products.PageTemplates.PageTemplate import PageTemplate
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from Products.PageTemplates.interfaces import IPageTemplate

from chameleon import PageTemplateFile

from . import util


@implementer(IPageTemplate)
class AqPageTemplate(PageTemplate):
    """Acquisition-aware Page Template."""
    pass


@implementer(IPageTemplate)
class AqZopePageTemplate(ZopePageTemplate):
    """Acquisition-aware Zope Page Template."""
    pass


class Folder(object):
    """Simple folder-like object for traversal tests."""

    def __init__(self):
        self._objects = {}

    def __getitem__(self, name):
        return self._objects[name]

    def __setitem__(self, name, value):
        self._objects[name] = value

    def __contains__(self, name):
        return name in self._objects


@implementer(Interface)
class UnitTestSecurityPolicy(SecurityPolicy):
    """Security policy that permits all actions."""

    def checkPermission(self, permission, object):
        return True

    def checkPermissionForPrincipal(self, permission, principal, object):
        return True

    def validate(self, *args, **kwargs):
        return True

    def __call__(self, *args, **kwargs):
        return True


class HTMLTests(unittest.TestCase, PlacelessSetup):
    """Test suite for HTML rendering of page templates."""

    def setUp(self):
        super(HTMLTests, self).setUp()
        self._old_policy = getSecurityManager().getSecurityPolicy()
        setSecurityPolicy(UnitTestSecurityPolicy())
        noSecurityManager()
        self.folder = Folder()
        provideAdapter(AqPageTemplate, (Interface,), IPageTemplate, name='')
        provideAdapter(AqZopePageTemplate, (Interface,), IPageTemplate, name='')

    def tearDown(self):
        setSecurityPolicy(self._old_policy)
        noSecurityManager()
        super(HTMLTests, self).tearDown()

    def assert_expected(self, template_file, expected_file):
        tmpl = util.readFile(template_file)
        expected = util.readFile(expected_file)
        pt = AqPageTemplate(tmpl)
        try:
            result = pt()
        except Exception as e:
            raise AssertionError("Template rendering failed: %s" % e)
        util.check_html(result, expected)

    def assert_expected_unicode(self, template_file, expected_file):
        tmpl = util.readFile(template_file)
        expected = util.readFile(expected_file)
        pt = AqPageTemplate(tmpl)
        try:
            result = pt()
        except Exception as e:
            raise AssertionError("Template rendering failed: %s" % e)
        if not isinstance(result, str):
            raise AssertionError("Result is not a Unicode string")
        util.check_html(result, expected)

    def getProducts(self):
        return [
            {'id': 'Products.Foo', 'title': 'Foo'},
            {'id': 'Products.Bar', 'title': 'Bar'}
        ]

    def test_1(self):
        self.assert_expected('templates/test_1.pt', 'expected/test_1.html')

    def test_2(self):
        self.assert_expected('templates/test_2.pt', 'expected/test_2.html')

    def test_unicode(self):
        self.assert_expected_unicode('templates/test_unicode.pt', 'expected/test_unicode.html')

    def test_module_traversal(self):
        setSecurityPolicy(self._old_policy)
        noSecurityManager()
        self.assert_expected('templates/test_module_traversal.pt', 'expected/test_module_traversal.html')