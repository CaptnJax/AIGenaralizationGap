# RQ1: Frozen vulnerability-detector evaluation results

Status: October 15, 2026. Compiled from completed local evaluations; metrics were independently recomputed from saved predictions during preparation of this report.

## Summary

The completed RQ1 work evaluates how existing, frozen vulnerability detectors perform on different code datasets, with PrimeVul and LLMVul providing the principal human-written versus LLM-generated comparison. Both LineVul and VulBERTa have been evaluated on those datasets. A 2,000-function BigVul test sample provides a LineVul sanity benchmark, and a newly converted CWEval subset provides an additional paired reference/unsafe diagnostic for both models.

LineVul achieved 91.00% F1 on the BigVul sample, but only 10.32% on PrimeVul, 10.49% on LLMVul and 0.00% on filtered CWEval. Corrected VulBERTa achieved 4.55%, 14.26% and 57.14% F1 on PrimeVul, LLMVul and filtered CWEval, respectively. CWEval pair-level results are weak: LineVul classified both members correctly in 0 of 29 pairs and VulBERTa in 5 of 29.

The principal comparison does **not demonstrate an F1 decrease on LLM-generated code**: both models have higher F1 on LLMVul than on PrimeVul. Performance is poor on both large external datasets, however, and the datasets differ in label prevalence, construction and labeling practice. These results establish a performance gap across datasets; they do not establish its cause or isolate an effect of human versus LLM authorship.

## Evaluation scope and preparation

| Evaluation data | Functions | Vulnerable / unsafe (1) | Reference / non-vulnerable (0) | Role |
| --- | ---: | ---: | ---: | --- |
| BigVul test sample | 2,000 | 112 | 1,888 | LineVul sanity benchmark |
| PrimeVul test | 24,788 | 549 | 24,239 | Principal human-written-code evaluation |
| LLMVul labeled records | 18,751 | 1,540 | 17,211 | Principal LLM-generated-code evaluation |
| Filtered CWEval | 58 | 29 | 29 | Supplementary paired diagnostic |

PrimeVul's supplied validation and test files are separate splits of the same dataset. The frozen-model RQ1 evaluations use only the official test split. The 23,948-function validation split is not a second RQ1 result. Its later use in fine-tuning belongs to RQ3.

LLMVul evaluation includes all 18,751 records with a binary label. The 2,679 uncertain records are excluded. The existing labeling pipeline supplies these labels; they were not independently human-verified for this evaluation. All labeled records were retained, including 877 extra rows with identical function text. This is an external evaluation set, not a newly randomized held-out split.

PrimeVul/LLMVul conversion preserved source code, source labels and row order. The [format audit](../../dataset_format_audit.json) verified required columns, valid labels, absence of missing code, and exact agreement with source records. Nine identical function bodies occur in both evaluated datasets, without conflicting labels in the exact-code audit. The datasets are reported separately rather than pooled as independent observations.

BigVul uses a reproducible, stratified 2,000-row sample of the official test data. No completed full-BigVul evaluation or VulBERTa-on-BigVul evaluation was found in the saved local results.

### CWEval conversion

All three supplied Parquet files were processed: `core_c` (20 tasks), `core_cpp` (21 tasks) and `lang_c` (11 tasks). Their 52 tasks provide 104 reference/unsafe implementations. Every candidate is retained in an audit catalog; 58 functions form the shared evaluation set.

Target functions were matched against pinned upstream reference and unsafe implementations, extracted with C/C++ syntax parsers, and stripped of comments and surrounding harness code. Labels are 0 for the upstream reference and 1 for the intentionally unsafe variant. They describe the benchmark's specified CWE, not universal proof of safety. These implementations are not verified LLM generations, so CWEval does not independently answer the human/LLM comparison.

Complete pairs were excluded when either variant required omitted local context, changed under existing VulBERTa cleaning, exceeded either model's input limit, or had identical extracted code with opposing labels. This excluded 46 functions. Exclusion reasons overlap: local context affects 21 pairs, cleaner changes 6, LineVul truncation 10, VulBERTa truncation 2, and conflicting identical functions 1. Both models received the same selected code and labels.

The resulting set covers 22 CWEs and 22 related-problem groups. C/C++ counterparts, both variants and token-identical functions share grouping metadata. See the [CWEval protocol and manifest](../../prepared_datasets/cweval/README.md). Upstream security tests were not executed; labels were checked against source implementations.

## Model and execution protocol

Both models perform **function-level binary vulnerability classification**, not CWE-type prediction. CWE and provenance metadata are not model inputs. Line localization is disabled. Models remain frozen, with seed 42, batch size 16 and a fixed vulnerability threshold of 0.5. No RQ1 threshold tuning or fine-tuning was performed.

- **LineVul:** official wrapper at commit `9401ec6e60b762a9308645961268203244bee048`, trained `12heads_linevul_model.bin` checkpoint, CodeBERT tokenizer and 512-token limit. All four reported LineVul jobs record the same checkpoint and evaluation-implementation hashes. CWEval additionally pins and audits the local tokenizer snapshot.
- **VulBERTa:** `claudios/VulBERTa-MLP-Devign`, revision `fecabdee24a3ef6e804d7629d6eed03dc6b4f61e`, custom Clang/BPE tokenizer and 1,024-token limit. The established Clang fix skips semantic function-body parsing while retaining lexical tokenization. Reported results use `original_vulberta_cleaner_v1`: the authors' regex cleaning followed by newline/tab removal.

The original VulBERTa regex can alter comment-like text inside string literals. CWEval explicitly excludes affected pairs; an equivalent dataset-wide lexical-preservation audit has not been completed for PrimeVul/LLMVul. Their original stored code is preserved, but inference still applies the respective model's preprocessing and length limit.

Runs used an NVIDIA GeForce RTX 3080 Ti, PyTorch 2.7.1+cu128, Transformers 4.57.1, tokenizers 0.22.1, libclang 18.1.1, pandas 3.0.6 and scikit-learn 1.9.1. Checkpoint loading, settings, dataset identities and completion status are recorded in each run. LineVul's initial base-model initialization warning is followed by successful loading of the trained checkpoint; it is not evidence that these results used an untrained classifier.

## Consolidated results

All metric values below are percentages. Precision, recall and F1 use vulnerable/unsafe label 1 as the positive class.

| Model | Dataset | Accuracy | Precision | Recall | F1 |
| --- | --- | ---: | ---: | ---: | ---: |
| LineVul | BigVul sample | 99.05 | 96.97 | 85.71 | 91.00 |
| LineVul | PrimeVul test | 91.65 | 6.77 | 21.68 | 10.32 |
| LineVul | LLMVul | 81.53 | 8.72 | 13.18 | 10.49 |
| VulBERTa, corrected | PrimeVul test | 70.39 | 2.45 | 31.88 | 4.55 |
| VulBERTa, corrected | LLMVul | 63.45 | 8.83 | 37.01 | 14.26 |
| LineVul | Filtered CWEval | 50.00 | 0.00* | 0.00 | 0.00 |
| VulBERTa, corrected | Filtered CWEval | 53.45 | 52.94 | 62.07 | 57.14 |

*LineVul made no positive predictions on CWEval. Precision is therefore undefined and is recorded as zero by the reporting convention.*

| Model / dataset | True positives | False negatives | False positives | True negatives |
| --- | ---: | ---: | ---: | ---: |
| LineVul / BigVul sample | 96 | 16 | 3 | 1,885 |
| LineVul / PrimeVul | 119 | 430 | 1,639 | 22,600 |
| LineVul / LLMVul | 203 | 1,337 | 2,126 | 15,085 |
| VulBERTa / PrimeVul | 175 | 374 | 6,966 | 17,273 |
| VulBERTa / LLMVul | 570 | 970 | 5,883 | 11,328 |
| LineVul / CWEval | 0 | 29 | 0 | 29 |
| VulBERTa / CWEval | 18 | 11 | 16 | 13 |

### Interpretation of the principal comparison

LineVul's LLMVul F1 is 0.18 percentage points higher than its PrimeVul F1, although recall falls from 21.68% to 13.18%. Corrected VulBERTa's F1 rises by 9.71 percentage points, with recall rising from 31.88% to 37.01%. VulBERTa detects more labeled vulnerable functions than LineVul in each dataset but also produces substantially more false positives.

Accuracy alone obscures these weaknesses because non-vulnerable labels dominate both datasets. A classifier predicting every function as non-vulnerable would have higher accuracy than either model on each of these two datasets, while detecting no vulnerabilities. Precision, recall and the error counts therefore matter more than the apparently high LineVul accuracy.

The strong BigVul sample result shows that LineVul can detect vulnerable functions in this installation. It supports an operational sanity check, but it does not prove why performance falls elsewhere. Compatible CSV structure does not establish equivalent code patterns, vulnerability coverage, labeling practices or effective input after tokenization. Generalization difficulty is one possible explanation; dataset-specific input effects and label differences remain unseparated.

### CWEval pair analysis

| Outcome for reference/unsafe pair | LineVul | VulBERTa |
| --- | ---: | ---: |
| Both correctly classified | 0 | 5 |
| Both predicted non-vulnerable | 29 | 8 |
| Both predicted vulnerable | 0 | 13 |
| Both classifications reversed | 0 | 3 |

LineVul misses all 29 unsafe variants. VulBERTa assigns the same class to both variants in 21 of 29 pairs, correctly distinguishes five and reverses three. Its probability-based ROC AUC is 0.571, indicating weak separation on this selected set.

| CWEval subset | Functions | LineVul accuracy | VulBERTa accuracy |
| --- | ---: | ---: | ---: |
| `core_c` | 16 | 50.00% | 50.00% |
| `core_cpp` | 20 | 50.00% | 45.00% |
| `lang_c` | 22 | 50.00% | 63.64% |

CWEval's balanced labels make its F1 values unsuitable for direct interpretation as an improvement over the imbalanced PrimeVul/LLMVul results. An always-vulnerable classifier would achieve 50% accuracy and 66.67% F1 on this balanced set. VulBERTa's 57.14% F1 consequently does not, by itself, demonstrate strong vulnerability discrimination. These small, related pairs also do not support a claim of statistically established superiority between models.

## Provenance and verification

The following completed runs supply the report:

| Run | Selected results | Evidence |
| --- | --- | --- |
| `20261009_203652_921773` | LineVul / BigVul sample | [Summary](../results/20261009_203652_921773/summary.csv) |
| `20261009_203942_809681` | LineVul / PrimeVul and LLMVul only | [Summary](../results/20261009_203942_809681/summary.csv) |
| `20261009_211327_299195` | Corrected VulBERTa / PrimeVul and LLMVul | [Summary](../results/20261009_211327_299195/summary.csv) |
| `20261015_230324_309261` | Both models / CWEval | [Summary](../results/20261015_230324_309261/summary.csv) |

The earlier VulBERTa rows in run `20261009_203942_809681` are superseded by the corrected-cleaning run. Their PrimeVul/LLMVul F1 values were 4.87%/14.77%; they are retained historically but are not mixed into the main comparison. The LineVul rows from that same run remain the selected results.

For all seven selected jobs, report preparation checked completed status, current dataset SHA-256 against the recorded job, prediction count and alignment, labels, and saved confusion matrices. Accuracy, precision, recall and F1 were recomputed from predictions and matched the recorded values. VulBERTa probability-to-prediction thresholding was also verified. No models were rerun to compile this report.

Supporting documentation: [dataset preparation](../../prepared_datasets/README.md), [format audit](../../dataset_format_audit.json), [local evaluator](../README.md), [CWEval manifest](../../prepared_datasets/cweval/manifest.json), and [earlier RQ1/RQ3 progress](rq1_rq3_progress.md). Raw runs under `localScripts/results/` are Git-ignored; the tables here preserve the selected results in the repository. Those raw-result links require the local artifacts.

## Limits and remaining RQ1 work

The current evidence consists of two frozen detectors, one execution seed and existing dataset labels. No statistical significance analysis, exhaustive training-data overlap audit, or causal explanation of the performance gaps has been completed. Exact-code checks do not rule out semantic duplicates or pretraining exposure. The BigVul result is sampled; CWEval is small, filtered and grouped. LLMVul duplicates and its automated labels further limit independent-sample and ground-truth interpretations.

The next diagnostic work is to:

1. Compare actual tokenized inputs and truncation rates across BigVul, PrimeVul and LLMVul; audit how preprocessing changes code and whether relevant vulnerability context remains visible.
2. Save LineVul vulnerability probabilities, inspect representative false negatives/positives, and verify their labels. Any threshold selection should use independent development data, not optimize against these reported test sets.
3. Complete the full BigVul LineVul baseline and extend category-level analysis where reliable CWE metadata exists.
4. Quantify uncertainty using the relevant duplicate/task groups and assess dataset overlap before stronger comparative claims.

Dataset-specific fine-tuning results belong to RQ3 and are deliberately excluded from the frozen-model tables. In particular, the RQ3 LLMVul holdout has 1,676 records, whereas the RQ1 external evaluation has 18,751; those scores are not interchangeable. See the [separate fine-tuning report](finetuning_run1_cancelled.md).
