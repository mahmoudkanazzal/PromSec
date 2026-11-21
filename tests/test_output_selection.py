"""Output selection, compile repair, and public-interface preservation."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from evaluation.functional_similarity import api_preserved, public_api
from promsec.llm import LLMClient
from promsec.runner import _best_iteration_index, _generate_valid_python

BROKEN = (
    "ADMIN_PASSWORD = 'x'\n"
    "def check(value):\n"
    "    if value == ADMIN_PASSWORD:\n"
    "        return True\n"
    "    global ADMIN_PASSWORD\n"
    "    return False\n"
)
FIXED = "import os\nADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')\ndef check(value):\n    return value == ADMIN_PASSWORD\n"


class OutputSelectionTest(unittest.TestCase):
    def test_fewest_cwes_then_earliest(self):
        iterations = [{"cwe_count": 2}, {"cwe_count": 1}, {"cwe_count": 3}, {"cwe_count": 1}]
        self.assertEqual(_best_iteration_index(iterations), 1)
        self.assertEqual(_best_iteration_index([{"cwe_count": 0}]), 0)


class CompileRepairTest(unittest.TestCase):
    def test_repair_prompt_contains_rejected_program(self):
        prompts: list[str] = []

        def transport(prompt, model, temperature):
            prompts.append(prompt)
            return (BROKEN if len(prompts) == 1 else FIXED), 1, 1

        with tempfile.TemporaryDirectory() as tmp:
            llm = LLMClient("offline", cache_path=Path(tmp) / "cache.sqlite", transport=transport)
            code, rounds = _generate_valid_python("Write a password check.", llm, "tag", 2)
        self.assertEqual(code.strip(), FIXED.strip())
        self.assertEqual(rounds, 1)
        self.assertIn("Rejected program:", prompts[1])
        self.assertIn("global ADMIN_PASSWORD", prompts[1])


class PublicInterfaceTest(unittest.TestCase):
    ORIGINAL = (
        "from flask import Flask\n"
        "app = Flask(__name__)\n"
        "@app.route('/service', methods=['POST'])\n"
        "def create_service():\n"
        "    return 'ok'\n"
        "def helper(a, b):\n"
        "    return a + b\n"
    )

    def test_route_handler_rename_and_added_helper_are_allowed(self):
        candidate = (
            "from flask import Flask\n"
            "app = Flask(__name__)\n"
            "def get_db_connection():\n"
            "    return None\n"
            "@app.route('/service', methods=['POST'])\n"
            "def service_create():\n"
            "    return 'ok'\n"
            "def helper(a, b):\n"
            "    return a + b\n"
        )
        self.assertIn("route:POST /service", public_api(self.ORIGINAL))
        self.assertTrue(api_preserved(public_api(self.ORIGINAL), candidate))

    def test_removed_route_or_changed_signature_is_rejected(self):
        no_route = "def create_service():\n    return 'ok'\ndef helper(a, b):\n    return a + b\n"
        changed = self.ORIGINAL.replace("def helper(a, b)", "def helper(a)")
        self.assertFalse(api_preserved(public_api(self.ORIGINAL), no_route))
        self.assertFalse(api_preserved(public_api(self.ORIGINAL), changed))


if __name__ == "__main__":
    unittest.main()
