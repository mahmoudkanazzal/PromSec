import unittest
from unittest.mock import patch
from page_template import PageTemplate
from utils import read_input_file, read_output_file, check_html_output

class TestPageTemplate(unittest.TestCase):

    def setUp(self):
        self.template = PageTemplate()

    def tearDown(self):
        pass

    @patch('page_template.SecurityPolicy')
    def test_render_template(self, mock_security_policy):
        input_data = read_input_file('input.html')
        expected_output = read_output_file('output.html')
        
        rendered_output = self.template.render_template(input_data)
        
        self.assertEqual(rendered_output, expected_output)

    @patch('page_template.SecurityPolicy')
    def test_handle_expressions(self, mock_security_policy):
        input_data = "Hello {{ name }}"
        expected_output = "Hello John"
        
        rendered_output = self.template.render_template(input_data, {'name': 'John'})
        
        self.assertEqual(rendered_output, expected_output)

    @patch('page_template.SecurityPolicy')
    def test_attribute_rendering(self, mock_security_policy):
        input_data = "<div class='{{ class }}'>Hello</div>"
        expected_output = "<div class='important'>Hello</div>"
        
        rendered_output = self.template.render_template(input_data, {'class': 'important'})
        
        self.assertEqual(rendered_output, expected_output)

    @patch('page_template.SecurityPolicy')
    def test_interpolation(self, mock_security_policy):
        input_data = "My name is {{ first_name }} {{ last_name }}"
        expected_output = "My name is John Doe"
        
        rendered_output = self.template.render_template(input_data, {'first_name': 'John', 'last_name': 'Doe'})
        
        self.assertEqual(rendered_output, expected_output)

    @patch('page_template.SecurityPolicy')
    def test_error_handling(self, mock_security_policy):
        input_data = "Hello {{ name }}"
        
        with self.assertRaises(KeyError):
            self.template.render_template(input_data)

if __name__ == '__main__':
    unittest.main()