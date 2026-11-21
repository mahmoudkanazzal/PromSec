# Training

```bash
python -m promsec train --config configs/default.yaml
```

The discriminator minimizes Eq. (6) and the generator minimizes Eq. (2), L_G = L_contrastive + lambda * L_adv, with the contrastive loss of Eqs. (4)-(5):

```
L_contrastive = -log( exp(a*dk_i + b*S_i) / ( exp(a*dk_i + b*S_i) + sum_j exp(a*dk_ij + b*S_ij) ) )
```

- dk_i is the CWE reduction of program i. It is computed differentiably from the Bandit-flagged statements that the generator changes.
- S_i is the similarity of g_i and g_hat_i.
- The negatives g_j are other training graphs, with dk_ij = k(c_i) - k(c_j) and S_ij the cosine similarity of the graph embeddings.

The settings are in `configs/default.yaml`.

Training uses 450 of the 500 training programs and holds out 50 for validation. The training and validation losses of every epoch are printed and saved with their curves in `runs/<name>/training/`. The packaged checkpoints and their losses are in `models/`.
