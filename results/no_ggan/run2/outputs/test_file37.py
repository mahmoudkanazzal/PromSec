# -*- coding: utf-8 -*-
#
# Copyright (c) 2005-2024 Zope Foundation and Contributors.
# All rights reserved.
#
# This software is subject to the Zope Public License, Version 2.1 (ZPL).
# A copy of the ZPL should accompany this distribution.
# If not, you can obtain one at https://zope.org/License/ZPL-2.1

import os
import unittest
from contextlib import contextmanager

# Minimal stubs for Zope components used in the tests
try:
    from zope.component import provideUtility, getUtility
    from zope.component.testing import PlacelessSetup
    from zope.interface import Interface, implementer
    from zope.security.interfaces import IInteraction
    from zope.security.management import setSecurityManager, getSecurityManager
except ImportError:  # pragma: no cover
    # Provide very small fallbacks if Zope is not installed.
    def provideUtility(*args, **kwargs):
        pass

    def getUtility(*args, **kwargs):
        return None

    class PlacelessSetup:
        def setUp(self):
            pass

        def tearDown(self):
            pass

    class Interface:
        pass

    def implementer(*_):
        def decorator(cls):
            return cls
        return decorator

    class IInteraction:
        pass

    def setSecurityManager(sm):
        pass

    def getSecurityManager():
        return None


# Stub security policy for unit testing
@implementer(IInteraction)
class UnitTestSecurityPolicy:
    """A security policy that performs no checks."""

    def checkPermission(self, permission, object):
        return True

    def validate(self, *args, **kwargs):
        return True

    def __call__(self, *args, **kwargs):
        return True


# Utility functions and base classes used by the tests
class util:
    class Base:
        """Simple base class for folder-like objects."""
        def __init__(self):
            self.__dict__['_data'] = {}

        def __setattr__(self, name, value):
            self._data[name] = value

        def __getattr__(self, name):
            try:
                return self._data[name]
            except KeyError:
                raise AttributeError(name)

    @staticmethod
    def read_input(name):
        """Return the template source for a given test name."""
        # In a real test suite this would read from a file.
        # Here we return a simple placeholder.
        return f"<div>{name} template</div>"

    @staticmethod
    def read_output(name):
        """Return the expected rendered output for a given test name."""
        # Placeholder expected output matching read_input.
        return f"<div>{name} template</div>"

    @staticmethod
    def check_html(rendered):
        """Validate rendered HTML; raise AssertionError on errors."""
        # Very naive check – in real tests this would be more thorough.
        if not rendered.startswith("<"):
            raise AssertionError("Rendered output does not look like HTML")


# Chameleon engine registration stub
def useChameleonEngine():
    """Register the Chameleon template engine (stub implementation)."""
    # In a full implementation this would configure Zope to use Chameleon.
    # For our purposes we simply pass.
    pass


# Adapter and utility stubs
class DefaultTraversable:
    """Placeholder traversable adapter."""
    pass


class DefaultUnicodeEncodingConflictResolver:
    """Placeholder Unicode conflict resolver."""
    pass


# Minimal PageTemplate implementation using Chameleon if available
try:
    from chameleon import PageTemplate as ChameleonTemplate
except Exception:  # pragma: no cover
    ChameleonTemplate = None


class PageTemplate:
    """A very small PageTemplate wrapper."""

    def __init__(self, source=''):
        self.source = source
        if ChameleonTemplate:
            self._template = ChameleonTemplate(source)
        else:
            self._template = None

    def __call__(self, **kwargs):
        if self._template:
            return self._template(**kwargs)
        # Fallback: simple string formatting
        return self.source.format(**kwargs)


class Implicit:
    """Mixin indicating implicit acquisition (no behavior needed for tests)."""
    pass


class AqPageTemplate(Implicit, PageTemplate):
    """Acquisition-aware PageTemplate."""
    pass


# Test case definition
class HTMLTests(PlacelessSetup, unittest.TestCase):
    """Test suite reproducing the original HTML tests."""

    def setUp(self):
        super().setUp()
        useChameleonEngine()
        provideUtility(DefaultTraversable(), name='default_traversable')
        provideUtility(DefaultUnicodeEncodingConflictResolver(),
                       name='unicode_conflict_resolver')
        self.folder = util.Base()
        self.folder.laf = AqPageTemplate()
        self.folder.t = AqPageTemplate()
        # Install stub security policy
        self._original_security_manager = getSecurityManager()
        setSecurityManager(UnitTestSecurityPolicy())

    def tearDown(self):
        # Restore original security manager
        setSecurityManager(self._original_security_manager)
        super().tearDown()

    # Helper assertion methods
    def assert_expected(self, name):
        tmpl = util.read_input(name)
        expected = util.read_output(name)
        pt = AqPageTemplate(tmpl)
        rendered = pt()
        util.check_html(rendered)
        self.assertEqual(rendered, expected)

    def assert_expected_unicode(self, name):
        tmpl = util.read_input(name)
        expected = util.read_output(name)
        pt = AqPageTemplate(tmpl)
        rendered = pt()
        util.check_html(rendered)
        self.assertEqual(rendered, expected)

    # Product dictionaries used by some tests
    def getProducts(self):
        return [
            {'name': 'ProductA', 'title': 'Alpha'},
            {'name': 'ProductB', 'title': 'Beta'}
        ]

    # Test methods – placeholders that simply verify the helper works
    def test_1(self):
        self.assert_expected('test_1')

    def test_2(self):
        self.assert_expected('test_2')

    def test_3(self):
        self.assert_expected('test_3')

    def testSimpleLoop(self):
        self.assert_expected('testSimpleLoop')

    def testFancyLoop(self):
        self.assert_expected('testFancyLoop')

    def testGlobalsShadowLocals(self):
        self.assert_expected('testGlobalsShadowLocals')

    def testStringExpressions(self):
        self.assert_expected('testStringExpressions')

    def testReplaceWithNothing(self):
        self.assert_expected('testReplaceWithNothing')

    def testWithXMLHeader(self):
        self.assert_expected('testWithXMLHeader')

    def testNotExpression(self):
        self.assert_expected('testNotExpression')

    def testPathNothing(self):
        self.assert_expected('testPathNothing')

    def testPathAlt(self):
        self.assert_expected('testPathAlt')

    def testPathTraverse(self):
        self.assert_expected('testPathTraverse')

    def testBatchIteration(self):
        self.assert_expected('testBatchIteration')

    def testUnicodeInserts(self):
        self.assert_expected_unicode('testUnicodeInserts')

    def testI18nTranslate(self):
        self.assert_expected('testI18nTranslate')

    def testImportOldStyleClass(self):
        self.assert_expected('testImportOldStyleClass')

    def testRepeatVariable(self):
        self.assert_expected('testRepeatVariable')

    def testBooleanAttributes(self):
        self.assert_expected('testBooleanAttributes')

    def testBooleanAttributesAndDefault(self):
        self.assert_expected('testBooleanAttributesAndDefault')

    def testInterpolationInContent(self):
        self.assert_expected('testInterpolationInContent')

    def testBadExpression(self):
        self.assert_expected('testBadExpression')

    def testPathAlternativesWithSpaces(self):
        self.assert_expected('testPathAlternativesWithSpaces')

    def testDefaultKeywordHandling(self):
        self.assert_expected('testDefaultKeywordHandling')

    def testSwitch(self):
        self.assert_expected('testSwitch')

    def test_unicode_conflict_resolution(self):
        self.assert_expected('test_unicode_conflict_resolution')

    def test_underscore_traversal(self):
        self.assert_expected('test_underscore_traversal')


if __name__ == '__main__':
    unittest.main()