# RQ1 results

Start with the [final RQ1 findings](findings/rq1_answer.md), the October 31, 2026 synthesis of the completed evaluations and diagnostic analyses. The [October 15 results report](findings/rq1_results.md) documents the earlier baseline evaluations and their protocol.

| Folder | Contents | Where to start |
| --- | --- | --- |
| [findings](findings/README.md) | Overall conclusion and the historical baseline results report. | [RQ1 answer](findings/rq1_answer.md) |
| [evaluation_runs](evaluation_runs/README.md) | The four timestamped baseline runs: saved predictions, metrics, execution logs, and environment records. | [Run guide and selection table](evaluation_runs/README.md) |
| [diagnostics](diagnostics/README.md) | Supporting evidence grouped by evaluation validity, input preprocessing, score analysis, dataset quality, and generalization controls. | [Diagnostic index](diagnostics/README.md) |
| [development](development/README.md) | The diagnostic work plan, historical progress report, and tokenizer debugging record. | [Development index](development/README.md) |

The latest synthesis includes the full BigVul and Devign controls in [generalization_controls](diagnostics/generalization_controls/rq1_priority5_diagnostics.md). These later controls are separate from the four baseline evaluation runs.

Reports, summary JSON files, figures, and detailed artifacts are grouped together by subject. Original run IDs and artifact filenames are retained so they can be matched to the recorded evidence. Source and prepared datasets are in [datasets/raw](../datasets/raw) and [datasets/pruned](../datasets/pruned).

This organization adds navigation to existing work. Saved predictions, metrics, scripts, and machine-readable provenance records retain their original contents. Paths and hashes recorded inside those artifacts, archived source documents, and historical reproduction commands describe the development repository layout; the reviewer links in the reports use this public copy's layout.
