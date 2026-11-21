# Reproduce RQ1: vulnerability-detector generalization

This repository documents our completed RQ1 investigation of cross-dataset
generalization in two transformer-based vulnerability detectors, LineVul and
VulBERTa. We evaluated their published checkpoints with frozen weights on LLMVul
(18,751 functions), drawn from AI-attributed open-source commits, and on
human-written code from PrimeVul (24,788 functions). The full BigVul test set and
the CodeXGLUE Devign test split served as original-domain controls for LineVul
and VulBERTa, respectively.

Relative to these controls, LineVul's vulnerable-class F1 fell from 91.42% on
BigVul to 10.49% on LLMVul, while VulBERTa's fell from 56.99% on Devign to 14.26%
on LLMVul. Their ROC-AUC scores on LLMVul were 0.597 and 0.553, respectively.
Both models also performed poorly on PrimeVul, with F1 scores of 10.32% and
4.55%, respectively, contextualizing the LLMVul results against independently
collected human-written code.

We examined vulnerability prevalence, dataset labeling and construction,
preprocessing, and overlap with documented training and validation data.
Matched-cohort comparisons balanced language, function length, and label
prevalence, with additional comparisons restricted to inputs passing quality
checks and excluding detected training/validation token matches. Substantial
performance gaps remained. A supplementary evaluation covered 58 CWEval
functions in 29 reference/unsafe pairs.

These findings show limited cross-dataset generalization for the evaluated
checkpoints and support evaluating vulnerability detectors on independently
collected code, including AI-attributed code. Differences in source composition,
labeling, and commit-level authorship evidence prevent attributing the gap
specifically to LLM authorship. The [final findings](results/findings/rq1_answer.md)
and [completed diagnostic analyses](results/diagnostics/README.md) provide the
supporting results and limitations.

## Start here

Install Git with Git LFS. In PowerShell, clone with text conversion disabled so
the audited dataset and tokenizer bytes retain their recorded hashes:

```powershell
git clone -c core.autocrlf=false https://github.com/CaptnJax/AIGenaralizationGap.git
cd AIGenaralizationGap
git lfs install --local
git lfs pull
git lfs fsck
```

Run subsequent commands from this repository root. A downloaded ZIP may contain
LFS pointer files instead of large data files; use the clone above for reproduction.
Python 3.12 (64-bit) is required for the documented local workflow.

| What to reproduce | Instructions | Expected output |
| --- | --- | --- |
| Published classification metrics from saved predictions | [Recalculate the scores](results/evaluation_runs/README.md#recalculate-the-published-metrics) | Nine jobs match their saved accuracy, precision, recall, and F1; no models or GPU needed. |
| Four primary frozen-model evaluations | [Local setup and runner](localScripts/README.md) | New predictions and metrics for both models on PrimeVul and LLMVul. |
| Primary dataset preparation | [Prepared dataset guide](datasets/pruned/README.md#rebuild-the-primary-datasets) | Six CSVs regenerated from the supplied raw files. |
| Supplementary CWEval preparation and inference | [CWEval guide](datasets/pruned/cweval/README.md#reproduce-and-run) | 58 functions in 29 pairs, then two frozen-model evaluations. |
| Full control, overlap, and uncertainty analyses | [Diagnostic reproduction requirements](results/diagnostics/README.md#reproduction-requirements) | Scripts read the public layout and saved earlier-stage inputs; model inference requires cached checkpoints. New controls go under `reproductions/`. |

The primary runner is documented for Windows/PowerShell and supports CUDA or CPU.
It downloads model weights on the first run; allow several GB for the environment,
cache, and outputs. Restoring the full BigVul training CSV requires additional
disk space beyond the compressed archive.

## Repository layout

- `datasets/raw/`: supplied source files and official control splits.
- [datasets/pruned](datasets/pruned/README.md): prepared inputs, manifests, and provenance.
- [localScripts](localScripts/README.md): setup, inference, preparation, and diagnostic scripts.
- [results](results/README.md): saved predictions, reports, and diagnostic evidence.

Fresh evaluations write to `localScripts/results/`; the delivered evidence is
under `results/`. Use fresh output directories for reproductions. Recorded
environments and hashes support comparisons, but hardware and package differences
can affect numerical parity. Source READMEs marked as excerpts have been edited;
historical documentation hashes refer to the original source versions.
