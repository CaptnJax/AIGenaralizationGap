# RQ1 diagnostics: priority-two results

Started October 28 and completed October 29, 2026. Scope: priority 2 of the [diagnostic plan](../../development/rq1_diagnostic_plan.md), using the seven frozen RQ1 jobs reconciled in [priority 1](../evaluation_validation/rq1_diagnostics.md). All errors below are measured against the existing dataset labels; this audit does not independently validate those labels.

## Finding

**VulBERTa's cleaner demonstrably damages some source code, and both models discard code through truncation. These issues affect individual predictions, but the tested corrections do not explain or resolve the overall low F1.**

The lexical-preserving cleaner experiment corrected 52 errors and introduced 141 errors across 1,598 affected functions. Replacing only those tested predictions in the original cohorts would change VulBERTa F1 from **4.551% to 4.475% on PrimeVul** and **14.262% to 14.248% on LLMVul**. These are diagnostic hybrid calculations, not replacement RQ1 results or a full-cohort evaluation of a new cleaner.

Low F1 remains on functions that pass the input checks. On parse-clean, untruncated functions with unchanged lexical tokens, VulBERTa F1 is **2.48% on PrimeVul** and **13.26% on LLMVul**. All 58 CWEval functions fit both models' input budgets and show no confirmed cleaning damage, yet LineVul still has zero F1. Priority 1 found no binary-evaluation defect; priority 2 now establishes that the measured cleaning/truncation problems are insufficient as a complete explanation. Threshold/ranking behavior, source-label validity, context, and transfer remain unresolved.

## Scope and validation

The audit covers **45,597 dataset rows** and **89,194 model–dataset records**. These are not independent unique functions: exact duplicates and cross-dataset matches remain present. Each record includes sample ID, code/cleaned-code hashes, language metadata, project, duplicate group, length, lexical evidence, token counts, unknown-token fraction, truncation, label, prediction, and probability.

- Exported all 45,597 LineVul probabilities with **zero historical prediction changes**. The 195 priority-one selected scores also matched exactly. VulBERTa probabilities were joined from the corrected historical exports.
- Completed **2,095 paired input comparisons** with frozen checkpoints and the original strict `p(vulnerable) > 0.5` rule. Every baseline prediction matched history.
- All **196 unchanged-input controls** had identical input IDs and exactly identical probabilities.
- Clang checks passed on **32 sampled functions and four fixtures**, with no timeouts, errors, or lexical discrepancies between skip-body/full-body parsing or the tested C/C++ paths. This is sampled evidence, not a universal parser guarantee.
- All **six input-audit unit tests** passed: literals, comment/token boundaries, preprocessor lines, unknown flaw locations, UTF-8 cutoffs, and token-window packing.

Original source files, labels, evaluator defaults, checkpoints, thresholds, and historical RQ1 tables were preserved. The run directory retains its October 28 start date: `localScripts/results/rq1_priority2_20261028/`.

## Truncation and retained code

The exact tokenizers confirm that LineVul retains at most **510 code tokens plus two special tokens**; VulBERTa retains **1,022 plus two**. Token counts below include special tokens and precede truncation. Their different tokenizers and preprocessing make token counts incomparable as a direct measure of source complexity.

| Model / dataset | Rows | Median tokens | Truncated rows | False negatives on truncated rows |
| --- | ---: | ---: | ---: | ---: |
| LineVul / BigVul sample | 2,000 | 164 | 400 (20.00%) | 10 / 16 |
| LineVul / PrimeVul | 24,788 | 227 | 6,576 (26.53%) | 305 / 430 |
| LineVul / LLMVul | 18,751 | 207 | 3,568 (19.03%) | 648 / 1,337 |
| VulBERTa / PrimeVul | 24,788 | 135 | 1,313 (5.30%) | 97 / 374 |
| VulBERTa / LLMVul | 18,751 | 125 | 190 (1.01%) | 58 / 970 |
| LineVul / CWEval | 58 | 184.5 | 0 | 0 / 29 |
| VulBERTa / CWEval | 58 | 118 | 0 | 0 / 11 |

These are exposure counts, not counts of errors caused by truncation. PrimeVul/LLMVul have no verified local vulnerability-span annotations, so the audit cannot establish whether the omitted suffix contains the decisive flaw. Empty flaw-line placeholders were recorded as unknown.

BigVul supplies patch-derived line annotations: 85 of its 112 positive rows had annotations that matched source text; 27 lacked usable annotations. In 21 of those 85, truncation removed at least part of an annotated line. Among the 16 false negatives, only five had matched annotations, and none of those five lost an annotated line; the other 11 lacked annotations. Patch-derived lines are not independently verified vulnerability locations, and retaining them does not establish retention of all required context.

### Controlled tail-window comparison

For each model/dataset, a seed-42 sample selected up to 16 truncated functions from each TP/FP/FN/TN cell before inference. The alternative retained the last code tokens within the same positional budget. It discards the prefix and was not chosen using a known flaw location. The sample is deliberately enriched for errors and is not a population performance estimate.

| Model / dataset | Pairs | FN → TP | FP → TN | TP → FN | TN → FP |
| --- | ---: | ---: | ---: | ---: | ---: |
| LineVul / BigVul sample | 45 | 2 | 3 | 2 | 0 |
| LineVul / PrimeVul | 64 | 3 | 8 | 8 | 1 |
| LineVul / LLMVul | 64 | 0 | 5 | 3 | 0 |
| VulBERTa / PrimeVul | 64 | 2 | 2 | 2 | 3 |
| VulBERTa / LLMVul | 64 | 0 | 3 | 4 | 3 |

Changing the window can change errors in both directions. Neither model recovered a positive LLMVul case in its sampled tail experiment. These results demonstrate sensitivity to the retained context; they do not validate a tail-window remedy or rule out benefits from another context strategy.

## VulBERTa cleaning damage

The audit screened lexical leaves with C/C++ parsers and confirmed flagged changes using Clang token spellings. The alternative blanks parser-identified comments while retaining whitespace and line boundaries, and its Clang lexical stream must match the original before it is tested. This checks lexical preservation, not full semantic equivalence. Parse errors, directives, and tokenizer behavior still limit the screen's completeness.

| Dataset | Confirmed lexical changes | Confirmed changes visible in retained input | Baseline FN / FP among those visible changes | Cleaner introduces a parse error |
| --- | ---: | ---: | ---: | ---: |
| PrimeVul | 2,926 (11.80%) | 1,058 | 45 / 236 | 1,058 |
| LLMVul | 1,637 (8.73%) | 540 | 41 / 116 | 938 |
| CWEval | 0 | 0 | 0 / 0 | 0 |

For 1,868 PrimeVul and 1,096 LLMVul confirmed lexical changes, the checked retained token IDs are unchanged: the changes are outside the retained window or collapse to the same model representation. One further LLMVul case has unresolved alternative preservation; it is a historical TP. Separately, one LLMVul TN has different alternative input IDs without a confirmed Clang lexical change and is excluded from the affected-cleaner experiment. The raw `cleaner_retained_input_change` slice includes that extra TN (541 rows); the confirmed slice and experiment contain 540.

Concrete examples, with probabilities from the paired runs:

| Sample | Historical damage | Result after lexical preservation |
| --- | --- | --- |
| `primevul:413626` | The `"radr://"` literal is cut at `//`, removing the rest of that source line | FP → TN; probability 0.98488 → 0.07535 |
| `llmvul:ID_C1E7846B921CCF9B` | Removing the newline joins `NTSTATUS` to the function name | FP → TN; 0.93241 → 0.30731 |
| `primevul:434103` | Tab deletion turns `int\t\ti` into `inti`; another boundary produces `elsei` | TN → FP; 0.31245 → 0.96111 |
| `llmvul:ID_4746EE74F4E3F83A` | Newline removal changes `#define`/`#undef` and continuation-line structure | FP → TN; 0.68593 → 0.30992 |

The regression example matters: restoring source tokens does not guarantee agreement with the benchmark label. The checkpoint may depend on its training preprocessing, and label validity remains untested.

### Controlled cleaner comparison

All confirmed, model-visible cases with a lexical-preserving alternative were selected before inference. The fully untruncated comparisons isolate the cleaner without changing which end of a long function is retained. The other comparisons are separate because cleaning also changes truncation boundaries.

| Dataset / condition | Pairs | FN → TP | FP → TN | TP → FN | TN → FP |
| --- | ---: | ---: | ---: | ---: | ---: |
| PrimeVul, both inputs untruncated | 824 | 1 | 26 | 1 | 70 |
| PrimeVul, either input truncated | 234 | 1 | 8 | 3 | 7 |
| LLMVul, both inputs untruncated | 525 | 4 | 12 | 1 | 59 |
| LLMVul, either input truncated | 15 | 0 | 0 | 0 | 0 |

Across all tested cleaner cases, **52 errors were corrected and 141 introduced**. Hypothetically substituting these tested predictions while retaining every other historical prediction gives:

| Dataset | Historical TP / FN / FP / TN | Hybrid TP / FN / FP / TN | Historical F1 | Hybrid F1 |
| --- | --- | --- | ---: | ---: |
| PrimeVul | 175 / 374 / 6,966 / 17,273 | 173 / 376 / 7,009 / 17,230 | 4.551% | 4.475% |
| LLMVul | 570 / 970 / 5,883 / 11,328 | 573 / 967 / 5,930 / 11,281 | 14.262% | 14.248% |

This establishes a real input-integrity problem and some individual error recoveries, but provides no aggregate F1 improvement from the tested intervention. It does not evaluate every possible cleaner or a complete alternative training/inference pipeline.

## Errors that remain after input checks

The following descriptive subsets have different positive prevalence and difficulty. Their F1 differences must not be interpreted as causal effects of filtering.

| Model / dataset / subset | Rows | Positive prevalence | F1 |
| --- | ---: | ---: | ---: |
| LineVul / BigVul, untruncated | 1,600 | 4.06% | 95.16% |
| LineVul / PrimeVul, untruncated | 18,212 | 0.73% | 1.83% |
| LineVul / LLMVul, untruncated | 15,183 | 5.07% | 7.22% |
| VulBERTa / PrimeVul, parse-clean + untruncated + lexical screen unchanged | 17,409 | 1.49% | 2.48% |
| VulBERTa / LLMVul, same checks | 13,770 | 7.52% | 13.26% |
| LineVul / CWEval, all functions | 58 | 50.00% | 0.00% |
| VulBERTa / CWEval, all functions | 58 | 50.00% | 57.14% |

For VulBERTa, the union of truncation and visible cleaner changes covers **118/374 PrimeVul FNs (31.55%)** and **94/970 LLMVul FNs (9.69%)**; overlapping flags are counted once. The corresponding FP counts are **633/6,966** and **157/5,883**. These are upper exposure counts for the measured flags, not causal attributions or bounds on all possible input defects.

There were **no empty/degenerate tokenizations** and no LineVul unknown tokens. VulBERTa's token-weighted unknown fractions were 2.01% on PrimeVul, 2.60% on LLMVul, and 2.80% on CWEval (retained-token fractions: 1.80%, 2.56%, 2.80%). A minority of functions had much higher unknown rates: 139 PrimeVul and 284 LLMVul rows reached at least 20%. These should remain review candidates; the audit does not demonstrate an unknown-token cause of the overall score gap.

## Missing context and source uncertainty

The standalone parsers reported errors for 230/2,000 BigVul, 4,456/24,788 PrimeVul, and 3,575/18,751 LLMVul functions, versus none in CWEval. Missing macros, extensions, declarations, or extracted fragments can all cause these errors; they do not establish invalid source code or wrong labels. PrimeVul has no declared language in the local source metadata. The audit retains that unknown value separately from its heuristic C/C++ parser choice.

A seed-42 illustrative review selected nine functions missed by both models that were parse-clean, untruncated for LineVul, and unchanged by the lexical screen. This is an error-enriched context review, not independent label adjudication:

- **PrimeVul:** `primevul:195399` retains `graph.GetNode(...)` followed by `IsSwitch(*input_node)` without a local null check. Its supplied CVE description corroborates the missing-node risk. The suspicious operation is visible, while the API contract and graph construction are absent. `primevul:197305` retains protocol length/padding arithmetic but lacks structure/macro/helper definitions. `primevul:204138` depends on QEMU state, FIFO helpers, and callbacks; its supplied CVE text does not identify an exact flaw line.
- **LLMVul:** `ID_46D8AE673E2768F6` uses bounded `vsnprintf`, but its struct definition and format provenance are absent. `ID_89BF7580AD6ED9B7` has a visible output-length check but missing macro/helper contracts. `ID_176FE7F8EEAE498A` retains a copy and length checks but lacks the caller's output capacity and `furi_check` semantics. None justifies affirming or overturning its automated label from the function alone.
- **CWEval:** `cwe_078_0_cpp:y_negative` retains direct concatenation of `dir_path` into a `popen` command, yet both models miss it. The MD5 call in `cwe_327_0_c:y_negative` is also visible. Conversely, `cwe_918_1_c:y_negative` only constructs a URL, so its SSRF interpretation requires task/caller context. The prior catalog's `benchmark_checked` flag denotes static dependency screening; security tests were not executed in this audit.

These examples distinguish visible risk-bearing operations from absent contracts. They do not estimate missing-context or label-error prevalence. Full notes and the reproducible selection are saved with the run.

## Artifacts and reproduction

The [machine-readable summary](rq1_priority2_summary.json) contains counts, metrics, transitions, provenance hashes, limitations, and context-review notes. Detailed local evidence is in [the run directory](rq1_priority2_20261028):

- `profiles/*`: per-function profiles, compressed before/after lexical tokens, and a frozen profiler/manifest.
- `linevul/*.csv`: aligned full-cohort probabilities and export manifest.
- `joined_inputs.csv`: all 89,194 model–dataset records with probabilities and input flags.
- `ablations/selection.json`, `predictions.csv`, `summary.json`: fixed selections and paired predictions, with the frozen runner.
- `clang_checks/summary.json`, `examples.json`, `context_review_selection.json`, `context_review_notes.json`: parser evidence and concrete source reviews.
- `verification.json`: final artifact identities and independent numerical reconciliation.

Run from the repository root, using a new output directory. Cached checkpoints, tokenizers, original datasets, and priority-one evidence are required; inference is offline.

```powershell
$rq1Out = '.\localScripts\results\rq1_priority2_repeat'
.\localScripts\.venv\Scripts\python.exe .\localScripts\rq1_linevul_scores.py --output $rq1Out
.\localScripts\.venv\Scripts\python.exe .\localScripts\rq1_priority2_audit.py profile --output $rq1Out
.\localScripts\.venv\Scripts\python.exe .\localScripts\rq1_clang_input_check.py --output $rq1Out
.\localScripts\.venv\Scripts\python.exe .\localScripts\rq1_priority2_ablations.py --output $rq1Out
.\localScripts\.venv\Scripts\python.exe .\localScripts\rq1_priority2_summary.py --output $rq1Out
.\localScripts\.venv\Scripts\python.exe -m unittest discover -s localScripts -p test_rq1_priority2.py -v
```

The manual context-review notes are preserved evidence rather than regenerated judgments. Historical provenance limitations from priority 1 still apply, including the missing early LineVul tokenizer identity and historical VulBERTa weight hash.

**Next diagnostic step: priority 3**, using the now-aligned scores to separate weak ranking from threshold and prevalence effects. Source-label adjudication remains priority 4. The current evidence supports neither flipping labels nor replacing the reported RQ1 scores.
