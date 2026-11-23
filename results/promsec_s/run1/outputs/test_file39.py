import unittest
from chameleon.exc import ExpressionError
from zope.component.testing import PlacelessSetup, useChameleonEngine
from AccessControl.SecurityManagement import noSecurityManager
from AccessControl import SecurityManager
from Acquisition import Implicit
from Products.PageTemplates.interfaces import IUnicodeEncodingConflictResolver
from Products.PageTemplates.PageTemplate import PageTemplate
from Products.PageTemplates.tests import util
from Products.PageTemplates.unicodeconflictresolver import DefaultUnicodeEncodingConflictResolver, PreferredCharsetResolver
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from zExceptions import NotFound
from zope.component import provideUtility
from zope.location.interfaces import LocationError
from zope.traversing.adapters import DefaultTraversable
from Products.PageTemplates.tests.test_html import (
    AqPageTemplate,
    AqZopePageTemplate,
    Folder,
    UnitTestSecurityPolicy,
    HTMLTests,
)

if __name__ == '__main__':
    unittest.main(exit=False)