import os
import unittest
from jinja2 import Template

class TestPageTemplates(unittest.TestCase):

    def test_render_template_with_name(self):
        os.environ['SECRET_KEY'] = 'my_secret_key'
        template = Template("Hello, {{ name }}!")
        rendered_output = template.render(name='Alice')
        self.assertEqual(rendered_output, "Hello, Alice!")

    def test_render_template_with_number(self):
        os.environ['SECRET_KEY'] = 'my_secret_key'
        template = Template("The number is: {{ number }}")
        rendered_output = template.render(number=42)
        self.assertEqual(rendered_output, "The number is: 42")

    def test_render_template_with_list(self):
        os.environ['SECRET_KEY'] = 'my_secret_key'
        template = Template("Items: {% for item in items %}{{ item }}, {% endfor %}")
        rendered_output = template.render(items=['apple', 'banana', 'cherry'])
        self.assertEqual(rendered_output, "Items: apple, banana, cherry, ")

if __name__ == '__main__':
    unittest.main()