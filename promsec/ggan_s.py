"""PromSec-S: a supervised gGAN that selects the statements to fix and proposes a fix for each.

This is an extension of PromSec; it is not part of the CCS 2024 paper. It uses the
same statement graph and training states as the PromSec gGAN and differs in the
objective and in what reaches the LLM:

* the generator outputs, per statement, a change score s, a fix class (replace the
  call, change its arguments, modify, delete, insert a step before) and an updated
  graph x' = x + s * delta;
* it is trained with L_G = L_loc + L_fix + lambda * L_adv: L_loc is the binary
  cross-entropy of s against Bandit's flagged statements, L_fix the cross-entropy of
  the fix class against the edit of the accepted fix, and L_adv the adversarial loss
  of a discriminator that separates graphs of Bandit-clean programs from generated
  graphs;
* in the loop, the selected statements (score >= ``threshold``, at most ``top_k``)
  and a proposed fix for each reach the LLM.

The epoch with the best localization F1 on validation program groups is kept.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import torch

from . import graph as g
from . import states as st
from .config import resolve_path
from .io import atomic_write_json


class Generator(torch.nn.Module):
    """Relational graph encoder; per statement: change score, fix class and feature update."""

    def __init__(self, in_dim: int = g.FEATURE_DIM, hidden: int = 128):
        super().__init__()
        from torch_geometric.nn import RGCNConv

        self.conv1 = RGCNConv(in_dim, hidden, g.NUM_RELATIONS)
        self.conv2 = RGCNConv(hidden, hidden, g.NUM_RELATIONS)
        self.skip = torch.nn.Linear(in_dim, hidden)
        self.score = torch.nn.Linear(hidden, 1)
        self.fix = torch.nn.Linear(hidden, len(g.EDIT_CLASSES))
        self.delta = torch.nn.Sequential(torch.nn.Linear(hidden, hidden), torch.nn.ReLU(), torch.nn.Linear(hidden, in_dim))

    def forward(self, x, edge_index, edge_type):
        h = torch.relu(self.conv1(x, edge_index, edge_type) + self.skip(x))
        h = torch.relu(self.conv2(h, edge_index, edge_type) + h)
        logit = self.score(h).squeeze(-1)
        s = torch.sigmoid(logit)
        updated = x + s.unsqueeze(-1) * self.delta(h)
        return logit, self.fix(h), updated


class Discriminator(torch.nn.Module):
    """Graph-level probability that a statement graph comes from a Bandit-clean program."""

    def __init__(self, in_dim: int = g.FEATURE_DIM, hidden: int = 64):
        super().__init__()
        from torch_geometric.nn import RGCNConv

        self.conv = RGCNConv(in_dim, hidden, g.NUM_RELATIONS)
        self.out = torch.nn.Linear(hidden, 1)

    def forward(self, x, edge_index, edge_type):
        h = torch.relu(self.conv(x, edge_index, edge_type))
        return self.out(h.mean(dim=0, keepdim=True)).squeeze()


def select(logit: torch.Tensor, top_k: int, threshold: float) -> list[int]:
    """Statements the gGAN selects: score >= threshold, at most ``top_k``, highest first."""
    scores = torch.sigmoid(logit).tolist()
    ranked = sorted(range(len(scores)), key=lambda i: -scores[i])
    return [i for i in ranked[:top_k] if scores[i] >= threshold]


def evaluate(model, data: list[tuple], top_k: int, threshold: float) -> dict:
    model.eval()
    by_kind: dict[str, tuple[list, list]] = {"all": ([], []), "original": ([], []), "rewritten": ([], [])}
    fix_truth, fix_pred = [], []
    with torch.no_grad():
        for (x, ei, et, loc, fix), record in data:
            logit, fix_logits, _ = model(x, ei, et)
            chosen = set(select(logit, top_k, threshold))
            pred = [1 if i in chosen else 0 for i in range(len(loc))]
            truth = [int(v) for v in loc.tolist()]
            for kind in ("all", "original" if record["round"] == 0 else "rewritten"):
                by_kind[kind][0].extend(truth)
                by_kind[kind][1].extend(pred)
            mask = fix != -100
            fix_truth.extend(fix[mask].tolist())
            fix_pred.extend(fix_logits.argmax(dim=1)[mask].tolist())
    out: dict = {kind: st.loc_scores(t, p) for kind, (t, p) in by_kind.items()}
    out["fix_macro_f1"] = round(g.macro_f1(fix_truth, fix_pred, list(range(1, len(g.EDIT_CLASSES)))), 4) if fix_truth else None
    out["fix_statements"] = len(fix_truth)
    return out


def train(cfg: dict, train_data: list[tuple], val_data: list[tuple], adv_weight: float, device) -> tuple[Generator, dict]:
    s = cfg["ggan_s"]
    seed, epochs = int(s["seed"]), int(s["epochs"])
    top_k, threshold = int(s["top_k"]), float(s["threshold"])
    torch.manual_seed(seed)
    gen, disc = Generator().to(device), Discriminator().to(device)
    opt_g = torch.optim.Adam(gen.parameters(), lr=1e-3, weight_decay=1e-4)
    opt_d = torch.optim.Adam(disc.parameters(), lr=1e-3)
    data = [(tuple(t.to(device) for t in tensors), rec) for tensors, rec in train_data]
    vdata = [(tuple(t.to(device) for t in tensors), rec) for tensors, rec in val_data]
    positives = sum(float(t[3].sum()) for t, _ in data)
    total = sum(len(t[3]) for t, _ in data)
    pos_weight = torch.tensor((total - positives) / max(positives, 1.0), device=device)
    bce = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    ce = torch.nn.CrossEntropyLoss(ignore_index=-100)
    adv = torch.nn.BCEWithLogitsLoss()
    clean = [t for t, rec in data if not rec["tests"]]
    rng = torch.Generator().manual_seed(seed)
    best_state, best_f1, best_epoch, history = None, -1.0, 0, []
    for epoch in range(epochs):
        gen.train()
        disc.train()
        totals = {"loc": 0.0, "fix": 0.0, "adv": 0.0, "disc": 0.0}
        for i in torch.randperm(len(data), generator=rng).tolist():
            (x, ei, et, loc, fix), rec = data[i]
            logit, fix_logits, updated = gen(x, ei, et)
            loss_loc = bce(logit, loc)
            loss_fix = ce(fix_logits, fix) if bool((fix != -100).any()) else logit.sum() * 0.0
            loss = loss_loc + loss_fix
            if adv_weight > 0 and rec["tests"] and clean:
                loss_adv = adv(disc(updated, ei, et).reshape(1), torch.ones(1, device=device))
                loss = loss + adv_weight * loss_adv
                totals["adv"] += float(loss_adv)
            opt_g.zero_grad()
            loss.backward()
            opt_g.step()
            totals["loc"] += float(loss_loc)
            totals["fix"] += float(loss_fix)
            if adv_weight > 0 and rec["tests"] and clean:
                cx, cei, cet, _, _ = clean[int(torch.randint(len(clean), (1,), generator=rng))]
                d_real = disc(cx, cei, cet).reshape(1)
                d_fake = disc(updated.detach(), ei, et).reshape(1)
                loss_d = adv(d_real, torch.ones(1, device=device)) + adv(d_fake, torch.zeros(1, device=device))
                opt_d.zero_grad()
                loss_d.backward()
                opt_d.step()
                totals["disc"] += float(loss_d)
        scores = evaluate(gen, vdata, top_k, threshold) if vdata else {"rewritten": {"f1": 0.0}}
        f1 = scores["rewritten"]["f1"] or scores.get("all", {}).get("f1") or 0.0
        history.append({"epoch": epoch + 1, **{k: round(v / max(len(data), 1), 4) for k, v in totals.items()},
                        "val_inloop_f1": f1})
        if f1 > best_f1:
            best_f1, best_epoch = f1, epoch + 1
            best_state = {k: v.detach().clone() for k, v in gen.state_dict().items()}
    if best_state is not None:
        gen.load_state_dict(best_state)
    return gen.cpu(), {"history": history, "best_val_inloop_f1": best_f1, "kept_epoch": best_epoch}


def model_dir(cfg: dict) -> Path:
    return resolve_path(cfg, cfg["ggan_s"]["model_dir"])


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _example(cfg: dict, record: dict) -> dict:
    directory = st.states_dir(cfg)
    code = (directory / f"{record['id']}.py").read_text(encoding="utf-8")
    nxt = (directory / f"{record['id']}.next.py").read_text(encoding="utf-8")
    stmts, labels, detail = g.edit_labels(code, nxt)
    return {"statements": stmts, "labels": labels, "detail": detail}


def run_training(cfg: dict, out_dir: Path | None = None) -> dict:
    """Train PromSec-S on the training states, with held-out localization and leave-one-scenario-out
    generalization. Saves the model, the hint table, the record and curves."""
    started = time.time()
    s = cfg["ggan_s"]
    out = out_dir or model_dir(cfg)
    out.mkdir(parents=True, exist_ok=True)
    labeled = st.load_states(cfg)
    pairs = [(st.tensors(cfg, r), r) for r in labeled]
    seed = int(s["seed"])
    held = st.split_groups([r["group"] for r in labeled], float(s["holdout_fraction"]), seed)
    train_all = [p for p in pairs if p[1]["group"] not in held]
    test = [p for p in pairs if p[1]["group"] in held]
    inner = st.split_groups([p[1]["group"] for p in train_all], float(s["validation_fraction"]), seed + 1)
    train_set = [p for p in train_all if p[1]["group"] not in inner] or train_all
    val = [p for p in train_all if p[1]["group"] in inner]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    top_k, threshold = int(s["top_k"]), float(s["threshold"])
    print(f"== PromSec-S gGAN: {len(train_set)} train, {len(val)} validation, {len(test)} held-out states on {device}",
          flush=True)
    model, info = train(cfg, train_set, val, float(s["adv_weight"]), device)
    record: dict = {"states": len(labeled), "train_states": len(train_set), "validation_states": len(val),
                    "heldout_states": len(test), "heldout_groups": sorted(held), "device": str(device),
                    "top_k": top_k, "threshold": threshold, "adv_weight": float(s["adv_weight"]),
                    "training": info, "heldout_localization": evaluate(model, test, top_k, threshold)}
    if s.get("leave_one_scenario_out", True):
        print("== PromSec-S gGAN: leave one weakness scenario out", flush=True)
        loso = {}
        for scenario in sorted({r["scenario"] for r in labeled if r["source"] == "synth"}):
            tr = [p for p in pairs if p[1]["scenario"] != scenario]
            te = [p for p in pairs if p[1]["scenario"] == scenario]
            m, _ = train(cfg, tr, [], float(s["adv_weight"]), device)
            loso[scenario] = evaluate(m, te, top_k, threshold)["all"]
            print(f"   {scenario}: {json.dumps(loso[scenario])}", flush=True)
        record["leave_one_scenario_out"] = loso
    torch.save(model.state_dict(), out / "generator.pt")
    hints = g.HintTable.fit([_example(cfg, p[1]) for p in train_all if "fix" in p[1]])
    atomic_write_json(out / "hints.json", hints.to_dict())
    atomic_write_json(out / "meta.json", {"top_k": top_k, "threshold": threshold, "feature_dim": g.FEATURE_DIM,
                                          "generator_sha256": _sha(out / "generator.pt")})
    record["seconds"] = round(time.time() - started, 1)
    atomic_write_json(out / "training.json", record)
    plot_training(record, out)
    return record


def plot_training(record: dict, out: Path) -> list[Path]:
    """Training curves: supervised terms, the adversarial game, and validation localization."""
    from .figures import three_panel_figure

    info = record["training"]
    hist = info["history"]
    ep = [h["epoch"] for h in hist]
    panels = [
        ("(a) Supervised terms", "Loss",
         [("localization (BCE)", [h["loc"] for h in hist]), ("fix class (CE)", [h["fix"] for h in hist])]),
        ("(b) Adversarial game", "Loss",
         [("generator adversarial", [h["adv"] for h in hist]), ("discriminator", [h["disc"] for h in hist])]),
        ("(c) Validation localization", "F1", [("validation F1", [h["val_inloop_f1"] for h in hist])]),
    ]
    kept = info.get("kept_epoch") or max(hist, key=lambda h: h["val_inloop_f1"])["epoch"]
    return three_panel_figure(ep, panels, out / "training_curves", markers=False, vline=(2, kept, f"kept: epoch {kept}"))


class Selector:
    """The trained PromSec-S gGAN in the loop: selected statements with a proposed fix each."""

    def __init__(self, cfg: dict):
        directory = model_dir(cfg)
        meta = json.loads((directory / "meta.json").read_text(encoding="utf-8"))
        if _sha(directory / "generator.pt") != meta["generator_sha256"]:
            raise RuntimeError(f"PromSec-S checkpoint in {directory} does not match its recorded hash")
        self.model = Generator()
        self.model.load_state_dict(torch.load(directory / "generator.pt", map_location="cpu", weights_only=True))
        self.model.eval()
        self.hints = g.HintTable.from_dict(json.loads((directory / "hints.json").read_text(encoding="utf-8")))
        self.top_k, self.threshold = int(meta["top_k"]), float(meta["threshold"])
        self.sha = meta["generator_sha256"]

    def __call__(self, code: str) -> tuple[list[g.Statement], list[dict]]:
        stmts, x, ei, et = g.graph(code)
        with torch.no_grad():
            logit, fix_logits, _ = self.model(x, ei, et)
        scores = torch.sigmoid(logit).tolist()
        fixes = fix_logits.argmax(dim=1).tolist()
        marked = []
        for i in select(logit, self.top_k, self.threshold):
            label = g.EDIT_CLASSES[fixes[i]]
            marked.append({"node": i, "ast_type": stmts[i].type, "lineno": stmts[i].lineno, "end_lineno": stmts[i].end_lineno,
                           "change": round(scores[i], 4), "fix": "modify_other" if label == "keep" else label})
        return stmts, sorted(marked, key=lambda m: m["lineno"])

    def fix_text(self, code: str, stmts: list[g.Statement], marked: list[dict]) -> str:
        labels = ["keep"] * len(stmts)
        for m in marked:
            labels[m["node"]] = m["fix"]
        return g.render_plan(code, stmts, labels, hints=self.hints)
