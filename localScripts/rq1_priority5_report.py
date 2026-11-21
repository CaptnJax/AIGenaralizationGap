"""Render the verified Priority 5 results without changing historical RQ1 tables."""
from __future__ import annotations
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from rq1_priority5_controls import RUN, jsonl
from rq1_priority5_sources import digest
import rq1_priority5_analysis as a
import rq1_priority4_audit as p4

c=a.c
NAMES={'bigvul_test':'BigVul full test','devign_test':'Devign test','primevul_test':'PrimeVul','llmvul_test':'LLMVul','cweval_test':'CWEval'}
MODELS={'linevul':'LineVul','vulberta':'VulBERTa'}


def pct(v):return '—' if v is None else f'{100*v:.2f}%'
def decimal(v):return '—' if v is None else f'{v:.3f}'
def ci(value):return f"{pct(value['low'])}–{pct(value['high'])}"


def run():
    s=c.read_json(RUN/'summary.json');v=c.read_json(RUN/'verification.json')
    assert v['status']=='pass'
    expected={r['path']:r['sha256'] for r in v['artifacts']}
    assert expected[(RUN/'summary.json').relative_to(c.ROOT).as_posix()]==digest(RUN/'summary.json')
    lookup={(r['model'],r['dataset']):r for r in s['full']}
    report=RUN/'rq1_priority5_diagnostics.md'
    figure_dir=report.parent/'rq1_priority5_figures';figure_dir.mkdir(exist_ok=True)
    fig,axes=plt.subplots(1,2,figsize=(11,5.2),layout='constrained')
    for axis,model in zip(axes,a.MODELS):
        control='bigvul_test' if model=='linevul' else 'devign_test'
        datasets=[control,'primevul_test','llmvul_test']
        for i,stem in enumerate(datasets):
            entry=lookup[model,stem];m=entry['metrics'];bounds=entry['bootstrap']['related']['intervals'][model]
            for shift,metric,color in [(-.13,'f1','#276aaf'),(.13,'roc_auc','#c15b26')]:
                y=m[metric];lo=bounds[metric]['low'];hi=bounds[metric]['high']
                axis.errorbar(i+shift,y,yerr=[[y-lo],[hi-y]],fmt='o',capsize=4,color=color,label=metric.upper().replace('ROC_AUC','ROC-AUC') if i==0 else None)
        axis.set_xticks(range(3),[NAMES[x] for x in datasets]);axis.set_ylim(0,1.03);axis.set_title(MODELS[model])
        axis.set_ylabel('Score');axis.grid(axis='y',alpha=.2);axis.legend(loc='lower left')
    fig.suptitle('Original-domain controls versus external data\n95% related-group intervals; F1 also depends on prevalence',fontsize=12)
    fig.savefig(figure_dir/'controls_and_transfer.png',dpi=180);plt.close(fig)
    lines=['# RQ1 diagnostics: priority-five results','',
        'October 31, 2026. **The original-domain controls, documented training-overlap audit, matched-cohort analyses and grouped uncertainty estimates are complete.** Independent label adjudication from Priority 4 remains pending; pretraining exposure and the original converted-checkpoint training history are not fully auditable.','',
        '**Finding:** the checkpoints reproduce their original benchmark results, but transfer poorly. The gap persists after controlling observable language, length and prevalence, screening damaged/truncated inputs, and excluding detected fine-tuning overlap. VulBERTa’s ranking also degrades on unfamiliar commits within Devign itself. This supports limited transfer as a major explanation for low F1. It does not identify syntax differences, AI authorship, or label error as a single causal explanation.','',
        f"Verification passed: **{v['checks']} checks and {v['unit_tests']} focused tests**, including independent scikit-learn point metrics, matching balance, source split membership, all overlap counts, preserved historical inputs, and an independent replication of the 2,000-draw Devign confidence intervals.",'',
        '## 1. Original-domain controls','',
        '| Model / dataset | N / positives | Prevalence | Precision | Recall | F1 | F1 95% interval | ROC-AUC | AP |',
        '| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |']
    for entry in s['full']:
        m=entry['metrics'];model=entry['model'];bounds=entry['bootstrap']['related']['intervals'][model]
        lines.append(f"| {model.title()} / {NAMES[entry['dataset']]} | {m['rows']:,} / {m['positives']:,} | {pct(m['prevalence'])} | {pct(m['precision'])} | {pct(m['recall'])} | {pct(m['f1'])} | {ci(bounds['f1'])} | {decimal(m['roc_auc'])} | {decimal(m['average_precision'])} |")
    lines+=['','Precision is displayed as zero when no functions are predicted vulnerable; undefined precision bootstrap draws are recorded separately. AP is average precision and should be interpreted against each dataset’s prevalence. These control runs add new evidence; the seven original RQ1 results and their thresholds remain unchanged.','',
        '![Control and transfer scores](rq1_priority5_figures/controls_and_transfer.png)','',
        'LineVul used all **18,864** functions in the official test CSV. All **2,000** earlier sample probabilities and predictions matched exactly, both in the preliminary parity check and embedded in the full run. Its full-test confusion matrix is **TN 17,782 / FP 27 / FN 144 / TP 911**.','']
    vb=c.read_json(RUN/'vulberta/manifest.json');vm=vb['measured'];cm=vm['confusion_matrix']
    lines += [f"VulBERTa used the official CodeXGLUE **2,732-row Devign test split**, with **1,255 positives**, after passing parity on 64 existing PrimeVul/LLMVul examples (maximum score difference {vb['max_parity_delta']:.3g}). Its confusion matrix is **TN {cm['tn']:,} / FP {cm['fp']:,} / FN {cm['fn']:,} / TP {cm['tp']:,}**. The pinned conversion’s model card reports 56.93% F1; this run measures {pct(vm['test_f1'])}. The run uses the previously audited explicit author cleaner and local Clang adaptation; it is not a byte-for-byte reproduction of the author’s original environment.",'',
        'Both evaluations retain frozen weights, class 1 = vulnerable, strict `p > 0.5`, batch 16, seed 42, and the existing 512/1,024-token limits. No fitting, calibration, threshold selection or new checkpoint selection occurred.','',
        'The [pinned VulBERTa model card](https://huggingface.co/claudios/VulBERTa-MLP-Devign/blob/fecabdee24a3ef6e804d7629d6eed03dc6b4f61e/README.md) identifies an unofficial conversion fine-tuned on CodeXGLUE Devign. The [CodeXGLUE split](https://github.com/microsoft/CodeXGLUE/tree/ac74a62802a0dd159b3258c78a2df8ad36cdf2b9/Code-Code/Defect-detection) has 21,854 train / 2,732 validation / 2,732 test rows. The author’s [fine-tuning notebook](https://github.com/ICL-ml4csec/VulBERTa/blob/75ab355bf8be124751084c0ff3563df24f48fe38/Finetuning_VulBERTa-MLP.ipynb) uses train/validation indices, with test indices in a separate evaluation notebook. LineVul’s [published implementation](https://github.com/awsm-research/LineVul/tree/9401ec6e60b762a9308645961268203244bee048) saves its best validation-F1 checkpoint. These records support the intended protocol; they do not prove the actual converted checkpoint’s complete history. The author’s separate OneDrive bundle was not verified.','',
        '## 2. Training overlap and control limitations','',
        'Downloaded and hashed the officially linked BigVul training (**150,908**) and validation (**18,864**) rows, plus all Devign splits. Original row indices are unique within each split and disjoint between splits. Code overlap nevertheless exists. The following exclusions combine each checkpoint’s own train and validation sets; counts are unions, not sums.','',
        '| Model / control | Exclusion screen | Removed rows / positives | Remaining N | F1 | ROC-AUC |',
        '| --- | --- | ---: | ---: | ---: | ---: |']
    labels={'code_sha256':'Exact text','token_sha256':'Same tokens; comments/whitespace removed','structural_sha256':'Identifier-normalized candidates'}
    for entry in s['overlap_sensitivity']:
        if entry['dataset'] not in ['bigvul_test','devign_test']:continue
        m=entry['metrics']
        lines.append(f"| {entry['model'].title()} / {NAMES[entry['dataset']]} | {labels[entry['exclude_overlap']]} | {entry['excluded_rows']:,} / {entry['excluded_positive']:,} | {m['rows']:,} | {pct(m['f1'])} | {decimal(m['roc_auc'])} |")
    lines+=['','The token screen preserves operators and literal values. Identifier normalization can erase meaningful API/variable differences, so its matches are **candidates**, not established semantic duplicates. No exhaustive edited-clone, semantic-clone or pretraining audit was performed. Exact matches include opposite-label cases: all three BigVul test functions with exact training matches, and four Devign test functions with exact training matches, have a conflicting training label.','',
        'More importantly, **all 18,864 BigVul test rows belong to training projects**, and **18,779 share a training commit**. Devign also uses the same two projects, FFmpeg and QEMU; **1,777/2,732** test rows share a training commit. Thus these are reproduction controls within familiar source distributions, not project-held-out generalization tests. Grouped intervals account for dependence inside the evaluated set; they do not repair training/test provenance overlap or rule out dataset shortcuts.','',
        '| Control | Known commit absent from both train and validation | Positives | F1 | Recall | ROC-AUC / 95% interval |',
        '| --- | ---: | ---: | ---: | ---: | --- |']
    for entry in s['provenance_sensitivity']:
        if entry['condition']!='known_commit_absent_training_validation':continue
        m=entry['metrics'] or {}
        interval=entry.get('bootstrap',{}).get('intervals',{}).get(entry['model'],{}).get('roc_auc')
        bounds=f" / {decimal(interval['low'])}–{decimal(interval['high'])}" if interval else ' / too few groups'
        lines.append(f"| {NAMES[entry['dataset']]} | {entry['rows']:,} | {entry['positives']:,} | {pct(m.get('f1'))} | {pct(m.get('recall'))} | {decimal(m.get('roc_auc'))}{bounds} |")
    lines+=['','**VulBERTa’s Devign AUC drops from 0.711 overall to 0.543 on the 914 functions with commits absent from both train and validation.** Their positive prevalence is 54.92%, so the 50.39% F1 should not be mistaken for strong discrimination. This observational result is consistent with dependence on familiar commit/source patterns; it does not prove memorization. BigVul has only 15 such known-commit examples, including just one negative: its perfect scores on this tiny subset cannot establish generalization.','',
        'No test rows in either control come from projects absent from its train/validation data. Missing commit IDs are kept separate. Single-class commit slices have no category-level precision/F1 claim.','',
        'External overlap was also checked. See `overlap_summary.json` for all 20 evaluation/source comparisons and `overlap_sensitivity` in the summary for resulting scores. Cross-source matches are not automatically training exposure for the other checkpoint.','',
        '## 3. Comparable cohorts','',
        'For each model, match its original-domain control, PrimeVul and LLMVul on **language × source-line bin × binary label**. The bins are 1–10, 11–25, 26–50, 51–100 and 101+ lines. Each shared cell receives the smallest count among the three datasets; a row receives that mass divided by its dataset’s cell count. This exactly balances these observed cells and prevalence without using model scores. Unknown languages and unsupported cells are excluded, with every membership and weight saved.','',
        '“Intact” means one parsed function, no source parse error, no model truncation, and, for VulBERTa, unchanged lexical tokens after cleaning. This does not certify runtime completeness or label correctness. “Intact + overlap excluded” additionally removes own train/validation token matches.','',
        '| Model / condition | Weighted prevalence | Control F1 / AUC | PrimeVul F1 / AUC | LLMVul F1 / AUC | Retained rows: control / Prime / LLM |',
        '| --- | ---: | --- | --- | --- | --- |']
    for model in a.MODELS:
        control='bigvul_test' if model=='linevul' else 'devign_test'
        for condition in ['full','intact','intact_novel']:
            records={r['dataset']:r for r in s['matched'] if r['comparison']==model+'_'+condition}
            entries=[records[x] for x in [control,'primevul_test','llmvul_test']]
            values=[f"{pct(r['metrics']['f1'])} / {decimal(r['metrics']['roc_auc'])}" for r in entries]
            retained=' / '.join(f"{r['metrics']['rows']:,}" for r in entries)
            label={'full':'Full inputs','intact':'Intact','intact_novel':'Intact + overlap excluded'}[condition]
            lines.append(f"| {model.title()} / {label} | {pct(entries[0]['metrics']['prevalence'])} | "+' | '.join(values)+f" | {retained} |")
    lines+=['','These are conditional descriptive comparisons, not estimates of a causal authorship effect. VulBERTa’s original domain is C-only, so its three-way matched comparison excludes C++ examples. The two model-specific matched cohorts differ and should not be used as a paired comparison between models. A separate external comparison uses identical PrimeVul/LLMVul examples and weights for both models, with paired cluster resampling; it is saved under `paired_external`.','',
        '## 4. Metadata, labels and reviewed examples','',
        'Language uses an explicit `.c` or C++ file extension where supplied, otherwise the source declaration; it is not inferred from model scores or parser preference. **8,095 BigVul test rows declared C have C++ file extensions.** PrimeVul has **6,294 rows without usable language metadata**, so language matching selects a subset. All original declarations and the chosen language basis are retained.','',
        'The slice tables include language, project, length, source labeling method, published review status and LLMVul authorship-signal category. CWE results use **recall among positive examples only**, with support counts; negative functions do not supply a valid denominator for category precision. Categories remain source-supplied and are not independently validated. Devign has no per-function CWE metadata in this source.','',
        'Reliable local-versus-cross-function vulnerability judgments are unavailable at population scale, and label evidence differs by dataset. Consequently neither property is claimed to be balanced. Priority 4’s targeted source judgments are carried into the row audit separately; unreviewed rows stay unreviewed. Commit authorship signals do not verify authorship of every function.','',
        '| Model / published positive review subset | N | Detected | Recall |',
        '| --- | ---: | ---: | ---: |']
    for r in s['reviewed_positive_sensitivity']:
        lines.append(f"| {r['model'].title()} / {r['condition']} | {r['rows']} | {r['detected']} | {pct(r['recall'])} |")
    lines+=['','These are exact-code matches where both published LLMVul raters agreed positive. The source sample is enriched for positives, so these figures support recall observations only—not overall F1 or a population label-error rate. Independent blinded adjudication is still pending.','',
        '## 5. Uncertainty and what the evidence establishes','',
        'All main controls, external results and matched comparisons use 2,000 cluster-bootstrap draws with recorded seeds derived from 20261031. Connected components keep token-identical variants, shared commits/CVEs, and supplied CWEval task families together. Project clustering is additionally reported for full cohorts. Draws with undefined metrics are counted explicitly; zero-prediction precision draws are undefined. The same draws and row weights are used for paired model differences. Matched intervals hold the observed matching weights fixed and therefore condition on the chosen common support. Devign has only two project clusters: its project interval is a descriptive sensitivity, not reliable cross-project uncertainty.','',
        'The strongest current explanation is **limited transfer across source and labeling distributions, amplified by low positive prevalence**. Successful original-domain controls make a universal broken binary-classification path less plausible. Those controls use familiar projects and commits, which limits how far their scores generalize. The remaining gaps on balanced, intact, overlap-screened examples are not explained by the measured input defects, direct duplicates or prevalence alone.','',
        'Syntax/style differences may contribute, but this analysis does not isolate them. Project/API conventions, vulnerability families, missing runtime context, label definitions, source selection and unmeasured pretraining exposure remain competing explanations. The pending independent review prevents assigning a population fraction of errors to incorrect labels.','',
        '## Artifacts and reproduction','',
        f'Run directory: `{RUN.relative_to(c.ROOT).as_posix()}/`. Key files: `analysis_plan.json`, `preserved_inputs.json`, `inputs/manifest.json`, model `manifest.json`/`parity.json`/`predictions.jsonl`, `checkpoint_selection.json`, `overlap_summary.json`, `domain_exposure.json`, `joined_evaluation.jsonl`, `matched_membership.csv`, `matched_cells.json`, `slice_metrics.csv`, `metadata_coverage.csv`, `bootstrap/`, `summary.json`, and `verification.json`. Download manifests record source URLs, bytes and SHA-256. Generated inputs/results remain in the ignored reproduction directory.','',
        'The tracked implementation is split into `rq1_priority5_sources.py`, `rq1_priority5_controls.py`, `rq1_priority5_profiles.py`, `rq1_priority5_analysis.py`, `rq1_priority5_verify.py`, and this report generator. See the localScripts README for execution order. Re-running inference verifies hashes and reuses a completed run; it does not select or alter a checkpoint.','']
    report.write_text('\n'.join(lines).replace('Linevul','LineVul').replace('Vulberta','VulBERTa'),encoding='utf-8')
    s['status']='pass';s['verification']=dict(checks=v['checks'],unit_tests=v['unit_tests'],manifest_sha256=digest(RUN/'verification.json'))
    p4.write(report.with_name('rq1_priority5_summary.json'),s)
    print(report)


if __name__=='__main__':run()
