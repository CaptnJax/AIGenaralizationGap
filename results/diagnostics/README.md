# Diagnostic evidence by subject

Each subject folder contains its existing report, machine-readable summary, and detailed run artifacts. The original `priority1` through `priority5` names identify stages of the completed diagnostic analyses.

| Subject | Report and summary | Detailed evidence |
| --- | --- | --- |
| Evaluation validation | [Report](evaluation_validation/rq1_diagnostics.md) · [Summary JSON](evaluation_validation/rq1_priority1_summary.json) | [Verified audit](evaluation_validation/rq1_priority1_20261028_verified) of label semantics, checkpoint loading, prediction alignment, and metrics; the [earlier audit](evaluation_validation/rq1_priority1_20261028) is retained as history. |
| Input preprocessing | [Report](input_preprocessing/rq1_priority2_diagnostics.md) · [Summary JSON](input_preprocessing/rq1_priority2_summary.json) | [Input profiles and controlled comparisons](input_preprocessing/rq1_priority2_20261028), including cleaning, truncation, parsing, and LineVul score exports. |
| Score analysis | [Report](score_analysis/rq1_priority3_diagnostics.md) · [Summary JSON](score_analysis/rq1_priority3_summary.json) | [Score-analysis artifacts](score_analysis/rq1_priority3_20261029) and [figures](score_analysis/rq1_priority3_figures): ranking, thresholds, prevalence, reliability, uncertainty, and CWEval pairs. |
| Dataset quality | [Report](dataset_quality/rq1_priority4_diagnostics.md) · [Summary JSON](dataset_quality/rq1_priority4_summary.json) | [Source and label audits](dataset_quality/rq1_priority4_20261029), duplicate sensitivity, case evidence, and the [prepared review artifacts](dataset_quality/rq1_priority4_20261029/review/README.md). No completed independent reviewer judgments are included. |
| Generalization controls | [Report](generalization_controls/rq1_priority5_diagnostics.md) · [Summary JSON](generalization_controls/rq1_priority5_summary.json) | [Full BigVul and Devign controls, overlap screens, matched cohorts, and bootstrap results](generalization_controls/rq1_priority5_20261031), plus the [control/transfer figure](generalization_controls/rq1_priority5_figures/controls_and_transfer.png). |

Begin with a report for the interpretation, then its summary JSON for structured results. The dated run directories contain row-level records, manifests, source evidence, verification output, and archived implementations. JSONL files contain one JSON record per line; CSV files are tabular.

The large source datasets and prepared control inputs were organized into the dataset folders when this public copy was assembled:

| Control data | Public-copy location |
| --- | --- |
| BigVul source test/validation CSVs and lossless training CSV archive | [datasets/raw/BigVul and restoration instructions](../../datasets/raw/BigVul/README.md) |
| Devign source data and official split indices | [datasets/raw/Devign](../../datasets/raw/Devign) |
| Prepared BigVul test and Devign train/validation/test JSONL inputs, with their manifest | [datasets/pruned/controls](../../datasets/pruned/controls) |
| Original 2,000-row BigVul sample and selection record | [datasets/pruned/BigVul](../../datasets/pruned/BigVul) |

Recorded provenance paths retain the development layout. Source READMEs marked as RQ excerpts have been pruned for scope; historical documentation hashes refer to the original downloaded versions. Archived scripts and machine-readable evidence remain unchanged.

## Reproduction requirements

Run commands from the repository root. The saved evidence can be read in the public layout above. The
[metric verification example](../evaluation_runs/README.md#recalculate-the-published-metrics)
recalculates the classification metrics, including both full controls.
The active scripts under `localScripts/` read this public layout through
`rq1_paths.py`. It resolves old paths in saved manifests without editing those
manifests or relaxing their hash checks. Existing files, including runtime caches,
take precedence. Archived script copies remain historical evidence.

The reader handles these relocated inputs:

| Legacy location expected by scripts | Location in this public copy |
| --- | --- |
| `prepared_datasets/` | `datasets/pruned/` |
| Root `primevul_*.jsonl` and `LLMVul_v3-Updated.csv` | `datasets/raw/PrimeVul/` and `datasets/raw/LLMVul/` |
| `localScripts/results/<baseline-run-id>/` | `results/evaluation_runs/<baseline-run-id>/` |
| `localScripts/results/rq1_priority1_*` | `results/diagnostics/evaluation_validation/rq1_priority1_*` |
| `localScripts/results/rq1_priority2_*` | `results/diagnostics/input_preprocessing/rq1_priority2_*` |
| `localScripts/results/rq1_priority3_*` | `results/diagnostics/score_analysis/rq1_priority3_*` |
| `localScripts/results/rq1_priority4_*` | `results/diagnostics/dataset_quality/rq1_priority4_*` |
| `localScripts/results/rq1_priority5_*` | `results/diagnostics/generalization_controls/rq1_priority5_*` |
| `localScripts/reports/` | Findings in `results/findings/`; per-stage summaries/reports in the diagnostic subject folders |
| `localScripts/.cache/data/` | Full source test in `datasets/raw/BigVul/`; original sample and selection record in `datasets/pruned/BigVul/` |
| `localScripts/.cache/LineVul/` | Clone the pinned implementation with the [runner guide](../../localScripts/README.md#2-pin-the-linevul-implementation); `localScripts/upstream/LineVul/` is a source reference, not a Git checkout |
| `localScripts/.cache/huggingface/hub/` | Tokenizer snapshots in `localScripts/upstream/huggingface/`; download the matching model weights before offline inference |
| Control-run `inputs/` and large `sources/` | Prepared inputs in `datasets/pruned/controls/`; sources in `datasets/raw/BigVul/` and `datasets/raw/Devign/` |

Install dependencies and cache the pinned model weights using the
[runner guide](../../localScripts/README.md). Setup and `--dry-run` do not download
model weights; complete the guide's primary evaluations to populate the caches
before the offline diagnostic inference commands. Tokenizer-only work can use
the bundled snapshots directly; inference requires the runtime model caches.
Restore the [BigVul training CSV](../../datasets/raw/BigVul/README.md) before
the training-overlap analysis.

Run stages in this dependency order:

| Stage | Entry points under `localScripts/` | Main prerequisite and output |
| --- | --- | --- |
| Evaluation validation | `rq1_priority1_audit.py artifacts --output <new-dir>`, then `inference --output <same-dir>` | Saved baseline runs and cached models; produces artifact/inference audits and a parity cohort. |
| Input preprocessing | `rq1_priority2_audit.py`, `rq1_linevul_scores.py`, `rq1_priority2_ablations.py`, `rq1_clang_input_check.py`, `rq1_priority2_summary.py` | Verified baseline and tokenizer assets; produces profiles, score exports, and controlled comparisons. |
| Score analysis | `rq1_priority3_scores.py`, `rq1_priority3_figures.py` | Input-stage joined records; produces score curves, group-bootstrap results, and figures. |
| Dataset quality | `rq1_priority4_audit.py`, `rq1_priority4_evidence.py`, `rq1_priority4_verify.py` | Source data and earlier audits; produces row-level structure/evidence and review forms. |
| Controls and generalization | `rq1_priority5_sources.py`, `rq1_priority5_controls.py`, `rq1_priority5_profiles.py`, `rq1_priority5_analysis.py`, `rq1_priority5_verify.py`, `rq1_priority5_report.py` | Earlier stages, full BigVul/Devign splits, and cached checkpoints; produces controls, overlap screens, matching, intervals, and a report. |

Use each script's CLI help where available. The controls share the output directory
`reproductions/rq1_controls/`; set `RQ1_CONTROL_RUN` to another directory under
`reproductions/` before starting any control-stage command to make a separate run.
Its report and figures are written inside the same run. Install the
[base dependencies](../../localScripts/requirements.txt) and
[parsing/conversion dependencies](../../localScripts/requirements-cweval.txt).
The latter support the syntax-tree audits as well as CWEval conversion.

For example, recalculate score diagnostics from the supplied verified input stage,
without running models:

```powershell
.\localScripts\.venv\Scripts\python.exe .\localScripts\rq1_priority3_scores.py --output .\reproductions\rq1_scores
.\localScripts\.venv\Scripts\python.exe .\localScripts\rq1_priority3_figures.py --source .\reproductions\rq1_scores --destination .\reproductions\rq1_scores\figures
```

To rerun the controls after model setup and training-CSV restoration:

```powershell
$env:RQ1_CONTROL_RUN = 'reproductions/rq1_controls'
.\localScripts\.venv\Scripts\python.exe .\localScripts\rq1_priority5_sources.py devign
.\localScripts\.venv\Scripts\python.exe .\localScripts\rq1_priority5_sources.py bigvul_train
.\localScripts\.venv\Scripts\python.exe .\localScripts\rq1_priority5_sources.py bigvul_valid
.\localScripts\.venv\Scripts\python.exe .\localScripts\rq1_priority5_sources.py documentation
.\localScripts\.venv\Scripts\python.exe .\localScripts\rq1_priority5_controls.py prepare
.\localScripts\.venv\Scripts\python.exe .\localScripts\rq1_priority5_controls.py linevul
.\localScripts\.venv\Scripts\python.exe .\localScripts\rq1_priority5_controls.py vulberta
foreach ($split in 'bigvul_test', 'devign_test', 'devign_train', 'devign_valid', 'bigvul_train', 'bigvul_valid', 'external', 'overlap') {
    .\localScripts\.venv\Scripts\python.exe .\localScripts\rq1_priority5_profiles.py $split
    if ($LASTEXITCODE -ne 0) { throw "Profiling failed: $split" }
}
.\localScripts\.venv\Scripts\python.exe .\localScripts\rq1_priority5_analysis.py
.\localScripts\.venv\Scripts\python.exe .\localScripts\rq1_priority5_verify.py
.\localScripts\.venv\Scripts\python.exe .\localScripts\rq1_priority5_report.py
```

Source-data commands verify the supplied files instead of downloading duplicates.
The `documentation` command retrieves pinned upstream documentation. These
controls use the supplied verified input-preprocessing and dataset-quality stages.
Likewise, the score command defaults to the supplied input-preprocessing stage;
`--source` can select another verified run. The dataset-quality audit needs its
`analysis_plan.json` and `sources/` staged in the new output directory before
running its audit, evidence, and verification entry points.

Historical checks still compare byte hashes, implementations, and environments.
The evaluation audit can recover exact implementation bytes from captured
`evidence/` files, accepting them only when the full recorded SHA-256 matches.
Edited source READMEs do not match their historical documentation hashes.
Use fresh output directories: a verifier that checks the current script's identity
must be run on artifacts generated by that script, and an inference resume must
retain the same implementation, inputs, and settings.

Validation covers focused diagnostic/path tests, relocated baseline input and
prediction hashes, and dataset reconstruction. It does not include a new model
inference run or the complete diagnostic pipeline. The
[review artifacts](dataset_quality/rq1_priority4_20261029/review/README.md)
contain prepared packets and blank forms, with no independent adjudicated labels.

Return to the [final findings](../findings/README.md) or the [results index](../README.md).
