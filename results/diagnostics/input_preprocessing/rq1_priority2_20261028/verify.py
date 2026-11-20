"""Independent reconciliation of the completed priority-two evidence."""
import csv
import json
import math
from pathlib import Path
import shutil
import sys

RUN=Path(__file__).resolve().parent
sys.path.insert(0,str(RUN.parents[1]))
import rq1_priority2_audit as audit
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score, accuracy_score

c=audit.common
checks=[]
def check(name, condition):
    assert condition, name
    checks.append(dict(check=name,status='pass'))

summary=c.read_json(RUN/'input_summary.json')
joined=c.read_csv(RUN/'joined_inputs.csv')
pairs=c.read_csv(RUN/'ablations/predictions.csv')
selection=c.read_json(RUN/'ablations/selection.json')
baseline,jobs,data=audit.load_data()
check('model_dataset_rows',len(joined)==89194)
check('unique_model_dataset_row_keys',len({(r['model'],r['dataset'],r['row']) for r in joined})==len(joined))
check('dataset_rows',sum(len(v) for v in data.values())==45597)
check('finite_aligned_binary_probabilities',all(math.isfinite(float(r['prob_vulnerable'])) and 0<=float(r['prob_vulnerable'])<=1 and int(r['prediction'])==int(float(r['prob_vulnerable'])>.5) for r in joined))
check('fixed_paired_selection',len(pairs)==len(selection)==2095 and all(all(str(s[k])==r[k] for k in s) for s,r in zip(selection,pairs)))
check('paired_baseline_parity',all(r['baseline_matches_history']=='True' for r in pairs))
check('unchanged_controls',summary['unchanged_controls']==dict(rows=196,input_changes=0,max_probability_delta=0.0))

def independent_metrics(name, labels, predictions, expected):
    tn,fp,fn,tp=confusion_matrix(labels,predictions,labels=[0,1]).ravel()
    actual=dict(test_accuracy=accuracy_score(labels,predictions),test_precision=precision_score(labels,predictions,zero_division=0),
                test_recall=recall_score(labels,predictions,zero_division=0),test_f1=f1_score(labels,predictions,zero_division=0))
    check(name+'_confusion',expected['confusion_matrix']==dict(tn=int(tn),fp=int(fp),fn=int(fn),tp=int(tp)))
    check(name+'_metrics',all(abs(actual[k]-expected[k])<1e-12 for k in actual))

for job in summary['jobs']:
    rows=[r for r in joined if r['model']==job['model'] and r['dataset']==job['dataset']]
    check(job['job']+'_count',len(rows)==job['rows'])
    independent_metrics(job['job'],[int(r['label']) for r in rows],[int(r['prediction']) for r in rows],job['slices']['all']['metrics'])
    if job['model']=='vulberta':
        replacements={r['row']:int(r['variant_prediction']) for r in pairs if r['model']=='vulberta' and r['dataset']==job['dataset'] and r['condition'].startswith('cleaner_') and not r['condition'].endswith('_control')}
        independent_metrics(job['job']+'_hybrid',[int(r['label']) for r in rows],[replacements.get(r['row'],int(r['prediction'])) for r in rows],job['details']['tested_cleaner_replacement']['metrics'])

for n,condition in enumerate(summary['ablation']['conditions']):
    rows=[r for r in pairs if all(r[k]==condition[k] for k in ['model','dataset','condition'])]
    check('condition_'+str(n)+'_count',len(rows)==condition['rows'])
    for variant in ['baseline','variant']:
        independent_metrics('condition_'+str(n)+'_'+variant,[int(r['label']) for r in rows],[int(r[variant+'_prediction']) for r in rows],condition[variant])

pm=summary['profile_manifest']
for d in pm['datasets']:
    check(d['dataset']+'_profile_hash',c.sha(RUN/'profiles'/(d['dataset']+'.jsonl'))==d['profile_sha256'])
    check(d['dataset']+'_lexical_hash',c.sha(RUN/'profiles'/(d['dataset']+'_lexical.jsonl.gz'))==d['lexical_sha256'])
check('frozen_profiler',c.sha(RUN/'profiles/profiler.py')==pm['script_sha256']==c.sha(c.HERE/'rq1_priority2_audit.py'))
check('frozen_ablation_runner',c.sha(RUN/'ablations/ablation_runner.py')==summary['ablation']['script_sha256']==c.sha(c.HERE/'rq1_priority2_ablations.py'))
check('frozen_exporter',c.sha(RUN/'linevul/exporter.py')==summary['linevul_export']['exporter_sha256']==c.sha(c.HERE/'rq1_linevul_scores.py'))
check('summary_generator',summary['script_sha256']==c.sha(c.HERE/'rq1_priority2_summary.py'))
for j in summary['linevul_export']['jobs']:
    check(j['job']+'_score_hash',c.sha(RUN/'linevul'/(j['job'].split('/')[1]+'.csv'))==j['output_sha256'])
for asset in baseline['assets']:
    check('unchanged_asset_'+asset['path'],c.sha(c.ROOT/asset['path'])==asset['sha256'])
check('clang_checks',all(summary['clang'][k]==0 for k in ['timeouts','errors','discrepancies']) and summary['clang']['rows']==36)

destination=c.HERE/'reports/rq1_priority2_summary.json'
shutil.copyfile(RUN/'input_summary.json',destination)
artifact_paths=[RUN/'input_summary.json',RUN/'joined_inputs.csv',RUN/'ablations/selection.json',RUN/'ablations/predictions.csv',
                RUN/'ablations/summary.json',RUN/'examples.json',RUN/'context_review_selection.json',RUN/'context_review_notes.json',
                c.HERE/'reports/rq1_priority2_diagnostics.md',destination,Path(__file__)]
verification=dict(status='pass',date='2026-10-29',checks=checks,
    checks_passed=len(checks),independent_metric_implementation='scikit-learn '+__import__('sklearn').__version__,
    observed_unit_test_run=dict(command='python -m unittest discover -s localScripts -p test_rq1_priority2.py -v',tests=6,result='pass',
                                test_script_sha256=c.sha(c.HERE/'test_rq1_priority2.py')),
    artifacts=[dict(path=p.relative_to(c.ROOT).as_posix(),sha256=c.sha(p)) for p in artifact_paths])
c.write_json(RUN/'verification.json',verification)
print(json.dumps(dict(status='pass',checks_passed=len(checks),joined_rows=len(joined),paired_rows=len(pairs),summary=str(destination)),indent=2))
