# Diagnostic evidence by subject

Each subject folder contains its existing report, machine-readable summary, and detailed run artifacts. The original `priority1` through `priority5` names identify stages of the diagnostic work plan.

| Subject | Report and summary | Detailed evidence |
| --- | --- | --- |
| Evaluation validation | [Report](evaluation_validation/rq1_diagnostics.md) · [Summary JSON](evaluation_validation/rq1_priority1_summary.json) | [Verified audit](evaluation_validation/rq1_priority1_20261028_verified) of label semantics, checkpoint loading, prediction alignment, and metrics; the [earlier audit](evaluation_validation/rq1_priority1_20261028) is retained as history. |
| Input preprocessing | [Report](input_preprocessing/rq1_priority2_diagnostics.md) · [Summary JSON](input_preprocessing/rq1_priority2_summary.json) | [Input profiles and controlled comparisons](input_preprocessing/rq1_priority2_20261028), including cleaning, truncation, parsing, and LineVul score exports. |
| Score analysis | [Report](score_analysis/rq1_priority3_diagnostics.md) · [Summary JSON](score_analysis/rq1_priority3_summary.json) | [Score-analysis artifacts](score_analysis/rq1_priority3_20261029) and [figures](score_analysis/rq1_priority3_figures): ranking, thresholds, prevalence, reliability, uncertainty, and CWEval pairs. |
| Dataset quality | [Report](dataset_quality/rq1_priority4_diagnostics.md) · [Summary JSON](dataset_quality/rq1_priority4_summary.json) | [Source and label audits](dataset_quality/rq1_priority4_20261029), duplicate sensitivity, case evidence, and the [independent-review package](dataset_quality/rq1_priority4_20261029/review/README.md). The independent review remains pending. |
| Generalization controls | [Report](generalization_controls/rq1_priority5_diagnostics.md) · [Summary JSON](generalization_controls/rq1_priority5_summary.json) | [Full BigVul and Devign controls, overlap screens, matched cohorts, and bootstrap results](generalization_controls/rq1_priority5_20261031), plus the [control/transfer figure](generalization_controls/rq1_priority5_figures/controls_and_transfer.png). |

Begin with a report for the interpretation, then its summary JSON for structured results. The dated run directories contain row-level records, manifests, source evidence, verification output, and archived implementations. JSONL files contain one JSON record per line; CSV files are tabular.

The large source datasets and prepared control inputs were organized into the dataset folders when this public copy was assembled:

| Control data | Public-copy location |
| --- | --- |
| BigVul source test/validation CSVs and lossless training CSV archive | [datasets/raw/BigVul and restoration instructions](../../datasets/raw/BigVul/README.md) |
| Devign source data and official split indices | [datasets/raw/Devign](../../datasets/raw/Devign) |
| Prepared BigVul test and Devign train/validation/test JSONL inputs, with their manifest | [datasets/pruned/controls](../../datasets/pruned/controls) |
| Original 2,000-row BigVul sample and selection record | [datasets/pruned/BigVul](../../datasets/pruned/BigVul) |

Recorded provenance paths retain the development layout. Source snapshots and archived scripts inside the evidence directories are preserved unchanged.

Return to the [final findings](../findings/README.md) or the [results index](../README.md).
