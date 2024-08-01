import unittest
from chameleon import PageTemplate

class TestHTMLTemplates(unittest.TestCase):

    def test_render_html_content(self):
        template = PageTemplate('<h1>Hello, ${name}!</h1>')
        result = template({'name': 'Alice'})
        self.assertEqual(result, '<h1>Hello, Alice!</h1>')

    def test_handle_boolean_attributes(self):
        template = PageTemplate('<input type="checkbox" checked="${checked}" />')
        result = template({'checked': True})
        self.assertEqual(result, '<input type="checkbox" checked />')

    def test_interpolation(self):
        template = PageTemplate('<p>${"Hello, " + name + "!"}</p>')
        result = template({'name': 'Bob'})
        self.assertEqual(result, '<p>Hello, Bob!</p>')

    def test_error_handling(self):
        template = PageTemplate('<h1>${1/0}</h1>')
        with self.assertRaises(ZeroDivisionError):
            template()

    def test_unicode_conflict_resolution(self):
        template = PageTemplate('<p>${text}</p>')
        result = template({'text': '日本語'})
        self.assertEqual(result, '<p>日本語</p>')

if __name__ == '__main__':
    unittest.main()