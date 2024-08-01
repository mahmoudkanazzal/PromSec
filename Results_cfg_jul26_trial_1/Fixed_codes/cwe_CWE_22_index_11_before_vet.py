import unittest
from unittest.mock import Mock
from my_page_template import MyPageTemplate

class TestMyPageTemplate(unittest.TestCase):

    def setUp(self):
        self.template = MyPageTemplate()

    def test_render_template(self):
        self.assertEqual(self.template.render_template(), "Hello, World!")

    def test_handle_boolean_attributes(self):
        self.assertEqual(self.template.handle_boolean_attributes(True), "checked")
        self.assertEqual(self.template.handle_boolean_attributes(False), "")

    def test_interpolation_in_content(self):
        self.assertEqual(self.template.interpolation_in_content("John"), "Hello, John!")

    def test_unicode_conflict_resolution(self):
        self.assertEqual(self.template.unicode_conflict_resolution("é"), "e")

if __name__ == '__main__':
    unittest.main()