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

# promsec    the gGAN trained with the paper's objective; its selected statements reach the LLM.
# promsec-s  extension: the supervised gGAN; selected statements and a proposed fix each reach the LLM.
# none       ablation: the same loop without a gGAN.
GUIDANCE_MODES = ("promsec", "promsec-s", "none")

DEFAULTS = {
    "run": {"name": "promsec", "root": "runs"},
    "data": {"training_dir": "data/training", "test_dir": "data/test", "test_limit": None},
    "llm": {
        "model_env": "PROMSEC_LLM_MODEL",
        "api_key_env": "OPENAI_API_KEY",
        "base_url_env": "PROMSEC_LLM_BASE_URL",
        "temperature": 0.0,
        "max_retries": 2,
        "syntax_repair_attempts": 3,
        "cache_path": "cache/llm_cache.sqlite",
    },
    "loop": {"max_iterations": 20, "parallel_programs": 8},
    "guidance": {"mode": "promsec"},
    "ggan": {
        "model_dir": "models/promsec",
        "seed": 0,
        "holdout_fraction": 0.2,
        "epochs": 7,
        "learning_rate": 0.001,
        "discriminator_steps": 5,
        "alpha": 1.0,
        "beta": 10.0,
        "lambda_adv": 0.01,
        "security_margin": 0.25,
        "negatives": 16,
        "top_k": 5,
        "min_change": 0.1,
    },
    "ggan_s": {
        "model_dir": "models/promsec_s",
        "seed": 0,
        "holdout_fraction": 0.2,
        "validation_fraction": 0.15,
        "epochs": 40,
        "adv_weight": 0.1,
        "top_k": 5,
        "threshold": 0.5,
        "leave_one_scenario_out": True,
    },
    "training_data": {
        "run_dir": "runs/training_data",
        "states_dir": "data/states",
        "training_programs": 100,
        "synth_per_scenario": 10,
        "scenarios": [],
        "samples": 2,
        "rounds": 3,
        "temperature": 0.7,
        "laaj_min": 0.6,
        "parallel": 8,
        "cpu_workers": 8,
    },
    "judge": {
        "model_env": "PROMSEC_JUDGE_MODEL",
        "api_key_env": "OPENAI_API_KEY",
        "base_url_env": "PROMSEC_JUDGE_BASE_URL",
        "temperature": 0.0,
        "max_retries": 2,
        "stability_check": True,
        "calibration_limit": 4,
    },
    "supervisor": {
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


def _read_yaml(path: Path, package_root: Path, seen: tuple[Path, ...] = ()) -> dict:
    """Read a YAML configuration; a top-level ``base`` key names a configuration it extends."""
    if path in seen:
        raise ValueError(f"Configuration base cycle at {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Configuration root must be a mapping: {path}")
    base = data.pop("base", None)
    if base is None:
        return data
    base_path = Path(base)
    if not base_path.is_absolute():
        base_path = package_root / base_path
    return _merge(_read_yaml(base_path.resolve(), package_root, seen + (path,)), data)


def load_config(path: str | Path | None = None, root: str | Path | None = None) -> dict:
    """Load a YAML configuration over the defaults and validate it."""
    package_root = Path(root or Path.cwd()).resolve()
    user = {}
    if path is not None:
        config_path = Path(path)
        if not config_path.is_absolute():
            config_path = package_root / config_path
        user = _read_yaml(config_path.resolve(), package_root)
    cfg = _merge(DEFAULTS, user)
    cfg["_root"] = str(package_root)
    validate_config(cfg)
    return cfg


def resolve_path(cfg: dict, value: str) -> Path:
    """Resolve ``value`` relative to the package root unless it is absolute."""
    path = Path(value)
    return path if path.is_absolute() else Path(cfg["_root"]) / path


def _positive(cfg: dict, section: str, keys: tuple[str, ...]) -> None:
    for key in keys:
        value = float(cfg[section][key])
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{section}.{key} must be finite and positive")


def _nonnegative(cfg: dict, section: str, keys: tuple[str, ...]) -> None:
    for key in keys:
        value = float(cfg[section][key])
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{section}.{key} must be finite and nonnegative")


def validate_config(cfg: dict) -> None:
    """Raise ``ValueError`` if a configuration value is missing or out of range."""
    if cfg["guidance"].get("mode") not in GUIDANCE_MODES:
        raise ValueError("guidance.mode must be one of: " + ", ".join(GUIDANCE_MODES))
    if int(cfg["loop"]["max_iterations"]) < 1:
        raise ValueError("loop.max_iterations must be at least 1")
    if int(cfg["loop"].get("parallel_programs", 1)) < 1:
        raise ValueError("loop.parallel_programs must be at least 1")
    limit = cfg["data"].get("test_limit")
    if limit is not None and int(limit) < 1:
        raise ValueError("data.test_limit must be null or at least 1")
    if int(cfg["llm"].get("max_retries", 0)) < 0 or int(cfg["judge"].get("max_retries", 0)) < 0:
        raise ValueError("max_retries cannot be negative")
    if int(cfg["llm"].get("syntax_repair_attempts", 0)) < 0:
        raise ValueError("llm.syntax_repair_attempts cannot be negative")
    for section in ("llm", "judge"):
        _nonnegative(cfg, section, ("temperature",))
    if int(cfg["judge"]["calibration_limit"]) < 1:
        raise ValueError("judge.calibration_limit must be at least 1")

    for key in ("epochs", "discriminator_steps", "negatives", "top_k"):
        if int(cfg["ggan"][key]) < 1:
            raise ValueError(f"ggan.{key} must be at least 1")
    _positive(cfg, "ggan", ("learning_rate", "security_margin"))
    _nonnegative(cfg, "ggan", ("alpha", "beta", "lambda_adv", "min_change"))
    for key in ("epochs", "top_k"):
        if int(cfg["ggan_s"][key]) < 1:
            raise ValueError(f"ggan_s.{key} must be at least 1")
    _nonnegative(cfg, "ggan_s", ("adv_weight",))
    if not 0.0 <= float(cfg["ggan_s"]["threshold"]) <= 1.0:
        raise ValueError("ggan_s.threshold must be in [0, 1]")
    for section in ("ggan", "ggan_s"):
        if int(cfg[section]["seed"]) < 0:
            raise ValueError(f"{section}.seed must be nonnegative")
        fraction = float(cfg[section]["holdout_fraction"])
        if not 0.0 < fraction < 1.0:
            raise ValueError(f"{section}.holdout_fraction must be in (0, 1)")
        if not str(cfg[section].get("model_dir", "")).strip():
            raise ValueError(f"{section}.model_dir must be a nonempty path")

    t = cfg["training_data"]
    for key in ("samples", "rounds", "parallel", "cpu_workers"):
        if int(t[key]) < 1:
            raise ValueError(f"training_data.{key} must be at least 1")
    for key in ("training_programs", "synth_per_scenario"):
        if int(t[key]) < 0:
            raise ValueError(f"training_data.{key} cannot be negative")
    if not 0.0 <= float(t["laaj_min"]) <= 1.0:
        raise ValueError("training_data.laaj_min must be in [0, 1]")
    _nonnegative(cfg, "training_data", ("temperature",))

    for key in ("max_enforcement_passes", "max_judge_passes", "retry_seconds"):
        if int(cfg["supervisor"][key]) < 1:
            raise ValueError(f"supervisor.{key} must be at least 1")


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


def active_model_dir(cfg: dict) -> Path | None:
    """Checkpoint folder of the configured variant (``None`` for the ablation without a gGAN)."""
    mode = cfg["guidance"]["mode"]
    if mode == "promsec":
        return resolve_path(cfg, cfg["ggan"]["model_dir"])
    if mode == "promsec-s":
        return resolve_path(cfg, cfg["ggan_s"]["model_dir"])
    return None


def relevant_config_hash(cfg: dict) -> str:
    """Hash of every input that affects enforcement results."""
    llm = cfg["llm"]
    model_dir = active_model_dir(cfg)
    subset = {
        "data": cfg["data"],
        "loop": {k: v for k, v in cfg["loop"].items() if k != "parallel_programs"},
        "guidance": cfg["guidance"],
        "llm": llm,
        "resolved_llm_model": os.environ.get(llm.get("model_env", "")),
        "resolved_llm_base_url": os.environ.get(llm.get("base_url_env", "")),
        "generator_sha256": _file_sha256(model_dir / "generator.pt") if model_dir else None,
        "hints_sha256": _file_sha256(model_dir / "hints.json") if model_dir else None,
        "implementation": implementation_hash(cfg, [
            "promsec/runner.py", "promsec/prompts.py", "promsec/graph.py", "promsec/ggan.py", "promsec/ggan_s.py",
            "promsec/security.py", "promsec/metrics.py", "promsec/records.py", "promsec/llm.py", "promsec/config.py",
        ]),
        "dependencies": {name: installed_version(name) for name in ("bandit", "torch", "torch-geometric")},
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
