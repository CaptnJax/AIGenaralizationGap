"""Prepare lossless, function-level detector inputs; never alter source datasets.

Run: python prepare_evaluation_datasets.py
Requires pandas for optional compatibility with the original VulBERTa notebooks.
"""
import csv
import hashlib
import json
import platform
import zipfile
from collections import Counter
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "prepared_datasets"
SOURCES = ["primevul_test.jsonl", "primevul_valid.jsonl", "LLMVul_v3-Updated.csv"]
csv.field_size_limit(10_000_000)


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_source(name):
    path = ROOT / name
    if path.suffix == ".jsonl":
        with path.open(encoding="utf-8") as handle:
            rows = [json.loads(line) for line in handle if line.strip()]
        return rows
    with path.open(encoding="utf-8-sig", newline="") as handle:
        title = next(csv.reader(handle))
        assert title == ["LLMVul_v3-Updated"], title
        rows = list(csv.DictReader(handle))
    assert all(None not in row and all(v is not None for v in row.values()) for row in rows)
    return rows


def main():
    # Refuse to mix this run with an existing bundle.
    OUT.mkdir(exist_ok=False)
    for folder in ("linevul", "vulberta", "audit"):
        (OUT / folder).mkdir()
    original_hashes = {name: digest(ROOT / name) for name in SOURCES}
    report = {
        "task": "Frozen-model function-level binary vulnerability evaluation",
        "labels": {"0": "non-vulnerable", "1": "vulnerable"},
        "duplicate_policy": "Retain all labeled source records, including identical code, as requested",
        "uncertain_policy": "Exclude only LLMVul uncertain records with blank vuln_label",
        "code_policy": "Preserve exact decoded code text, comments, whitespace and newlines; no tokenization or truncation",
        "source_sha256": original_hashes,
        "runtime": {"python": platform.python_version(), "pandas": pd.__version__},
        "datasets": {},
    }
    exported_files = []
    all_ids = set()
    for source in SOURCES:
        raw = load_source(source)
        is_llm = source.endswith(".csv")
        stem = "llmvul_test" if is_llm else Path(source).stem
        selected, provenance, exclusions = [], [], []
        for ordinal, row in enumerate(raw, start=1):
            source_id = str(row["unique_id"] if is_llm else row["idx"])
            sample_id = ("llmvul:" if is_llm else "primevul:") + source_id
            assert sample_id not in all_ids, sample_id
            all_ids.add(sample_id)
            if is_llm:
                status = row["ensemble_label"]
                assert status in ("safe", "vulnerable", "uncertain")
                if status == "uncertain":
                    assert row["vuln_label"] == ""
                    exclusions.append({"sample_id": sample_id, "source_record": ordinal,
                                       "reason": "uncertain ensemble_label; missing binary vuln_label"})
                    continue
                target = {"safe": 0, "vulnerable": 1}[status]
                assert float(row["vuln_label"]) == target
                code = row["function_body"]
            else:
                target, code = row["target"], row["func"]
                assert type(target) is int and target in (0, 1)
            assert isinstance(code, str) and code.strip()
            selected.append({"sample_id": sample_id, "code": code, "target": target})
            provenance.append({
                "sample_id": sample_id, "source_file": source, "source_record": ordinal,
                "source_id": source_id, "target": target,
                "code_sha256": hashlib.sha256(code.encode("utf-8")).hexdigest(),
                "project": row.get("project_name", row.get("project")),
                "project_url": row.get("project_url"), "commit_id": row.get("commit_id"),
                "file_name": row.get("file_name"),
            })

        lv = OUT / "linevul" / f"{stem}.csv"
        vb = OUT / "vulberta" / f"{stem}.csv"
        pk = vb.with_suffix(".pkl")
        write_csv(lv, ["sample_id", "processed_func", "target", "flaw_line", "flaw_line_index"],
                  ({"sample_id": r["sample_id"], "processed_func": r["code"], "target": r["target"],
                    "flaw_line": "", "flaw_line_index": ""} for r in selected))
        write_csv(vb, ["sample_id", "func", "label"],
                  ({"sample_id": r["sample_id"], "func": r["code"], "label": r["target"]} for r in selected))
        # Explicit object strings avoid pandas 3-only StringDtype pickle requirements.
        frame = pd.DataFrame({
            "sample_id": pd.Series([r["sample_id"] for r in selected], dtype=object),
            "func": pd.Series([r["code"] for r in selected], dtype=object),
            "label": pd.Series([r["target"] for r in selected], dtype="int64"),
        })
        frame.to_pickle(pk, protocol=4)
        exported_files.extend((lv, vb, pk))
        audit = OUT / "audit" / f"{stem}_provenance.jsonl"
        with audit.open("w", encoding="utf-8", newline="\n") as handle:
            for r in provenance:
                handle.write(json.dumps(r, ensure_ascii=False) + "\n")
        if exclusions:
            write_csv(OUT / "audit" / "llmvul_excluded_uncertain.csv",
                      ["sample_id", "source_record", "reason"], exclusions)

        # Read every exported row through pandas, as the target loaders do.
        expected_ids = [r["sample_id"] for r in selected]
        expected_code = [r["code"] for r in selected]
        expected_labels = [r["target"] for r in selected]
        for path, code_col, label_col in ((lv, "processed_func", "target"), (vb, "func", "label"),
                                         (pk, "func", "label")):
            loaded = pd.read_pickle(path) if path.suffix == ".pkl" else pd.read_csv(path)
            assert loaded["sample_id"].tolist() == expected_ids
            assert loaded[code_col].tolist() == expected_code, f"Code changed: {path}"
            assert loaded[label_col].tolist() == expected_labels
            assert pd.api.types.is_integer_dtype(loaded[label_col])
            if path == lv:
                assert loaded["flaw_line"].isna().all()
                assert loaded["flaw_line_index"].isna().all()
        counts = Counter(expected_labels)
        report["datasets"][stem] = {
            "source_records": len(raw), "exported_records": len(selected),
            "non_vulnerable": counts[0], "vulnerable": counts[1],
            "excluded_uncertain": len(exclusions),
            "duplicate_code_extra_rows_retained": len(expected_code) - len(set(expected_code)),
            "split": "valid" if stem.endswith("valid") else "test",
            "split_note": "All labeled rows used as external test set" if is_llm else "Original split preserved",
            "verification": "All rows reloaded; IDs, exact code strings and integer labels match source selection",
        }
        print(stem, json.dumps(report["datasets"][stem]), flush=True)

    assert original_hashes == {name: digest(ROOT / name) for name in SOURCES}
    report["original_files_unchanged"] = True
    report["output_sha256"] = {str(p.relative_to(OUT)).replace("\\", "/"): digest(p) for p in exported_files}
    (OUT / "manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (OUT / "README.md").write_text(README, encoding="utf-8")
    archive = ROOT / "prepared_datasets.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as handle:
        for path in sorted(OUT.rglob("*")):
            if path.is_file():
                handle.write(path, path.relative_to(ROOT))
    with zipfile.ZipFile(archive) as handle:
        assert handle.testzip() is None
    print(f"Verified bundle: {archive} ({archive.stat().st_size / 1024**2:.1f} MiB)")


README = """# LineVul and VulBERTa evaluation datasets

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
"""


if __name__ == "__main__":
    main()
