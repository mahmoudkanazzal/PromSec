"""Training data, training states, and both gGANs: losses, training, checkpoints, and the shipped models."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import torch

from promsec import ggan, ggan_s, states, trainingdata
from promsec.config import load_config
from tests.helpers import ROOT, VULN, FakeEndpoint, package_root

HAS_BANDIT = shutil.which("bandit") is not None


class LossTests(unittest.TestCase):
    def test_contrastive_loss_prefers_changing_flagged_statements(self):
        x = torch.zeros((4, 3))
        labels = torch.tensor([0.0, 1.0, 0.0, 0.0])
        neg_dk, neg_s = torch.tensor([0.0, 0.0]), torch.tensor([0.9, 0.9])
        on_target = x.clone()
        on_target[1] += 0.3
        off_target = x.clone()
        off_target[2] += 0.3
        good, dk_good, _ = ggan.compute_contrastive_loss(on_target, x, labels, 2.0, neg_dk, neg_s)
        bad, dk_bad, _ = ggan.compute_contrastive_loss(off_target, x, labels, 2.0, neg_dk, neg_s)
        self.assertGreater(float(dk_good), float(dk_bad))
        self.assertLess(float(good), float(bad))

    def test_adversarial_losses(self):
        self.assertLess(float(ggan.adversarial_loss(torch.tensor([0.9]))), float(ggan.adversarial_loss(torch.tensor([0.1]))))
        self.assertLess(float(ggan.discriminator_loss(torch.tensor([0.9]), torch.tensor([0.1]))),
                        float(ggan.discriminator_loss(torch.tensor([0.1]), torch.tensor([0.9]))))

    def test_selection_rules(self):
        x = torch.zeros((4, 3))
        updated = torch.tensor([[0.3, 0.3, 0.3], [0.05, 0.0, 0.0], [1.0, 1.0, 1.0], [0.2, 0.2, 0.2]])
        self.assertEqual(ggan.select_changed(x, updated, 5, 0.1), [2, 0, 3])
        self.assertEqual(ggan.select_changed(x, updated, 2, 0.1), [2, 0])
        logit = torch.tensor([3.0, -3.0, 2.0, 1.0, 0.5, 4.0, 2.5])
        self.assertEqual(ggan_s.select(logit, 3, 0.5), [5, 0, 6])
        self.assertEqual(ggan_s.select(torch.tensor([-1.0, -2.0]), 5, 0.5), [])


class ShippedModelTests(unittest.TestCase):
    """The checkpoints in models/ load, pass their hash check, and select the expected statements."""

    def test_promsec_selection(self):
        cfg = load_config(root=ROOT)
        _, marked = ggan.Selector(cfg)((ROOT / "data/test/test_file11.py").read_text())
        self.assertEqual([m["lineno"] for m in marked], [3, 7, 13, 29, 112])

    def test_promsec_s_selection_and_fixes(self):
        cfg = load_config("configs/promsec_s.yaml", root=ROOT)
        selector = ggan_s.Selector(cfg)
        code = (ROOT / "data/test/test_file11.py").read_text()
        stmts, marked = selector(code)
        self.assertEqual([m["lineno"] for m in marked], [3, 7, 13, 29, 112])
        self.assertIn("for example `yaml.safe_load`", selector.fix_text(code, stmts, marked))

    def test_tampered_checkpoint_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(ROOT / "models/promsec", Path(tmp) / "m")
            (Path(tmp) / "m" / "generator.pt").write_bytes((Path(tmp) / "m" / "generator.pt").read_bytes() + b"x")
            cfg = load_config(root=ROOT)
            cfg["ggan"]["model_dir"] = str(Path(tmp) / "m")
            with self.assertRaises(RuntimeError):
                ggan.Selector(cfg)

    def test_training_records(self):
        record = json.loads((ROOT / "models/promsec/training.json").read_text())
        self.assertEqual(record["settings"]["epochs"], len(record["history"]))
        self.assertEqual(record["settings"]["lambda_adv"], 0.01)
        record_s = json.loads((ROOT / "models/promsec_s/training.json").read_text())
        hist = record_s["training"]["history"]
        self.assertEqual(record_s["training"]["kept_epoch"], max(hist, key=lambda h: h["val_inloop_f1"])["epoch"])

    def test_states_match_their_labels(self):
        cfg = load_config(root=ROOT)
        records = states.load_states(cfg)
        self.assertGreater(len(records), 500)
        for record in records[:40]:
            x, _, _, loc, fix = states.tensors(cfg, record)
            self.assertEqual(x.shape[0], loc.shape[0])
            self.assertEqual(fix.shape[0], loc.shape[0])


class LifecycleTests(unittest.TestCase):
    def test_allowed_transitions(self):
        for table in (trainingdata.ITEM_TRANSITIONS, trainingdata.STAGE_TRANSITIONS):
            for current, targets in table.items():
                for target in targets:
                    self.assertEqual(trainingdata.transition(table, current, target), target)

    def test_invalid_transitions_raise(self):
        with self.assertRaises(trainingdata.TransitionError):
            trainingdata.transition(trainingdata.ITEM_TRANSITIONS, "ok", "running")
        with self.assertRaises(trainingdata.TransitionError):
            trainingdata.transition(trainingdata.ITEM_TRANSITIONS, "pending", "ok")
        with self.assertRaises(trainingdata.TransitionError):
            trainingdata.transition(trainingdata.STAGE_TRANSITIONS, "complete", "running")

    def test_fix_request_lists_findings(self):
        finding = {"line_number": 2, "test_id": "B605", "issue_cwe": {"id": 78}, "issue_text": "Starting a process with a shell."}
        text = trainingdata.fix_prompt("import os\nos.system(x)\n", [finding])
        self.assertIn("- Line 2: B605 (CWE-78) Starting a process with a shell. Code: `os.system(x)`", text)
        self.assertTrue(text.endswith("Return the complete fixed program."))


@unittest.skipUnless(HAS_BANDIT, "Bandit is required")
class PipelineTests(unittest.TestCase):
    """Training data -> states -> both gGANs, offline with a mock endpoint; the evaluation programs are never read."""

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("PROMSEC_LLM_MODEL", "offline-model")
        os.environ.setdefault("PROMSEC_JUDGE_MODEL", "offline-model")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = package_root(Path(cls.tmp.name))
        cls.cfg = load_config(root=cls.root)
        cls.cfg["training_data"]["states_dir"] = str(cls.root / "states")
        cls.stages = trainingdata.run(cls.cfg, transport=FakeEndpoint())
        cls.labeled = states.label_states(cls.cfg, states.collect_states(trainingdata.run_dir(cls.cfg)))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_training_data_and_states(self):
        self.assertEqual(self.stages, dict.fromkeys(trainingdata.STAGES, "complete"))
        self.assertFalse((self.root / "data" / "test").exists())
        self.assertTrue(any(r["source"] == "synth" for r in self.labeled))
        self.assertTrue(any("fix" in r for r in self.labeled))
        self.assertTrue(any(r["tests"] for r in self.labeled) and any(not r["tests"] for r in self.labeled))
        again = states.label_states(self.cfg, states.collect_states(trainingdata.run_dir(self.cfg)))
        self.assertEqual(again, self.labeled)

    def test_promsec_training_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = ggan.run_training(self.cfg, out_dir=Path(tmp) / "a")
            b = ggan.run_training(self.cfg, out_dir=Path(tmp) / "b")
            self.assertEqual(a["history"], b["history"])
            self.assertTrue((Path(tmp) / "a" / "training_curves.png").is_file())
            cfg = dict(self.cfg, ggan={**self.cfg["ggan"], "model_dir": str(Path(tmp) / "a")})
            _, marked = ggan.Selector(cfg)(VULN["os.system"])
            self.assertLessEqual(len(marked), cfg["ggan"]["top_k"])

    def test_promsec_s_training(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = ggan_s.run_training(self.cfg, out_dir=Path(tmp))
            self.assertTrue(record["leave_one_scenario_out"])
            for name in ("generator.pt", "hints.json", "meta.json", "training.json", "training_curves.png"):
                self.assertTrue((Path(tmp) / name).is_file(), name)
            cfg = dict(self.cfg, ggan_s={**self.cfg["ggan_s"], "model_dir": tmp})
            _stmts, marked = ggan_s.Selector(cfg)(VULN["os.system"])
            self.assertTrue(all("fix" in m for m in marked))


@unittest.skipUnless(HAS_BANDIT, "Bandit is required")
class ResumeTests(unittest.TestCase):
    def test_kill_and_resume_gives_identical_training_data(self):
        os.environ.setdefault("PROMSEC_LLM_MODEL", "offline-model")
        os.environ.setdefault("PROMSEC_JUDGE_MODEL", "offline-model")
        with tempfile.TemporaryDirectory() as tmp:
            clean = package_root(Path(tmp) / "clean")
            trainingdata.run(load_config(root=clean), transport=FakeEndpoint())
            killed = package_root(Path(tmp) / "killed")
            with self.assertRaises(KeyboardInterrupt):
                trainingdata.run(load_config(root=killed), transport=FakeEndpoint(interrupt_after=30))
            trainingdata.run(load_config(root=killed), transport=FakeEndpoint())
            for stage in trainingdata.STAGES:
                a = {p.name: json.loads(p.read_text()) for p in (clean / "runs/training_data" / stage).glob("*.json")}
                b = {p.name: json.loads(p.read_text()) for p in (killed / "runs/training_data" / stage).glob("*.json")}
                self.assertEqual(set(a), set(b))
                for name in a:
                    for record in (a[name], b[name]):
                        record.pop("timestamp", None)
                        record.pop("retries", None)
                    self.assertEqual(a[name], b[name], name)


if __name__ == "__main__":
    unittest.main()
