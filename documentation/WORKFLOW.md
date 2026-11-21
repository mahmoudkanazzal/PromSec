# Workflow

## PromSec iteration

Each iteration on code c follows Fig. 3 of the paper:

1. **Graph construction.** A statement-level control-flow graph (CFG) g is built from c. Each node holds 111 features: structural flags, statement type, expression counts, string operators, and hashed identifiers.
2. **gGAN.** The generator produces the updated graph g_hat.
3. **Code reconstruction.** The LLM receives c, g, and g_hat, with the most-changed statements listed, and returns c_hat.
4. **Prompt inference.** The LLM writes a prompt p_hat for c_hat.
5. **Generation and security analysis.** p_hat generates new code, which Bandit scans.

The loop stops when Bandit reports no CWE or after 20 iterations. The output is the generated program with the fewest CWE types. The prompts are defined in `utils.py`.

## Results

`python -m promsec report` writes the per-program and aggregate results to `runs/<name>/report/`, including the figure `performance_eval.png` (also as PDF): (a) CWE count per program before and after PromSec, (b) functionality preservation per program, and (c) CWE ID histogram.

Functionality preservation is reported as graph similarity and as an LLM-as-a-Judge (LAAJ) score in [0, 1]. The gated LAAJ score is 0 when the output does not compile or changes the original program's public interface or entry points. LAAJ is set with `PROMSEC_JUDGE_MODEL` and is used only for evaluation.

`python -m promsec results` prints a table row for each program as it finishes.
