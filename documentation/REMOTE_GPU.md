# Unattended GPU runs

`configs/cluster_gpu.yaml` trains a fresh gGAN, runs PromSec on the 100 evaluation programs, scores LAAJ, and writes the report. The run continues in `tmux` after you disconnect and resumes where it stopped.

## Setup

```bash
cp api_key.txt.example api_key.txt          # API key on one line
cp llm_config.env.example llm_config.env    # endpoint and model
bash scripts/setup_gpu_venv.sh
bash scripts/gpu_preflight.sh
```

`api_key.txt` and `llm_config.env` are ignored by git.

## Start, watch, stop

```bash
bash scripts/start_or_resume.sh
tail -f runs/cluster_gpu/logs/results.log   # one row per finished program
bash scripts/watch.sh                       # supervisor log
bash scripts/stop.sh
bash scripts/start_or_resume.sh --clear-stop   # resume after a stop
```
