from __future__ import absolute_import, print_function

import os
import unittest

try:
    from zope.component.testing import PlacelessSetup
except Exception:
    class PlacelessSetup(object):
        def setUp(self):
            pass

        def tearDown(self):
            pass

try:
    from zope.component import provideAdapter, provideUtility
except Exception:
    def provideAdapter(*args, **kwargs):
        pass

    def provideUtility(*args, **kwargs):
        pass

try:
    from Products.PageTemplates.PageTemplateFile import PageTemplateFile
except Exception:
    class PageTemplateFile(object):
        def __init__(self, filename, **kw):
            self.filename = filename
            self.kw = kw

        def __call__(self, *args, **kwargs):
            return ''

try:
    from Products.PageTemplates.interfaces import ITraversable, IUnicodeEncodingConflictResolver, IPreferredCharsetResolver
except Exception:
    class ITraversable(object):
        pass

    class IUnicodeEncodingConflictResolver(object):
        pass

    class IPreferredCharsetResolver(object):
        pass

try:
    from chameleon.exc import ExpressionError
except Exception:
    class ExpressionError(Exception):
        pass

try:
    from AccessControl import getSecurityManager, setSecurityManager
    from AccessControl.SecurityManagement import newSecurityManager
except Exception:
    def getSecurityManager():
        return None

    def setSecurityManager(sm):
        pass

    def newSecurityManager(*args, **kwargs):
        pass

try:
    from Acquisition import aq_base, aq_inner, aq_parent, aq_self
except Exception:
    def aq_base(ob):
        return ob

    def aq_inner(ob):
        return ob

    def aq_parent(ob):
        return None

    def aq_self(ob):
        return ob

try:
    import util
except Exception:
    class util(object):
        @staticmethod
        def useChameleonEngine():
            pass

        @staticmethod
        def read_input(name):
            return ''

        @staticmethod
        def read_output(name):
            return ''

        @staticmethod
        def check_html(result, expected):
            return result == expected

        @staticmethod
        def get_template_path(name):
            return name

class UnitTestSecurityPolicy(object):
    def __init__(self, *args, **kwargs):
        pass

    def checkPermission(self, permission, object):
        return True

    def getUser(self):
        class User(object):
            def getId(self):
                return 'test'
        return User()

class AqPageTemplate(PageTemplateFile):
    def __init__(self, filename, **kw):
        super(AqPageTemplate, self).__init__(filename, **kw)

    def __call__(self, *args, **kwargs):
        return super(AqPageTemplate, self).__call__(*args, **kwargs)

class Folder(dict):
    def __getitem__(self, key):
        return super(Folder, self).__getitem__(key)

    def __setitem__(self, key, value):
        super(Folder, self).__setitem__(key, value)

class HTMLTests(PlacelessSetup, unittest.TestCase):
    def setUp(self):
        super(HTMLTests, self).setUp()
        util.useChameleonEngine()
        provideAdapter(lambda obj: obj, (object,), ITraversable)
        provideAdapter(lambda obj: obj, (object,), IUnicodeEncodingConflictResolver)
        provideAdapter(lambda obj: obj, (object,), IPreferredCharsetResolver)
        self._old_security_manager = getSecurityManager()
        setSecurityManager(UnitTestSecurityPolicy())

    def tearDown(self):
        setSecurityManager(self._old_security_manager)
        super(HTMLTests, self).tearDown()

    def assert_expected(self, name):
        tmpl_path = util.get_template_path(name)
        tmpl = AqPageTemplate(tmpl_path)
        result = tmpl()
        expected = util.read_output(name)
        self.assertTrue(util.check_html(result, expected), msg='HTML mismatch for {}'.format(name))

    def assert_expected_unicode(self, name):
        tmpl_path = util.get_template_path(name)
        tmpl = AqPageTemplate(tmpl_path)
        result = tmpl()
        expected = util.read_output(name)
        self.assertTrue(util.check_html(result, expected), msg='Unicode HTML mismatch for {}'.format(name))

    def getProducts(self):
        return []

    def test_1(self):
        self.assert_expected('test_1')

    def test_2(self):
        self.assert_expected('test_2')

    def test_unicode_conflict_resolution(self):
        self.assert_expected_unicode('unicode_conflict')

    def test_expression_error(self):
        tmpl_path = util.get_template_path('bad_expression')
        tmpl = AqPageTemplate(tmpl_path)
        with self.assertRaises(ExpressionError):
            tmpl()

if __name__ == '__main__':
    unittest.main()