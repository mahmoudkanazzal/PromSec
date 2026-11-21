import unittest

from promsec.metrics import strip_code_fences


class CodeExtractionTest(unittest.TestCase):
    def test_fenced_reply(self):
        self.assertEqual(strip_code_fences("```python\nprint(1)\n```"), "print(1)")

    def test_fenced_block_after_text(self):
        reply = "Here’s the program:\n```python\nimport os\nprint(os.getcwd())\n```\nDone."
        self.assertEqual(strip_code_fences(reply), "import os\nprint(os.getcwd())")

    def test_plain_code(self):
        self.assertEqual(strip_code_fences("print(2)\n"), "print(2)")


if __name__ == "__main__":
    unittest.main()
