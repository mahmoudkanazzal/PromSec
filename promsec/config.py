"""Run configuration: defaults, loading, validation, and identity hashes."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from importlib import metadata
from pathlib import Path

import yaml


DEFAULTS = {
    "run": {"name": "default", "root": "runs"},
    "data": {"training_dir": "data/training", "test_dir": "data/test", "test_limit": None},
    "models": {
        "pretrained_generator": "models/trained_generator_cfg.pt",
        "pretrained_discriminator": "models/trained_discriminator_cfg.pt",
        "fresh_generator": "models/fresh_generator_cfg.pt",
        "fresh_discriminator": "models/fresh_discriminator_cfg.pt",
    },
    "llm": {
        "model_env": "PROMSEC_LLM_MODEL",
        "api_key_env": "OPENAI_API_KEY",
        "base_url_env": "PROMSEC_LLM_BASE_URL",
        "temperature": 0.0,
        "max_retries": 2,
        "syntax_repair_attempts": 3,
        "cache_path": "cache/llm_cache.sqlite",
    },
    "loop": {"max_iterations": 20},
    "guidance": {"top_k": 5, "min_abs_change": 0.1},
    "judge": {
        "model_env": "PROMSEC_JUDGE_MODEL",
        "api_key_env": "OPENAI_API_KEY",
        "base_url_env": "PROMSEC_JUDGE_BASE_URL",
        "temperature": 0.0,
        "max_retries": 2,
        "stability_check": True,
        "calibration_limit": 4,
    },
    "training": {
        "train_from_scratch": 0,
        "seed": 0,
        "epochs": 7,
        "learning_rate": 0.001,
        "discriminator_steps": 5,
        "limit": 500,
        "validation_fraction": 0.1,
        "resume": True,
        "alpha": 1.0,
        "beta": 10.0,
        "lambda_adv": 0.01,
        "security_margin": 0.25,
        "negatives": 16,
        "label_workers": 8,
    },
    "supervisor": {
        "max_training_passes": 3,
        "max_enforcement_passes": 3,
        "max_judge_passes": 3,
        "retry_seconds": 60,
    },
}


def _merge(base: dict, update: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in (update or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def _select_active_models(cfg: dict) -> None:
    """Resolve the model pair used by enforcement."""
    models = cfg["models"]
    mode = int(cfg["training"].get("train_from_scratch", 0))
    if mode == 1:
        models["generator"] = models["fresh_generator"]
        models["discriminator"] = models["fresh_discriminator"]
    else:
        models["generator"] = models["pretrained_generator"]
        models["discriminator"] = models["pretrained_discriminator"]


def load_config(path: str | Path | None = None, root: str | Path | None = None) -> dict:
    """Load a YAML configuration over the defaults, resolve the active checkpoints, and validate it."""
    package_root = Path(root or Path.cwd()).resolve()
    user = {}
    if path is not None:
        config_path = Path(path)
        if not config_path.is_absolute():
            config_path = package_root / config_path
        with config_path.open("r", encoding="utf-8") as handle:
            user = yaml.safe_load(handle) or {}
        if not isinstance(user, dict):
            raise ValueError("Configuration root must be a mapping")
    cfg = _merge(DEFAULTS, user)
    cfg["_root"] = str(package_root)
    _select_active_models(cfg)
    validate_config(cfg)
    return cfg


def resolve_path(cfg: dict, value: str) -> Path:
    """Resolve ``value`` relative to the package root unless it is absolute."""
    path = Path(value)
    return path if path.is_absolute() else Path(cfg["_root"]) / path


def validate_config(cfg: dict) -> None:
    """Raise ``ValueError`` if a configuration value is out of range."""
    if int(cfg["loop"]["max_iterations"]) < 1:
        raise ValueError("loop.max_iterations must be at least 1")
    limit = cfg["data"].get("test_limit")
    if limit is not None and int(limit) < 1:
        raise ValueError("data.test_limit must be null or at least 1")
    if int(cfg["llm"].get("max_retries", 0)) < 0 or int(cfg["judge"].get("max_retries", 0)) < 0:
        raise ValueError("max_retries cannot be negative")
    if int(cfg["llm"].get("syntax_repair_attempts", 0)) < 0:
        raise ValueError("llm.syntax_repair_attempts cannot be negative")

    if int(cfg["guidance"]["top_k"]) < 1:
        raise ValueError("guidance.top_k must be at least 1")
    min_abs_change = float(cfg["guidance"]["min_abs_change"])
    if not math.isfinite(min_abs_change) or min_abs_change < 0:
        raise ValueError("guidance.min_abs_change must be finite and nonnegative")

    train_mode = int(cfg["training"].get("train_from_scratch", 0))
    if train_mode not in (0, 1):
        raise ValueError("training.train_from_scratch must be exactly 0 or 1")
    seed = int(cfg["training"].get("seed", 0))
    if seed < 0:
        raise ValueError("training.seed must be nonnegative")
    if int(cfg["training"].get("epochs", 1)) < 1:
        raise ValueError("training.epochs must be at least 1")
    for key in ("discriminator_steps", "limit", "label_workers", "negatives"):
        if int(cfg["training"][key]) < 1:
            raise ValueError(f"training.{key} must be at least 1")
    fraction = float(cfg["training"]["validation_fraction"])
    if not math.isfinite(fraction) or not 0.0 < fraction <= 0.5:
        raise ValueError("training.validation_fraction must be in (0, 0.5]")
    for key in ("learning_rate", "security_margin"):
        value = float(cfg["training"][key])
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"training.{key} must be finite and positive")
    for key in ("alpha", "beta", "lambda_adv"):
        value = float(cfg["training"][key])
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"training.{key} must be finite and nonnegative")

    if int(cfg["judge"]["calibration_limit"]) < 1:
        raise ValueError("judge.calibration_limit must be at least 1")
    for section in ("llm", "judge"):
        value = float(cfg[section]["temperature"])
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{section}.temperature must be finite and nonnegative")

    for key in ("max_training_passes", "max_enforcement_passes", "max_judge_passes", "retry_seconds"):
        if int(cfg["supervisor"][key]) < 1:
            raise ValueError(f"supervisor.{key} must be at least 1")

    required_model_keys = (
        "pretrained_generator", "pretrained_discriminator",
        "fresh_generator", "fresh_discriminator", "generator", "discriminator",
    )
    for key in required_model_keys:
        if not str(cfg["models"].get(key, "")).strip():
            raise ValueError(f"models.{key} must be a nonempty path")


def _file_sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def implementation_hash(cfg: dict, files: list[str]) -> dict:
    """SHA-256 of each listed implementation file."""
    return {name: _file_sha256(resolve_path(cfg, name)) for name in files}


def installed_version(package: str) -> str | None:
    """Installed version of ``package``, or ``None`` if it is not installed."""
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return None


def training_config_hash(cfg: dict) -> str:
    """Hash of every input that affects training results."""
    subset = {
        "training": cfg["training"],
        "training_dir": cfg["data"]["training_dir"],
        "data_manifest_sha256": _file_sha256(resolve_path(cfg, "data/MANIFEST.csv")),
        "fresh_generator": cfg["models"]["fresh_generator"],
        "fresh_discriminator": cfg["models"]["fresh_discriminator"],
        "implementation": implementation_hash(cfg, [
            "utils.py", "promsec/model.py", "promsec/train.py", "promsec/config.py",
            "promsec/security.py", "promsec/metrics.py",
        ]),
        "dependencies": {name: installed_version(name) for name in ("bandit", "torch", "torch-geometric", "networkx", "numpy")},
    }
    raw = json.dumps(subset, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def relevant_config_hash(cfg: dict) -> str:
    """Hash of every input that affects enforcement results."""
    llm = cfg["llm"]
    subset = {
        "data": cfg["data"],
        "active_models": {
            "generator": cfg["models"]["generator"],
            "discriminator": cfg["models"]["discriminator"],
        },
        "train_from_scratch": int(cfg["training"].get("train_from_scratch", 0)),
        "loop": cfg["loop"],
        "guidance": cfg["guidance"],
        "llm": llm,
        "resolved_llm_model": os.environ.get(llm.get("model_env", "")),
        "resolved_llm_base_url": os.environ.get(llm.get("base_url_env", "")),
        "generator_sha256": _file_sha256(resolve_path(cfg, cfg["models"]["generator"])),
        "discriminator_sha256": _file_sha256(resolve_path(cfg, cfg["models"]["discriminator"])),
        "implementation": implementation_hash(cfg, [
            "utils.py", "promsec/model.py", "promsec/runner.py", "promsec/security.py",
            "promsec/metrics.py", "promsec/records.py", "promsec/llm.py", "promsec/config.py",
        ]),
        "dependencies": {name: installed_version(name) for name in ("bandit", "torch", "torch-geometric", "networkx")},
    }
    raw = json.dumps(subset, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def judge_config_hash(cfg: dict) -> str:
    """Hash of every input that affects functional-similarity results."""
    judge = cfg["judge"]
    subset = {
        "judge": judge,
        "resolved_judge_model": os.environ.get(judge.get("model_env", "")),
        "resolved_judge_base_url": os.environ.get(judge.get("base_url_env", "")),
        "implementation": implementation_hash(cfg, [
            "evaluation/functional_similarity.py", "promsec/judge.py", "promsec/config.py",
        ]),
    }
    raw = json.dumps(subset, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
