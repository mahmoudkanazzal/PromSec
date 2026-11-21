"""Training/validation split and the per-epoch training and validation losses."""

from __future__ import annotations

import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from promsec.config import load_config
from promsec.train import LOSS_KEYS, split_training_files, train_models

ROOT = Path(__file__).resolve().parents[1]


class SplitTest(unittest.TestCase):
    def test_split_is_disjoint_deterministic_and_sized(self):
        files = sorted((ROOT / "data" / "training").glob("*.py"))
        train, validation = split_training_files(files, 0.1, 0)
        self.assertEqual(len(validation), 50)
        self.assertEqual(len(train) + len(validation), len(files))
        self.assertFalse(set(train) & set(validation))
        self.assertEqual(split_training_files(files, 0.1, 0), (train, validation))
        self.assertNotEqual(split_training_files(files, 0.1, 1)[1], validation)

    def test_packaged_validation_list_matches_split(self):
        files = sorted((ROOT / "data" / "training").glob("*.py"))
        _, validation = split_training_files(files, 0.1, 0)
        listed = (ROOT / "models" / "validation_files.txt").read_text(encoding="utf-8").split()
        self.assertEqual(listed, sorted(path.name for path in validation))


@unittest.skipIf(shutil.which("bandit") is None, "Bandit is required")
class TrainingLossTest(unittest.TestCase):
    def test_epochs_log_training_and_validation_losses(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = load_config(root=ROOT)
            cfg["run"]["root"] = str(Path(tmp) / "runs")
            cfg["run"]["name"] = "train"
            cfg["training"].update(limit=20, epochs=2, negatives=4)
            cfg["models"]["fresh_generator"] = str(Path(tmp) / "g.pt")
            cfg["models"]["fresh_discriminator"] = str(Path(tmp) / "d.pt")
            result = train_models(cfg, force=True)
            self.assertEqual((result["train_samples"], result["validation_samples"]), (18, 2))
            training_dir = Path(tmp) / "runs" / "train" / "training"
            rows = [json.loads(line) for line in (training_dir / "training.jsonl").read_text().splitlines()]
            self.assertEqual([row["epoch"] for row in rows], [1, 2])
            for row in rows:
                for key in LOSS_KEYS:
                    self.assertIn("train_" + key, row)
                    self.assertIn("val_" + key, row)
            with (training_dir / "training_curves.csv").open(newline="") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 2)
            self.assertGreater((training_dir / "training_curves.png").stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
