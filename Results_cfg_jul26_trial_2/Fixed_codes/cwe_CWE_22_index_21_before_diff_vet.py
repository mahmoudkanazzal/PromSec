import unittest
from myapp import AqPageTemplate, Folder

class HTMLTests(unittest.TestCase):

    def setUp(self):
        self.folder = Folder()

    def tearDown(self):
        pass

    def test_template_rendering(self):
        template = AqPageTemplate("<html><body>Hello, ${name}!</body></html>")
        result = template.render({'name': 'Alice'})
        self.assertEqual(result, "<html><body>Hello, Alice!</body></html>")

    def test_loops(self):
        template = AqPageTemplate("<ul tal:repeat='item items'><li>${item}</li></ul>")
        result = template.render({'items': ['apple', 'banana', 'cherry']})
        self.assertEqual(result, "<ul><li>apple</li><li>banana</li><li>cherry</li></ul>")

    def test_string_expressions(self):
        template = AqPageTemplate("<p>${'Hello, ' + name + '!'}</p>")
        result = template.render({'name': 'Bob'})
        self.assertEqual(result, "<p>Hello, Bob!</p>")

    def test_path_traversal(self):
        template = AqPageTemplate("<p>${folder.title}</p>")
        self.folder.title = "My Folder"
        result = template.render({'folder': self.folder})
        self.assertEqual(result, "<p>My Folder</p>")

    def test_batch_iteration(self):
        template = AqPageTemplate("<ul tal:repeat='item items' tal:attributes='class python: item.class'><li>${item.name}</li></ul>")
        result = template.render({'items': [{'name': 'apple', 'class': 'red'}, {'name': 'banana', 'class': 'yellow'}]})
        self.assertEqual(result, "<ul><li class='red'>apple</li><li class='yellow'>banana</li></ul>")

    def test_unicode_inserts(self):
        template = AqPageTemplate("<p>${u'Hello, 世界!'}</p>")
        result = template.render({})
        self.assertEqual(result, "<p>Hello, 世界!</p>")

    def test_boolean_attributes(self):
        template = AqPageTemplate("<input type='checkbox' tal:attributes='checked python: True'/>")
        result = template.render({})
        self.assertEqual(result, "<input type='checkbox' checked>")

    def test_interpolation_in_content(self):
        template = AqPageTemplate("<p>${'Hello, ' + name + '!'}</p>")
        result = template.render({'name': 'Charlie'})
        self.assertEqual(result, "<p>Hello, Charlie!</p>")

    def test_exception_handling(self):
        template = AqPageTemplate("<p>${1/0}</p>")
        with self.assertRaises(ZeroDivisionError):
            template.render({})

if __name__ == '__main__':
    unittest.main()