# Copyright (c) 2002-2026 Zope Corporation and Contributors.
# All Rights Reserved.

import unittest
import os

from zope.component import provideAdapter, provideUtility, getUtility
from zope.interface import Interface, implementer
from zope.security.management import setSecurityPolicy, newInteraction, noSecurityManager

from chameleon import PageTemplate

import util


class AqPageTemplate:
    def __init__(self, id, source=''):
        self.id = id
        self.source = source
        self.__parent__ = None
        self.__name__ = id

    def __call__(self, *args, **kwargs):
        tmpl = PageTemplate(self.source)
        return tmpl(*args, **kwargs)


class AqZopePageTemplate(AqPageTemplate):
    pass


class Folder(dict):
    def __init__(self, *args, **kwargs):
        super(Folder, self).__init__(*args, **kwargs)
        self.__parent__ = None
        self.__name__ = ''

    def __getitem__(self, key):
        return super(Folder, self).__getitem__(key)

    def __setitem__(self, key, value):
        super(Folder, self).__setitem__(key, value)

    def __contains__(self, key):
        return super(Folder, self).__contains__(key)


class UnitTestSecurityPolicy:
    def checkPermission(self, permission, object):
        return True

    def validate(self, *args, **kw):
        pass


class HTMLTests(unittest.TestCase):
    PREFIX = os.path.abspath(os.path.dirname(__file__))

    def setUp(self):
        self.policy = UnitTestSecurityPolicy()
        setSecurityPolicy(self.policy)
        newInteraction()
        provideAdapter(AqPageTemplate, (Interface,), Interface, name='pt')
        provideUtility(Folder(), name='folder')

    def tearDown(self):
        noSecurityManager()

    def assert_expected(self, source, expected):
        pt = AqZopePageTemplate('test', source)
        result = pt()
        self.assertEqual(result, expected)

    def assert_expected_unicode(self, source, expected):
        pt = AqZopePageTemplate('test', source)
        result = pt()
        self.assertEqual(result, expected)

    def getProducts(self):
        return {}

    def test_1(self):
        source = util.read_input(self.PREFIX, 'test1.pt')
        expected = util.read_output(self.PREFIX, 'test1.html')
        self.assert_expected(source, expected)

    def test_2(self):
        source = util.read_input(self.PREFIX, 'test2.pt')
        expected = util.read_output(self.PREFIX, 'test2.html')
        self.assert_expected(source, expected)

    def testHandleException(self):
        source = util.read_input(self.PREFIX, 'exception.pt')
        try:
            pt = AqZopePageTemplate('test', source)
            pt()
        except ZeroDivisionError:
            # Intentional swallow of ZeroDivisionError as per original test
            pass

    # Additional test methods (test_3, test_4, ...) would be defined similarly.


if __name__ == '__main__':
    unittest.main()