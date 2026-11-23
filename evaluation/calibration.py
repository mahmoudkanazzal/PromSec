"""Behavioral controls with concrete input/output witnesses."""

from typing import Any

CASES: tuple[dict[str, Any], ...] = (
    {
        "name": "addition",
        "original": "def calculate(a, b):\n    return a + b\n",
        "changed": "def calculate(a, b):\n    return a - b\n",
        "arguments": [2, 3], "expected": 5, "changed_expected": -1,
    },
    {
        "name": "parity",
        "original": "def calculate(n):\n    return n % 2 == 0\n",
        "changed": "def calculate(n):\n    return n % 2 == 1\n",
        "arguments": [2], "expected": True, "changed_expected": False,
    },
    {
        "name": "clamping",
        "original": "def calculate(value, lower, upper):\n    return max(lower, min(value, upper))\n",
        "changed": "def calculate(value, lower, upper):\n    return value\n",
        "arguments": [5, 0, 3], "expected": 3, "changed_expected": 5,
    },
    {
        "name": "sorting",
        "original": "def calculate(items):\n    return sorted(items)\n",
        "changed": "def calculate(items):\n    return list(items)\n",
        "arguments": [[2, 1]], "expected": [1, 2], "changed_expected": [2, 1],
    },
)
