import unittest
from zope.component.testing import PlacelessSetup
from zope.component import provideAdapter, provideUtility
from chameleon.exc import ExpressionError
from AccessControl.SecurityManagement import (
    setSecurityPolicy,
    getSecurityPolicy,
    noSecurityManager,
)
from AccessControl.SecurityManagement import SecurityManager  # noqa: F401
from Products.PageTemplates.engine import useChameleonEngine
from Products.PageTemplates.PageTemplate import PageTemplate, Implicit
from Products.PageTemplates.traversable import Traversable
from Products.PageTemplates.utils import UnicodeConflictResolver
import util
from ZPublisher.NotFound import NotFound


class UnitTestSecurityPolicy:
    """Permissive security policy stub for unit tests."""

    def checkPermission(self, permission, obj):
        return True

    def validate(self, obj, permission):
        return True

    def getInteraction(self):
        return None


class AqPageTemplate(Implicit, PageTemplate):
    """PageTemplate subclass with implicit expressions."""


class Folder(util.Base):
    """Simple folder object for tests."""


class HTMLTests(PlacelessSetup, unittest.TestCase):
    PREFIX = None

    def setUp(self):
        super().setUp()
        useChameleonEngine()
        provideAdapter(Traversable)
        provideUtility(UnicodeConflictResolver())
        self.folder = Folder()
        self.folder.laf = AqPageTemplate()
        self.folder.t = AqPageTemplate()
        self._old_policy = getSecurityPolicy()
        setSecurityPolicy(UnitTestSecurityPolicy())
        noSecurityManager()

    def tearDown(self):
        setSecurityPolicy(self._old_policy)
        noSecurityManager()
        super().tearDown()

    def assert_expected(self, t, fname, *args, **kwargs):
        src = util.read_input(fname)
        t.write(src)
        if hasattr(t, "_v_errors") and t._v_errors:
            self.fail("Template errors: %s" % t._v_errors)
        expected = util.read_output(fname)
        if self.PREFIX:
            expected = expected.replace("PREFIX", self.PREFIX)
        output = t(*args, **kwargs)
        util.check_html(output, expected)

    def assert_expected_unicode(self, t, fname, *args, **kwargs):
        # In Python 3 all strings are Unicode; reuse the same logic.
        self.assert_expected(t, fname, *args, **kwargs)

    def getProducts(self):
        return [
            {"title": "Apple", "price": 1.0, "quantity": 10},
            {"title": "Banana", "price": 0.5, "quantity": 20},
            {"title": "Cherry", "price": 2.0, "quantity": 5},
        ]

    def test_1(self):
        self.assert_expected(self.folder.t, "test_1.pt")

    def test_2(self):
        self.assert_expected(self.folder.t, "test_2.pt")

    def test_3(self):
        self.assert_expected(self.folder.t, "test_3.pt")

    def testSimpleLoop(self):
        self.assert_expected(
            self.folder.t, "test_simple_loop.pt", getProducts=self.getProducts
        )

    def testFancyLoop(self):
        self.assert_expected(
            self.folder.t, "test_fancy_loop.pt", getProducts=self.getProducts
        )

    def testGlobalsShadowLocals(self):
        self.assert_expected(self.folder.t, "test_globals_shadow_locals.pt")

    def testStringExpressions(self):
        self.assert_expected(self.folder.t, "test_string_expressions.pt")

    def testReplaceWithNothing(self):
        self.assert_expected(self.folder.t, "test_replace_with_nothing.pt")

    def testWithXMLHeader(self):
        self.assert_expected(self.folder.t, "test_with_xml_header.pt")

    def testNotExpression(self):
        self.assert_expected(self.folder.t, "test_not_expression.pt")

    def testPathNothing(self):
        self.assert_expected(self.folder.t, "test_path_nothing.pt")

    def testPathAlt(self):
        self.assert_expected(self.folder.t, "test_path_alt.pt")

    def testPathTraverse(self):
        from OFS.Folder import Folder as OFSFolder

        self.folder = OFSFolder()
        self.folder.laf = AqPageTemplate()
        self.folder.t = AqPageTemplate()
        self.assert_expected(self.folder.t, "test_path_traverse.pt")

    def testBatchIteration(self):
        self.assert_expected(
            self.folder.t, "test_batch_iteration.pt", getProducts=self.getProducts
        )

    def testUnicodeInserts(self):
        self.assert_expected_unicode(
            self.folder.t, "test_unicode_inserts.pt", getProducts=self.getProducts
        )

    def testI18nTranslate(self):
        self.assert_expected(
            self.folder.t, "test_i18n_translate.pt", getProducts=self.getProducts
        )

    def testImportOldStyleClass(self):
        self.assert_expected(
            self.folder.t, "test_import_old_style_class.pt", getProducts=self.getProducts
        )

    def testRepeatVariable(self):
        self.assert_expected(
            self.folder.t, "test_repeat_variable.pt", getProducts=self.getProducts
        )

    def testBooleanAttributes(self):
        self.assert_expected(self.folder.t, "test_boolean_attributes.pt")

    def testBooleanAttributesAndDefault(self):
        self.assert_expected(self.folder.t, "test_boolean_attributes_and_default.pt")

    def testInterpolationInContent(self):
        self.assert_expected(self.folder.t, "test_interpolation_in_content.pt")

    def testBadExpression(self):
        src = util.read_input("bad_expression.pt")
        self.folder.t.write(src)
        with self.assertRaises(ExpressionError):
            self.folder.t()

    def testPathAlternativesWithSpaces(self):
        self.assert_expected(self.folder.t, "test_path_alternatives_with_spaces.pt")

    def testDefaultKeywordHandling(self):
        self.assert_expected(self.folder.t, "test_default_keyword_handling.pt")

    def testSwitch(self):
        self.assert_expected(
            self.folder.t, "test_switch.pt", getProducts=self.getProducts
        )

    def test_unicode_conflict_resolution(self):
        self.assert_expected_unicode(
            self.folder.t,
            "test_unicode_conflict_resolution.pt",
            getProducts=self.getProducts,
        )

    def test_underscore_traversal(self):
        unsafe = ["_private", "__dict__", "__class__"]
        for name in unsafe:
            with self.assertRaises(NotFound):
                self.folder.t(name=name)

    def testHandleException(self):
        src = '<p tal:define="x python: 1/0">test</p>'
        self.folder.t.write(src)
        with self.assertRaises(ZeroDivisionError):
            self.folder.t()


if __name__ == "__main__":
    import sys

    unittest.main(argv=[sys.argv[0]], exit=False)