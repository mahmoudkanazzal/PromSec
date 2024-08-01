import unittest
from chameleon import PageTemplate

def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def write_file(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)

class TestPageTemplates(unittest.TestCase):

    def setUp(self):
        self.security_policy = PageTemplate.security_policy
        PageTemplate.security_policy = None

    def tearDown(self):
        PageTemplate.security_policy = self.security_policy

    def test_render_html_template(self):
        template = PageTemplate(read_file('templates/template1.pt'))
        rendered = template()
        expected = read_file('expected_outputs/template1.html')
        self.assertEqual(rendered, expected)

    def test_unicode_inserts(self):
        template = PageTemplate(read_file('templates/template2.pt'))
        rendered = template(name='Alice')
        expected = read_file('expected_outputs/template2.html')
        self.assertEqual(rendered, expected)

    def test_batch_iteration(self):
        template = PageTemplate(read_file('templates/template3.pt'))
        rendered = template(items=['apple', 'banana', 'cherry'])
        expected = read_file('expected_outputs/template3.html')
        self.assertEqual(rendered, expected)

    def test_boolean_attributes(self):
        template = PageTemplate(read_file('templates/template4.pt'))
        rendered = template(disabled=True)
        expected = read_file('expected_outputs/template4.html')
        self.assertEqual(rendered, expected)

    def test_interpolation_in_content(self):
        template = PageTemplate(read_file('templates/template5.pt'))
        rendered = template(name='Bob')
        expected = read_file('expected_outputs/template5.html')
        self.assertEqual(rendered, expected)

    def test_path_alternatives(self):
        template = PageTemplate(read_file('templates/template6.pt'))
        rendered = template()
        expected = read_file('expected_outputs/template6.html')
        self.assertEqual(rendered, expected)

if __name__ == '__main__':
    unittest.main()