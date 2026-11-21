# RQ1: Generalization of existing vulnerability detectors

Consolidated findings from the evaluations and diagnostic analyses completed through October 31, 2026. The reported evaluation labels were not independently adjudicated.

**The evaluated frozen LineVul and VulBERTa checkpoints showed limited generalization to the external code datasets. The evidence supports limited transfer across source and labeling distributions as the leading explanation for the low F1 scores, with class imbalance further reducing precision. Implementation errors are unlikely to be the main cause. However, the results do not establish a performance penalty caused specifically by LLM authorship.**

We evaluated both checkpoints on 24,788 PrimeVul test functions and 18,751 binary-labeled LLMVul functions. PrimeVul provided the principal human-written-code comparison, while LLMVul provided the AI-associated-code comparison. All reported baseline predictions used frozen weights and a fixed decision rule of `p(vulnerable) > 0.5`; no threshold tuning or fine-tuning was performed. Additional evaluations used each checkpoint's original dataset as a control: the full BigVul test set for LineVul and the CodeXGLUE Devign test split for VulBERTa. F1 refers to the vulnerable class. The intervals below are 95% percentile intervals from 2,000 resamples of related-function groups, preserving duplicates, shared commits/CVEs and task families where applicable. [Evaluation protocol](#evaluation-protocol-and-provenance); [control and uncertainty analyses](../diagnostics/generalization_controls/rq1_priority5_diagnostics.md).

| Checkpoint | Evaluation dataset | Functions | F1 | F1 95% interval | ROC-AUC |
| --- | --- | ---: | ---: | --- | ---: |
| LineVul | BigVul, original-dataset control | 18,864 | 91.42% | 90.05–92.72% | 0.979 |
| LineVul | PrimeVul | 24,788 | 10.32% | 8.39–12.55% | 0.737 |
| LineVul | LLMVul | 18,751 | 10.49% | 7.37–14.25% | 0.597 |
| VulBERTa | Devign, original-dataset control | 2,732 | 56.99% | 53.82–60.17% | 0.711 |
| VulBERTa | PrimeVul | 24,788 | 4.55% | 3.66–5.60% | 0.595 |
| VulBERTa | LLMVul | 18,751 | 14.26% | 9.81–19.61% | 0.553 |

Both models had higher F1 on LLMVul than on PrimeVul. This does not establish better detection of LLM-generated vulnerabilities: the datasets differ substantially in prevalence, source composition and labeling practice. Vulnerable labels account for 2.21% of PrimeVul and 8.21% of LLMVul. Under these conditions, false positives strongly reduce precision, and differences in prevalence affect F1. ROC-AUC provides additional evidence about score ranking: LineVul retained some discrimination on PrimeVul, but its LLMVul AUC was much lower; VulBERTa showed weak discrimination on both external datasets. The low scores therefore reflect a combination of the operating point, class prevalence and limited separation between the supplied vulnerable and non-vulnerable labels. [Score and prevalence analysis](../diagnostics/score_analysis/rq1_priority3_diagnostics.md).

The diagnostic checks make a general implementation failure an unlikely explanation. Label mapping, checkpoint loading, probability interpretation, prediction alignment and metric calculations were audited without finding a binary-evaluation defect. The full BigVul run reproduced all 2,000 earlier sample probabilities exactly, and VulBERTa reproduced the 64 historical examples used in its control-run parity check. The original-dataset controls also reproduced the expected benchmark performance. These findings support the correctness of the evaluated classification path, although they cannot exclude every possible implementation issue. [Binary-evaluation audit](../diagnostics/evaluation_validation/rq1_diagnostics.md); [control-run verification](../diagnostics/generalization_controls/rq1_priority5_diagnostics.md).

Input and dataset problems were nevertheless present. VulBERTa's inherited cleaner changed some code tokens, both models truncated long inputs, and the source audit identified extraction defects and label ambiguities. However, the tested cleaning correction did not improve aggregate F1, duplicate weighting had little effect, and poor performance remained on functions passing the input checks. These results show that the measured defects are insufficient to explain the overall performance gap; they do not establish that all remaining inputs or labels are correct. [Input audit](../diagnostics/input_preprocessing/rq1_priority2_diagnostics.md); [source-label and construction audit](../diagnostics/dataset_quality/rq1_priority4_diagnostics.md).

The strongest evidence for limited generalization comes from comparisons that matched language, function-length bins and label prevalence, restricted evaluation to parsed, untruncated functions with unchanged lexical tokens, and excluded detected token matches with each checkpoint's training and validation data. Within these model-specific cohorts, LineVul's ROC-AUC was 0.982 on BigVul, compared with 0.480 on PrimeVul and 0.528 on LLMVul. VulBERTa's corresponding AUCs were 0.748 on Devign, 0.529 on PrimeVul and 0.555 on LLMVul. The remaining gap supports a transfer limitation beyond the observed prevalence, length, language, input-defect and direct-overlap differences. These matched results describe selected common-support cohorts; they do not isolate a causal authorship effect or balance unobserved vulnerability characteristics. [Matched-cohort analysis](../diagnostics/generalization_controls/rq1_priority5_diagnostics.md).

The original-dataset controls also require caution. All BigVul test projects occurred in training, and 18,779 of its 18,864 test functions shared a training commit. Devign likewise contained the same two projects as training. On the 914 Devign test functions whose commits were absent from both training and validation, VulBERTa's AUC fell from 0.711 overall to 0.543, with a 95% group-bootstrap interval of 0.505–0.580. This demonstrates weak discrimination on unfamiliar commits within the same source projects and is consistent with limited transfer. It does not prove memorization or identify which code features the model uses. [Training-overlap and provenance analysis](../diagnostics/generalization_controls/rq1_priority5_diagnostics.md).

The supplementary CWEval results were consistent with limited discrimination: LineVul correctly classified both members of none of the 29 reference/unsafe pairs, while VulBERTa did so for five pairs. This small, filtered benchmark is a diagnostic rather than an independent human-versus-LLM comparison. [CWEval pair analysis](#cweval-pair-analysis).

The answer to RQ1 is therefore that **these frozen checkpoints did not generalize sufficiently to provide reliable vulnerability detection on the evaluated external datasets, including LLMVul**. Their original-dataset scores should not be assumed to transfer to unfamiliar code. The leading explanation is limited checkpoint generalization, with prevalence and differences in labeling and available context also affecting the measured results. Syntax or coding-style differences remain plausible contributors, but their causal role has not been demonstrated. The findings apply to the evaluated checkpoints and datasets, rather than all vulnerability detectors. LLMVul's automated labels and commit-level authorship signals, the absence of independent adjudication, incomplete pretraining-exposure records and differing vulnerability contexts prevent attributing the gap solely to model limitations or specifically to LLM-generated code.

The protocol and detailed results below consolidate the original baseline evaluations with the full controls. Saved predictions, run identities, and audit evidence remain available for reproduction.

## Evaluation protocol and provenance

The task is function-level binary vulnerability classification. Vulnerable/unsafe is label 1; non-vulnerable/reference is label 0. CWE metadata, sample IDs, and provenance are not model inputs, and line localization is disabled. All reported baseline and control predictions use frozen weights, seed 42, batch size 16, and the strict rule `p(vulnerable) > 0.5`. Exploratory score/threshold analyses did not change these predictions or select a checkpoint.

| Evaluation data | Functions | Vulnerable / unsafe (1) | Non-vulnerable / reference (0) | Role |
| --- | ---: | ---: | ---: | --- |
| BigVul test sample | 2,000 | 112 | 1,888 | Original LineVul sanity check |
| BigVul full test | 18,864 | 1,055 | 17,809 | Final LineVul original-domain control |
| Devign test | 2,732 | 1,255 | 1,477 | VulBERTa original-domain control |
| PrimeVul test | 24,788 | 549 | 24,239 | Principal human-written-code comparison |
| LLMVul labeled records | 18,751 | 1,540 | 17,211 | Principal AI-attributed-code comparison |
| Filtered CWEval | 58 | 29 | 29 | Supplementary paired diagnostic |

PrimeVul evaluations use the supplied official test split; the 23,948-function validation split is not an additional reported evaluation. LLMVul includes all binary-labeled records, including 877 extra rows with identical function text; 2,679 uncertain records were excluded. It is an external evaluation set, not a newly randomized split. Conversion preserved source code, labels, and row order. Nine identical function bodies occur in PrimeVul test and LLMVul without conflicting labels in the exact-code check; the datasets are reported separately. See the [preparation protocol](../../datasets/pruned/README.md) and [format audit](../../datasets/pruned/dataset_format_audit.json).

The 2,000-row BigVul sample was stratified by label with seed 42; its [selection record](../../datasets/pruned/BigVul/bigvul_test_sample_2000.selection.json) retains the source hash and row indices. The full control subsequently evaluated all 18,864 official test functions. Devign uses the official CodeXGLUE test indices.

- **LineVul:** wrapper commit `9401ec6e60b762a9308645961268203244bee048`, trained `12heads_linevul_model.bin` checkpoint, CodeBERT tokenizer, and a 512-token limit. The checkpoint SHA-256 is `1b18ff8e75af787520a00139bd86e70d02eb448c716290ee7b2cb20bda61a67b`. CWEval additionally pins and audits the local tokenizer snapshot.
- **VulBERTa:** `claudios/VulBERTa-MLP-Devign`, revision `fecabdee24a3ef6e804d7629d6eed03dc6b4f61e`, custom Clang/BPE tokenizer, and a 1,024-token limit. Reported results use `original_vulberta_cleaner_v1`: the authors' regex cleaner followed by newline/tab removal. The Clang adaptation skips semantic function-body parsing while retaining lexical tokenization. The completed [input audit](../diagnostics/input_preprocessing/rq1_priority2_diagnostics.md) examines cleaning and truncation effects.

The baseline runs record an NVIDIA GeForce RTX 3080 Ti, Python 3.12.7, PyTorch 2.7.1+cu128, Transformers 4.57.1, tokenizers 0.22.1, libclang 18.1.1, pandas 3.0.6, and scikit-learn 1.9.1. Per-run environment files, job signatures, and logs retain the settings and input/checkpoint identities. The successful trained-checkpoint load follows LineVul's base-model initialization warning.

| Run / evidence | Selected results |
| --- | --- |
| [20261009_203652_921773](../evaluation_runs/20261009_203652_921773/summary.csv) | LineVul / BigVul sample |
| [20261009_203942_809681](../evaluation_runs/20261009_203942_809681/summary.csv) | LineVul / PrimeVul and LLMVul |
| [20261009_211327_299195](../evaluation_runs/20261009_211327_299195/summary.csv) | Corrected VulBERTa / PrimeVul and LLMVul |
| [20261015_230324_309261](../evaluation_runs/20261015_230324_309261/summary.csv) | Both models / CWEval |
| [LineVul control manifest](../diagnostics/generalization_controls/rq1_priority5_20261031/linevul/manifest.json) | Full BigVul test |
| [VulBERTa control manifest](../diagnostics/generalization_controls/rq1_priority5_20261031/vulberta/manifest.json) | Official Devign test split |

The uncorrected VulBERTa rows in `20261009_203942_809681` had PrimeVul/LLMVul F1 values of 4.87%/14.77%. They are retained as execution history and superseded by the corrected-cleaning run; they are excluded from the reported comparison. The LineVul rows from that run remain selected.

The artifact audits verified completion, dataset hashes, prediction counts and alignment, labels, saved confusion matrices, and metric calculations. VulBERTa probabilities were checked against the fixed decision rule. The [saved-metric verification](../evaluation_runs/README.md#recalculate-the-published-metrics) recalculates all nine selected baseline/control jobs from their predictions without rerunning models.

## Detailed classification results

Accuracy, precision, recall, and F1 below are percentages. Precision, recall, and F1 use vulnerable/unsafe label 1 as the positive class. The BigVul sample is retained as a sanity-check result; the full test set supplies the final original-domain comparison.

| Model | Dataset | Accuracy | Precision | Recall | F1 |
| --- | --- | ---: | ---: | ---: | ---: |
| LineVul | BigVul sample | 99.05 | 96.97 | 85.71 | 91.00 |
| LineVul | BigVul full test | 99.09 | 97.12 | 86.35 | 91.42 |
| LineVul | PrimeVul test | 91.65 | 6.77 | 21.68 | 10.32 |
| LineVul | LLMVul | 81.53 | 8.72 | 13.18 | 10.49 |
| VulBERTa, corrected | Devign test | 64.75 | 64.84 | 50.84 | 56.99 |
| VulBERTa, corrected | PrimeVul test | 70.39 | 2.45 | 31.88 | 4.55 |
| VulBERTa, corrected | LLMVul | 63.45 | 8.83 | 37.01 | 14.26 |
| LineVul | Filtered CWEval | 50.00 | 0.00* | 0.00 | 0.00 |
| VulBERTa, corrected | Filtered CWEval | 53.45 | 52.94 | 62.07 | 57.14 |

*LineVul made no positive predictions on CWEval. Precision is undefined and recorded as zero by the reporting convention.*

| Model / dataset | True positives | False negatives | False positives | True negatives |
| --- | ---: | ---: | ---: | ---: |
| LineVul / BigVul sample | 96 | 16 | 3 | 1,885 |
| LineVul / BigVul full test | 911 | 144 | 27 | 17,782 |
| LineVul / PrimeVul | 119 | 430 | 1,639 | 22,600 |
| LineVul / LLMVul | 203 | 1,337 | 2,126 | 15,085 |
| VulBERTa / Devign | 638 | 617 | 346 | 1,131 |
| VulBERTa / PrimeVul | 175 | 374 | 6,966 | 17,273 |
| VulBERTa / LLMVul | 570 | 970 | 5,883 | 11,328 |
| LineVul / CWEval | 0 | 29 | 0 | 29 |
| VulBERTa / CWEval | 18 | 11 | 16 | 13 |

LineVul's LLMVul F1 is 0.18 percentage points higher than its PrimeVul F1, while recall falls from 21.68% to 13.18%. VulBERTa's F1 rises by 9.71 percentage points, with recall increasing from 31.88% to 37.01%. VulBERTa detects more labeled positives on both datasets but produces substantially more false positives. An always-negative classifier has higher accuracy than either model on each of these two imbalanced datasets while detecting no vulnerabilities; accuracy alone therefore obscures the detection failures.

## CWEval pair analysis

The three supplied Parquets contain 52 tasks: 20 `core_c`, 21 `core_cpp`, and 11 `lang_c`. All 104 reference/unsafe implementations are retained in the audit catalog. Target functions were matched to pinned upstream implementations, extracted with C/C++ syntax parsers, and stripped of comments and surrounding harness code. Labels describe the task's specified CWE, not universal vulnerability freedom. These implementations are not verified LLM generations, and upstream security tests were not executed.

Both variants had to match upstream, parse, preserve lexical tokens under the existing VulBERTa cleaner, fit both token limits, and have no detected dependence on omitted local context. Identical functions with opposing labels were excluded. Exclusion reasons overlap: local context affected 21 pairs, cleaner changes 6, LineVul truncation 10, VulBERTa truncation 2, and conflicting identical functions 1. The selected set contains 58 functions in 29 complete pairs, covering 22 CWEs and 22 related-problem groups. See the [CWEval preparation protocol](../../datasets/pruned/cweval/README.md) and [manifest](../../datasets/pruned/cweval/manifest.json).

| Outcome for reference/unsafe pair | LineVul | VulBERTa |
| --- | ---: | ---: |
| Both correctly classified | 0 | 5 |
| Both predicted non-vulnerable | 29 | 8 |
| Both predicted vulnerable | 0 | 13 |
| Both classifications reversed | 0 | 3 |

LineVul misses all 29 unsafe variants. VulBERTa assigns the same class to both variants in 21 pairs, correctly distinguishes five, and reverses three. Its ROC-AUC is 0.571 on this selected set.

| CWEval subset | Functions | LineVul accuracy | VulBERTa accuracy |
| --- | ---: | ---: | ---: |
| `core_c` | 16 | 50.00% | 50.00% |
| `core_cpp` | 20 | 50.00% | 45.00% |
| `lang_c` | 22 | 50.00% | 63.64% |

An always-vulnerable classifier would achieve 50% accuracy and 66.67% F1 on this balanced cohort. VulBERTa's 57.14% F1 does not establish strong discrimination or an improvement over the differently labeled and imbalanced PrimeVul/LLMVul datasets. The small, related pairs do not establish statistically significant superiority between the models.
