import unittest
from chameleon import PageTemplate

class TestPageTemplates(unittest.TestCase):

    def test_render_template(self):
        template = PageTemplate('Hello, ${name}!')
        result = template({'name': 'World'})
        self.assertEqual(result, 'Hello, World!')

    def test_unicode_inserts(self):
        template = PageTemplate('Hello, ${name}!')
        result = template({'name': u'World'})
        self.assertEqual(result, 'Hello, World!')

    def test_boolean_attributes(self):
        template = PageTemplate('<input type="checkbox" checked="${checked}" />')
        result = template({'checked': True})
        self.assertEqual(result, '<input type="checkbox" checked="checked" />')

    def test_interpolation_in_content(self):
        template = PageTemplate('<p>${content}</p>')
        result = template({'content': 'Hello, World!'})
        self.assertEqual(result, '<p>Hello, World!</p>')

    def test_bad_expressions(self):
        template = PageTemplate('${1/0}')
        with self.assertRaises(ZeroDivisionError):
            template()

    def test_traversal_using_underscores(self):
        template = PageTemplate('Hello, ${context/name}!')
        result = template({'context': {'name': 'World'}})
        self.assertEqual(result, 'Hello, World!')

    def test_module_traversal(self):
        template = PageTemplate('Hello, ${module.name}!')
        result = template({'module': {'name': 'World'}})
        self.assertEqual(result, 'Hello, World!')

    def test_exception_handling(self):
        template = PageTemplate('${1/0}')
        try:
            template()
        except ZeroDivisionError as e:
            self.assertIsInstance(e, ZeroDivisionError)

if __name__ == '__main__':
    unittest.main()