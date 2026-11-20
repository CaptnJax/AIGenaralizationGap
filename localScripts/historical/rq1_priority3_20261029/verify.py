"""Reconcile saved curves, test-set maxima, bootstrap intervals, and artifacts."""
import json
from pathlib import Path
import re
import shutil
import sys
import numpy as np
from sklearn.metrics import precision_recall_curve

RUN=Path(__file__).resolve().parent
sys.path.insert(0,str(RUN.parents[1]))
import rq1_priority3_scores as scores
c=scores.common
report=c.read_json(RUN/'summary.json')
checks=[]
def check(name,condition):
    assert condition,name
    checks.append(dict(check=name,status='pass'))

check('completed_analysis',report['status']=='pass')
source=c.ROOT/report['source_run']
for name,digest in report['source_hashes'].items(): check('input_'+name,c.sha(source/name)==digest)
for artifact in report['artifacts']: check('artifact_'+artifact['path'],c.sha(RUN/artifact['path'])==artifact['sha256'])
figure_manifest=c.read_json(RUN/'figure_manifest.json')
for artifact in figure_manifest['artifacts']: check('figure_'+artifact['path'],c.sha(c.ROOT/artifact['path'])==artifact['sha256'])
check('frozen_analysis_script',c.sha(c.HERE/'rq1_priority3_scores.py')==report['script_sha256']==c.sha(RUN/'score_audit.py'))
check('frozen_figure_script',c.sha(c.HERE/'rq1_priority3_figures.py')==figure_manifest['script_sha256']==c.sha(RUN/'figure_renderer.py'))

joined=c.read_csv(source/'joined_inputs.csv')
grid=c.read_csv(RUN/'threshold_grid.csv')
bins=c.read_csv(RUN/'reliability.csv')
loaded={}
for job in report['jobs']:
    model,stem=job['model'],job['dataset']; name=job['job']
    rows=[r for r in joined if r['model']==model and r['dataset']==stem]
    y=np.array([int(r['label']) for r in rows]); s=np.array([float(r['prob_vulnerable']) for r in rows])
    precision,recall,threshold=precision_recall_curve(y,s)
    f1=np.divide(2*precision*recall,precision+recall,out=np.zeros(len(precision)),where=(precision+recall)!=0)
    check(name+'_global_maximum',abs(float(f1.max())-job['exploratory_best_f1']['f1'])<1e-12)
    for r in [job['exploratory_best_f1']]+[x for x in grid if x['model']==model and x['dataset']==stem]:
        pred=s>float(r['threshold'])
        actual=[int(sum((y==truth)&(pred==prediction))) for truth,prediction in [(1,1),(0,1),(1,0),(0,0)]]
        assert actual==[int(float(r[k])) for k in ['tp','fp','fn','tn']],name
    check(name+'_threshold_grid',True)
    for strategy in ['uniform','quantile']:
        selected=[r for r in bins if r['model']==model and r['dataset']==stem and r['strategy']==strategy]
        check(name+'_'+strategy+'_bin_counts',sum(int(r['count']) for r in selected)==len(rows) and sum(int(r['positives']) for r in selected)==int(y.sum()))
    for scheme in ['related','project']:
        path=RUN/(model+'_'+stem+'_'+scheme+'_bootstrap.csv')
        if not path.exists():
            check(name+'_project_reuses_families',stem=='cweval_test')
            path=RUN/(model+'_'+stem+'_related_bootstrap.csv')
        replicates=c.read_csv(path)
        check(name+'_'+scheme+'_replicates',len(replicates)==2000)
        array=np.array([[float(r[k]) if r[k] else np.nan for k in scores.METRICS] for r in replicates])
        loaded[model,stem,scheme]=array
        actual=scores.intervals(array)
        check(name+'_'+scheme+'_intervals',actual==job['intervals'][scheme])
for comparison in report['model_differences']:
    stem,scheme=comparison['dataset'],comparison['scheme']
    delta=loaded['linevul',stem,scheme]-loaded['vulberta',stem,scheme]
    check(stem+'_'+scheme+'_paired_difference',scores.intervals(delta)==comparison['intervals'])

pairs=c.read_csv(RUN/'cweval_pairs.csv')
for model in ['linevul','vulberta']:
    rows=[r for r in joined if r['model']==model and r['dataset']=='cweval_test']
    bytask={}
    for r in rows: bytask.setdefault(r['sample_id'].rsplit(':',1)[0],{})[int(r['label'])]=float(r['prob_vulnerable'])
    selected=[p for p in pairs if p['model']==model]
    check(model+'_29_pairs',len(selected)==len(bytask)==29)
    for pair in selected:
        value=bytask[pair['task']]
        assert value[1]-value[0]==float(pair['delta'])
        assert (value[1]>.5 and value[0]<=.5)==(pair['both_correct']=='True')
    check(model+'_pair_values',True)

destination=c.HERE/'reports/rq1_priority3_summary.json'
shutil.copyfile(RUN/'summary.json',destination)
for filename in ['rq1_priority3_diagnostics.md','rq1_diagnostic_plan.md']:
    path=c.HERE/'reports'/filename
    for target in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
        if not target.startswith(('http://','https://','#')): assert (path.parent/target).exists(),target
    check(filename+'_links',True)

result=dict(status='pass',date='2026-10-29',checks_passed=len(checks),checks=checks,
    prior_independent_metric_checks=len(report['checks']),
    observed_unit_tests=dict(count=8,result='pass',script_sha256=c.sha(c.HERE/'test_rq1_priority3.py')),
    artifacts=[dict(path=p.relative_to(c.ROOT).as_posix(),sha256=c.sha(p)) for p in [RUN/'summary.json',RUN/'figure_manifest.json',
        c.HERE/'reports/rq1_priority3_diagnostics.md',destination,Path(__file__)]])
c.write_json(RUN/'verification.json',result)
print(json.dumps(dict(status='pass',final_checks=len(checks),independent_metric_checks=len(report['checks']),unit_tests=8),indent=2))
