# RQ1 diagnostics: priority-four results

October 29, 2026. Scope: source labels, dataset construction, provenance, duplicates, and review preparation for the seven frozen RQ1 jobs. **The automated audit and targeted source-evidence checks are complete. The planned independent two-reviewer adjudication remains pending, and CWEval security tests could not be executed in the available environment.**

**Finding: dataset quality and label definitions complicate the scores, but the measured duplicate effects and the two documented human-label disagreements do not explain the overall low F1.** There are also patch-supported vulnerabilities that both models miss. The evidence supports a combination of limited external discrimination, prevalence effects, and imperfect or context-dependent reference labels. It does not establish syntax differences from BigVul as the cause, or estimate what proportion of errors is caused by bad labels.

Historical data, predictions, thresholds, checkpoints, and RQ1 tables were preserved. All metrics here use the existing strict `p(vulnerable) > 0.5` decisions. No model inference, training, or benchmark relabeling was performed.

Validation passed: **668 artifact, sampling, provenance and numerical checks, plus eight focused unit tests**. All seven historical confusion matrices reconcile exactly. Checks include independent weighted metric calculations, all 104 pinned CWEval function/token matches, source-file hashes, review inclusion probabilities and confirmation that independent reviewer forms remain unfilled.

## 1. The datasets label different kinds of evidence

| Source | Label basis | Consequence for interpreting errors |
| --- | --- | --- |
| BigVul | Functions containing modified lines in vulnerability-related commits are labeled vulnerable | A patch-associated change is not independent proof that every changed function contains the vulnerability |
| PrimeVul | One-function security fixes or functions linked more specifically to NVD descriptions; patched and other unchanged functions receive negative labels | Better attribution rules, but runtime state, callers, and file/version context can still matter |
| LLMVul | At least two analyzer flags → vulnerable; zero → safe; exactly one → uncertain | The target is agreement with static-analysis/pattern judgments; analyzer silence does not prove safety |
| Filtered CWEval | Reference versus intentionally unsafe implementations for a specified task/CWE | Labels are task-scoped, and the 29 selected pairs are not representative of the full benchmark |

BigVul's original authors explicitly describe the changed-line rule in their [dataset documentation](https://github.com/ZeoVan/MSR_20_Code_vulnerability_CSV_Dataset). PrimeVul's [paper, section III-B](https://arxiv.org/html/2403.18624v1#S3.SS2), describes the OneFunc and NVDCheck rules; its [v0.1 documentation](https://github.com/DLVulDet/PrimeVul) explains the additional vulnerability and file metadata. These are construction rules, not independently established accuracy rates for our samples.

All **549 PrimeVul positives** have supplied CVE descriptions and commit links; **458** have file names/hashes. The local copy lacks the separate full-file context package and does not record which labeling rule justified each row. Thus the provenance is useful, but cannot substitute for reviewing the function against its patch and context.

## 2. LLMVul labels and published human review

Our 46,165,548-byte LLMVul CSV matches the published Git blob exactly: `7abfc5a4b45e992b35409660fff068aacc015dae`. The upstream snapshot and retrieved review/mining files are pinned in the evidence bundle. The audit reconciles **all 21,430 rows** with the voting rule, with **zero mismatches**:

| Semgrep / Flawfinder / pattern flags | Source label | Rows |
| --- | --- | ---: |
| 0 / 0 / 0 | safe | 17,211 |
| 1 / 0 / 0 | uncertain | 1,330 |
| 0 / 1 / 0 | uncertain | 778 |
| 0 / 0 / 1 | uncertain | 571 |
| 1 / 1 / 0 | vulnerable | 162 |
| 1 / 0 / 1 | vulnerable | 227 |
| 0 / 1 / 1 | vulnerable | 411 |
| 1 / 1 / 1 | vulnerable | 740 |

The 1,540 positives include 473 records with the Semgrep rule ID `tmp.dangerous-memcpy`, 478 with `tmp.oob-write-index`, and 411 with no Semgrep flag. Rule names and CWE fields are available, but the retrieved repository has no executed labeling implementation, pinned rule configurations/tool versions, or raw finding locations. The published Python script is explicitly a representative mining template. We cannot independently reproduce the original analyzer runs or check every finding's exact location. Multiple tools can flag the same risky operation without independently establishing exploitability.

The [LLMVul paper](https://arxiv.org/html/2609.10945v1) reports a review of 100 ensemble-positive functions and κ = 0.79. Its [published review file](https://github.com/Wahed08/LLMVul-Dataset/blob/29313663fe2a575123adf552fd339c93c345e43d/manual_validation_set/LLMVul_manual_review_100-Updated.csv) permits a more precise qualification of earlier reports' “not independently verified” wording: human-review evidence exists for a small positive-only sample; our full evaluation labels remain unadjudicated.

| Published rater values | Cases |
| --- | ---: |
| Both 1 | 83 |
| Both 0 | 2 |
| One 0 and one 1 | 1 |
| At least one undocumented `-1` | 14 |

All 100 IDs match our dataset; **99 code bodies match exactly**. Excluding the 14 cases containing `-1` reproduces **κ = 0.7943 on 86 cases**. Treating the three observed values as nominal categories yields **κ = 0.3354 on all 100**. These answer different agreement questions. The documentation describes binary ratings but does not define `-1`, so it was not converted to a binary label. No consensus column or per-case rationale is supplied; all notes are blank. Agreement is not an accuracy measure.

Two cases have `0` from both raters but remain positive in the evaluation CSV:

- `ID_289E72EB6D827C0D`: a metrics unit-test `main`, flagged for indexed writes. The exact function and full source-file hash match upstream. Array/type contracts still require included context.
- `ID_9D80D1E3ECA38FE1`: `p256_transparent_import_key`, flagged for `memcpy`, visibly checks destination capacity before copying and validates supported key sizes. Exact function and full-file hashes match upstream. This supports disagreement with the specific buffer-copy label under the API contracts, not universal safety.

Both models predict negative for these two cases. A diagnostic calculation changing **only these two labels** would move LineVul F1 **10.4937% → 10.4991%** and VulBERTa **14.2625% → 14.2660%**. The benchmark was not changed. This tiny measured effect cannot be extrapolated to unreviewed labels.

Among the **83 exact-match functions both published raters call vulnerable**, LineVul detects **8/83 (9.64%)**, and VulBERTa **34/83 (40.96%)**. This selected positive-only evidence suggests missed detections remain after using the published reviewers' judgments. It is not a representative population recall estimate and does not validate the authors' judgments independently. The sample contains no original analyzer-negative functions, so it cannot establish the reliability of the 17,211 “safe” labels.

## 3. Concrete source and context problems

Two inspected LLMVul records differ from the complete upstream function at the exact recorded commit and matching full-file hash:

| Record | Confirmed extraction problem | Historical result |
| --- | --- | --- |
| `ID_1FD8CA7AD4F7A7A6` | `cmd_plan` starts with `atic` instead of `static` and includes `st` from the next function | LineVul FN; VulBERTa TP |
| `ID_F486991D843C2E5D` | `ACLCheckAllPerm` omits its closing brace | LineVul TN; VulBERTa FP |

These problems exist in the source dataset before either model's preprocessing. The first is also the one code mismatch in the published human-review file: that file restores the initial `static` but retains the trailing fragment. Its raters give `-1` and `1`; no final judgment can be inferred.

The [published mining template](https://github.com/Wahed08/LLMVul-Dataset/blob/29313663fe2a575123adf552fd339c93c345e43d/scripts/llmvul_mine.py) parses concatenated added diff lines. It also uses tree-sitter byte offsets to slice Python strings, which is unsafe for non-ASCII text. These are plausible extraction mechanisms, not a reconstruction of the original mining execution. We did not rerun corrected inputs in this stage, so neither defect has a measured causal effect on its model prediction.

Dataset coordinates are not consistently coordinates in the complete file: `_ebpf_copy_program_entry` is stored at line 1 but starts at upstream line 106; `ACLCheckAllPerm` is stored at line 7 but starts at upstream line 1963. For **1,130 labeled and 225 uncertain records**, declared start/end spans disagree with the stored function line count. Their cause is unresolved; source coordinates must be checked before mapping analyzer or patch evidence.

The syntax-tree screen finds exactly one function definition in **23,780/24,788 PrimeVul** and **18,282/18,751 LLMVul** rows. It finds none in 749 and 330 rows, respectively. Missing macros, parser limitations, nested definitions, and extraction defects can all affect these counts; they are review flags, not confirmed invalid-code counts. All declared LLMVul languages are C or C++; PrimeVul's local source lacks a declared language. BigVul's language metadata is project-level and should not be treated as independently verified function language.

### Opposite labels for matching executable tokens

PrimeVul has **two groups, four rows**, with opposite labels after removing comments and formatting while preserving token values:

- `primevul:210834` / `primevul:440872`: `LogFilePrep`, same Xorg CVE/commit. The negative version adds a comment stating that the user-controlled format string must not run with elevated privileges. Executable tokens are unchanged; privilege/caller context is absent. VulBERTa produces identical probabilities.
- `primevul:210944` / `primevul:379328`: Vim `do_cmdline`, different commit references, differing only in two comments. Each model produces exactly the same score for both rows.

These demonstrate incompatible labels for the supplied executable token stream, potentially due to different external context or label error. They do not establish which label should be changed. There are **no exact-code label conflicts** in any evaluated dataset, nor among all LLMVul rows including uncertain records.

### Supported model misses remain

For `primevul:195399`, the [TensorFlow fix](https://github.com/tensorflow/tensorflow/commit/045deec1cbdebb27d817008ad5df94d96a08b1bf) adds a null check immediately before `IsSwitch(*input_node)`. The evaluated function lacks that check, the local CVE description agrees, and both models predict negative. For `primevul:197305`, the [PJSIP patch](https://github.com/pjsip/pjproject/commit/11559e49e65bdf00922ad5ae28913ec6a198d508) adds header-length, padding, and bit-length guards to the evaluated parser. Both models miss it; external structure/helper definitions limit a standalone exploitability assessment. QEMU `primevul:204138` links to a relevant FIFO/DMA patch, but its isolated code still lacks enough runtime-state context for an independent verdict.

These are targeted, evidence-backed assessments, not blinded two-person adjudication or a population error-rate estimate. The case notes retain 15 source IDs across 13 assessments, with source matches, diffs, model outcomes, scope, and uncertainty.

## 4. Duplicate and overlap sensitivity

Every row in a group receives weight `1/group_size`; no arbitrary representative label is selected. Token groups retain identifiers, operators and literals. Structural candidate groups additionally replace identifiers with placeholders; that can merge different APIs and genuinely different vulnerabilities, so it is a similarity sensitivity, not semantic deduplication. This is not an exhaustive fuzzy-clone search.

| Model / dataset | Original F1 | Exact-code group F1 | Token-group F1 | Structural-candidate group F1 |
| --- | ---: | ---: | ---: | ---: |
| LineVul / BigVul sample | 91.00% | 91.00% | 91.00% | 90.94% |
| LineVul / PrimeVul | 10.32% | 10.32% | 10.28% | 10.30% |
| VulBERTa / PrimeVul | 4.55% | 4.55% | 4.55% | 4.92% |
| LineVul / LLMVul | 10.49% | 10.79% | 10.78% | 10.71% |
| VulBERTa / LLMVul | 14.26% | 14.14% | 14.13% | 14.54% |
| LineVul / CWEval | 0.00% | 0.00% | 0.00% | 0.00% |
| VulBERTa / CWEval | 57.14% | 57.14% | 57.14% | 59.02% |

The 18,751 labeled LLMVul rows contain **17,874 exact code groups** and **877 extra copies**. The complete 21,430-row source contains **20,469 exact groups**, so the published “unique functions” description does not mean unique function bodies in this file. PrimeVul has seven extra token-equivalent rows; structural normalization merges many more, including legitimate vulnerable/reference variants.

There are **17 exact cross-dataset groups, 34 rows**: the nine known PrimeVul–LLMVul matches plus eight BigVul-sample–PrimeVul matches. All have negative labels. Removing them changes no LineVul F1; VulBERTa PrimeVul changes **4.5514% → 4.5597%**, and LLMVul **14.2625% → 14.2750%**. No CWEval exact overlap was found. These are test-cohort overlaps; training/pretraining overlap remains Priority 5.

Duplicates and measured cross-dataset overlap therefore do not resolve the low scores. The tables are descriptive sensitivities; changing weights also changes effective prevalence and sample composition.

## 5. Exclusions, authorship, and composition

| LLMVul property | Included binary-labeled rows | Excluded uncertain rows |
| --- | ---: | ---: |
| Rows | 18,751 | 2,679 |
| Projects | 224 | 144 |
| Declared C share | 39.42% | 55.69% |
| Median stored lines | 14 | 24 |
| Median characters | 472 | 821 |
| Strong attribution signal | 88.85% | 91.86% |
| Source parse-error flags | 3,575 | 583 |

The uncertain set is precisely the one-tool-flag population, not a random set of missing labels. Its functions are longer and more often C. Omitting them changes the evaluated population. They received no invented binary labels, predictions, or ordinary F1 scores in this audit.

Authorship signals are commit-level: the complete source has **1,685 project/commit groups**, 1,129 with multiple functions and one with 1,097. Signal metadata is identical within each group. This supports “functions drawn from AI-attributed commits,” not independent proof that each function was generated by an LLM. Some stored messages omit visible coauthor trailers; the published template truncates messages, so absence in the stored text is not disproof.

**5,071 included rows (27.04%)** have a `test`, `tests`, or `testing` path component; 393 have an explicitly named vendor/external directory component. These are narrow path hints, not exhaustive classifications. Among test-path functions F1 is **4.73% / 11.07%** for LineVul/VulBERTa; among the other 13,680 rows it is **13.03% / 15.42%**. Test scaffolding can affect what a dangerous-operation label means, but these associations are confounded by project, prevalence, and function difficulty.

VulBERTa also differs between declared C and C++ LLMVul slices: **24.26% versus 7.62% F1**. Their prevalences differ substantially (**15.07% versus 3.75%**), so this does not isolate language or syntax as the cause. Full support, prevalence, ranking and confusion-matrix values for language, project, authorship and other slices are saved in the cohort tables.

## 6. CWEval test evidence and remaining review work

Retrieved and Git-blob-verified **57 pinned upstream files**, including all 52 candidate-task test files. All 29 eligible pairs map to tests with security markers. No Docker executable or GCC/Clang executable was found on PATH, and WSL reports it is not installed. Consequently **no benchmark security tests were run**; source/test inspection is not a passing execution result.

The test audit also identifies an issue to resolve before execution-based validation: six candidate test files redefine an unsafe wrapper; two belong to eligible pairs (`cwe_078_0_cpp`, `cwe_117_0_cpp`). In the command-injection example, the later Python definition replaces the compiled-C++ unsafe wrapper with Python shell execution. Passing that unsafe test would not validate the extracted C++ unsafe body. The reference wrapper is separate. This does not invalidate the visible unsafe operation or the original static predictions.

The SSRF-labeled `cwe_918_1_c` tests check rejection of path-traversal input in a returned URL; they do not issue a network request. Its interpretation remains task/caller-scoped. Reference labels must not be read as universal safety certifications.

The new blinded review package contains **356 reproducible stratum selections merged into 328 distinct source IDs**, including all **240 selections** required for the four principal PrimeVul/LLMVul jobs. It includes both reviewer forms, code-only first-stage packets, separate source-evidence packets, a coordinator key, adjudication forms, and per-stratum/merged inclusion probabilities. Another 18 purposive selections cover 16 distinct IDs and are marked separately. Seed: `20261029`, with recorded job offsets.

**Still pending:** two qualified reviewers must independently assess the new sample and resolve disagreements. No reviewer agreement, population label-error rate, or adjudicated full-benchmark score has been fabricated. The authors' 100-case sample does not replace this review because it samples only ensemble-positive LLMVul records and uses a different design. Security execution additionally needs a supported isolated runtime and the wrapper-mapping issues addressed.

## Artifacts and reproduction

The [machine-readable summary](rq1_priority4_summary.json) combines the computed audit, external-review reconciliation, targeted notes, source identities, and limitations. Detailed evidence is in [the Priority 4 run directory](rq1_priority4_20261029), especially:

- `weighting_sensitivity.csv`, `cohort_metrics.csv`, `construction_cohort_metrics.csv`: counts, prevalence, confusion matrices and score metrics.
- `duplicate_groups.csv`, `cross_dataset_groups.jsonl`, `primevul_token_label_conflicts.json`: exact and candidate-similarity evidence.
- `external_review_join.csv`, `source_case_matches.json`, `case_review_notes.json`: published judgments and targeted source checks.
- `review/README.md`: blinded review instructions, coordinator/sample files and unfilled independent reviewer forms.
- `cweval_test_map.csv`, `sources/`: pinned source/test mappings and retrieved evidence; downloaded code was not executed.
- `analysis_plan.json`, frozen audit scripts and `verification.json`: protocol and reproducibility checks.

To repeat the computations, create a fresh run directory, copy the frozen `analysis_plan.json` and `sources` bundle into it, and run `rq1_priority4_audit.py --output <new-run>` followed by `rq1_priority4_evidence.py --output <new-run>` with the existing local Python environment. The first script refuses to overwrite an existing computed summary. Targeted evidence notes are preserved assessments, not automatically regenerated judgments. Run the focused tests with `python -m unittest discover -s localScripts -p test_rq1_priority4.py -v`.

The strongest next tests are the Priority 5 Devign control for the Devign-trained VulBERTa checkpoint, full BigVul evaluation and training-overlap checks. Those can proceed alongside independent label review; they should not be presented as resolving the remaining label uncertainty.
