# LineVul and VulBERTa evaluation datasets

The separately prepared [CWEval bundle](cweval/README.md) adds a combined
58-function reference/unsafe evaluation set for both models, with all 104
candidates retained in its audit catalog. It has its own conversion protocol
and manifest; the primary preparation details below apply to PrimeVul/LLMVul.

The primary bundle was prepared from `datasets/raw/PrimeVul/primevul_test.jsonl`,
`datasets/raw/PrimeVul/primevul_valid.jsonl`, and
`datasets/raw/LLMVul/LLMVul_v3-Updated.csv`. Original files are unchanged.
Use the same frozen checkpoint and decision rule on both test datasets.
Start with the [RQ runner guide](../../localScripts/README.md) for inference.

| Dataset stem | Rows | Vulnerable (1) | Non-vulnerable (0) |
| --- | ---: | ---: | ---: |
| primevul_test | 24,788 | 549 | 24,239 |
| primevul_valid | 23,948 | 593 | 23,355 |
| llmvul_test | 18,751 | 1,540 | 17,211 |

## Preparation

- PrimeVul validation and test splits, labels and source order are preserved.
- LLMVul's first title line is skipped. Its 2,679 uncertain records with blank
  binary labels are excluded and listed in audit/llmvul_excluded_uncertain.csv.
- All 18,751 labeled LLMVul source records are retained as requested, including
  877 extra records with identical function text. No deduplication or balancing.
- llmvul_test names the entire labeled external evaluation set; it is not an
  official published split or a newly randomized train/test split.
- During dataset preparation, code text is preserved exactly after decoding the
  original CSV/JSONL: no comments, whitespace or lines are removed, and no
  functions are truncated. Model-specific cleaning and token limits apply during
  inference.
- Only code is a model feature. IDs are for prediction alignment. Supplied labels
  are used for scoring; this study did not independently adjudicate those labels.
  Provenance and existing analyzer outputs are not model input.
- Nine identical function bodies occur in LLMVul and PrimeVul test. These
  remain in their respective datasets. Do not pool the datasets as independent
  records without accounting for overlap.

## LineVul

linevul/*.csv contains sample_id, processed_func, target, flaw_line,
flaw_line_index. Use processed_func as input and target as the binary label.

The two flaw-line columns are EMPTY compatibility placeholders for the original
LineVul test routine. Empty means unavailable, not that a vulnerable function
has zero vulnerable lines. These datasets support function-level classification.
Leave --do_local_explanation, --do_sorting_by_line_scores, and
--do_sorting_by_pred_prob disabled. Do not report localization/line-ranking
metrics from these placeholders. Use pandas' default CSV missing-value handling
for the original routine so these blank columns are read as NaN.

Load the trained LineVul checkpoint and its original tokenizer/model wrapper;
loading only the base CodeBERT model is insufficient. Each test CSV can be
passed to --test_data_file. The validation CSV is available if independently
needed, but no training or validation is required for fixed-model inference.

## VulBERTa

vulberta/*.csv and *.pkl contain the SAME sample_id, func, label records.
CSV is the portable choice for Colab/Hugging Face. The pickle files are pandas
DataFrames for the original notebook's func/label loader branch. Adapt that
notebook's input path and checkpoint selection; merely choosing a new dataset
name in its hard-coded paths does not create a compatible model checkpoint.
These pickles use object strings, int64 labels, and pickle protocol 4.

Load func using the tokenizer/preprocessing required by the chosen fine-tuned
VulBERTa classifier. label is an integer, with 1 meaning vulnerable. The original
Devign branch uses target instead; rename label to target if using that branch.

## Load the supplied data

After the [environment setup](../../localScripts/README.md#1-set-up-the-environment),
run Python examples from the repository root. CSVs can be inspected directly
in `datasets/pruned/`; the inference runner uses the extracted `prepared_datasets/`
layout documented in its guide.

```python
from pathlib import Path
import pandas as pd

root = Path('datasets/pruned')
linevul_prime = pd.read_csv(root / 'linevul/primevul_test.csv')
linevul_llm = pd.read_csv(root / 'linevul/llmvul_test.csv')
vulberta_prime = pd.read_csv(root / 'vulberta/primevul_test.csv')
vulberta_llm = pd.read_csv(root / 'vulberta/llmvul_test.csv')
assert len(linevul_prime) == len(vulberta_prime) == 24788
assert len(linevul_llm) == len(vulberta_llm) == 18751
```

Store `sample_id` with each prediction and check IDs/order before scoring.
F1 uses vulnerable class 1, binary averaging, and `zero_division=0`.
IDs and labels are not model features.

## Rebuild the primary datasets

The converter reads the supplied files in `datasets/raw/` directly. Run it from
the repository root with a fresh output directory:

```powershell
.\localScripts\.venv\Scripts\python.exe .\localScripts\prepare_evaluation_datasets.py --output-root .\reproductions\primary\prepared_datasets
```

Expected output: `reproductions/primary/prepared_datasets/`, its manifest/audits,
and `reproductions/primary/prepared_datasets.zip`. The converter checks every
exported row against the source. Compare the six regenerated CSV hashes with
`datasets/pruned/manifest.json` using this Python example from the repository root:

```python
import hashlib, json
from pathlib import Path

expected = json.loads(Path('datasets/pruned/manifest.json').read_text(encoding='utf-8'))
for name, digest in expected['output_sha256'].items():
    if name.endswith('.csv'):
        path = Path('reproductions/primary/prepared_datasets') / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
print('All six primary CSV hashes match.')
```

Pickle serialization and generated environment metadata may vary with package
versions; use the CSVs for portable input comparisons. The generated README
describes the preparation step; this file describes the current RQ status.

## Verification and provenance

Every exported CSV and pickle was reloaded and checked against every selected
source row for identical IDs, exact code text, and integer labels. Source file
SHA-256 values before and after preparation match. manifest.json records counts,
versions and hashes. audit/*_provenance.jsonl links exported IDs back to original
records. source_record counts data records starting at 1, excluding headers/title;
it is not a physical CSV line number because code and messages contain newlines.

Both models have been evaluated on PrimeVul and LLMVul. The
[October 31, 2026 RQ findings](../../results/findings/rq1_answer.md) summarize the
completed evaluations and diagnostic analyses: the frozen checkpoints showed
limited generalization to these external datasets, but the results do not
establish a performance penalty caused specifically by LLM authorship. F1 scores
and predictions are available in the
[saved evaluation runs](../../results/evaluation_runs/README.md), including the
corrected VulBERTa runs used for the baseline comparison. See the
[RQ reproduction instructions](../../localScripts/README.md) to rerun the primary
evaluations.

Loader references:

- https://github.com/awsm-research/LineVul/blob/main/linevul/linevul_main.py
- https://github.com/ICL-ml4csec/VulBERTa/blob/main/Evaluation_VulBERTa-MLP.ipynb
