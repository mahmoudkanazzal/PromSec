import unittest
from jinja2 import Environment, FileSystemLoader

class HTMLTests(unittest.TestCase):

    def setUp(self):
        self.env = Environment(loader=FileSystemLoader('templates/'))

    def test_template_rendering(self):
        template = self.env.get_template('template.html')
        output = template.render()
        self.assertEqual(output, '<html><body>Hello World!</body></html>')

    def test_loops(self):
        template = self.env.get_template('loop.html')
        output = template.render(items=['item1', 'item2', 'item3'])
        self.assertEqual(output, '<ul><li>item1</li><li>item2</li><li>item3</li></ul>')

    def test_string_expressions(self):
        template = self.env.get_template('string.html')
        output = template.render(name='Alice')
        self.assertEqual(output, 'Hello, Alice!')

    def test_path_traversal(self):
        template = self.env.get_template('path.html')
        output = template.render()
        self.assertEqual(output, 'templates/path.html')

    def test_batch_iteration(self):
        template = self.env.get_template('batch.html')
        output = template.render(items=['item1', 'item2', 'item3'])
        self.assertEqual(output, 'item1, item2, item3')

    def test_unicode_inserts(self):
        template = self.env.get_template('unicode.html')
        output = template.render(name='Alice')
        self.assertEqual(output, 'Hello, Alice!')

    def test_boolean_attributes(self):
        template = self.env.get_template('boolean.html')
        output = template.render(active=True)
        self.assertEqual(output, '<button class="active">Click me</button>')

    def test_interpolation_in_content(self):
        template = self.env.get_template('interpolation.html')
        output = template.render(name='Alice')
        self.assertEqual(output, '<p>Hello, Alice!</p>')

    def test_exception_handling(self):
        template = self.env.get_template('exception.html')
        output = template.render()
        self.assertEqual(output, 'An error occurred')

if __name__ == '__main__':
    unittest.main()