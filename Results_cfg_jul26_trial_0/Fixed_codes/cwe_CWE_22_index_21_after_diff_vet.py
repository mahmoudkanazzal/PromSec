import unittest
from chameleon import PageTemplate

class TestPageTemplates(unittest.TestCase):

    def setUp(self):
        self.template = PageTemplate("""
            <html>
                <body>
                    <h1>Hello, ${name}!</h1>
                    <p>${content}</p>
                    <input type="checkbox" checked="${is_checked}" />
                </body>
            </html>
        """)

    def tearDown(self):
        pass

    def test_render_template(self):
        result = self.template.render(name="Alice", content="Welcome to Chameleon!", is_checked=True)
        self.assertIn("Hello, Alice!", result)
        self.assertIn("Welcome to Chameleon!", result)
        self.assertIn("checked", result)

    def test_unicode_inserts(self):
        result = self.template.render(name="Bob", content=u"Unicode ☺", is_checked=False)
        self.assertIn(u"Unicode ☺", result)

    def test_boolean_attributes(self):
        result = self.template.render(name="Charlie", content="Boolean test", is_checked=False)
        self.assertNotIn("checked", result)

    def test_interpolation_in_content(self):
        result = self.template.render(name="David", content="${name}", is_checked=True)
        self.assertIn("${name}", result)

    def test_bad_expressions(self):
        with self.assertRaises(Exception):
            self.template.render(name="Eve", content="Bad expression ${}", is_checked=False)

    def test_traversal_using_underscores(self):
        result = self.template.render(name="Frank", content="Traversal test", is_checked=True)
        self.assertIn("Traversal test", result)

    def test_module_traversal(self):
        result = self.template.render(name="Grace", content="Module traversal test", is_checked=False)
        self.assertIn("Module traversal test", result)

    def test_exception_handling(self):
        with self.assertRaises(Exception):
            template = PageTemplate("""
                <html>
                    <body>
                        <h1>Hello, ${name}!</h1>
                        <p>${content}</p>
                        <input type="checkbox" checked="${is_checked}" />
                    </body>
                </html>
            """)
            template.render(name="Ivy", content="Exception test", is_checked=True)

if __name__ == '__main__':
    unittest.main()