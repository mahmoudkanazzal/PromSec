"""The PromSec gGAN: graph generator and discriminator trained with the paper's objective.

Generator G maps a statement graph g to an updated graph G(g) with the same nodes and
edges. It is trained with

    L_G = L_contrastive + lambda * L_adv                                  (Eqs. 2-5)
    z_i = alpha * dk_i + beta * S_i

where dk_i is a differentiable surrogate of the CWE reduction (k(c_i) times the share
of Bandit-flagged statements whose features change by at least ``security_margin``),
S_i is the similarity between g_i and G(g_i) (one minus the mean node change), and the
negatives are other training graphs j with dk_ij = k(c_i) - k(c_j) and S_ij the cosine
similarity of the graph embeddings. Discriminator D separates real graphs from
generated ones (Eq. 6) and takes ``discriminator_steps`` steps per generator step.

In the PromSec loop, the statements whose nodes G changes most (at most ``top_k``,
change >= ``min_change``) are passed to the LLM for the code reconstruction.
"""

from __future__ import annotations

import hashlib
import json
import random
import time
from pathlib import Path

import torch
import torch.nn.functional as F

from . import graph as g
from . import states as st
from .config import resolve_path
from .io import atomic_write_json

_EPS = 1e-7
LOSS_KEYS = ("generator_loss", "discriminator_loss", "contrastive_loss", "adversarial_loss",
             "delta_k_surrogate", "similarity")


# --------------------------------------------------------------------------- model


class Generator(torch.nn.Module):
    """Two relational graph convolutions mapping a statement graph to an updated graph (same nodes and edges)."""

    def __init__(self, in_dim: int = g.FEATURE_DIM, hidden: int = 128):
        super().__init__()
        from torch_geometric.nn import RGCNConv

        self.conv1 = RGCNConv(in_dim, hidden, g.NUM_RELATIONS)
        self.conv2 = RGCNConv(hidden, in_dim, g.NUM_RELATIONS)

    def forward(self, x, edge_index, edge_type):
        return self.conv2(torch.relu(self.conv1(x, edge_index, edge_type)), edge_index, edge_type)


class Discriminator(torch.nn.Module):
    """Per-statement probabilities that a graph is real (Eq. 6); the losses average them."""

    def __init__(self, in_dim: int = g.FEATURE_DIM, hidden: int = 64):
        super().__init__()
        from torch_geometric.nn import RGCNConv

        self.conv1 = RGCNConv(in_dim, hidden, g.NUM_RELATIONS)
        self.conv2 = RGCNConv(hidden, 1, g.NUM_RELATIONS)

    def forward(self, x, edge_index, edge_type):
        return torch.sigmoid(self.conv2(torch.relu(self.conv1(x, edge_index, edge_type)), edge_index, edge_type))


# --------------------------------------------------------------------------- losses


def aligned_similarity(x: torch.Tensor, updated_x: torch.Tensor) -> torch.Tensor:
    """S_i: one minus the mean node change between g_i and G(g_i)."""
    return 1.0 - g.node_change_scores(x, updated_x).mean()


def surrogate_cwe_reduction(x: torch.Tensor, updated_x: torch.Tensor, labels: torch.Tensor, cwe_count: float,
                            margin: float) -> torch.Tensor:
    """Differentiable surrogate of dk_i = k(c_i) - k(c_hat_i)."""
    labels = labels.to(device=x.device, dtype=x.dtype).reshape(-1)
    if labels.numel() != int(x.shape[0]):
        raise ValueError("Security labels do not match the graph node count")
    if float(labels.sum()) == 0.0:
        return torch.zeros((), dtype=x.dtype, device=x.device)
    change = g.node_change_scores(x, updated_x)
    addressed = (labels * torch.clamp(change / margin, max=1.0)).sum() / labels.sum()
    return float(cwe_count) * addressed


def compute_contrastive_loss(updated_x: torch.Tensor, x: torch.Tensor, labels: torch.Tensor, cwe_count: float,
                             negative_delta_k: torch.Tensor, negative_similarity: torch.Tensor,
                             alpha: float = 1.0, beta: float = 10.0, margin: float = 0.25):
    """Contrastive loss (Eqs. 4-5). Returns the loss, dk_i and S_i."""
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


def select_changed(x: torch.Tensor, updated: torch.Tensor, top_k: int, min_change: float) -> list[int]:
    """The most-changed statements, at most ``top_k``, change >= ``min_change``, largest first."""
    change = g.node_change_scores(x, updated).tolist()
    ranked = sorted(range(len(change)), key=lambda i: -change[i])
    return [i for i in ranked[:top_k] if change[i] >= min_change]


# --------------------------------------------------------------------------- training


def settings(cfg: dict) -> dict:
    s = cfg["ggan"]
    return {"alpha": float(s["alpha"]), "beta": float(s["beta"]), "lambda_adv": float(s["lambda_adv"]),
            "margin": float(s["security_margin"]), "negatives": int(s["negatives"]),
            "d_steps": int(s["discriminator_steps"]), "epochs": int(s["epochs"]), "lr": float(s["learning_rate"]),
            "seed": int(s["seed"]), "top_k": int(s["top_k"]), "min_change": float(s["min_change"])}


def train(train_data: list[tuple], s: dict, device) -> tuple[Generator, list[dict]]:
    """Train with the paper's objective; ``d_steps`` discriminator steps before each generator step."""
    seed = s["seed"]
    torch.manual_seed(seed)
    gen, disc = Generator().to(device), Discriminator().to(device)
    opt_g = torch.optim.Adam(gen.parameters(), lr=s["lr"])
    opt_d = torch.optim.Adam(disc.parameters(), lr=s["lr"])
    samples = [(tuple(t.to(device) for t in tensors), rec) for tensors, rec in train_data]
    cwe_counts = torch.tensor([float(rec["cwe_count"]) for _, rec in samples], device=device)
    embeddings = torch.stack([t[0].mean(dim=0) for t, _ in samples])
    pair_similarity = F.cosine_similarity(embeddings.unsqueeze(1), embeddings.unsqueeze(0), dim=2)
    history = []
    for epoch in range(s["epochs"]):
        gen.train()
        disc.train()
        order = list(range(len(samples)))
        random.Random(f"{seed}:epoch:{epoch}").shuffle(order)
        totals = dict.fromkeys(LOSS_KEYS, 0.0)
        for i in order:
            (x, ei, et, loc, _), _ = samples[i]
            loss_d = torch.zeros((), device=device)
            for _ in range(s["d_steps"]):
                opt_d.zero_grad()
                updated = gen(x, ei, et)
                loss_d = discriminator_loss(disc(x, ei, et), disc(updated.detach(), ei, et))
                loss_d.backward()
                opt_d.step()
            others = [j for j in range(len(samples)) if j != i]
            negatives = random.Random(f"{seed}:negatives:{epoch}:{i}").sample(others, min(s["negatives"], len(others)))
            opt_g.zero_grad()
            updated = gen(x, ei, et)
            loss_c, delta_k, similarity = compute_contrastive_loss(
                updated, x, loc, float(cwe_counts[i]), cwe_counts[i] - cwe_counts[negatives],
                pair_similarity[i, negatives], alpha=s["alpha"], beta=s["beta"], margin=s["margin"])
            loss_adv = adversarial_loss(disc(updated, ei, et))
            loss_g = loss_c + s["lambda_adv"] * loss_adv
            loss_g.backward()
            opt_g.step()
            for key, value in (("generator_loss", loss_g), ("discriminator_loss", loss_d), ("contrastive_loss", loss_c),
                               ("adversarial_loss", loss_adv), ("delta_k_surrogate", delta_k), ("similarity", similarity)):
                totals[key] += float(value.detach())
        history.append({"epoch": epoch + 1, **{k: round(v / max(len(samples), 1), 4) for k, v in totals.items()}})
        print(f"   epoch {epoch + 1}/{s['epochs']}: {json.dumps(history[-1])}", flush=True)
    return gen.cpu(), history


def evaluate(gen: Generator, data: list[tuple], top_k: int, min_change: float) -> dict:
    """Localization of the selected statements against Bandit's, on original and on LLM-revised states."""
    gen.eval()
    by_kind: dict[str, tuple[list, list]] = {"all": ([], []), "original": ([], []), "rewritten": ([], [])}
    with torch.no_grad():
        for (x, ei, et, loc, _), record in data:
            chosen = set(select_changed(x, gen(x, ei, et), top_k, min_change))
            pred = [1 if i in chosen else 0 for i in range(len(loc))]
            truth = [int(v) for v in loc.tolist()]
            for kind in ("all", "original" if record["round"] == 0 else "rewritten"):
                by_kind[kind][0].extend(truth)
                by_kind[kind][1].extend(pred)
    return {kind: st.loc_scores(t, p) for kind, (t, p) in by_kind.items()}


def model_dir(cfg: dict) -> Path:
    return resolve_path(cfg, cfg["ggan"]["model_dir"])


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_training(cfg: dict, out_dir: Path | None = None) -> dict:
    """Train the PromSec gGAN on the training states; held-out localization; save model, record and curves."""
    started = time.time()
    s = settings(cfg)
    out = out_dir or model_dir(cfg)
    out.mkdir(parents=True, exist_ok=True)
    labeled = st.load_states(cfg)
    pairs = [(st.tensors(cfg, r), r) for r in labeled]
    held = st.split_groups([r["group"] for r in labeled], float(cfg["ggan"]["holdout_fraction"]), s["seed"])
    train_set = [p for p in pairs if p[1]["group"] not in held]
    test = [p for p in pairs if p[1]["group"] in held]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"== PromSec gGAN: training on {len(train_set)} states, {len(test)} held out, on {device}", flush=True)
    gen, history = train(train_set, s, device)
    torch.save(gen.state_dict(), out / "generator.pt")
    record = {"states": len(labeled), "train_states": len(train_set), "heldout_states": len(test),
              "heldout_groups": sorted(held), "settings": s, "history": history, "device": str(device),
              "heldout_localization": evaluate(gen, test, s["top_k"], s["min_change"]),
              "seconds": round(time.time() - started, 1)}
    atomic_write_json(out / "meta.json", {"top_k": s["top_k"], "min_change": s["min_change"],
                                          "feature_dim": g.FEATURE_DIM, "generator_sha256": _sha(out / "generator.pt")})
    atomic_write_json(out / "training.json", record)
    plot_training(record, out)
    return record


def plot_training(record: dict, out: Path) -> list[Path]:
    """Training curves: generator vs discriminator, the two terms of L_G, and the contrastive components
    (``training_curves``); the contrastive components alone (``contrastive_components``)."""
    from .figures import line_figure, three_panel_figure

    hist = record["history"]
    lam = float(record["settings"]["lambda_adv"])
    ep = [h["epoch"] for h in hist]
    panels = [
        ("(a) Generator vs discriminator", "Loss",
         [("generator", [h["generator_loss"] for h in hist]), ("discriminator", [h["discriminator_loss"] for h in hist])]),
        ("(b) Terms of the generator loss", "Loss",
         [("contrastive", [h["contrastive_loss"] for h in hist]),
          (f"λ × adversarial (λ = {lam:g})", [lam * h["adversarial_loss"] for h in hist])]),
        ("(c) Contrastive components", "Value",
         [("Δk surrogate", [h["delta_k_surrogate"] for h in hist]), ("similarity", [h["similarity"] for h in hist])]),
    ]
    paths = three_panel_figure(ep, panels, out / "training_curves", markers=True)
    return paths + line_figure(ep, "Contrastive components of the PromSec gGAN", "Value", panels[2][2],
                               out / "contrastive_components")


# --------------------------------------------------------------------------- inference in the loop


class Selector:
    """The trained gGAN in the PromSec loop: the statements whose nodes it changes most."""

    def __init__(self, cfg: dict):
        directory = model_dir(cfg)
        meta = json.loads((directory / "meta.json").read_text(encoding="utf-8"))
        if _sha(directory / "generator.pt") != meta["generator_sha256"]:
            raise RuntimeError(f"gGAN checkpoint in {directory} does not match its recorded hash")
        self.model = Generator()
        self.model.load_state_dict(torch.load(directory / "generator.pt", map_location="cpu", weights_only=True))
        self.model.eval()
        self.top_k, self.min_change = int(meta["top_k"]), float(meta["min_change"])
        self.sha = meta["generator_sha256"]

    def __call__(self, code: str) -> tuple[list[g.Statement], list[dict]]:
        stmts, x, ei, et = g.graph(code)
        with torch.no_grad():
            updated = self.model(x, ei, et)
        change = g.node_change_scores(x, updated).tolist()
        marked = [{"node": i, "ast_type": stmts[i].type, "lineno": stmts[i].lineno, "end_lineno": stmts[i].end_lineno,
                   "change": round(change[i], 4)} for i in select_changed(x, updated, self.top_k, self.min_change)]
        return stmts, sorted(marked, key=lambda m: m["lineno"])
