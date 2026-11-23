import unittest
from chameleon.exc import ExpressionError
from AccessControl import SecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from Acquisition import Implicit
from Products.PageTemplates.interfaces import IUnicodeEncodingConflictResolver
from Products.PageTemplates.PageTemplate import PageTemplate
from Products.PageTemplates.tests import util
from Products.PageTemplates.unicodeconflictresolver import DefaultUnicodeEncodingConflictResolver, PreferredCharsetResolver
from zExceptions import NotFound
from zope.component import getGlobalSiteManager, provideAdapter
from zope.component.testing import PlacelessSetup
from .util import useChameleonEngine


class AqPageTemplate(Implicit, PageTemplate):
    pass


class Folder(util.Base):
    pass


class UnitTestSecurityPolicy:
    def validate(self, *args, **kwargs):
        return 1

    def checkPermission(self, *args, **kwargs):
        return 1


class HTMLTests(PlacelessSetup, unittest.TestCase):
    PREFIX = None

    def setUp(self):
        super().setUp()
        useChameleonEngine()
        from zope.traversing.adapters import DefaultTraversable
        provideAdapter(DefaultTraversable)
        getGlobalSiteManager().registerUtility(
            DefaultUnicodeEncodingConflictResolver(),
            IUnicodeEncodingConflictResolver,
        )
        self.folder = Folder()
        self.laf = AqPageTemplate()
        self.t = AqPageTemplate()
        self.policy = UnitTestSecurityPolicy()
        self._old_policy = SecurityManager.setSecurityPolicy(self.policy)
        noSecurityManager()

    def tearDown(self):
        SecurityManager.setSecurityPolicy(self._old_policy)
        noSecurityManager()
        super().tearDown()

    def assert_expected(self, name, **kw):
        tmpl = util.read_input(name)
        self.t.write(tmpl)
        if getattr(self.t, "_v_errors", None):
            raise AssertionError(self.t._v_errors)
        expected = util.read_output(name, self.PREFIX)
        if not isinstance(expected, str):
            expected = str(expected)
        result = self.t(**kw)
        util.check_html(result, expected)

    def assert_expected_unicode(self, name, **kw):
        tmpl = util.read_input(name)
        self.t.write(tmpl)
        if getattr(self.t, "_v_errors", None):
            raise AssertionError(self.t._v_errors)
        expected = util.read_output(name, self.PREFIX)
        if not isinstance(expected, str):
            expected = str(expected)
        result = self.t(**kw)
        util.check_html(result, expected)

    def getProducts(self):
        return {
            "Products.PageTemplates": {"PageTemplate": PageTemplate},
            "Products.Foo": {"Bar": object},
        }

    def test_1(self):
        self.assert_expected("test_1")

    def test_2(self):
        self.assert_expected("test_2")

    def test_3(self):
        self.assert_expected("test_3")

    def testSimpleLoop(self):
        self.assert_expected("simple_loop")

    def testFancyLoop(self):
        self.assert_expected("fancy_loop")

    def testGlobalsShadowLocals(self):
        self.assert_expected("globals_shadow_locals")

    def testStringExpressions(self):
        self.assert_expected("string_expressions")

    def testReplaceWithNothing(self):
        self.assert_expected("replace_with_nothing")

    def testWithXMLHeader(self):
        self.assert_expected("with_xml_header")

    def testNotExpression(self):
        self.assert_expected("not_expression")

    def testPathNothing(self):
        self.assert_expected("path_nothing")

    def testPathAlt(self):
        self.assert_expected("path_alt")

    def testPathTraverse(self):
        from OFS.Folder import Folder as ZopeFolder
        self.folder = ZopeFolder('folder')
        self.assert_expected("path_traverse")

    def testBatchIteration(self):
        self.assert_expected("batch_iteration")

    def testUnicodeInserts(self):
        self.assert_expected_unicode("unicode_inserts")

    def testI18nTranslate(self):
        self.assert_expected("i18n_translate")

    def testImportOldStyleClass(self):
        self.assert_expected("import_old_style_class")

    def testRepeatVariable(self):
        self.assert_expected("repeat_variable")

    def testBooleanAttributes(self):
        self.assert_expected("boolean_attributes")

    def testBooleanAttributesAndDefault(self):
        self.assert_expected("boolean_attributes_and_default")

    def testInterpolationInContent(self):
        self.assert_expected("interpolation_in_content")

    def testBadExpression(self):
        with self.assertRaises(ExpressionError):
            self.assert_expected("bad_expression")

    def testPathAlternativesWithSpaces(self):
        self.assert_expected("path_alternatives_with_spaces")

    def testDefaultKeywordHandling(self):
        self.assert_expected("default_keyword_handling")

    def testSwitch(self):
        self.assert_expected("switch")

    def test_unicode_conflict_resolution(self):
        getGlobalSiteManager().registerUtility(
            PreferredCharsetResolver(),
            IUnicodeEncodingConflictResolver,
        )
        pt = PageTemplate()
        pt.write(util.read_input("unicode_conflict"))
        result = pt()
        expected = util.read_output("unicode_conflict", self.PREFIX)
        util.check_html(result, expected)

    def test_underscore_traversal(self):
        snippets = [
            "tal:content='nothing/_'",
            "tal:content='nothing/_/foo'",
            "tal:content='nothing/_'",
        ]
        for snippet in snippets:
            self.t.write(f"<div {snippet}></div>")
            with self.assertRaises(NotFound):
                self.t()

    def testHandleException(self):
        self.t.write("<div tal:content='1/0'></div>")
        with self.assertRaises(ZeroDivisionError):
            self.t()


if __name__ == "__main__":
    unittest.main()