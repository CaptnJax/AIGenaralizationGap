# RQ1 low-F1 diagnostic plan

Prepared: October 22, 2026. Scope: diagnose the frozen-model results in [rq1_results.md](../findings/rq1_results.md). This is a plan, not a completed root-cause analysis. No model inference, threshold tuning, relabeling, or fine-tuning was performed while preparing it.

Execution update, October 31, 2026: **Priorities 1–3 and 5 completed; Priority 6 written from the available evidence; Priority 4 automated audit and targeted source checks completed, with independent adjudication pending.** The [priority-one report](../diagnostics/evaluation_validation/rq1_diagnostics.md) found no binary-evaluation defect. The [priority-two report](../diagnostics/input_preprocessing/rq1_priority2_diagnostics.md) audits 45,597 dataset rows and completes 2,095 paired input comparisons. The [priority-three report](../diagnostics/score_analysis/rq1_priority3_diagnostics.md) identifies limited external discrimination and a strong prevalence contribution. The [priority-four report](../diagnostics/dataset_quality/rq1_priority4_diagnostics.md) reconciles LLMVul voting labels and published human reviews, confirms source-extraction defects and PrimeVul token/label conflicts, and finds little effect from duplicate weighting. The [priority-five report](../diagnostics/generalization_controls/rq1_priority5_diagnostics.md) completes full BigVul and Devign controls, fine-tuning overlap screens, matched comparisons and grouped uncertainty estimates. It supports limited transfer and documents extensive shared training/test provenance, including weak VulBERTa ranking on unfamiliar Devign commits. The [RQ1 answer](../findings/rq1_answer.md) synthesizes these findings, preserves the historical results, and distinguishes the leading transfer explanation from unresolved label, context and authorship effects. Complete pretraining exposure and original converted-checkpoint training attestation remain unresolved. A blinded 328-case review package is ready; two qualified independent reviewers are still required. CWEval security execution remains unavailable in the current environment, with pinned test-wrapper issues documented.

## Objective and current evidence

Determine how much of the low vulnerable-class F1 is attributable to (1) evaluation or binary-classification implementation errors, (2) threshold choice and class prevalence, (3) damaged or incomplete model inputs, (4) dataset labels and construction, and (5) limited transfer from the checkpoint's training distribution. Several causes may coexist. Binary classification is the intended task; using two classes is not itself evidence of an error.

The report already establishes the following:

- Saved prediction metrics were independently recomputed. Dataset conversion preserved source code, labels, and order. These checks reduce the likelihood of a reporting or CSV-conversion error but do not validate source labels or the inputs after preprocessing.
- LineVul reaches 91.00% F1 on the BigVul sample. A failure affecting every LineVul evaluation is therefore less likely. This is not a complete sanity check for VulBERTa, whose checkpoint is Devign-specific.
- PrimeVul is 2.21% positive; LLMVul is 8.21% positive. LLMVul labels are automated and not independently human-verified. Its 877 duplicate extra rows and 2,679 excluded uncertain records warrant sensitivity checks.
- The VulBERTa cleaner can alter string literals. A dataset-wide audit is still missing for PrimeVul/LLMVul. Neither dataset has a completed audit of effective inputs after tokenization and truncation.
- Both models have higher F1 on LLMVul than PrimeVul. The results do not demonstrate an F1 penalty caused by LLM authorship.

Additional quantities calculated directly from the report's confusion matrices help prioritize the investigation. All entries are percentages; these are descriptive calculations, not new model results.

| Model / dataset | Positive prevalence | Recall / TPR | False-positive rate | Predicted positive | Balanced accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
| LineVul / BigVul sample | 5.60 | 85.71 | 0.16 | 4.95 | 92.78 |
| LineVul / PrimeVul | 2.21 | 21.68 | 6.76 | 7.09 | 57.46 |
| LineVul / LLMVul | 8.21 | 13.18 | 12.35 | 12.42 | 50.41 |
| VulBERTa / PrimeVul | 2.21 | 31.88 | 28.74 | 28.81 | 51.57 |
| VulBERTa / LLMVul | 8.21 | 37.01 | 34.18 | 34.41 | 51.42 |

Here FPR = FP / (FP + TN), and balanced accuracy = (TPR + 1 - FPR) / 2. Three external evaluations have TPR close to FPR at the fixed threshold. Class imbalance contributes to low precision, but it does not by itself explain this weak discrimination at that operating point. Probability-level analysis is needed before concluding that ranking is also poor.

An always-positive classifier has F1 of 4.33% on PrimeVul and 15.18% on LLMVul. Both LLMVul scores fall below that F1 baseline. This illustrates F1's sensitivity to prevalence and decision policy; always predicting vulnerable is not a proposed detector.

## Order of work

| Priority | Work | Main question | Required output |
| --- | --- | --- | --- |
| 1 | Freeze evidence and audit binary evaluation | Are the scores being computed from the correct outputs and labels? | Reconciled run manifest and pass/fail checklist |
| 2 | Audit actual inputs and recover scores | Are code meaning or relevant context lost before inference? | Per-function input audit and aligned probability files |
| 3 | Analyze scores and prevalence | Is the problem a threshold, weak ranking, or both? | Score distributions, PR/ROC curves, baseline and threshold tables |
| 4 | Review labels and dataset construction | Do reference labels and dataset membership represent the intended task? | Evidence-backed error review and cohort sensitivity tables |
| 5 | Test generalization and robustness | Does the gap persist after identified artifacts are controlled? | Original-domain controls, grouped comparisons, uncertainty estimates |
| 6 | Write the explanation | Which causes are demonstrated, plausible, or unresolved? | Diagnostic report with evidence and scoped conclusions |

Start with existing artifacts and CPU-only audits. Run small inference parity checks before any full rerun. Stages 3 and 4 can begin with existing VulBERTa scores while LineVul score export is prepared. Finding a pipeline defect takes precedence over interpreting downstream metrics.

## 1. Verify the binary-classification and evaluation path

### Preserve the exact baseline

- Use only the seven selected jobs identified in the RQ1 report: LineVul BigVul sample from `20261009_203652_921773`; LineVul PrimeVul/LLMVul from `20261009_203942_809681`; corrected VulBERTa PrimeVul/LLMVul from `20261009_211327_299195`; and both CWEval jobs from `20261015_230324_309261`.
- Record dataset, checkpoint, tokenizer, and implementation identities from the saved manifests. Distinguish the implementation used in each historical run from today's working files. Keep the superseded, uncleaned VulBERTa results out of the baseline.
- Create a new diagnostic output directory. Preserve historical files and RQ1 tables; label each new condition explicitly. Keep RQ3 checkpoints, splits, and results separate.

### Check label semantics, probabilities, alignment, and metrics

- Trace `1 = vulnerable` and `0 = non-vulnerable` from original source through conversion, loader, checkpoint training convention, output column, and metric calculation. Check checkpoint documentation/training code as well as configuration: two output classes or generic `LABEL_0`/`LABEL_1` names do not establish their meaning. Use independently verified vulnerable/fixed examples as corroboration, not as the sole mapping proof.
- Inspect the tensor path. The cached LineVul wrapper already returns softmax probabilities although the evaluation variable is named `logits`. VulBERTa uses raw `.logits.softmax(dim=-1)[:, 1]`. Verify softmax is applied exactly once, on the class axis, and column 1 is the intended positive score. Do not apply sigmoid independently to the two logits.
- Confirm both rules are exactly `p_vulnerable > 0.5`, including tie handling. Check probability ranges, finite values, class-probability sums, and constant or saturated outputs. An inverted-score diagnostic may flag a mapping problem, but changing labels solely because F1 improves is invalid.
- Join predictions by stable sample ID; verify code hash, label, row count, ordering, uniqueness, and absence of missing or repeated batches. For legacy BigVul rows, retain source indices from the saved sampling selection. Verify both models receive the same source functions.
- Independently reproduce TP, FP, FN, TN and `F1 = 2TP / (2TP + FP + FN)` with label 1 positive. Compare binary F1 with macro/weighted F1 only as additional measures; do not silently substitute them. Treat zero positive predictions as undefined precision reported as zero by convention. Include small hand-calculated cases covering all-negative predictions, perfect predictions, and reversed labels.
- Check trained weights and classifier-head loading, tokenizer compatibility, padding/attention masks, and evaluation mode. For a fixed, stratified mini-cohort, compare saved predictions with a fresh run and compare batch size 1 with the original batch size. Explain numerical differences and threshold crossings rather than demanding identical floating-point scores across devices.

**Decision:** A verified mapping, alignment, weight-loading, probability, or metric error is an implementation defect. Repair it, demonstrate the change on the same examples, and rerun only affected conditions into a new run. If these checks pass, stop treating binary classification as an unverified generic explanation.

## 2. Audit what each model actually sees

- For every evaluated function, record original language and source length; cleaned-code hash; lexical tokens before and after cleaning; token count before truncation including special tokens; retained-token count; truncation fraction; unknown-token fraction; and empty/degenerate tokenization flags. Join these to label, prediction, probability, project, and duplicate group.
- Apply the exact checkpoint tokenizers. LineVul's 512-position input retains at most 510 code tokens in its normal path. Verify VulBERTa's effective code-token budget within its 1,024-position input. Character or line counts alone cannot establish truncation.
- Extend the CWEval lexical-preservation check to PrimeVul and LLMVul. Look for comment-like sequences inside literals, newline/tab removal merging tokens, altered preprocessor directives, and incomplete code. Check the Clang skip-function-bodies modification preserves body tokens on representative C and C++ inputs, including cases parsed through the current `tmp.c` path.
- Compare truncation and cleaning damage by dataset and label, especially among false negatives. When patch evidence, verified flaw locations, or reviewed code spans exist, determine whether the vulnerability-relevant span and required context survive. Record unavailable locations as unknown; empty LineVul flaw-line placeholders are not evidence that no flaw exists.
- Inspect missing declarations, helper functions, macros, caller assumptions, and cross-function dependencies. Distinguish a genuinely function-local label from a vulnerability that cannot be determined from the supplied function alone.
- Compare metrics for damaged/intact and truncated/untruncated cohorts, with counts and label prevalence. Differences between these cohorts are associations because code difficulty also changes.
- On a fixed affected subset, compare the historical preprocessing with a lexical-preserving alternative, keeping checkpoint and threshold fixed. Use unchanged examples as controls. Treat altered cleaning as a diagnostic variant because it may also differ from training-time preprocessing. Truncation-window or added-context variants must respect the model's positional limit and be reported separately; selecting a window using the known flaw is an oracle diagnostic, not deployable performance.

**Decision:** Document concrete lost or altered code and whether correcting only that input changes the error. A large truncation rate alone does not establish that truncation caused low F1. Report how many errors each input issue can plausibly account for, including unresolved cases.

## 3. Separate threshold behavior, ranking, and prevalence

- Reuse corrected VulBERTa `predictions.csv`, which already contains `prob_vulnerable`. Extend the generated LineVul evaluation entry point to save sample ID, label, positive probability, and binary prediction without changing inference. Its current raw export contains binary predictions but not scores. Verify export parity on a small cohort, then obtain scores for the selected datasets and BigVul control in new runs.
- Plot score distributions by true label; report quantiles and predicted-positive rates. Compute ROC AUC, average precision (name the estimator explicitly), PR curves, recall at specified false-positive rates, balanced accuracy, MCC, and positive-class precision/recall/F1. Compare average precision with each dataset's positive prevalence as a no-skill reference. Report group-aware intervals rather than a single point estimate.
- Tabulate threshold behavior, including 0.5, and reliability/calibration summaries. Useful ranking with poor fixed-threshold performance motivates a threshold/calibration investigation. Ranking near chance across thresholds points toward weak discrimination, input problems, or labels; changing a threshold cannot improve the score ordering.
- Preserve the original 0.5 RQ1 result. Test-set threshold sweeps are exploratory. Any chosen threshold or calibration fit must use separate development data, followed by an untouched evaluation. PrimeVul validation is a candidate only after overlap checks. All labeled LLMVul rows have already appeared in RQ1: a retrospective partition does not create an unseen confirmatory test. Obtain independent data for a confirmatory LLMVul calibration result.
- Report always-negative and always-positive baselines, positive prevalence, TPR, and FPR. Quantify prevalence effects analytically or with class weights rather than discarding data to balance the main test set. At prevalence `pi`, holding TPR and FPR fixed, `precision = pi*TPR / (pi*TPR + (1-pi)*FPR)` and `F1 = 2*pi*TPR / (pi*(1+TPR) + (1-pi)*FPR)`. Compare datasets at one prespecified common prevalence as a sensitivity analysis. This isolates a mathematical prevalence effect under fixed class-conditional rates; it does not simulate all aspects of dataset shift.
- For all 29 CWEval pairs, inspect `p(unsafe) - p(reference)`, ties, and whether both labels are correct. LineVul's zero positive predictions could coexist with useful ordering below 0.5, which current binary outputs cannot reveal. Keep the 66.67% always-positive F1 baseline visible for this balanced set.

**Decision:** Classify the evidence as poor operating threshold, weak ranking, prevalence contribution, or a combination. Higher F1 after test-set optimization is not a validated remedy.

## 4. Audit source labels, provenance, and dataset composition

- Trace the original label rule for each source. For LLMVul, inspect how `tool_semgrep`, `tool_flawfinder`, `pattern_match`, and their evidence produce `ensemble_label`/`vuln_label`. Determine whether analyzer silence is being interpreted as safety, whether rules target actual vulnerabilities or risky patterns, and whether findings refer to the same function. Preserving source labels does not validate them.
- For PrimeVul, inspect available vulnerability/fix evidence and how labels attach to functions. For CWEval, retain the distinction between correctness for the specified CWE and universal safety. Where feasible, execute the pinned security tests in an isolated environment and map their result back to the extracted function; existing evaluations did not execute these tests.
- Check language coverage, extraction boundaries, parse failures, fragments, stubs, generated scaffolding, and missing context. Audit LLM authorship evidence using the source's `ai_tool`, `signal_strength`, and `signal_type` fields. Determine whether the signal applies to the individual function, a commit, or a repository before interpreting an authorship effect.
- Create a reproducible review sample for each model/dataset combination: 20 FN, 20 FP, 10 TP, and 10 TN, or all available cases if a stratum is smaller. For the four PrimeVul/LLMVul combinations this is at most 240 selections before merging overlapping IDs. Randomly sample within strata with a fixed seed and preserve selection probabilities. Add a separately identified purposive set of extreme-score or suspicious-input examples; do not use it to estimate dataset-wide error rates.
- Have two qualified reviewers independently assess source code and supporting patch/test evidence, initially blinded to model predictions and, where practicable, supplied labels. Resolve disagreements with evidence. Record vulnerable, non-vulnerable with stated scope, uncertain, or insufficient context; distinguish label disagreement from a confirmed label error. Automated analyzer agreement is not independent confirmation.
- For each reviewed case, retain sample ID, original label, review judgment, relevant code span, CWE if supported, provenance, confidence, and explanation. Allow multiple tags: wrong/ambiguous label, insufficient context, preprocessing damage, lost span, unsupported language, model miss, or spurious model positive. Reviewer agreement and weighted estimates must reflect the sampling design; raw percentages in an error-enriched sample are not population label-error rates.
- Evaluate original-row weighting and one-vote-per-exact-code-group weighting, then examine normalized-token/near-duplicate families. Recheck conflicts within these groups. Assess the nine known cross-dataset exact matches and any additional overlap without pooling them as independent examples.
- Profile the 2,679 excluded uncertain LLMVul records for project, language, code length, analyzer disagreement, and authorship evidence. Compare them with included records to assess selection bias. They have no usable binary ground truth; do not assign them to the negative class or include them in ordinary F1 without adjudication.

**Decision:** Use evidence-backed reviews to establish whether errors reflect wrong labels, incompatible label definitions, unverifiable examples, or real detector failures. Keep adjudicated-subset metrics separate from the original benchmark, and report review uncertainty and selection bias.

## 5. Test generalization after the preceding checks

- Complete LineVul's full official BigVul test evaluation after verifying parity with the existing sample. Establish an equivalent original-domain check for the Devign-trained VulBERTa checkpoint using the documented held-out split and preprocessing. Confirm the evaluation data were not used for training or checkpoint selection where records permit. A VulBERTa BigVul run could be an additional external comparison but is not a substitute for this Devign control.
- Audit exact and near-duplicate overlap between evaluation cohorts and available checkpoint training data. Report unavailable training/pretraining exposure as a limitation. Strong BigVul performance alone does not rule out overlap or dataset-specific shortcuts.
- Compare reliable CWE categories, language, project, function length, local versus cross-function vulnerabilities, labeling method, and authorship evidence. Publish support counts and missing metadata for every slice. Prefer recall by positive CWE when negative examples lack a meaningful CWE assignment; avoid inventing category-level precision from an invalid denominator.
- Compare matched or weighted cohorts on observable properties such as language, length, vulnerability category, and label evidence. Preserve original full-cohort results. If performance remains poor on reviewed, intact, comparable examples while original-domain controls succeed, limited transfer becomes a stronger explanation. This still does not isolate authorship causally from unmeasured differences.
- Use group bootstrap intervals for F1, precision, recall, and probability metrics. Keep code duplicates, related variants, and shared task families together; use the supplied CWEval groups rather than treating its 58 functions as independent. Assess project clustering where supported. Compare models on the same examples with paired group resampling. Record resampling seed, repetitions, grouping rules, and undefined resamples. Avoid strong category or significance claims from very small groups.

**Decision:** Describe a generalization limitation only after showing that the gap persists beyond identified implementation, input, prevalence, and label effects. Additional detectors and fine-tuning can be later work; they are not required to validate the present evaluation and belong outside the frozen RQ1 baseline.

## Deliverables and completion criteria

Save new outputs under a distinct diagnostic run, with a tracked narrative at `localScripts/reports/rq1_diagnostics.md` when execution is complete:

1. **Evidence manifest and evaluation checks:** selected runs, hashes, label mapping, alignment, loading, threshold, and metric verification outcomes.
2. **Joined function-level audit:** source ID/group, original label, model score/prediction, error type, input changes, length/truncation, and provenance. Store reviewed judgments separately with evidence links.
3. **Diagnostic figures and tables:** score distributions; PR/ROC curves; threshold and prevalence sensitivity; input, duplicate, and metadata slices; CWEval paired score changes; group-aware intervals.
4. **Cause assessment:** for every hypothesis, state the supporting observation, controlled check, number/proportion of affected errors where estimable, competing explanations, and status: demonstrated, supported, unsupported, or unresolved. Do not add overlapping cause counts as if they were disjoint or extrapolate purposive reviews to the full dataset.
5. **Report revision:** explain the observed low F1 with the strongest available evidence, retain the original results and protocol, and clearly label any corrected baseline or diagnostic variant. Identify remaining dependencies instead of inventing a single root cause.

The first useful milestone is completion of the binary path audit, existing VulBERTa probability analysis, and dataset-wide input profiling. Together these determine whether expensive reruns should target a concrete pipeline problem, probability export, or further source-label validation.

## Local implementation references

- [RQ1 report](../findings/rq1_results.md) and [format audit](../../datasets/pruned/dataset_format_audit.json): selected evidence and checks already completed.
- [Dataset converter](../../localScripts/prepare_evaluation_datasets.py): source-label mapping, uncertainty exclusion, provenance, and exact-text export.
- [Evaluation runner](../../localScripts/pivd_local.py): job signatures, checkpoint safeguards, sampling, and LineVul metric reconciliation.
- [VulBERTa evaluator](../../localScripts/vulberta_eval.py): cleaning, Clang fix, class-1 softmax, strict threshold, and probability export.
- [Cached LineVul wrapper](../../localScripts/upstream/LineVul/linevul/linevul_model.py) and [generated evaluator](../../localScripts/upstream/LineVul/linevul/linevul_main_local.py): softmax return values, effective token budget, threshold, and current raw-prediction export. These local cache files are not portable evidence; pin the upstream commit and generated implementation hash when executing the plan.
- [CWEval preparation](../../localScripts/prepare_cweval_datasets.py) and [protocol](../../datasets/pruned/cweval/README.md): reusable lexical-preservation checks, exclusions, pairing, and grouping.

Raw results and cached model files are Git-ignored. Preserve the diagnostic manifest and summarized evidence in the tracked report, and identify any artifacts needed to reproduce it.
