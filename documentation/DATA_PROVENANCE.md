# Data

`data/training/` holds the 500 training programs and `data/test/` the 100 evaluation programs. The programs come from the Python dataset of Pearce et al. [1], which contains code from MITRE documentation, CodeQL documentation, and examples written by the authors of [1]. They are included unmodified; `data/MANIFEST.csv` lists their hashes.

Some programs contain hard-coded credentials, hostnames, or addresses as part of their vulnerable code. PromSec only analyzes them and never uses them.

[1] H. Pearce, B. Tan, B. Ahmad, R. Karri, and B. Dolan-Gavitt, "Examining Zero-Shot Vulnerability Repair with Large Language Models," in *Proc. IEEE Symposium on Security and Privacy (SP)*, 2023, pp. 2339–2356.
