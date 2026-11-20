# Saved baseline evaluation runs

Each dated folder contains one completed invocation of the frozen-model evaluation runner. The name is a run ID generated from the local clock in `YYYYMMDD_HHMMSS_microseconds` format. For example, `20261009_203652_921773` means October 9, 2026 at 20:36:52.921773. The name does not encode a timezone. Original IDs are retained to match the reports and provenance records.

## What each run contains

| Run | Evaluation | How it is used in the reported baseline |
| --- | --- | --- |
| [20261009_203652_921773](20261009_203652_921773) | LineVul on the stratified 2,000-function BigVul test sample. | The original sanity check. [Summary](20261009_203652_921773/summary.csv) |
| [20261009_203942_809681](20261009_203942_809681) | Both models on PrimeVul test (24,788 functions) and labeled LLMVul (18,751 functions). | Use the two **LineVul** rows. Its two VulBERTa rows are superseded by the next run and retained as history. [Summary](20261009_203942_809681/summary.csv) |
| [20261009_211327_299195](20261009_211327_299195) | VulBERTa on the same PrimeVul and LLMVul datasets after applying the original authors' explicit cleaning step. | Use these two **corrected VulBERTa** rows for the reported comparison. [Summary](20261009_211327_299195/summary.csv) |
| [20261015_230324_309261](20261015_230324_309261) | Both models on filtered CWEval: 58 functions comprising 29 reference/unsafe pairs. | The supplementary paired diagnostic. [Summary](20261015_230324_309261/summary.csv) |

These selections are the seven jobs in the [October 15 baseline report](../findings/rq1_results.md). The later full BigVul/LineVul and Devign/VulBERTa controls are in [diagnostics/generalization_controls](../diagnostics/generalization_controls/rq1_priority5_20261031), with their [report](../diagnostics/generalization_controls/rq1_priority5_diagnostics.md).

## How to read a run

1. Open `summary.csv` and select the relevant model/dataset row using the table above. Numeric metrics are fractions from 0 to 1; the prose reports often display percentages.
2. Open the corresponding `<model>/<dataset>/metrics.json` for full-precision metrics and the confusion matrix. Positive class 1 means vulnerable/unsafe; class 0 is the supplied non-vulnerable/reference label. The decision rule is `p(vulnerable) > 0.5`.
3. Inspect the prediction file to trace individual outcomes, then use `job.json`, `environment.json`, and `test.log` for provenance and execution details.

| File within a run | Contents |
| --- | --- |
| `summary.csv` | One row per completed job, with row count, accuracy, F1, precision, recall, and threshold. |
| `environment.json` | Recorded Python/package versions and device information. |
| `<model>/<dataset>/job.json` | Completion status and the job signature, including dataset and implementation identities and execution settings. |
| `<model>/<dataset>/metrics.json` | Full-precision classification metrics and confusion matrix; VulBERTa also records model, tokenizer, and dataset metadata. |
| `linevul/<dataset>/results/raw_preds.csv` | Source rows and binary predictions in `raw_preds`; supplied labels are in `target`. Use `sample_id` where present, or the original source index for BigVul. |
| `vulberta/<dataset>/predictions.csv` | `sample_id`, supplied `label`, `prob_vulnerable`, and binary `prediction`. |
| `<model>/<dataset>/test.log` | Captured execution output. |
| `linevul/<dataset>/test_precision_recall_12heads_linevul_model.bin.pdf` | The precision-recall plot saved by the original LineVul evaluation. |
| `vulberta/<dataset>/progress.json` and `current_batch.json` | Batch/resume bookkeeping from the run. These do not represent additional evaluations. |

Preserved JSON records and logs may reference the original development paths. Dataset files are in [datasets/raw](../../datasets/raw) and [datasets/pruned](../../datasets/pruned). The evidence files in these run folders have not been regenerated or edited.

Return to the [results index](../README.md) or the [final findings](../findings/rq1_answer.md).
