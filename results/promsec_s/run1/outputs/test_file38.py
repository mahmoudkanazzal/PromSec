import unittest
import os
import sys
import tempfile
import shutil
from contextlib import contextmanager

class SecurityManager:
    def __init__(self):
        self.policy = None

    def setSecurityPolicy(self, policy):
        self.policy = policy

    def getSecurityPolicy(self):
        return self.policy

security_manager = SecurityManager()

class UnitTestSecurityPolicy:
    def __init__(self):
        self.allowed = set()

    def allow(self, permission):
        self.allowed.add(permission)

    def checkPermission(self, permission, obj):
        return permission in self.allowed

def useChameleonEngine():
    pass

class util:
    @staticmethod
    def read_input(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

class AqPageTemplate:
    def __init__(self, source=''):
        self.source = source

    def render(self, **kwargs):
        return self.source.format(**kwargs)

class AqZopePageTemplate(AqPageTemplate):
    pass

class Folder(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

@contextmanager
def temporary_security_policy(policy):
    original = security_manager.getSecurityPolicy()
    security_manager.setSecurityPolicy(policy)
    try:
        yield
    finally:
        security_manager.setSecurityPolicy(original)

class HTMLTests(unittest.TestCase):
    def setUp(self):
        self.original_policy = security_manager.getSecurityPolicy()
        self.test_policy = UnitTestSecurityPolicy()
        security_manager.setSecurityPolicy(self.test_policy)
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(self.cleanup)

    def tearDown(self):
        security_manager.setSecurityPolicy(self.original_policy)

    def cleanup(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def assert_expected(self, result, expected):
        self.assertEqual(result, expected)

    def assert_expected_unicode(self, result, expected):
        self.assertEqual(result, expected)

    def getProducts(self):
        return {}

    def test_example(self):
        template = AqPageTemplate('Hello {name}')
        output = template.render(name='World')
        self.assert_expected(output, 'Hello World')

    def test_module_traversal(self):
        security_manager.setSecurityPolicy(self.original_policy)
        template = AqZopePageTemplate('Test')
        output = template.render()
        self.assert_expected(output, 'Test')

if __name__ == '__main__':
    unittest.main()