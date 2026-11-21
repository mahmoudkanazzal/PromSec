"""gGAN training (Algorithm 1)."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import torch
import torch.nn.functional as F
import torch.optim as optim

from utils import (
    bandit_findings,
    cfg_to_pyg_data,
    generate_cfg_from_source,
    load_original_code,
    node_change_scores,
    security_node_labels,
)

from .config import installed_version, resolve_path, training_config_hash
from .io import append_jsonl, atomic_write_json, atomic_write_text, sha256_text
from .model import Discriminator, Generator
from .runner import _device, _device_summary
from .security import SecurityAnalysisError

_EPS = 1e-7


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _training_dir(cfg: dict) -> Path:
    return resolve_path(cfg, cfg["run"]["root"]) / cfg["run"]["name"] / "training"


def _fresh_paths(cfg: dict) -> tuple[Path, Path]:
    return (
        resolve_path(cfg, cfg["models"]["fresh_generator"]),
        resolve_path(cfg, cfg["models"]["fresh_discriminator"]),
    )


def _atomic_torch_save(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    os.close(fd)
    try:
        torch.save(value, tmp)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def graph_embedding(x: torch.Tensor) -> torch.Tensor:
    """Graph-level embedding: mean of the node feature rows."""
    return x.mean(dim=0)


def aligned_similarity(x: torch.Tensor, updated_x: torch.Tensor) -> torch.Tensor:
    """S_i: one minus the mean node change score between g_i and g_hat_i."""
    return 1.0 - node_change_scores(x, updated_x).mean()


def surrogate_cwe_reduction(x: torch.Tensor, updated_x: torch.Tensor, labels: torch.Tensor, cwe_count: float, margin: float) -> torch.Tensor:
    """Differentiable surrogate of Delta k_i = k(c_i) - k(c_hat_i)."""
    labels = labels.to(device=x.device, dtype=x.dtype).reshape(-1)
    if labels.numel() != int(x.shape[0]):
        raise ValueError("Security labels do not match the graph node count")
    if float(labels.sum()) == 0.0:
        return torch.zeros((), dtype=x.dtype, device=x.device)
    change = node_change_scores(x, updated_x)
    addressed = (labels * torch.clamp(change / margin, max=1.0)).sum() / labels.sum()
    return float(cwe_count) * addressed


def compute_contrastive_loss(
    updated_x: torch.Tensor,
    x: torch.Tensor,
    labels: torch.Tensor,
    cwe_count: float,
    negative_delta_k: torch.Tensor,
    negative_similarity: torch.Tensor,
    alpha: float = 1.0,
    beta: float = 10.0,
    margin: float = 0.25,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Contrastive loss (Eqs. 4-5). Returns the loss, dk_i, and S_i."""
    delta_k = surrogate_cwe_reduction(x, updated_x, labels, cwe_count, margin)
    similarity = aligned_similarity(x, updated_x)
    z_positive = alpha * delta_k + beta * similarity
    z_negative = alpha * negative_delta_k.to(x) + beta * negative_similarity.to(x)
    scores = torch.cat([z_positive.reshape(1), z_negative.reshape(-1)])
    loss = -(z_positive - torch.logsumexp(scores, dim=0))
    return loss, delta_k, similarity


def adversarial_loss(fake_probabilities: torch.Tensor) -> torch.Tensor:
    """Eq. (3): L_adv = -E[log D(G(g))]."""
    return -torch.log(fake_probabilities + _EPS).mean()


def discriminator_loss(real_probabilities: torch.Tensor, fake_probabilities: torch.Tensor) -> torch.Tensor:
    """Eq. (6): L_D = -E[log D(g)] - E[log(1 - D(G(g)))]."""
    return -torch.log(real_probabilities + _EPS).mean() - torch.log(1.0 - fake_probabilities + _EPS).mean()


def load_security_findings(files: list[Path], cache_path: Path, workers: int = 8) -> dict[str, dict]:
    """Return Bandit finding lines and k(c) per training program."""
    cache: dict[str, dict] = {}
    if cache_path.is_file():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            cache = {}
    scanner = "bandit-" + str(installed_version("bandit"))
    sources = {path: load_original_code(path) for path in files}
    keys = {path: scanner + ":" + sha256_text(sources[path]) for path in files}
    missing = [path for path in files if not isinstance(cache.get(keys[path]), dict)]

    def scan(path: Path) -> tuple[str, dict]:
        try:
            lines, cwe_count = bandit_findings(sources[path])
        except (SecurityAnalysisError, SyntaxError, ValueError) as exc:
            raise RuntimeError(f"Bandit could not analyze training program {path.name}: {exc}") from exc
        return keys[path], {"lines": lines, "cwe_count": cwe_count}

    if missing:
        with ThreadPoolExecutor(max_workers=max(1, int(workers))) as pool:
            for key, row in pool.map(scan, missing):
                cache[key] = row
        atomic_write_json(cache_path, cache)
    return {path.name: cache[keys[path]] for path in files}


def split_training_files(files: list[Path], fraction: float, seed: int) -> tuple[list[Path], list[Path]]:
    """Deterministic split of the training programs into training and validation sets."""
    if len(files) < 2:
        raise RuntimeError("At least two training programs are needed for a training/validation split")
    ranked = sorted(files, key=lambda path: hashlib.sha256(f"{seed}:{path.name}".encode()).hexdigest())
    count = min(len(files) - 1, max(1, round(fraction * len(files))))
    validation = set(ranked[:count])
    return [path for path in files if path not in validation], [path for path in files if path in validation]


def _sample_losses(sample: dict, generator, discriminator, device, negative_delta_k, negative_similarity,
                   alpha: float, beta: float, lambda_adv: float, margin: float) -> dict[str, torch.Tensor]:
    """Loss terms for one graph, without parameter updates."""
    data = sample["data"].to(device)
    x, edge_index = data.x, data.edge_index
    updated_x, _ = generator(x, edge_index)
    loss_c, delta_k, similarity = compute_contrastive_loss(
        updated_x, x, sample["labels"], sample["cwe_count"], negative_delta_k, negative_similarity,
        alpha=alpha, beta=beta, margin=margin,
    )
    loss_adv = adversarial_loss(discriminator(updated_x, edge_index))
    return {
        "generator_loss": loss_c + lambda_adv * loss_adv,
        "contrastive_loss": loss_c,
        "adversarial_loss": loss_adv,
        "discriminator_loss": discriminator_loss(discriminator(x, edge_index), discriminator(updated_x, edge_index)),
        "delta_k_surrogate": delta_k,
        "similarity": similarity,
    }


def _last_log_row(log_path: Path) -> dict:
    """Most recent epoch row of the training log."""
    rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return max(rows, key=lambda row: int(row["epoch"]))


LOSS_KEYS = ("generator_loss", "discriminator_loss", "contrastive_loss", "adversarial_loss", "delta_k_surrogate", "similarity")


def _epoch_line(row: dict, epochs: int) -> str:
    def part(prefix: str) -> str:
        return (f"L_G {row[prefix + 'generator_loss']:.4f}  L_D {row[prefix + 'discriminator_loss']:.4f}  "
                f"contrastive {row[prefix + 'contrastive_loss']:.4f}  dk {row[prefix + 'delta_k_surrogate']:.3f}  "
                f"S {row[prefix + 'similarity']:.3f}")
    return f"epoch {row['epoch']}/{epochs}  |  train: {part('train_')}  |  validation: {part('val_')}"


def write_training_curves(log_path: Path, out_dir: Path) -> dict[str, str]:
    """Write the per-epoch training and validation losses as CSV and as a figure."""
    import csv

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows_by_epoch: dict[int, dict] = {}
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if "val_generator_loss" in row:
            rows_by_epoch[int(row["epoch"])] = row
    rows = [rows_by_epoch[e] for e in sorted(rows_by_epoch)]
    if not rows:
        raise RuntimeError(f"No per-epoch losses found in {log_path}")

    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "training_curves.csv"
    fields = ["epoch"] + [f"{split}_{key}" for split in ("train", "val") for key in LOSS_KEYS]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    from matplotlib import font_manager

    installed = {font.name for font in font_manager.fontManager.ttflist}
    family = next((name for name in ("Calibri", "Carlito") if name in installed), None)
    if family:
        plt.rcParams["font.family"] = family
    panels = (
        ("generator_loss", "Generator loss $L_G$"),
        ("discriminator_loss", "Discriminator loss $L_D$"),
        ("contrastive_loss", "Contrastive loss"),
    )
    fig = plt.figure(figsize=(9, 6.6))
    grid = fig.add_gridspec(2, 4, hspace=0.45, wspace=0.6)
    axes = [fig.add_subplot(grid[0, 0:2]), fig.add_subplot(grid[0, 2:4]), fig.add_subplot(grid[1, 1:3])]
    epochs = [row["epoch"] for row in rows]
    for ax, (key, title) in zip(axes, panels):
        ax.plot(epochs, [row["train_" + key] for row in rows], marker="o", color="#3b6fb6", label="Training")
        ax.plot(epochs, [row["val_" + key] for row in rows], marker="s", color="#d9822b", label="Validation")
        ax.set_title(title)
        ax.set_xlabel("Epoch")
        ax.set_xticks(epochs)
        ax.grid(alpha=0.3)
    axes[0].legend(frameon=False)
    png_path = out_dir / "training_curves.png"
    fig.savefig(png_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return {"training_curves_csv": str(csv_path), "training_curves_png": str(png_path)}


def training_status(cfg: dict) -> dict:
    """Completion state of fresh training for the current configuration."""
    train_dir = _training_dir(cfg)
    complete_path = train_dir / "complete.json"
    generator_path, discriminator_path = _fresh_paths(cfg)
    expected_hash = training_config_hash(cfg)
    status = {
        "train_from_scratch": int(cfg["training"].get("train_from_scratch", 0)),
        "training_config_hash": expected_hash,
        "complete": False,
        "generator": str(generator_path),
        "discriminator": str(discriminator_path),
    }
    if not complete_path.is_file():
        return status
    try:
        row = json.loads(complete_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return status
    if row.get("training_config_hash") != expected_hash:
        return status
    if row.get("generator_sha256") != _sha256(generator_path):
        return status
    if row.get("discriminator_sha256") != _sha256(discriminator_path):
        return status
    status.update(row)
    status["complete"] = True
    return status


def train_models(cfg: dict, *, force: bool = False) -> dict:
    """Train a fresh gGAN pair and write it to the fresh checkpoint paths."""
    if shutil.which("bandit") is None:
        raise RuntimeError("Bandit is required for training")

    settings = cfg["training"]
    train_dir = resolve_path(cfg, cfg["data"]["training_dir"])
    files = sorted(train_dir.glob("*.py"))[: int(settings.get("limit", 500))]
    if not files:
        raise RuntimeError("Training set is empty")

    seed = int(settings.get("seed", 0))
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    run_training_dir = _training_dir(cfg)
    run_training_dir.mkdir(parents=True, exist_ok=True)
    state_path = run_training_dir / "checkpoint.pt"
    log_path = run_training_dir / "training.jsonl"
    complete_path = run_training_dir / "complete.json"
    identity = training_config_hash(cfg)
    generator_path, discriminator_path = _fresh_paths(cfg)

    if force:
        state_path.unlink(missing_ok=True)
        complete_path.unlink(missing_ok=True)
        log_path.unlink(missing_ok=True)
        generator_path.unlink(missing_ok=True)
        discriminator_path.unlink(missing_ok=True)
    elif bool(settings.get("resume", True)):
        completed = training_status(cfg)
        if completed.get("complete"):
            return {**completed, "resumed_completed": True, "device": "not_reloaded"}

    device = _device()
    generator = Generator().to(device)
    discriminator = Discriminator().to(device)
    optimizer_g = optim.Adam(generator.parameters(), lr=float(settings["learning_rate"]))
    optimizer_d = optim.Adam(discriminator.parameters(), lr=float(settings["learning_rate"]))
    epochs = int(settings["epochs"])
    d_steps = int(settings["discriminator_steps"])
    alpha = float(settings["alpha"])
    beta = float(settings["beta"])
    lambda_adv = float(settings["lambda_adv"])
    margin = float(settings["security_margin"])
    num_negatives = int(settings["negatives"])
    start_epoch = 1
    resumed_epoch = 0

    if bool(settings.get("resume", True)) and state_path.is_file() and not force:
        try:
            state = torch.load(state_path, map_location=device, weights_only=False)
            if state.get("training_config_hash") == identity:
                generator.load_state_dict(state["generator"])
                discriminator.load_state_dict(state["discriminator"])
                optimizer_g.load_state_dict(state["optimizer_g"])
                optimizer_d.load_state_dict(state["optimizer_d"])
                resumed_epoch = int(state.get("epoch", 0))
                start_epoch = resumed_epoch + 1
        except (OSError, RuntimeError, KeyError, TypeError, ValueError):
            resumed_epoch = 0
            start_epoch = 1

    findings = load_security_findings(files, run_training_dir / "security_findings.json", int(settings["label_workers"]))
    _, validation_files = split_training_files(files, float(settings["validation_fraction"]), seed)
    validation_names = {path.name for path in validation_files}
    samples: list[dict] = []
    validation_samples: list[dict] = []
    for path in files:
        code = load_original_code(path)
        cfg_graph = generate_cfg_from_source(code, filename=str(path))
        (validation_samples if path.name in validation_names else samples).append(
            {
                "name": path.name,
                "code": code,
                "cfg_graph": cfg_graph,
                "data": cfg_to_pyg_data(cfg_graph),
                "labels": security_node_labels(cfg_graph, findings[path.name]["lines"]),
                "cwe_count": float(findings[path.name]["cwe_count"]),
            }
        )
    flagged_nodes = int(sum(float(sample["labels"].sum()) for sample in samples))
    embeddings = torch.stack([graph_embedding(sample["data"].x) for sample in samples])
    cwe_counts = torch.tensor([sample["cwe_count"] for sample in samples], dtype=torch.float32)
    pair_similarity = F.cosine_similarity(embeddings.unsqueeze(1), embeddings.unsqueeze(0), dim=2)

    validation_negatives = []
    for v, sample in enumerate(validation_samples):
        chosen = random.Random(f"{seed}:validation_negatives:{v}").sample(range(len(samples)), min(num_negatives, len(samples)))
        embedding = graph_embedding(sample["data"].x)
        validation_negatives.append((
            sample["cwe_count"] - cwe_counts[chosen],
            F.cosine_similarity(embedding.unsqueeze(0), embeddings[chosen], dim=1),
        ))
    print(f"gGAN training: {len(samples)} training programs, {len(validation_samples)} validation programs, "
          f"{epochs} epochs, device {device}", flush=True)

    for epoch in range(start_epoch, epochs + 1):
        generator.train()
        discriminator.train()
        totals = dict.fromkeys(LOSS_KEYS, 0.0)
        trained = 0
        order = list(range(len(samples)))
        random.Random(f"{seed}:epoch:{epoch}").shuffle(order)
        for i in order:
            sample = samples[i]
            data = sample["data"].to(device)
            x, edge_index = data.x, data.edge_index

            for _ in range(d_steps):
                optimizer_d.zero_grad()
                updated_x, _ = generator(x, edge_index)
                loss_d = discriminator_loss(discriminator(x, edge_index), discriminator(updated_x.detach(), edge_index))
                loss_d.backward()
                optimizer_d.step()

            others = [j for j in range(len(samples)) if j != i]
            negatives = random.Random(f"{seed}:negatives:{epoch}:{i}").sample(others, min(num_negatives, len(others)))
            negative_delta_k = cwe_counts[i] - cwe_counts[negatives]
            negative_similarity = pair_similarity[i, negatives]

            optimizer_g.zero_grad()
            updated_x, _ = generator(x, edge_index)
            loss_c, delta_k, similarity = compute_contrastive_loss(
                updated_x, x, sample["labels"], sample["cwe_count"], negative_delta_k, negative_similarity,
                alpha=alpha, beta=beta, margin=margin,
            )
            loss_adv = adversarial_loss(discriminator(updated_x, edge_index))
            loss_g = loss_c + lambda_adv * loss_adv
            loss_g.backward()
            optimizer_g.step()

            totals["generator_loss"] += float(loss_g.item())
            totals["discriminator_loss"] += float(loss_d.item())
            totals["contrastive_loss"] += float(loss_c.item())
            totals["adversarial_loss"] += float(loss_adv.item())
            totals["delta_k_surrogate"] += float(delta_k.detach())
            totals["similarity"] += float(similarity.detach())
            trained += 1

        generator.eval()
        discriminator.eval()
        validation_totals = dict.fromkeys(LOSS_KEYS, 0.0)
        validated = 0
        with torch.no_grad():
            for sample, (negative_delta_k, negative_similarity) in zip(validation_samples, validation_negatives):
                losses = _sample_losses(sample, generator, discriminator, device, negative_delta_k, negative_similarity,
                                        alpha, beta, lambda_adv, margin)
                for key in LOSS_KEYS:
                    validation_totals[key] += float(losses[key])
                validated += 1

        n = max(1, trained)
        m = max(1, validated)
        row: dict[str, object] = {
            "seed": seed,
            "epoch": epoch,
            **{"train_" + key: totals[key] / n for key in LOSS_KEYS},
            **{"val_" + key: validation_totals[key] / m for key in LOSS_KEYS},
            "train_samples": len(samples),
            "validation_samples": len(validation_samples),
            "flagged_nodes": flagged_nodes,
        }
        append_jsonl(log_path, row)
        print(_epoch_line(row, epochs), flush=True)
        _atomic_torch_save(
            state_path,
            {
                "training_config_hash": identity,
                "epoch": epoch,
                "generator": generator.state_dict(),
                "discriminator": discriminator.state_dict(),
                "optimizer_g": optimizer_g.state_dict(),
                "optimizer_d": optimizer_d.state_dict(),
            },
        )

    generator_path.parent.mkdir(parents=True, exist_ok=True)
    discriminator_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(generator.state_dict(), generator_path)
    torch.save(discriminator.state_dict(), discriminator_path)
    curves = write_training_curves(log_path, run_training_dir)
    validation_list = run_training_dir / "validation_files.txt"
    atomic_write_text(validation_list, "".join(name + "\n" for name in sorted(validation_names)))
    final = _last_log_row(log_path)
    result = {
        "training_config_hash": identity,
        "seed": seed,
        "epochs": epochs,
        "samples": len(files),
        "train_samples": len(samples),
        "validation_samples": len(validation_samples),
        "validation_files": str(validation_list),
        "final_train_generator_loss": final["train_generator_loss"],
        "final_val_generator_loss": final["val_generator_loss"],
        "final_train_discriminator_loss": final["train_discriminator_loss"],
        "final_val_discriminator_loss": final["val_discriminator_loss"],
        **curves,
        "resumed_from_epoch": resumed_epoch,
        "generator": str(generator_path),
        "discriminator": str(discriminator_path),
        "generator_sha256": _sha256(generator_path),
        "discriminator_sha256": _sha256(discriminator_path),
        **_device_summary(device),
    }
    atomic_write_json(complete_path, result)
    state_path.unlink(missing_ok=True)
    return {**result, "complete": True, "resumed_completed": False}
