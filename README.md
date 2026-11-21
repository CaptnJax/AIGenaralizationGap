# **Artifact: Cross-Dataset Generalization of Vulnerability Detectors**

## Overview

This repository documents our investigation of cross-dataset generalization in two transformer-based vulnerability detectors: **LineVul** and **VulBERTa**.

We evaluated their published checkpoints with frozen weights across four datasets:

- **LLMVul (18,751 functions):** Code collected from AI-attributed open-source commits.
- **PrimeVul (24,788 functions):** Independently collected human-written code.
- **BigVul:** Original-domain test set for LineVul.
- **Devign:** Original-domain test split for VulBERTa.

## Key Results

Both detectors experienced substantial performance degradation when evaluated on LLMVul compared with their respective original-domain benchmarks.

| Detector | Original-domain F1 | LLMVul F1 | PrimeVul F1 |
| -------- | ------------------ | --------- | ----------- |
| LineVul  | 91.42% (BigVul)     | 10.49%    | 10.32%      |
| VulBERTa | 56.99% (Devign)     | 14.26%    | 4.55%       |

Their ROC-AUC scores on LLMVul were **0.597 for LineVul** and **0.553 for VulBERTa**, indicating limited ranking performance.

The results on PrimeVul provide a human-written external comparison and help contextualize the generalization gaps observed on LLMVul.

## Diagnostic Analyses

Beyond the primary evaluation, we conducted additional analyses to investigate potential factors affecting detector performance:

- **Matched-cohort evaluation:** Balanced language, function length, and vulnerability-label prevalence across datasets.
- **Input quality and preprocessing:** Examined input quality and the effects of input truncation.
- **Training/validation overlap:** Investigated overlap with documented training and validation data, including token-match filtering.
- **Prevalence analysis:** Examined how differences in vulnerability prevalence affect evaluation metrics.
- **Calibration analysis:** Assessed the reliability of predicted vulnerability scores.
- **CWEval paired evaluation:** Examined 58 functions across 29 corresponding reference/unsafe pairs.

Substantial performance gaps remained after the additional comparisons and diagnostic analyses.

## Main Takeaway

The results demonstrate limited cross-dataset generalization for the evaluated pretrained checkpoints. They highlight the importance of evaluating vulnerability detectors on independently collected code, including AI-attributed open-source code, rather than relying solely on established benchmarks.

The [final findings](results/findings/rq1_answer.md) and [completed diagnostic analyses](results/diagnostics/README.md) provide the supporting results and limitations.

## Walkthrough

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
