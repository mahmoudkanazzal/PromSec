import unittest
from chameleon import PageTemplate
from chameleon.astutil import Symbol
from chameleon.zpt import security

class CustomSecurityPolicy(security.SecurityPolicy):
    def __init__(self):
        super(CustomSecurityPolicy, self).__init__()

    def validate(self, expression):
        return True

class TestPageTemplates(unittest.TestCase):
    def setUp(self):
        self.security_policy = CustomSecurityPolicy()

    def test_render_template(self):
        template = PageTemplate('<h1>Hello ${name}</h1>', security_policy=self.security_policy)
        result = template({'name': 'World'})
        self.assertEqual(result, '<h1>Hello World</h1>')

    def test_unicode_inserts(self):
        template = PageTemplate('<p>${unicode_text}</p>', security_policy=self.security_policy)
        result = template({'unicode_text': u'Unicode ☺'})
        self.assertEqual(result, '<p>Unicode ☺</p>')

    def test_boolean_attributes(self):
        template = PageTemplate('<input type="checkbox" checked="${is_checked}" />', security_policy=self.security_policy)
        result = template({'is_checked': True})
        self.assertEqual(result, '<input type="checkbox" checked="checked" />')

    def test_handle_exceptions(self):
        template = PageTemplate('<p>${undefined_variable}</p>', security_policy=self.security_policy)
        with self.assertRaises(NameError):
            result = template()

if __name__ == '__main__':
    unittest.main()