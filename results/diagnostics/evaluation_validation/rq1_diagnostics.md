# RQ1 diagnostics: priority-one results

Completed October 28, 2026. Scope: priority 1 of the [diagnostic plan](../../development/rq1_diagnostic_plan.md), covering the binary-classification and evaluation path.

Follow-up, October 29: [Priority 2 is complete](../input_preprocessing/rq1_priority2_diagnostics.md), including full input profiling, LineVul score export, and controlled cleaning/truncation comparisons. Findings below retain their priority-one scope.

## Finding

**No binary-evaluation defect was detected.** The low F1 values reproduce from the saved predictions and from fresh, frozen-model inference on the diagnostic cohort. The checks found no reversed label mapping, wrong probability column, double softmax, incorrect threshold application, row misalignment, missing trained classifier, or batch-size-dependent classification change.

This supports treating the reported scores as valid measurements of agreement with the supplied dataset labels. It does **not** establish that those labels are correct or that preprocessing preserves vulnerability-relevant code. Those questions remain for later priorities.

The audit passed **158 artifact checks and 66 inference checks**, and all **10 existing evaluator tests** passed. Historical provenance has several documented gaps; a pass on the executable checks does not eliminate those limitations.

## Reconciled results

All 89,194 prediction rows across the seven selected model/dataset jobs were checked. Counts below are recomputed from predictions; F1 is positive-class binary F1 with label 1 positive, expressed as a percentage. Source rows shared across jobs are not independent observations.

| Model / dataset | Rows | TP | FN | FP | TN | Recomputed F1 | Matches saved metrics |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| LineVul / BigVul sample | 2,000 | 96 | 16 | 3 | 1,885 | 91.00 | Yes |
| LineVul / PrimeVul | 24,788 | 119 | 430 | 1,639 | 22,600 | 10.32 | Yes |
| LineVul / LLMVul | 18,751 | 203 | 1,337 | 2,126 | 15,085 | 10.49 | Yes |
| VulBERTa / PrimeVul | 24,788 | 175 | 374 | 6,966 | 17,273 | 4.55 | Yes |
| VulBERTa / LLMVul | 18,751 | 570 | 970 | 5,883 | 11,328 | 14.26 | Yes |
| LineVul / CWEval | 58 | 0 | 29 | 0 | 29 | 0.00 | Yes |
| VulBERTa / CWEval | 58 | 18 | 11 | 16 | 13 | 57.14 | Yes |

The audit also matched accuracy, precision, recall, and run-summary entries, using both direct count formulas and scikit-learn. Macro and weighted F1 were calculated separately and preserved in the machine-readable summary; neither was substituted for the reported binary F1. LineVul/CWEval precision remains undefined because it predicts no positives, with zero used as the reporting convention.

## Checklist

| Check | Outcome | Evidence / scope |
| --- | --- | --- |
| Correct baseline selection | Pass | Only the seven selected jobs; superseded VulBERTa and RQ3 runs excluded |
| Dataset identities and completion | Pass | All jobs complete; every evaluated CSV matches its recorded SHA-256 |
| Source-to-input conversion | Pass | All evaluated code, IDs, labels, and order agree with original PrimeVul/LLMVul sources, selected CWEval catalog, or BigVul source indices |
| Binary label mapping | Supported | Source conversion and upstream training/evaluation convention agree on class 1 as vulnerable; conversion-history limit below |
| Prediction alignment | Pass | Counts, IDs where available, labels, code where exported, and VulBERTa progress scores agree; no missing/repeated prediction rows |
| Metric implementation | Pass | Confusion matrices, direct formulas, library metrics, and stored summaries agree within 1e-12 |
| Boundary cases | Pass | Hand-calculated perfect, reversed, all-negative, and mixed cases; strict 0.5 tie rule |
| Probability extraction | Pass | Forward hooks confirm exactly one softmax; correct class axis and positive column |
| Probability validity | Pass | Saved VulBERTa scores finite and in range; fresh two-class probabilities normalized within 1.20e-7 |
| Threshold rule | Pass | Both evaluators use `p(class 1) > 0.5`; every saved VulBERTa prediction matches its score |
| Trained weights and head | Pass | Strict LineVul loading; no VulBERTa missing/unexpected/mismatched weights; two-output heads; evaluation mode |
| Input shape and attention masks | Pass on cohort/batches | Expected lengths, valid vocabulary IDs, correct start/end IDs and padding masks; identical individual/batch tokenization for selected VulBERTa cases |
| Fresh prediction reproduction | Pass on cohort/batches | All 1,348 reconstructed-batch predictions match history; all 195 selected cases agree between batch sizes 1 and 16 |
| Historical code and asset provenance | Partial | Exact inference source available for every job; early launcher/tokenizer and historical VulBERTa weight-hash gaps remain |
| Source-label correctness and semantic input preservation | Not assessed here | Matching labels and valid tensor shapes do not validate vulnerability ground truth, cleaning, or retained context |

## Fresh inference and batch-size checks

Selection was fixed before rerunning inference: seed 42, up to four examples from each TP/FP/FN/TN cell for each large-dataset job, plus every CWEval function for both models. BigVul has only three false positives, so it contributes 15 selected examples. The cohort contains 195 model/function cases, not 195 independent functions.

To preserve historical batch context, each selected example was evaluated with its original neighbors in a batch of 16, including final partial batches. The selected examples were also evaluated individually. A repeated individual inference checked determinism. The batch-size comparison used the same encoded inputs; an additional check independently retokenized selected VulBERTa examples individually and confirmed identical IDs and masks.

| Model / dataset | Selected cases at both batch sizes | Rows in reconstructed original batches | Historical prediction changes | Batch-size prediction changes | Largest batch-size probability difference |
| --- | ---: | ---: | ---: | ---: | ---: |
| LineVul / BigVul sample | 15 | 224 | 0 | 0 | 9.98e-7 |
| LineVul / PrimeVul | 16 | 256 | 0 | 0 | 5.96e-8 |
| LineVul / LLMVul | 16 | 240 | 0 | 0 | 9.75e-10 |
| LineVul / CWEval | 58 | 58 | 0 | 0 | 2.18e-9 |
| VulBERTa / PrimeVul | 16 | 256 | 0 | 0 | 3.28e-7 |
| VulBERTa / LLMVul | 16 | 256 | 0 | 0 | 5.96e-7 |
| VulBERTa / CWEval | 58 | 58 | 0 | 0 | 5.36e-7 |

All **570 VulBERTa probabilities** in the reconstructed original batches exactly match the saved probability values. Historical LineVul exports contain binary predictions only, so its historical probability differences cannot be measured. New probabilities for the 195 selected cases are saved in the diagnostic output.

Inference used the same RTX 3080 Ti and recorded package versions: Python 3.12.7, PyTorch 2.7.1+cu128, Transformers 4.57.1, tokenizers 0.22.1, libclang 18.1.1, pandas 3.0.6, and scikit-learn 1.9.1. Models remained frozen. The audit reused the historical feature-conversion/model functions; it constructed the LineVul architecture locally and strictly loaded the complete trained state rather than downloading or initializing from base weights first.

## Label and implementation details

**The positive-class convention is consistent.** LineVul passes `target` unchanged into cross-entropy training and explicitly identifies label-1 true positives as vulnerable in its [pinned upstream evaluator](https://github.com/awsm-research/LineVul/blob/9401ec6e60b762a9308645961268203244bee048/linevul/linevul_main.py). Its wrapper returns softmax probabilities, despite the evaluation variable being named `logits`. Forward-hook checks confirmed that the audit uses these probabilities directly.

The [VulBERTa training notebook](https://github.com/ICL-ml4csec/VulBERTa/blob/main/Finetuning_VulBERTa-MLP.ipynb) passes Devign `target` values unchanged to cross entropy; the [evaluation notebook](https://github.com/ICL-ml4csec/VulBERTa/blob/main/Evaluation_VulBERTa-MLP.ipynb) uses probability column 1 for vulnerability metrics. [CodeXGLUE's task definition](https://github.com/microsoft/CodeXGLUE/blob/main/Code-Code/Defect-detection/README.md) assigns 1 to insecure code. The [conversion model card](https://huggingface.co/claudios/VulBERTa-MLP-Devign) identifies this as the Devign-trained MLP model. These sources support the implemented mapping; the conversion was not independently compared against the original authors' weight file.

Source inspection of two matched CWEval pairs corroborated their label meaning. The CWE-120 reference bounds `snprintf` by destination `buffer_size`; the unsafe variant substitutes a bound based on source-name length. The CWE-476 reference checks `malloc` for null before access; the unsafe variant omits that check. The catalog name `y_negative` denotes the unsafe variant and correctly maps to positive label 1. These inspections concern the specified CWEs, not proof of universal safety or a completed label-quality review.

**Two apparent configuration problems do not affect this inference path:**

- LineVul sets `config.num_labels = 1`, but its active custom classifier explicitly has two outputs. The trained two-output head loaded exactly, and the wrapper computes two-class softmax/cross entropy. The scalar configuration field does not make these runs regression or one-class evaluations.
- VulBERTa's high-level tokenizer has no registered `bos_token_id`/`eos_token_id`, but its backend template inserts IDs 0 and 2 correctly. The first diagnostic run incorrectly checked the missing properties. The audit assertion was corrected to check actual checkpoint token IDs, and the verified run passed. Attention masks and model inputs were not changed. The initial diagnostic results are retained separately.

The full saved VulBERTa probability vectors are nonconstant, with no exact 0, 1, or 0.5 values. The fresh LineVul/CWEval scores range from **0.0000491 to 0.0004128**, all far below 0.5. Its zero F1 therefore reproduces as model output under the existing input pipeline, not a tie-handling or metric-reporting artifact. This does not yet explain why the model assigns those low scores.

## Provenance and limits

The [machine-readable summary](rq1_priority1_summary.json) preserves the selected run IDs, dataset/prediction hashes, recorded settings, current model/tokenizer hashes, checks, and inference results. The large artifacts remain in `localScripts/results/rq1_priority1_20261028_verified/`.

- The generated LineVul evaluator has historical SHA-256 `346887a40012dce725a5a772cbba5382c7ff228cd46846d03f95db1e90dfc514`; the VulBERTa evaluator has `f1f6e5036d476afc4780be35ca74fcc2593a7ed7831fa157498cc48da0a563f4`. Both match the selected jobs exactly. LineVul's underlying source/model files also match its recorded Git commit, allowing only newline normalization.
- The LineVul checkpoint matches historical SHA-256 `1b18ff8e75af787520a00139bd86e70d02eb448c716290ee7b2cb20bda61a67b`.
- VulBERTa is pinned to revision `fecabdee24a3ef6e804d7629d6eed03dc6b4f61e`; its current weights hash is `cb46ffad38b612d03741ecd4a5359c6fa7d560ebaa81baf982d17f5344f97913`. Historical jobs recorded the revision, not a weight-file SHA-256. Exact score reproduction supports continuity, but cannot retroactively create that missing historical hash.
- Corrected VulBERTa and CWEval launcher versions were recovered from Git. The exact earlier launcher bytes for the three October 9 LineVul jobs could not be recovered. Their inference implementation, checkpoint, data identities, recorded arguments, and sampled predictions remain verifiable.
- Earlier LineVul jobs did not record tokenizer revision/hashes. Current tokenizer assets match the later CWEval audit, and sampled predictions reproduce, but this does not prove historical tokenizer identity for every earlier row.
- Upstream label-convention documentation was retrieved at current/main and saved with content hashes. It is supporting documentation, not a recovered record of the original training execution.
- A stratified diagnostic cohort is designed to expose implementation failures. It is not a new full-dataset evaluation or an unbiased estimator of generalization. Dataset-wide cleaning/truncation effects, source-label accuracy, training overlap, and threshold calibration remain untested here.

## Reproduction and next check

The reusable [audit script](../../../localScripts/rq1_priority1_audit.py) creates a fresh artifact manifest and then runs offline inference against it. Run from the repository root with a new output directory:

```powershell
.\localScripts\.venv\Scripts\python.exe .\localScripts\rq1_priority1_audit.py artifacts --output .\localScripts\results\rq1_priority1_repeat
.\localScripts\.venv\Scripts\python.exe .\localScripts\rq1_priority1_audit.py inference --output .\localScripts\results\rq1_priority1_repeat
.\localScripts\.venv\Scripts\python.exe -m unittest discover -s localScripts -p test_local.py -v
```

The ten evaluator tests initially encountered sandbox restrictions on temporary-file I/O. An approved unrestricted rerun passed all ten; these were environment-access failures, not evaluator test failures after execution.

No production evaluator, checkpoint, source dataset, label, threshold, or historical RQ1 result was changed. The subsequent [priority-two audit](../input_preprocessing/rq1_priority2_diagnostics.md) examines the code after cleaning and tokenization, including VulBERTa's regex cleaning and both models' truncation. Priority 1 provides no basis for flipping labels or replacing the reported F1 values.
