# Saved baseline evaluation runs

Each dated folder contains one completed invocation of the frozen-model evaluation runner. The name is a run ID generated from the local clock in `YYYYMMDD_HHMMSS_microseconds` format. For example, `20261009_203652_921773` means October 9, 2026 at 20:36:52.921773. The name does not encode a timezone. Original IDs are retained to match the reports and provenance records.

## What each run contains

| Run | Evaluation | How it is used in the reported baseline |
| --- | --- | --- |
| [20261009_203652_921773](20261009_203652_921773) | LineVul on the stratified 2,000-function BigVul test sample. | The original sanity check. [Summary](20261009_203652_921773/summary.csv) |
| [20261009_203942_809681](20261009_203942_809681) | Both models on PrimeVul test (24,788 functions) and labeled LLMVul (18,751 functions). | Use the two **LineVul** rows. Its two VulBERTa rows are superseded by the next run and retained as history. [Summary](20261009_203942_809681/summary.csv) |
| [20261009_211327_299195](20261009_211327_299195) | VulBERTa on the same PrimeVul and LLMVul datasets after applying the original authors' explicit cleaning step. | Use these two **corrected VulBERTa** rows for the reported comparison. [Summary](20261009_211327_299195/summary.csv) |
| [20261015_230324_309261](20261015_230324_309261) | Both models on filtered CWEval: 58 functions comprising 29 reference/unsafe pairs. | The supplementary paired diagnostic. [Summary](20261015_230324_309261/summary.csv) |

These selections are the seven baseline jobs documented in the [consolidated RQ report](../findings/rq1_answer.md#detailed-classification-results). The later full BigVul/LineVul and Devign/VulBERTa controls are in [diagnostics/generalization_controls](../diagnostics/generalization_controls/rq1_priority5_20261031), with their [report](../diagnostics/generalization_controls/rq1_priority5_diagnostics.md).

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

## Recalculate the published metrics

With Python 3.12 and the repository's LFS files available, run the following
PowerShell block from the repository root. It reads the seven selected baseline
jobs and both full controls, recalculates accuracy, precision, recall, and F1,
and asserts agreement with the saved metrics to an absolute tolerance of `1e-12`.
It uses only Python's standard library and does not run model inference.
LineVul CSV predictions may be `True`/`False`; the code handles that encoding.

```powershell
@'
import csv, json, math
from collections import Counter
from pathlib import Path

csv.field_size_limit(50_000_000)
root = Path('results')
jobs = [
    ('20261009_203652_921773', 'linevul', 'bigvul_test_sample_2000'),
    ('20261009_203942_809681', 'linevul', 'primevul_test'),
    ('20261009_203942_809681', 'linevul', 'llmvul_test'),
    ('20261009_211327_299195', 'vulberta', 'primevul_test'),
    ('20261009_211327_299195', 'vulberta', 'llmvul_test'),
    ('20261015_230324_309261', 'linevul', 'cweval_test'),
    ('20261015_230324_309261', 'vulberta', 'cweval_test'),
]

def binary(value):
    return int(value == 'True') if value in ('True', 'False') else int(value)

def check(name, pairs, expected):
    counts = Counter((binary(y), binary(p)) for y, p in pairs)
    assert set(counts) <= {(0, 0), (0, 1), (1, 0), (1, 1)}
    tn, fp, fn, tp = (counts[k] for k in ((0, 0), (0, 1), (1, 0), (1, 1)))
    n = tn + fp + fn + tp
    assert n == expected['rows'], (name, n, expected['rows'])
    divide = lambda a, b: a / b if b else 0.0
    measured = dict(test_accuracy=divide(tp + tn, n),
                    test_precision=divide(tp, tp + fp),
                    test_recall=divide(tp, tp + fn),
                    test_f1=divide(2 * tp, 2 * tp + fp + fn))
    for key, value in measured.items():
        assert math.isclose(value, expected[key], rel_tol=0, abs_tol=1e-12), (name, key)
    print(f"{name}: rows={n}, F1={measured['test_f1']:.8f} (matches saved metrics)")

for run, model, dataset in jobs:
    folder = root / 'evaluation_runs' / run / model / dataset
    metrics = json.loads((folder / 'metrics.json').read_text(encoding='utf-8'))
    filename = 'results/raw_preds.csv' if model == 'linevul' else 'predictions.csv'
    label, prediction = ('target', 'raw_preds') if model == 'linevul' else ('label', 'prediction')
    with (folder / filename).open(encoding='utf-8', newline='') as stream:
        check(f'{model}/{dataset}', ((r[label], r[prediction]) for r in csv.DictReader(stream)), metrics)

controls = root / 'diagnostics/generalization_controls/rq1_priority5_20261031'
for model in ('linevul', 'vulberta'):
    folder = controls / model
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    with (folder / 'predictions.jsonl').open(encoding='utf-8') as stream:
        rows = (json.loads(line) for line in stream)
        check(f"{model}/{manifest['dataset']}", ((r['label'], r['prediction']) for r in rows),
              dict(manifest['measured'], rows=manifest['rows']))
'@ | py -3.12 -
```

If Python was installed without the Windows `py` launcher, replace
`py -3.12 -` on the last line with
`.\localScripts\.venv\Scripts\python.exe -` after the local environment setup.

Expected output is nine matching jobs. The four primary F1 values are
0.10316428 / 0.10493668 for LineVul and 0.04551365 / 0.14262480 for VulBERTa
on PrimeVul / LLMVul. The full BigVul and Devign control F1 values are
0.91419970 and 0.56989728. This check verifies metrics from saved predictions;
it does not rerun inference, ROC-AUC, matched cohorts, or bootstrap intervals.

For fresh predictions use the [runner guide](../../localScripts/README.md).
Return to the [results index](../README.md) or the [final findings](../findings/rq1_answer.md).
