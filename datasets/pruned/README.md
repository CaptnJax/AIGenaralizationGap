# LineVul and VulBERTa evaluation datasets

The separate [DevGPT bundle](devgpt/README.md) uses only `snapshot_20240514`:
465 C/C++ functions with **unverified static-analysis weak labels** (12 positive,
453 negative). It includes matching LineVul/VulBERTa files and a complete audit in
`devgpt.zip`. These labels are analyzer heuristics, not vulnerability ground truth.

The separately prepared [CWEval bundle](cweval/README.md) adds a combined
58-function reference/unsafe evaluation set for both models, with all 104
candidates retained in its audit catalog. It has its own conversion protocol
and manifest; the legacy preparation details below apply to PrimeVul/LLMVul.

Prepared from the three supplied files. Original files are unchanged.
Use the same frozen checkpoint and decision rule on both test datasets.

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
- Code text is preserved exactly after decoding the original CSV/JSONL.
  No comments, whitespace or lines are removed; no functions are truncated.
- Only code is a model feature. IDs are for prediction alignment. Labels are
  ground truth. Provenance and existing analyzer outputs are not model input.
- Nine identical function bodies occur in LLMVul and PrimeVul test. These
  remain in their respective datasets. Do not pool the datasets as independent
  records without accounting for overlap.

## LineVul

linevul/*.csv contains sample_id, processed_func, target, flaw_line,
flaw_line_index. Use processed_func as input and target as the binary label.

The two flaw-line columns are EMPTY compatibility placeholders for the original
LineVul test routine. Empty means unavailable, not that a vulnerable function
has zero vulnerable lines. These datasets support function-level F1 only.
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

## Colab loading example

After uploading prepared_datasets.zip to /content:

```python
from pathlib import Path
from zipfile import ZipFile
import pandas as pd

with ZipFile('/content/prepared_datasets.zip') as z:
    z.extractall('/content')
root = Path('/content/prepared_datasets')

linevul_prime = pd.read_csv(root / 'linevul/primevul_test.csv')
linevul_llm = pd.read_csv(root / 'linevul/llmvul_test.csv')
vulberta_prime = pd.read_csv(root / 'vulberta/primevul_test.csv')
vulberta_llm = pd.read_csv(root / 'vulberta/llmvul_test.csv')

# Alternative for the original VulBERTa notebook:
vulberta_prime_pickle = pd.read_pickle(root / 'vulberta/primevul_test.pkl')
```

Run model inference separately and store sample_id with each prediction.
Compute sklearn.metrics.f1_score(y_true, y_pred, pos_label=1, average='binary',
zero_division=0) after checking predictions match the evaluated row IDs/order.
Do not encode the labels or sample IDs as input tokens.

## Verification and provenance

Every exported CSV and pickle was reloaded and checked against every selected
source row for identical IDs, exact code text, and integer labels. Source file
SHA-256 values before and after preparation match. manifest.json records counts,
versions and hashes. audit/*_provenance.jsonl links exported IDs back to original
records. source_record counts data records starting at 1, excluding headers/title;
it is not a physical CSV line number because code and messages contain newlines.

No detector was run and no F1 scores have been calculated. Dataset compatibility
was verified with pandas; checkpoint-specific inference remains to be run.

Loader references:
- https://github.com/awsm-research/LineVul/blob/main/linevul/linevul_main.py
- https://github.com/ICL-ml4csec/VulBERTa/blob/main/Evaluation_VulBERTa-MLP.ipynb
