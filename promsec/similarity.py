"""Code-level functionality-preservation measures between an original program and PromSec's output.

Both measures use the statement graph of ``promsec.graph`` and are computed the same
way for every variant, so they can be compared across variants:

graph similarity      cosine similarity of the Weisfeiler-Lehman subtree features of the
                      two statement graphs (node labels: statement type and called
                      functions; three refinement rounds over the typed edges). It is 1
                      for programs with the same statement structure.
embedding similarity  cosine similarity of the two graph embeddings (mean of the node
                      features), the similarity S_ij used in the gGAN's contrastive loss.

Both are structural proxies; LAAJ (``promsec.judge``) scores behavior.
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter

import torch

from . import graph as g

WL_ROUNDS = 3


def _label(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def wl_features(code: str, rounds: int = WL_ROUNDS) -> Counter:
    """Weisfeiler-Lehman subtree label counts of the statement graph of ``code``."""
    stmts = g.statements(code)
    ei, et = g.edges(stmts)
    labels = [_label(s.type + "|" + ",".join(".".join(c.split(".")[-2:]) for c in s.calls)) for s in stmts]
    neighbors: list[list[tuple[int, int]]] = [[] for _ in stmts]
    for (a, b), r in zip(ei.t().tolist(), et.tolist()):
        neighbors[b].append((r, a))
    counts = Counter(labels)
    for _ in range(rounds):
        labels = [_label(labels[i] + "|" + ",".join(sorted(f"{r}:{labels[j]}" for r, j in neighbors[i])))
                  for i in range(len(stmts))]
        counts.update(labels)
    return counts


def _cosine(a: Counter, b: Counter) -> float | None:
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0 or nb == 0:
        return None
    return sum(a[k] * b[k] for k in a.keys() & b.keys()) / (na * nb)


def graph_similarity(original: str, output: str) -> float | None:
    """WL-kernel cosine similarity of the statement graphs; ``None`` if either program does not parse."""
    try:
        return _cosine(wl_features(original), wl_features(output))
    except SyntaxError:
        return None


def embedding_similarity(original: str, output: str) -> float | None:
    """Cosine similarity of the mean node-feature embeddings; ``None`` if either program does not parse."""
    try:
        a = g.features(g.statements(original)).mean(dim=0)
        b = g.features(g.statements(output)).mean(dim=0)
    except SyntaxError:
        return None
    if a.numel() == 0 or b.numel() == 0 or float(a.norm()) == 0 or float(b.norm()) == 0:
        return None
    return float(torch.nn.functional.cosine_similarity(a, b, dim=0))


def similarities(original: str, output: str) -> dict:
    gs, es = graph_similarity(original, output), embedding_similarity(original, output)
    return {"graph_similarity": None if gs is None else round(gs, 4),
            "embedding_similarity": None if es is None else round(es, 4)}
