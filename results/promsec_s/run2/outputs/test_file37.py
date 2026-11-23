import sys

try:
    from chameleon.zpt import PageTemplate as ChameleonTemplate
except Exception:
    ChameleonTemplate = None

class ExpressionError(Exception):
    pass

class NotFound(Exception):
    pass

class UnitTestSecurityPolicy:
    def __init__(self, allowed=None):
        self.allowed = set(allowed) if allowed is not None else set()
    def check_access(self, obj, name):
        if name.startswith('_') and name not in self.allowed:
            raise NotFound(name)
        return getattr(obj, name)

class Folder:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    def __getitem__(self, name):
        if name.startswith('_'):
            raise NotFound(name)
        try:
            return getattr(self, name)
        except AttributeError:
            raise NotFound(name)
    def set_private(self, name, value):
        self.__dict__[name] = value

class AqPageTemplate:
    def __init__(self, source, security_policy=None):
        self.source = source
        self.security_policy = security_policy or UnitTestSecurityPolicy()
        if ChameleonTemplate is not None:
            self.template = ChameleonTemplate(source)
        else:
            self.template = None
    def __call__(self, context=None, **options):
        try:
            safe_ctx = {}
            if context:
                safe_ctx.update(context)
            safe_ctx.update(options)
            if self.template is not None:
                return self.template(**safe_ctx)
            result = self.source
            for key, value in safe_ctx.items():
                result = result.replace('${' + key + '}', str(value))
            if '${' in result:
                raise ExpressionError("Unresolved expression")
            return result
        except (KeyError, AttributeError) as e:
            raise ExpressionError(str(e)).with_traceback(sys.exc_info()[2])

import unittest

class HTMLTests(unittest.TestCase):
    def setUp(self):
        self.folder = Folder(name='World')
        self.security = UnitTestSecurityPolicy()
        self.template1 = AqPageTemplate('Hello ${name}', self.security)
        self.template2 = AqPageTemplate('Value: ${missing}', self.security)
    def tearDown(self):
        self.folder = None
        self.security = None
        self.template1 = None
        self.template2 = None
    def test_1(self):
        output = self.template1(self.folder.__dict__)
        self.assertEqual(output, 'Hello World')
    def test_2(self):
        with self.assertRaises(ExpressionError):
            self.template2(self.folder.__dict__)
    def test_underscore_traversal(self):
        self.folder.set_private('_secret', 'hidden')
        with self.assertRaises(NotFound):
            _ = self.folder['_secret']

if __name__ == '__main__':
    unittest.main()