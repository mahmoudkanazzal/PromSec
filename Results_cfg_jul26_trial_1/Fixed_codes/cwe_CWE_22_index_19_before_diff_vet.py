import unittest
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

class TestHTMLTemplates(unittest.TestCase):

    def read_file(self, file_path):
        with open(file_path, 'r') as file:
            return file.read()

    def write_file(self, file_path, content):
        with open(file_path, 'w') as file:
            file.write(content)

    def check_html_output(self, actual_output, expected_output):
        self.assertEqual(actual_output.strip(), expected_output.strip())

    def test_loop_template(self):
        template = PageTemplateFile('loop_template.pt')
        context = {}
        actual_output = template.pt_render(context)
        expected_output = self.read_file('loop_template_expected.html')
        self.check_html_output(actual_output, expected_output)

    def test_string_expression_template(self):
        template = PageTemplateFile('string_expression_template.pt')
        context = {}
        actual_output = template.pt_render(context)
        expected_output = self.read_file('string_expression_template_expected.html')
        self.check_html_output(actual_output, expected_output)

    def test_path_traversal_template(self):
        template = PageTemplateFile('path_traversal_template.pt')
        context = {}
        actual_output = template.pt_render(context)
        expected_output = self.read_file('path_traversal_template_expected.html')
        self.check_html_output(actual_output, expected_output)

    def test_batch_iteration_template(self):
        template = PageTemplateFile('batch_iteration_template.pt')
        context = {}
        actual_output = template.pt_render(context)
        expected_output = self.read_file('batch_iteration_template_expected.html')
        self.check_html_output(actual_output, expected_output)

    def test_boolean_attributes_template(self):
        template = PageTemplateFile('boolean_attributes_template.pt')
        context = {}
        actual_output = template.pt_render(context)
        expected_output = self.read_file('boolean_attributes_template_expected.html')
        self.check_html_output(actual_output, expected_output)

    def test_interpolation_in_content_template(self):
        template = PageTemplateFile('interpolation_in_content_template.pt')
        context = {}
        actual_output = template.pt_render(context)
        expected_output = self.read_file('interpolation_in_content_template_expected.html')
        self.check_html_output(actual_output, expected_output)

    def test_bad_expression_template(self):
        template = PageTemplateFile('bad_expression_template.pt')
        context = {}
        actual_output = template.pt_render(context)
        expected_output = self.read_file('bad_expression_template_expected.html')
        self.check_html_output(actual_output, expected_output)

    def test_underscore_traversal_template(self):
        template = PageTemplateFile('underscore_traversal_template.pt')
        context = {}
        actual_output = template.pt_render(context)
        expected_output = self.read_file('underscore_traversal_template_expected.html')
        self.check_html_output(actual_output, expected_output)

if __name__ == '__main__':
    unittest.main()