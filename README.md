# PromSec

Implementation of *PromSec: Prompt Optimization for Secure Generation of Functional Source Code with Large Language Models (LLMs)*, ACM CCS 2024 ([paper](https://doi.org/10.1145/3658644.3690298)).

PromSec optimizes prompts so that an LLM generates secure and functional Python code. In each iteration, a graph generative adversarial network (gGAN) updates the code's control-flow graph, the LLM rewrites the code and infers an optimized prompt from it, and Bandit checks the generated code for CWEs.

## Setup

Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m promsec selftest-offline
```

## Run

```bash
export OPENAI_API_KEY=...
export PROMSEC_LLM_MODEL=...
export PROMSEC_LLM_BASE_URL=...   # optional, for other OpenAI-compatible endpoints

python -m promsec run --config configs/default.yaml
python -m promsec report --config configs/default.yaml
```

Results are written to `runs/default/`. Runs resume after interruption.

## Train

```bash
python -m promsec train --config configs/default.yaml
```

The packaged checkpoints are in `models/`. Set `training.train_from_scratch: 1` to use freshly trained ones.

## Documentation

- `documentation/WORKFLOW.md`: the PromSec iteration and the reported results
- `documentation/TRAINING.md`: gGAN training
- `documentation/REMOTE_GPU.md`: unattended runs on a GPU server
- `documentation/DATA_PROVENANCE.md`: dataset

## Citation

If you use this code in your research, please cite our paper:

```bibtex
@inproceedings{nazzal2024promsec,
  title={PromSec: Prompt Optimization for Secure Generation of Functional Source Code with Large Language Models (LLMs)},
  author={Nazzal, Mahmoud and Khalil, Issa and Khreishah, Abdallah and Phan, Nguyen H},
  booktitle={Proceedings of the 31st ACM Conference on Computer and Communications Security (CCS)},
  year={2024},
  address={Salt Lake City, UT, USA}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/mahmoudkanazzal/PromSec/blob/main/LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Mahmoud Nazzal

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

## Contact

For any questions or issues, please contact Mahmoud Nazzal at [mnazzal@odu.edu](mailto:mnazzal@odu.edu) ([website](https://mahmoudkanazzal.github.io/)).
