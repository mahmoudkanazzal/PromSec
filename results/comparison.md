# Variant comparison

Per variant: mean [min-max] over complete runs. CWEs: distinct CWE IDs per program, summed over the programs (Bandit). Secured: programs with no CWE left. Localization: share of the statements passed to the LLM that hold a Bandit finding (precision) and share of Bandit-flagged statements passed (recall), over all iterations.

| Variant | Runs | CWEs before | CWEs left | Programs secured | Graph sim. | Embedding sim. | LAAJ | Gated LAAJ | Localization precision | Localization recall |
|---|---|---|---|---|---|---|---|---|---|---|
| PromSec | 2 | 216.0 [216-216] | 21.0 [17-25] | 79.5 [76-83] | 0.39 [0.38-0.40] | 0.85 [0.85-0.85] | 0.53 [0.52-0.53] | 0.45 [0.44-0.45] | 0.57 [0.52-0.61] | 0.39 [0.33-0.46] |
| PromSec-S | 2 | 216.0 [216-216] | 16.5 [16-17] | 84.0 [83-85] | 0.37 [0.36-0.38] | 0.84 [0.84-0.84] | 0.46 [0.44-0.47] | 0.39 [0.39-0.40] | 0.71 [0.66-0.76] | 0.33 [0.32-0.34] |
| No gGAN | 3 | 215.7 [215-216] | 51.0 [49-53] | 51.3 [49-55] | 0.38 [0.38-0.38] | 0.86 [0.86-0.86] | 0.49 [0.47-0.50] | 0.41 [0.40-0.43] | - | - |

## Runs

| Run | Variant | Done | Failed | CWEs before | CWEs left | Programs secured | Mean LAAJ | Mean gated LAAJ |
|---|---|---|---|---|---|---|---|---|
| promsec/run1 | PromSec | 100/100 | 0 | 216 | 17 | 83 | 0.53 | 0.44 |
| promsec/run2 | PromSec | 100/100 | 0 | 216 | 25 | 76 | 0.52 | 0.45 |
| promsec_s/run1 | PromSec-S | 100/100 | 0 | 216 | 16 | 85 | 0.47 | 0.40 |
| promsec_s/run2 | PromSec-S | 100/100 | 0 | 216 | 17 | 83 | 0.44 | 0.39 |
| no_ggan/run1 | No gGAN | 100/100 | 1 | 215 | 53 | 49 | 0.50 | 0.41 |
| no_ggan/run2 | No gGAN | 100/100 | 0 | 216 | 49 | 55 | 0.47 | 0.40 |
| no_ggan/run3 | No gGAN | 100/100 | 0 | 216 | 51 | 50 | 0.50 | 0.43 |

## Programs with each CWE left

| Run | CWE-78 | CWE-89 | CWE-259 | CWE-327 | CWE-377 | CWE-605 | CWE-703 | CWE-732 |
|---|---|---|---|---|---|---|---|---|
| promsec/run1 | 7 | 3 | 0 | 0 | 1 | 0 | 6 | 0 |
| promsec/run2 | 9 | 4 | 2 | 0 | 1 | 1 | 8 | 0 |
| promsec_s/run1 | 2 | 2 | 2 | 2 | 0 | 0 | 7 | 1 |
| promsec_s/run2 | 3 | 4 | 2 | 1 | 0 | 2 | 5 | 0 |
| no_ggan/run1 | 32 | 4 | 0 | 1 | 0 | 13 | 3 | 0 |
| no_ggan/run2 | 31 | 3 | 1 | 1 | 0 | 11 | 2 | 0 |
| no_ggan/run3 | 31 | 3 | 0 | 1 | 0 | 12 | 4 | 0 |
