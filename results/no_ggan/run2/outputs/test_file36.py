import os
import unittest

from Acquisition import aq_base, aq_inner, aq_parent
from AccessControl import getSecurityManager, setSecurityPolicy, newSecurityManager
from AccessControl.SecurityManagement import Unauthorized
from AccessControl.User import UnrestrictedUser
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PageTemplates.interfaces import IPageTemplate
from Products.PageTemplates.tests import util
from zope.component import provideUtility, provideAdapter
from zope.component.testing import PlacelessSetup
from zope.interface import implementer
from zope.schema import TextLine
from zope.schema.interfaces import IField
from zope.i18nmessageid import MessageFactory
from zope.i18n import translate
from zope.publisher.interfaces import NotFound
from zope.location.interfaces import LocationError
from chameleon import PageTemplate as ChameleonTemplate
from Products.PageTemplates.engine import useChameleonEngine


_ = MessageFactory('test')


def use_chameleon_engine():
    useChameleonEngine()


use_chameleon_engine()


@implementer(IPageTemplate)
class AqPageTemplate(PageTemplateFile):
    """Acquisition-aware page template."""

    def __init__(self, filename, _prefix=None, _debug=0):
        super().__init__(filename, _prefix=_prefix, _debug=_debug)

    def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


class AqZopePageTemplate(AqPageTemplate):
    """Zope-specific page template subclass."""

    def __init__(self, filename, _prefix=None, _debug=0):
        super().__init__(filename, _prefix=_prefix, _debug=_debug)


class Folder(dict):
    """Simple folder-like container supporting acquisition."""

    def __init__(self):
        super().__init__()
        self.__allow_groups__ = ()
        self.__allow_roles__ = ()
        self.__allow_users__ = ()
        self.__allow_all__ = 1
        self.__ac_local_roles__ = {}
        self.__ac_roles__ = ()
        self.__ac_permissions__ = {}
        self.__ac_groups__ = {}
        self.__ac_user__ = None

    def __getitem__(self, key):
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)


class UnitTestSecurityPolicy:
    """Minimal security policy for unit tests."""

    def __init__(self):
        self._allowed = {}

    def checkPermission(self, permission, object):
        return True

    def validate(self, *args, **kwargs):
        return True

    def getRoles(self, user):
        return ['Manager']

    def getPermissions(self, user, object):
        return []


class HTMLTests(PlacelessSetup, unittest.TestCase):
    PREFIX = os.path.join(os.path.dirname(__file__), 'html')

    def setUp(self):
        super().setUp()
        self._old_policy = getSecurityManager().getSecurityPolicy()
        self._policy = UnitTestSecurityPolicy()
        setSecurityPolicy(self._policy)
        self._unrestricted = UnrestrictedUser('test', '', ['Manager'], '')
        newSecurityManager(None, self._unrestricted)
        self.folder = Folder()
        self.folder.__ac_user__ = self._unrestricted

    def tearDown(self):
        setSecurityPolicy(self._old_policy)
        newSecurityManager(None, None)
        super().tearDown()

    def assert_expected(self, template_name, expected_name):
        tmpl_path = os.path.join(self.PREFIX, template_name)
        tmpl = AqZopePageTemplate(tmpl_path)
        result = tmpl(self.folder)
        expected_path = os.path.join(self.PREFIX, expected_name)
        with open(expected_path, 'r', encoding='utf-8') as f:
            expected = f.read()
        util.check_html(self, result, expected)

    def assert_expected_unicode(self, template_name, expected_name):
        tmpl_path = os.path.join(self.PREFIX, template_name)
        tmpl = AqZopePageTemplate(tmpl_path)
        result = tmpl(self.folder)
        expected_path = os.path.join(self.PREFIX, expected_name)
        with open(expected_path, 'r', encoding='utf-8') as f:
            expected = f.read()
        util.check_html(self, result, expected)

    def getProducts(self):
        return {}

    def test_1(self):
        self.assert_expected('test1.pt', 'test1.html')

    def test_2(self):
        self.assert_expected('test2.pt', 'test2.html')

    def test_3(self):
        self.assert_expected('test3.pt', 'test3.html')

    def test_4(self):
        self.assert_expected('test4.pt', 'test4.html')

    def test_5(self):
        self.assert_expected('test5.pt', 'test5.html')

    def test_6(self):
        self.assert_expected('test6.pt', 'test6.html')

    def test_7(self):
        self.assert_expected('test7.pt', 'test7.html')

    def test_8(self):
        self.assert_expected('test8.pt', 'test8.html')

    def test_9(self):
        self.assert_expected('test9.pt', 'test9.html')

    def test_10(self):
        self.assert_expected('test10.pt', 'test10.html')

    def test_11(self):
        self.assert_expected('test11.pt', 'test11.html')

    def test_12(self):
        self.assert_expected('test12.pt', 'test12.html')

    def test_13(self):
        self.assert_expected('test13.pt', 'test13.html')

    def test_14(self):
        self.assert_expected('test14.pt', 'test14.html')

    def test_15(self):
        self.assert_expected('test15.pt', 'test15.html')

    def test_16(self):
        self.assert_expected('test16.pt', 'test16.html')

    def test_17(self):
        self.assert_expected('test17.pt', 'test17.html')

    def test_18(self):
        self.assert_expected('test18.pt', 'test18.html')

    def test_19(self):
        self.assert_expected('test19.pt', 'test19.html')

    def test_20(self):
        self.assert_expected('test20.pt', 'test20.html')

    def test_21(self):
        self.assert_expected('test21.pt', 'test21.html')

    def test_22(self):
        self.assert_expected('test22.pt', 'test22.html')

    def test_23(self):
        self.assert_expected('test23.pt', 'test23.html')

    def test_24(self):
        self.assert_expected('test24.pt', 'test24.html')

    def test_25(self):
        self.assert_expected('test25.pt', 'test25.html')

    def test_26(self):
        self.assert_expected('test26.pt', 'test26.html')

    def test_27(self):
        self.assert_expected('test27.pt', 'test27.html')

    def test_28(self):
        self.assert_expected('test28.pt', 'test28.html')

    def test_29(self):
        self.assert_expected('test29.pt', 'test29.html')

    def test_30(self):
        self.assert_expected('test30.pt', 'test30.html')

    def test_31(self):
        self.assert_expected('test31.pt', 'test31.html')

    def test_32(self):
        self.assert_expected('test32.pt', 'test32.html')

    def test_33(self):
        self.assert_expected('test33.pt', 'test33.html')

    def test_34(self):
        self.assert_expected('test34.pt', 'test34.html')

    def test_35(self):
        self.assert_expected('test35.pt', 'test35.html')

    def test_36(self):
        self.assert_expected('test36.pt', 'test36.html')

    def test_37(self):
        self.assert_expected('test37.pt', 'test37.html')

    def test_38(self):
        self.assert_expected('test38.pt', 'test38.html')

    def test_39(self):
        self.assert_expected('test39.pt', 'test39.html')

    def test_40(self):
        self.assert_expected('test40.pt', 'test40.html')

    def test_41(self):
        self.assert_expected('test41.pt', 'test41.html')

    def test_42(self):
        self.assert_expected('test42.pt', 'test42.html')

    def test_43(self):
        self.assert_expected('test43.pt', 'test43.html')

    def test_44(self):
        self.assert_expected('test44.pt', 'test44.html')

    def test_45(self):
        self.assert_expected('test45.pt', 'test45.html')

    def test_46(self):
        self.assert_expected('test46.pt', 'test46.html')

    def test_47(self):
        self.assert_expected('test47.pt', 'test47.html')

    def test_48(self):
        self.assert_expected('test48.pt', 'test48.html')

    def test_49(self):
        self.assert_expected('test49.pt', 'test49.html')

    def test_50(self):
        self.assert_expected('test50.pt', 'test50.html')

    def test_module_traversal(self):
        tmpl_path = os.path.join(self.PREFIX, 'module_traversal.pt')
        tmpl = AqZopePageTemplate(tmpl_path)
        with self.assertRaises(NotFound):
            tmpl(self.folder)

if __name__ == '__main__':
    unittest.main()