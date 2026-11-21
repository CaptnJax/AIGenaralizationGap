# Reproduce RQ1

Run the frozen LineVul and VulBERTa checkpoints on PrimeVul and LLMVul with
`pivd_local.py`. Begin with the [repository setup](../README.md) to clone the
data with Git LFS. Run every command below from the repository root.

## 1. Set up the environment

Install **Python 3.12 (64-bit)** and **Git for Windows**. CUDA use requires an
NVIDIA GPU and a compatible driver. Open a new PowerShell window after installing.

```powershell
powershell -ExecutionPolicy Bypass -File .\localScripts\setup.ps1 -Compute cuda
```

Setup creates `localScripts/.venv`, installs dependencies, and checks PyTorch,
CUDA, and Clang. It pins PyTorch 2.7.1, Transformers 4.57.1, tokenizers 0.22.1,
and libclang 18.1.1; the remaining package ranges are in
[requirements.txt](requirements.txt). The installed versions are saved in
`localScripts/.venv/installed-packages.txt` and each run's `environment.json`.

For CPU use, replace `-Compute cuda` with `-Compute cpu` and use `--device cpu`
below. If Python has no Windows launcher, append `-Python "C:\path\to\python.exe"`
to setup. The first evaluation downloads model assets; allow several GB of space
and network access. Full CPU evaluations can take hours.

## 2. Pin the LineVul implementation

For a fresh checkout, populate the cache with the commit recorded in the saved
RQ1 runs before evaluating:

```powershell
git clone --no-checkout https://github.com/awsm-research/LineVul.git .\localScripts\.cache\LineVul
if ($LASTEXITCODE -ne 0) { throw 'LineVul clone failed.' }
git -C .\localScripts\.cache\LineVul checkout --detach 9401ec6e60b762a9308645961268203244bee048
if ($LASTEXITCODE -ne 0) { throw 'LineVul checkout failed.' }
```

If that cache already exists, check its commit with
`git -C .\localScripts\.cache\LineVul rev-parse HEAD` and reuse it only when it
matches the revision above. The runner otherwise clones the current upstream
default branch. Its required checkpoint is `12heads_linevul_model.bin`
(SHA-256 `1b18ff8e75af787520a00139bd86e70d02eb448c716290ee7b2cb20bda61a67b`).
VulBERTa is pinned by the runner to revision
`fecabdee24a3ef6e804d7629d6eed03dc6b4f61e`.

## 3. Extract the prepared RQ1 datasets

The public archive is in `datasets/pruned/`; the runner expects its
`prepared_datasets/` directory at the repository root. Extract it once:

```powershell
Expand-Archive -LiteralPath .\datasets\pruned\prepared_datasets.zip -DestinationPath .
```

| Dataset | Functions | Files under `prepared_datasets/` |
| --- | ---: | --- |
| PrimeVul test | 24,788 | `linevul/primevul_test.csv`, `vulberta/primevul_test.csv` |
| LLMVul, all binary-labeled records | 18,751 | `linevul/llmvul_test.csv`, `vulberta/llmvul_test.csv` |

Keep labels, code, and row order unchanged. See the
[dataset guide](../datasets/pruned/README.md) for rebuilding and checking the files.

## 4. Run the four evaluations

```powershell
.\localScripts\.venv\Scripts\python.exe .\localScripts\pivd_local.py --jobs rq1 --device cuda --run-dir .\localScripts\results\rq1_local
```

`--jobs rq1` selects both models on both datasets. Add `--dry-run` to list jobs
and paths; a dry run does not check that the data or models are present.
Defaults are batch size 16 on CUDA and 4 on CPU. If GPU memory is insufficient,
choose `--batch-size 4` and a new `--run-dir`.

The protocol uses frozen weights, seed 42, and `p(vulnerable) > 0.5`.
Input limits are 512 tokens for LineVul and 1,024 for VulBERTa. The current
VulBERTa runner includes the authors' explicit cleaning step and Clang tokenizer fix.

| Model | PrimeVul F1 | LLMVul F1 |
| --- | ---: | ---: |
| LineVul | 0.10316428 | 0.10493668 |
| VulBERTa, corrected preprocessing | 0.04551365 | 0.14262480 |

These are reference values from the saved runs, not a bitwise-parity guarantee
for every hardware/software combination. Compare row counts, dataset/checkpoint
hashes, settings, and `environment.json` when a fresh result differs.

## 5. Read results or resume

New outputs are under `localScripts/results/rq1_local/`:

- `summary.csv`: row counts, accuracy, F1, precision, recall, and threshold.
- `environment.json` and `<model>/<dataset>/job.json`: versions, inputs, settings, and status.
- `<model>/<dataset>/metrics.json` and `test.log`: detailed metrics and logs.
- Predictions: `linevul/<dataset>/results/raw_preds.csv` and `vulberta/<dataset>/predictions.csv`.

After an interruption, rerun with the same settings and `--resume`:

```powershell
.\localScripts\.venv\Scripts\python.exe .\localScripts\pivd_local.py --jobs rq1 --device cuda --run-dir .\localScripts\results\rq1_local --resume
```

Completed jobs are reused. VulBERTa resumes completed batches; an interrupted
LineVul job restarts that dataset. Use a new directory after changing data, code,
packages, device, or batch size. Only one process should use a run directory.

## Supplementary RQ1 work

The four-job alias covers the primary comparison. For the other evidence:

- [CWEval preparation and inference](../datasets/pruned/cweval/README.md#reproduce-and-run).
- [Recalculate all nine published job metrics](../results/evaluation_runs/README.md#recalculate-the-published-metrics).
- [Full control and diagnostic requirements](../results/diagnostics/README.md#reproduction-requirements).
- [Final RQ1 findings](../results/findings/rq1_answer.md).

The diagnostic scripts resolve recorded provenance paths to this public layout.
Use the diagnostic guide for prerequisites and fresh output directories.
