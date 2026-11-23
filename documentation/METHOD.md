# Method

## The PromSec loop

`promsec/runner.py` runs the loop on each evaluation program `c` for at most `loop.max_iterations` (20) iterations:

1. Bandit scans `c`. If it reports no CWE, the program is secured and the loop stops.
2. `c` is converted to its statement graph `g`, and the gGAN generator computes the updated graph `G(g)`.
3. **Code reconstruction.** The LLM receives `c` and the statements selected by the gGAN (type, source lines and code of each, in source order). It revises them to remove security weaknesses and keeps the other statements functionally unchanged.
4. **Prompt inference.** The LLM writes a prompt that would generate the revised code securely.
5. **Generation.** The LLM generates new code from that prompt, with an instruction to keep secrets in environment variables.
6. Bandit scans the new code, which becomes `c` for the next iteration.

The final program is the version with the fewest CWEs (the earliest one on ties). A reply that is not valid Python is sent back to the LLM for repair, up to three times. The exact requests are in `promsec/prompts.py`; the tests pin them with hashes.

## Statement graph

`promsec/graph.py` builds one node per Python statement (compound statements such as `if`, `for`, `with`, `try` and function definitions are nodes too). Edges have three types, each in both directions (six relations):

- **next-in-block:** a statement and the next statement of the same block;
- **parent-child:** a compound statement and each statement in its body;
- **def-use:** the statement that last defines a name and a statement that uses it, in the same scope or at module level.

Each node has 129 features computed from the code alone: the statement type (one-hot), hashed called-function names, hashed keyword-argument names, and ten flags (f-string, string concatenation, `%` formatting, `.format`, secret-like literal, bind to all interfaces, temporary path, user input, compound statement, nesting depth). No analyzer output is a feature.

## The PromSec gGAN

`promsec/ggan.py` implements the gGAN with the paper's objective.

- **Generator G:** two relational graph convolution layers (129 → 128 → 129) that map node features `x` to updated features `x'` on the same nodes and edges.
- **Discriminator D:** two relational graph convolution layers with a sigmoid output per statement; the losses average these probabilities that the graph is real.
- **Generator objective:** `L_G = L_contrastive + λ·L_adv` with `L_adv = -E[log D(G(g))]`. The contrastive loss ranks the generated graph of program `i` above 16 negatives (other training graphs) by the score `z = α·Δk + β·S`.
- **Δk** is the CWE reduction. Bandit cannot be differentiated, so training uses a surrogate: `k(c_i)` times the share of Bandit-flagged statements whose features change by at least the margin 0.25. For a negative `j`, `Δk_ij = k(c_i) − k(c_j)`.
- **S** is the similarity between `g_i` and `G(g_i)`: one minus the mean node change. For a negative, it is the cosine similarity of the two graphs' mean node features.
- **Discriminator objective:** `L_D = -E[log D(g)] − E[log(1 − D(G(g)))]`, five discriminator steps per generator step.
- **Settings:** α = 1, β = 10, λ = 0.01, 7 epochs, learning rate 0.001, Adam.

**Selection.** In the loop, the change of a node is the mean absolute difference between `x` and `x'`. The statements with the largest change, at most 5 and with change at least 0.1, are passed to the LLM. For example, on `data/test/test_file11.py` (76 statements):

```
$ python -m promsec select --file data/test/test_file11.py
76 statements; 5 selected by the promsec gGAN:
  L3        change 0.140  import yaml
  L7        change 0.265  MASTER_PASSWORD = "secure_pass_2024"
  L13       change 0.158  service_info = yaml.load(yaml_data, Loader=yaml.FullLoader)
  L29       change 0.208  os.system(f"sh run_operation.sh {operation} {parameter}")
  L112      change 0.280  os.system(f"python backup_data.py {backup_format}")
```

## PromSec-S (variant)

PromSec-S is not part of the CCS 2024 paper. It uses the same loop, graph and training states, and changes the gGAN's objective and what reaches the LLM: the generator predicts, per statement, a weakness score (supervised by Bandit labels), a fix class and a feature update; it is trained with binary cross-entropy for localization, cross-entropy for the fix class, and an adversarial term (weight 0.1) against graphs of Bandit-clean programs. The statements with score at least 0.5 (at most 5) reach the LLM with a proposed fix for each. `promsec/ggan_s.py` implements it.

## Implementation notes

| | Paper | This implementation |
|---|---|---|
| LLM | the LLMs evaluated in the paper | any OpenAI-compatible model; results with gpt-oss-120b |
| Code graph | control-flow graph | statement graph with control-structure and def-use edges |
| Graph to code | the LLM reconstructs code from the updated graph | the LLM receives the code and the statements whose graph nodes the gGAN changes most |
| Δk in training | CWE reduction | differentiable surrogate of the CWE reduction (above) |
| Training data | code graphs of the training programs | Bandit-labelled versions of LLM fix-and-rescan chains on training programs ([TRAINING.md](TRAINING.md)) |

The prompt-inference and generation requests follow the paper.

## Metrics

Computed for every program from its original and final code (`promsec/similarity.py`, `promsec/report.py`, `evaluation/`):

- **CWEs before / left:** distinct CWE IDs Bandit 1.9.4 reports, summed over the programs.
- **Programs secured:** programs with no CWE left.
- **Graph similarity:** cosine similarity of Weisfeiler-Lehman subtree features (3 rounds; node labels: statement type and called functions; typed edges) of the original and final statement graphs.
- **Embedding similarity:** cosine similarity of the mean node features of the two graphs.
Graph and embedding similarity measure structural closeness, which is not an accurate surrogate for functionality: regenerated code can be restructured and keep its behavior, or barely change and lose it. LAAJ scores the behavior directly, and gated LAAJ adds the hard checks below.

- **LAAJ:** the LLM judge extracts a behavioral contract from the original program and scores the final program against it (0 to 1).
- **Gated LAAJ:** LAAJ, set to 0 when the final program does not compile, changes a public function signature or route, or drops an entry point.
- **Localization precision / recall** (gGAN variants): the share of the statements passed to the LLM that hold a Bandit finding, and the share of Bandit-flagged statements that are passed, over all iterations.
