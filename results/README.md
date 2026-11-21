# RQ1 results

For reproduction, begin at the [repository guide](../README.md). You can
[recalculate the saved metrics](evaluation_runs/README.md#recalculate-the-published-metrics),
[run new primary evaluations](../localScripts/README.md), or review the
[requirements for regenerating diagnostics](diagnostics/README.md#reproduction-requirements).

Start with the [consolidated RQ1 findings](findings/rq1_answer.md), covering work completed through October 31, 2026. The report includes the baseline protocol and detailed results alongside the full controls and completed diagnostic analyses.

| Folder | Contents | Where to start |
| --- | --- | --- |
| [findings](findings/README.md) | Consolidated conclusion, evaluation protocol, and detailed results. | [RQ1 answer](findings/rq1_answer.md) |
| [evaluation_runs](evaluation_runs/README.md) | The four timestamped baseline runs: saved predictions, metrics, execution logs, and environment records. | [Run guide and selection table](evaluation_runs/README.md) |
| [diagnostics](diagnostics/README.md) | Supporting evidence grouped by evaluation validity, input preprocessing, score analysis, dataset quality, and generalization controls. | [Diagnostic index](diagnostics/README.md) |
| [development](development/README.md) | Historical tokenizer debugging evidence and links to completed diagnostics. | [Development index](development/README.md) |

The latest synthesis includes the full BigVul and Devign controls in [generalization_controls](diagnostics/generalization_controls/rq1_priority5_diagnostics.md). These later controls are separate from the four baseline evaluation runs.

Reports, summary JSON files, figures, and detailed artifacts are grouped together by subject. Original run IDs and artifact filenames are retained so they can be matched to the recorded evidence. Source and prepared datasets are in [datasets/raw](../datasets/raw) and [datasets/pruned](../datasets/pruned).

Saved predictions, metrics, scripts, and machine-readable provenance records retain their original contents. Historical paths describe the development repository layout; reviewer links use this public copy's layout. Source READMEs marked as RQ1 excerpts have been pruned for scope. Documentation hashes in historical records refer to the original downloaded versions.
