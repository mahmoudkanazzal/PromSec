# Data

## Programs

`data/training/` holds the 500 training programs and `data/test/` the 100 evaluation programs. They come from the Python dataset of Pearce et al. [1], which contains code from MITRE documentation, CodeQL documentation, and examples written by the authors of [1]. They are included unmodified; `data/MANIFEST.csv` lists their hashes (`python -m promsec validate` checks them).

Some programs contain hard-coded credentials, hostnames, or addresses as part of their vulnerable code. PromSec only analyzes them and never uses them.

## Training states

`data/states/` holds the 629 training states of the gGANs ([TRAINING.md](TRAINING.md)). `python -m promsec training-data` generates them in two stages, resumable per item:

1. **Pool.** 100 programs from `data/training/`, balanced over its scenarios, and 120 programs the LLM synthesizes: 12 common Bandit weakness scenarios, each in 10 application contexts. A synthesized program is kept only if Bandit reports the intended finding.
2. **Fix chains.** For each program, two chains of up to three rounds (LLM temperature 0.7): the LLM fixes the code given the Bandit report, and Bandit re-scans the result. A step is accepted, and the chain continues, only if the code compiles, keeps the program's public functions and entry points, reduces the findings, and adds no new finding type. For chains that end with no finding, the LLM judge also scores functionality preservation; the score is recorded in the run.

`python -m promsec states` turns every distinct program version of the chains, including rejected fix attempts, into a state labeled by Bandit. Accepted steps also give the fix labels that PromSec-S uses. The shipped states were generated with gpt-oss-120b: 281 from training programs and 348 from synthesized programs.

| Scenario | Bandit test | The synthesized program... |
|---|---|---|
| CWE-78 | B605 | runs a shell command built from user input with `os.system` |
| CWE-78 | B602 | runs a command built from user input with `subprocess` and `shell=True` |
| CWE-89 | B608 | builds an SQL query by string formatting and executes it with `sqlite3` |
| CWE-20 | B506 | parses user-supplied YAML with `yaml.load` without a safe loader |
| CWE-259 | B105 | compares user input against a hard-coded password |
| CWE-259 | B106 | passes a hard-coded password as a keyword argument |
| CWE-703 | B101 | checks user input or permissions with `assert` |
| CWE-327 | B324 | hashes passwords or tokens with MD5 or SHA-1 |
| CWE-502 | B301 | deserializes user-supplied data with `pickle.loads` |
| CWE-400 | B113 | calls an HTTP API with `requests` without a timeout |
| CWE-377 | B108 | writes temporary files to a hard-coded `/tmp` path |
| CWE-605 | B104 | binds its server to `0.0.0.0` |

Contexts: a Flask user-profile service, a command-line backup utility, a Flask file-upload endpoint, an inventory module, a log analysis script, a Flask library-catalog API, a microservice configuration loader, a record synchronization script, a Flask login service, and a maintenance job scheduler. `promsec/trainingdata.py` has the exact requests.

## Separation from the evaluation programs

The training-data pipeline never reads `data/test/`. No training state or fix is a copy of an evaluation program (whitespace and comments ignored). The highest token 5-gram Jaccard similarity between a training state and an evaluation program is 0.27, below that between the original training and evaluation programs of [1] (0.29).

[1] H. Pearce, B. Tan, B. Ahmad, R. Karri, and B. Dolan-Gavitt, "Examining Zero-Shot Vulnerability Repair with Large Language Models," in *Proc. IEEE Symposium on Security and Privacy (SP)*, 2023, pp. 2339–2356.
