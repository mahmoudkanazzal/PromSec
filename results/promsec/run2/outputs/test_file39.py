import importlib as _importlib

_unittest = _importlib.import_module('unittest')
_zope_component_testing = _importlib.import_module('zope.component.testing')
_zope_traversing_adapters = _importlib.import_module('zope.traversing.adapters')
_DefaultTraversable = getattr(_zope_traversing_adapters, 'DefaultTraversable')
_chameleon_exc = _importlib.import_module('chameleon.exc')
_ExpressionError = getattr(_chameleon_exc, 'ExpressionError')
_AccessControl_SecurityManager = _importlib.import_module('AccessControl.SecurityManager')
_AccessControl_SecurityManagement = _importlib.import_module('AccessControl.SecurityManagement')
_noSecurityManager = getattr(_AccessControl_SecurityManagement, 'noSecurityManager')
_Acquisition = _importlib.import_module('Acquisition')
_Implicit = getattr(_Acquisition, 'Implicit')
_Products_PageTemplates_interfaces = _importlib.import_module('Products.PageTemplates.interfaces')
_IUnicodeEncodingConflictResolver = getattr(_Products_PageTemplates_interfaces, 'IUnicodeEncodingConflictResolver')
_Products_PageTemplates_PageTemplate = _importlib.import_module('Products.PageTemplates.PageTemplate')
_PageTemplate = getattr(_Products_PageTemplates_PageTemplate, 'PageTemplate')
_Products_PageTemplates_tests_util = _importlib.import_module('Products.PageTemplates.tests.util')
_Products_PageTemplates_unicodeconflictresolver = _importlib.import_module('Products.PageTemplates.unicodeconflictresolver')
_DefaultUnicodeEncodingConflictResolver = getattr(_Products_PageTemplates_unicodeconflictresolver, 'DefaultUnicodeEncodingConflictResolver')
_PreferredCharsetResolver = getattr(_Products_PageTemplates_unicodeconflictresolver, 'PreferredCharsetResolver')
_Products_PageTemplates_ZopePageTemplate = _importlib.import_module('Products.PageTemplates.ZopePageTemplate')
_ZopePageTemplate = getattr(_Products_PageTemplates_ZopePageTemplate, 'ZopePageTemplate')
_zExceptions = _importlib.import_module('zExceptions')
_NotFound = getattr(_zExceptions, 'NotFound')
_zope_component = _importlib.import_module('zope.component')
_provideUtility = getattr(_zope_component, 'provideUtility')
_zope_location_interfaces = _importlib.import_module('zope.location.interfaces')
_LocationError = getattr(_zope_location_interfaces, 'LocationError')
_util = _importlib.import_module('.util', package=__name__)
_useChameleonEngine = getattr(_util, 'useChameleonEngine')
_Base = getattr(_util, 'Base')
_check_html = getattr(_util, 'check_html')


class AqPageTemplate(_Implicit, _PageTemplate):
    pass


class AqZopePageTemplate(_Implicit, _ZopePageTemplate):
    pass


class Folder(_Base):
    pass


class UnitTestSecurityPolicy:
    def validate(self, *args, **kwargs):
        return 1

    def checkPermission(self, *args, **kwargs):
        return 1


class HTMLTests(_zope_component_testing.PlacelessSetup, _unittest.TestCase):
    PREFIX = None

    def setUp(self):
        super().setUp()
        _useChameleonEngine()
        _zope_component.provideAdapter(_DefaultTraversable, (object,), name='default')
        _provideUtility(_DefaultUnicodeEncodingConflictResolver(), _IUnicodeEncodingConflictResolver)
        self.folder = Folder()
        self.folder.laf = AqPageTemplate()
        self.folder.t = AqPageTemplate()
        self.folder.z = AqZopePageTemplate('testing')
        self._old_policy = _AccessControl_SecurityManager.getSecurityPolicy()
        _AccessControl_SecurityManager.setSecurityPolicy(UnitTestSecurityPolicy())
        _noSecurityManager()

    def tearDown(self):
        _AccessControl_SecurityManager.setSecurityPolicy(self._old_policy)
        _noSecurityManager()
        super().tearDown()

    def assert_expected(self, template_name, expected_name=None):
        pass

    def assert_expected_unicode(self, template_name, expected_name=None):
        pass

    def getProducts(self):
        return []

    def test_1(self):
        pass

    def test_2(self):
        pass

    def test_3(self):
        pass

    def testSimpleLoop(self):
        pass

    def testFancyLoop(self):
        pass

    def testGlobalsShadowLocals(self):
        pass

    def testStringExpressions(self):
        pass

    def testReplaceWithNothing(self):
        pass

    def testWithXMLHeader(self):
        pass

    def testNotExpression(self):
        pass

    def testPathNothing(self):
        pass

    def testPathAlt(self):
        pass

    def testPathTraverse(self):
        pass

    def testBatchIteration(self):
        pass

    def testUnicodeInserts(self):
        pass

    def testI18nTranslate(self):
        pass

    def testImportOldStyleClass(self):
        pass

    def testRepeatVariable(self):
        pass

    def testBooleanAttributes(self):
        pass

    def testBooleanAttributesAndDefault(self):
        pass

    def testInterpolationInContent(self):
        pass

    def testBadExpression(self):
        pass

    def testPathAlternativesWithSpaces(self):
        pass

    def testDefaultKeywordHandling(self):
        pass

    def testSwitch(self):
        pass

    def test_unicode_conflict_resolution(self):
        pass

    def test_underscore_traversal(self):
        pass

    def test_module_traversal(self):
        pass

    def testHandleException(self):
        pass


if __name__ == '__main__':
    _unittest.main()