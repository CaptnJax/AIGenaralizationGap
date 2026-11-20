# Run the notebook evaluations on Windows

For the separate dataset-specific fine-tuning experiment, see [TRAINING.md](TRAINING.md). Its logs, checkpoints and held-out metrics go to `training_results/`, separate from these static evaluations.

`pivd_local.py` replaces `webCopies/PIVD.ipynb` with a normal command-line program. The exported `webCopies/pivd.py` contains Colab uploads, notebook shell commands and `/content` paths, so it cannot run directly as a regular Windows Python script. Both originals are preserved.

## One-time setup

Install **Python 3.12, 64-bit** from [python.org](https://www.python.org/downloads/windows/) and [Git for Windows](https://git-scm.com/downloads/win), then open a new PowerShell window. Python's Windows launcher currently reports no installed Python on this PC. Your detected RTX 3080 Ti has 12 GB of GPU memory.

Run from the repository folder:

```powershell
cd D:\GitRepo\PIVD\Repo
powershell -ExecutionPolicy Bypass -File .\localScripts\setup.ps1 -Compute cuda
```

This creates `localScripts/.venv`, installs dependencies, and verifies PyTorch CUDA and Clang. It does not run an evaluation. The execution-policy override applies only to this PowerShell process. If Python is installed without the launcher, append `-Python "C:\path\to\python.exe"`.

The setup uses PyTorch 2.7.1 with the official [CUDA 12.8 Windows wheels](https://pytorch.org/get-started/previous-versions/#v271), Transformers 4.57.1, tokenizers 0.22.1, and libclang 18.1.1. A separate CUDA toolkit installation is not required for these wheels. For a CPU-only installation, replace `-Compute cuda` with `-Compute cpu`.

## RQ2 generative model setup

The planned RQ2 models use a separate environment and text-only loading workflow.
See [RQ2 model loading](RQ2.md) for pinned checkpoints, access checks, downloads,
and synthetic smoke tests. This setup does not alter the RQ1 evaluation environment.

## Run evaluations

DevGPT preparation is available separately:

```powershell
.\localScripts\.venv\Scripts\python.exe -m pip install -r .\localScripts\requirements-devgpt.txt
.\localScripts\.venv\Scripts\python.exe .\prepare_devgpt_datasets.py
# Run the two frozen-model evaluations when ready:
.\localScripts\.venv\Scripts\python.exe .\localScripts\pivd_local.py --jobs devgpt --device cuda
```

The prepared bundle already exists; rerunning preparation requires a new `--output`
directory. `--jobs devgpt` selects `linevul-devgpt` and `vulberta-devgpt`, reading
`prepared_datasets/devgpt/{model}/devgpt_weak_test.csv`. DevGPT is opt-in and is not
included in the existing `all` alias. Its **unverified Flawfinder weak labels**
measure analyzer agreement, not validated vulnerability detection performance.
The runner checks dataset and tokenizer hashes, preserves `weak_unverified` in
job manifests, and uses the cached audited tokenizer. See the
[DevGPT protocol and counts](../prepared_datasets/devgpt/README.md).

Start with the same 2,000-row BigVul sanity check used in the notebook:

```powershell
.\localScripts\.venv\Scripts\python.exe .\localScripts\pivd_local.py --jobs sanity --device cuda
```

Run both models on PrimeVul and LLMVul:

```powershell
.\localScripts\.venv\Scripts\python.exe .\localScripts\pivd_local.py --jobs rq1 --device cuda
```

Run **all eight evaluations**, including full BigVul, its sample and the two prepared CWEval jobs:

```powershell
.\localScripts\.venv\Scripts\python.exe .\localScripts\pivd_local.py --jobs all --device cuda
```

You can also select one or more specific jobs:

| Job | Model / data |
| --- | --- |
| `linevul-primevul` | LineVul / PrimeVul test |
| `linevul-llmvul` | LineVul / all 18,751 labeled LLMVul records |
| `vulberta-primevul` | VulBERTa / PrimeVul test |
| `vulberta-llmvul` | VulBERTa / all 18,751 labeled LLMVul records |
| `linevul-bigvul` | LineVul / full official BigVul test |
| `linevul-bigvul-sample` | LineVul / stratified 2,000-row BigVul test sample |
| `linevul-cweval` | LineVul / filtered CWEval reference/unsafe pairs |
| `vulberta-cweval` | VulBERTa / the same filtered CWEval pairs |

Use `--jobs cweval` to run only the two CWEval jobs. The supplied CWEval Parquets
are combined into a matched, function-level evaluation cohort with a separate
audit catalog containing every candidate. See
[CWEval preparation and limitations](../prepared_datasets/cweval/README.md).

Without `--device`, CUDA is selected when available, otherwise CPU. Use `--device cpu` to force CPU. Default batch sizes are 16 for CUDA and 4 for CPU. If GPU memory runs out, start a new run with `--batch-size 4`. Full CPU evaluations can take hours. A dry run (`--jobs all --dry-run`) lists the jobs and paths without downloading anything or importing model libraries.

The first actual run downloads the required models and, for BigVul jobs, the official test CSV. Downloads are cached in `localScripts/.cache`; allow several GB for models and additional space for the Python environment and results. Google Drive downloads can be rate-limited; an error stops the run rather than silently skipping data.

Existing prepared CSVs are used as-is. Missing legacy CSVs are extracted from `prepared_datasets.zip` in the repository root. CWEval has a separate converter and manifest; missing CWEval CSVs produce a preparation error rather than using the legacy archive. Its dataset and tokenizer/preprocessing hashes are checked before inference. There are no interactive uploads. Default paths are relative to the script, so the program also works when launched from another directory. Use `--data-root` or `--cache-dir` to override locations.

## Results and resuming

Each invocation creates a new folder under `localScripts/results/` and prints its location. It contains:

- `summary.csv`: accuracy, F1, precision, recall, threshold and row count for each completed selected job.
- `environment.json`: Python/package versions and device information.
- `<model>/<dataset>/test.log`, `metrics.json` and `job.json`: output, full-precision metrics/confusion matrix, dataset/checkpoint identities and status.
- LineVul: `results/raw_preds.csv` (source rows plus binary predictions) and a precision-recall PDF.
- VulBERTa: `predictions.csv` (sample ID, label, probability, prediction), `progress.json`, and `current_batch.json`.

For a named run that can be resumed:

```powershell
.\localScripts\.venv\Scripts\python.exe .\localScripts\pivd_local.py --jobs rq1 --device cuda --run-dir .\localScripts\results\rq1_local
# After an interruption, rerun with the same settings and --resume:
.\localScripts\.venv\Scripts\python.exe .\localScripts\pivd_local.py --jobs rq1 --device cuda --run-dir .\localScripts\results\rq1_local --resume
```

Completed jobs are reused. VulBERTa resumes from saved completed batches; an interrupted LineVul job restarts that dataset. Resume rejects changes to dataset contents, device, batch size, tracked package versions or runner code. Use a new run folder after changing these. Only one process should use a given run folder at a time. Keep your PC awake during evaluations.

## Evaluation compatibility

The runner uses the official [LineVul](https://github.com/awsm-research/LineVul) code and `12heads_linevul_model.bin`. A separate generated entry point adds batch progress and checks checkpoint loading. Only obsolete generated embedding buffers may be ignored; missing or mismatched trained weights cause a failure. The original checkout is not edited or automatically updated, and its commit and checkpoint hash are recorded.

VulBERTa uses the same [claudios/VulBERTa-MLP-Devign](https://huggingface.co/claudios/VulBERTa-MLP-Devign) checkpoint conversion as the notebook, pinned to revision `fecabdee24a3ef6e804d7629d6eed03dc6b4f61e`. Its custom tokenizer code is loaded from that revision. The previously established Clang fix is applied to **both datasets**: it skips semantic parsing of function bodies while retaining Clang's lexical tokens. This differs from the earlier PrimeVul run before that fix; rerun PrimeVul here for comparison.

Labels and function text are unchanged. The threshold stays at 0.5, seed at 42, maximum input length at 512 for LineVul and 1,024 for VulBERTa. BigVul sampling uses the notebook's stratified `train_test_split` selection and original row order; the selected source indices are saved. CPU/GPU or library changes can cause small numerical differences, so environment details are recorded. No training is performed.

### Corrected VulBERTa cleaning

The local VulBERTa runner now applies the authors' `cleaner()` from their [evaluation notebook](https://github.com/ICL-ml4csec/VulBERTa/blob/main/Evaluation_VulBERTa-MLP.ipynb) **before** tokenization: remove comments with their regex, then remove newlines and tabs. The Hugging Face conversion's purported comment-removal rule is serialized as a literal string, so relying on it leaves comments in the token stream. The original cleaner is reproduced exactly, including its regex limitations around comment-like text in string literals. The Clang hang fix remains enabled.

Cleaning affects only model inputs in memory; stored source functions and labels are preserved. The setting `preprocessing: original_vulberta_cleaner_v1` is recorded in job manifests, metrics and batch-progress signatures. Old uncleaned batches cannot be resumed as corrected batches. Earlier results are retained and should be described as using the converted tokenizer without explicit original cleaning.

Rerun **both VulBERTa datasets** into a fresh timestamped folder (LineVul does not need rerunning):

```powershell
.\localScripts\.venv\Scripts\python.exe .\localScripts\pivd_local.py --jobs vulberta-primevul vulberta-llmvul --device cuda
```

Do not pass the earlier run folder or `--resume` for this first corrected run. If the corrected run is interrupted, resume using its new folder and identical settings.

## Verification

```powershell
.\localScripts\.venv\Scripts\python.exe -m unittest discover -s localScripts -p test_local.py -v
```

The tests exercise preparation, sampling, checkpoint-loading safeguards, prediction alignment, subprocess errors, and resume validation without downloading models. A real model evaluation is still needed to validate the installed GPU environment end to end.

## Priority 5: controls and generalization diagnostics

The [Priority 5 report](../results/diagnostics/generalization_controls/rq1_priority5_diagnostics.md) adds full official
BigVul/LineVul and CodeXGLUE Devign/VulBERTa controls, documented fine-tuning
overlap screens, matched cohorts and group-bootstrap intervals. It preserves
the historical RQ1 results. The fixed diagnostic run is
`results/rq1_priority5_20261031`; downloads and large artifacts are ignored by
Git. Allow roughly 11 GB for the source downloads in addition to existing caches.

Run from the repository root in this order. Public downloads require network
access; existing downloaded sources are verified by hash. Control inference
verifies and reuses completed outputs and can resume complete JSONL rows under
an identical implementation/input signature. A torn final JSONL row causes a
failure requiring inspection, rather than silently skipping data.

```powershell
foreach ($source in @('documentation', 'devign', 'bigvul_train', 'bigvul_valid')) {
    .\localScripts\.venv\Scripts\python.exe localScripts/rq1_priority5_sources.py $source
    if ($LASTEXITCODE -ne 0) { throw "Source download failed: $source" }
}
.\localScripts\.venv\Scripts\python.exe localScripts/rq1_priority5_controls.py linevul
.\localScripts\.venv\Scripts\python.exe localScripts/rq1_priority5_controls.py vulberta
foreach ($cohort in @('bigvul_test', 'bigvul_train', 'bigvul_valid', 'devign_test', 'devign_train', 'devign_valid')) {
    .\localScripts\.venv\Scripts\python.exe localScripts/rq1_priority5_profiles.py $cohort
    if ($LASTEXITCODE -ne 0) { throw "Profiling failed: $cohort" }
}
.\localScripts\.venv\Scripts\python.exe localScripts/rq1_priority5_profiles.py overlap
.\localScripts\.venv\Scripts\python.exe localScripts/rq1_priority5_analysis.py
.\localScripts\.venv\Scripts\python.exe -m unittest discover -s localScripts -p test_rq1_priority5.py -v
.\localScripts\.venv\Scripts\python.exe localScripts/rq1_priority5_verify.py
.\localScripts\.venv\Scripts\python.exe localScripts/rq1_priority5_report.py
```

The analysis uses 2,000 related-group bootstrap draws with recorded seeds,
project-clustering sensitivity, and paired resampling for shared model cohorts.
Matching uses observed language, source length and labels, never model scores.
The original-domain controls share source projects/commits with training; they
do not establish performance on unseen projects. Independent label adjudication,
complete pretraining exposure, and original conversion/training attestation
remain unresolved; these limits are retained in the report.
