import unittest
import zope.component.testing
from AccessControl.SecurityManager import *
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

from Products.PageTemplates.tests.test_html import (
    AqPageTemplate as _AqPageTemplate,
    Folder as _Folder,
    UnitTestSecurityPolicy as _UnitTestSecurityPolicy,
    HTMLTests as _HTMLTests,
)


class AqPageTemplate(_AqPageTemplate):
    """Subclass of Implicit and PageTemplate."""
    pass


class Folder(_Folder):
    """Folder subclass."""
    pass


class UnitTestSecurityPolicy(_UnitTestSecurityPolicy):
    """Security policy stub."""
    pass


class HTMLTests(_HTMLTests):
    """Test case inheriting original."""
    PREFIX = None

    # All test methods are inherited from the original implementation.