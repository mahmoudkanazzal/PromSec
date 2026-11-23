"""Shared test fixtures: small vulnerable programs, their fixes, and a deterministic stand-in for the LLM endpoint."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

VULN = {
    "os.system": "import os\n\n\ndef backup(name):\n    cmd = 'tar czf /backups/' + name\n    os.system(cmd)\n    return name\n",
    "shell=True": "import subprocess\n\n\ndef run(name):\n    return subprocess.call('ls ' + name, shell=True)\n",
    "yaml.load": "import yaml\n\n\ndef load(text):\n    data = yaml.load(text)\n    return data\n",
    "hard-coded password in a variable": "PASSWORD = 'hunter2'\n\n\ndef login(user, given):\n    return given == PASSWORD\n",
    "hashlib.md5": "import hashlib\n\n\ndef token(value):\n    return hashlib.md5(value.encode()).hexdigest()\n",
    "without a timeout": "import requests\n\n\ndef fetch(url):\n    response = requests.get(url)\n    return response.json()\n",
    "0.0.0.0": "from flask import Flask\napp = Flask(__name__)\n\n\n@app.route('/')\ndef index():\n    return 'ok'\n\n\nif __name__ == '__main__':\n    app.run(host='0.0.0.0')\n",
}
FIXES = [
    ("os.system(cmd)", "print(cmd)"),
    ("yaml.load(text)", "yaml.safe_load(text)"),
    ("PASSWORD = 'hunter2'", "import os\nPASSWORD = os.environ.get('APP_PASSWORD', '')"),
    ("hashlib.md5(", "hashlib.sha256("),
    ("requests.get(url)", "requests.get(url, timeout=10)"),
    ("host='0.0.0.0'", "host='127.0.0.1'"),
    ("/backups/", "./backups/"),
]


class FakeEndpoint:
    """Deterministic stand-in for the LLM endpoint (tests only)."""

    def __init__(self, interrupt_after: int | None = None):
        self.calls = 0
        self.prompts: list[str] = []
        self.interrupt_after = interrupt_after

    def __call__(self, prompt: str, model: str, temperature: float):
        self.calls += 1
        self.prompts.append(prompt)
        if self.interrupt_after is not None and self.calls > self.interrupt_after:
            raise KeyboardInterrupt("simulated kill")
        if "ORIGINAL PROGRAM:" in prompt:
            return json.dumps({"intent": "program behavior", "io_behavior": ["io"], "side_effects": [], "invariants": [],
                               "edge_cases": []}), 5, 5
        if "BEHAVIORAL CONTRACT" in prompt:
            return json.dumps({"behavior": 0.9, "io_semantics": 0.8, "side_effects": 0.9, "invariants": 0.8,
                               "edge_cases": 0.7, "confidence": 0.9, "rationale": "fake"}), 5, 5
        if prompt.startswith("Write a realistic"):
            for key, code in VULN.items():
                if key in prompt:
                    return code, 5, 5
            return "def noop():\n    return 1\n", 5, 5
        if prompt.startswith("You are a security engineer"):
            code = prompt.split("Program:\n", 1)[1].split("\n\nStatic analysis report:", 1)[0]
            for old, new in FIXES:
                code = code.replace(old, new)
            return code, 5, 5
        if prompt.startswith("Estimate a detailed prompt"):
            return "Write the program securely.", 5, 5
        if "Rejected program:" in prompt:
            return prompt.split("Rejected program:\n", 1)[1].split("\n\nReturn the complete corrected program.", 1)[0], 5, 5
        return "def fallback():\n    return 0\n", 5, 5


def package_root(tmp: Path, *, training_programs: int = 4, synth_per_scenario: int = 3) -> Path:
    """A package root with the configs, 8 training programs and no evaluation programs."""
    root = tmp / "pkg"
    shutil.copytree(ROOT / "configs", root / "configs")
    (root / "data" / "training").mkdir(parents=True)
    names = sorted(p.name for p in (ROOT / "data" / "training").glob("*.py"))
    picked = [n for n in names if "cwe-89_unsubscribe_scenario_code_sqlite" in n][:4] + [n for n in names if "dow" in n][:4]
    for name in picked:
        shutil.copy(ROOT / "data" / "training" / name, root / "data" / "training" / name)
    path = root / "configs" / "default.yaml"
    data = yaml.safe_load(path.read_text())
    data["training_data"].update(
        training_programs=training_programs, synth_per_scenario=synth_per_scenario, samples=2, rounds=2, parallel=2,
        scenarios=["cwe78_os_system", "cwe20_yaml_load", "cwe259_password_literal", "cwe327_weak_hash",
                   "cwe400_no_timeout", "cwe605_bind_all"])
    data["ggan"].update(epochs=2, negatives=4, discriminator_steps=1, holdout_fraction=0.34)
    data["ggan_s"].update(epochs=3, holdout_fraction=0.34, validation_fraction=0.34)
    path.write_text(yaml.safe_dump(data))
    return root
