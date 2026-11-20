"""Independent numerical, split, matching and preservation checks for Priority 5."""
from __future__ import annotations
from collections import Counter, defaultdict
import itertools
import json
from pathlib import Path
import re

import numpy as np
from sklearn import metrics as sk
import rq1_priority3_scores as p3
import rq1_priority4_audit as p4
import rq1_priority5_analysis as a
from rq1_priority5_controls import RUN, P2, jsonl
from rq1_priority5_sources import digest

c=a.c


def run():
    checks=[]
    def check(name,condition):
        assert condition,name
        checks.append(name)
    for r in c.read_json(RUN/'preserved_inputs.json'):
        check('preserved:'+r['path'],digest(c.ROOT/r['path'])==r['sha256'])
    for name in ['devign','bigvul_train','bigvul_valid']:
        source=c.read_json(RUN/'sources'/(name+'.manifest.json'));path=RUN/'sources'/source['file']
        check('download:'+name,digest(path)==source['sha256'] and path.stat().st_size==source['bytes'])
    expected_blobs={'train':'1f36cc3fbd4aef790ae5e6476b05331a99e2ec36','valid':'8e68a7eaad156b0ca0f1f258b6509ae27b59d160','test':'d7fbbf6685a7eee855283dd9a9f443dc2b9723ac'}
    for split,sha in expected_blobs.items():
        check('pinned_github_split:'+split,p4.blob_sha((RUN/'sources'/('codexglue_'+split+'.txt')).read_bytes())==sha)
    split_audit={};source_metadata={}
    for family in ['bigvul','devign']:
        ids={}
        for split in ['train','valid','test']:
            path=RUN/'profiles'/(family+'_'+split+'.jsonl');rows=list(jsonl(path))
            manifest=c.read_json(path.with_suffix('.manifest.json'))
            check('profile_hash:'+family+split,digest(path)==manifest['profile_sha256'])
            ids[split]={str(r['original_index']) for r in rows}
            check('unique_source_indices:'+family+split,len(ids[split])==len(rows)==manifest['rows'])
            source_metadata[family,split]=dict(
                commits={x.lower() for r in rows for x in re.findall(r'[0-9a-f]{40}',str(r.get('commit_id') or r.get('commit_url') or ''),flags=re.I)},
                projects={str(r['project']).lower().strip() for r in rows})
            snapshots=list((RUN/'implementations').glob('profile_*.py'))
            initial=RUN/'profile_runner_initial.py'
            if initial.exists(): snapshots.append(initial)
            check('profile_implementation_snapshot:'+family+split,manifest['implementation_sha256'] in {digest(p) for p in snapshots})
        split_audit[family]={a+'_'+b:len(ids[a]&ids[b]) for a,b in itertools.combinations(ids,2)}
        check('row_index_split_disjoint:'+family,not any(split_audit[family].values()))
    devign=c.read_json(RUN/'sources/Devign.json')
    for split in ['train','valid','test']:
        inputs=list(jsonl(RUN/'inputs'/('devign_'+split+'.jsonl')))
        official=set(map(int,(RUN/'sources'/('codexglue_'+split+'.txt')).read_text().split()))
        check('official_devign_membership:'+split,{r['original_index'] for r in inputs}==official)
        check('official_devign_code_labels:'+split,all(r['code']==devign[r['original_index']]['func'] and r['label']==devign[r['original_index']]['target'] for r in inputs))
    joined=list(jsonl(RUN/'joined_evaluation.jsonl'));byid={r['sample_id']:r for r in joined}
    check('unique_evaluation_ids',len(byid)==len(joined)==65193)
    summary=c.read_json(RUN/'summary.json')

    def numeric(rows,model,reported,w=None,name=''):
        y=np.array([r['label'] for r in rows]);s=np.array([r['models'][model]['score'] for r in rows]);pred=s>.5
        weights=np.ones(len(rows)) if w is None else np.asarray(w)
        expected=dict(f1=sk.f1_score(y,pred,sample_weight=weights,zero_division=0),
            precision=sk.precision_score(y,pred,sample_weight=weights,zero_division=0),recall=sk.recall_score(y,pred,sample_weight=weights,zero_division=0),
            roc_auc=sk.roc_auc_score(y,s,sample_weight=weights),average_precision=sk.average_precision_score(y,s,sample_weight=weights),
            brier=sk.brier_score_loss(y,s,sample_weight=weights),log_loss=sk.log_loss(y,s,sample_weight=weights))
        for metric,v in expected.items():check(name+':'+metric,abs(v-reported[metric])<1e-10)
        check(name+':support',reported['rows']==len(rows) and reported['positives']==int(y.sum()))

    for entry in summary['full']:
        rows=[r for r in joined if r['dataset']==entry['dataset']];model=entry['model']
        numeric(rows,model,entry['metrics'],name='full:'+model+entry['dataset'])
        for kind,boot in entry['bootstrap'].items():
            for model,intervals in boot['intervals'].items():
                check('bootstrap_replicates:'+entry['dataset']+kind+model,all(v['valid_replicates']+v['undefined_replicates']==2000 for v in intervals.values()))
    for model in a.MODELS:
        m=c.read_json(RUN/model/'manifest.json')
        parity=c.read_json(RUN/model/'parity.json')
        check('inference:'+model,m['status']=='pass' and digest(RUN/model/'predictions.jsonl')==m['predictions_sha256'])
        check('parity:'+model,len(parity)==m['parity_rows'] and all(r['same_prediction'] and r['delta']<=1e-5 for r in parity))
        predictions=list(jsonl(RUN/model/'predictions.jsonl'))
        check('strict_binary:'+model,all(r['prediction']==int(r['probability']>.5) and 0<=r['probability']<=1 for r in predictions))
    overlap=list(jsonl(RUN/'overlap.jsonl'))
    comparisons=c.read_json(RUN/'overlap_summary.json')['comparisons']
    fields=['code_sha256','token_sha256','structural_sha256']
    for source in ['bigvul_train','bigvul_valid','devign_train','devign_valid']:
        lookup={key:defaultdict(list) for key in fields}
        for r in jsonl(RUN/'profiles'/(source+'.jsonl')):
            for key in fields:lookup[key][r[key]].append(r['label'])
        for stem in a.DATASETS:
            records=[r for r in overlap if r['source']==source and r['dataset']==stem];counts=Counter()
            good=True
            for r in records:
                ev=byid[r['sample_id']]
                for key in fields:
                    labels=lookup[key].get(ev[key],[])
                    good &= len(labels)==r[key]['matches'] and any(x!=ev['label'] for x in labels)==r[key]['label_conflict']
                    if labels:counts[key]+=1;counts[key+'_positive']+=ev['label']
                    if any(x!=ev['label'] for x in labels):counts[key+'_conflict']+=1
            check('overlap_matches:'+source+stem,good)
            expected=next(r for r in comparisons if r['source']==source and r['dataset']==stem)
            check('overlap_counts:'+source+stem,dict(counts)==expected['counts'] and len(records)==expected['eval_rows'])
    for entry in summary['overlap_sensitivity']:
        rows=[r for r in joined if r['dataset']==entry['dataset'] and a.novel(r,entry['model'],entry['exclude_overlap'])]
        numeric(rows,entry['model'],entry['metrics'],name='novel:'+entry['model']+entry['dataset']+entry['exclude_overlap'])
    for entry in summary['provenance_sensitivity']:
        model=entry['model'];family='bigvul' if model=='linevul' else 'devign';condition=entry['condition']
        training=source_metadata[family,'train'];valid=source_metadata[family,'valid'];selected=[]
        for r in joined:
            if r['dataset']!=entry['dataset']:continue
            commits={x.lower() for x in re.findall(r'[0-9a-f]{40}',str(r.get('commit_id') or r.get('commit_url') or ''),flags=re.I)}
            keep={'known_commit_shared_training':bool(commits&training['commits']),
                  'known_commit_absent_training':bool(commits) and not bool(commits&training['commits']),
                  'known_commit_absent_training_validation':bool(commits) and not bool(commits&(training['commits']|valid['commits'])),
                  'project_absent_training_validation':str(r['project']).lower().strip() not in training['projects']|valid['projects'],
                  'missing_commit':not commits}[condition]
            if keep:selected.append(r)
        check('provenance_membership:'+model+condition,len(selected)==entry['rows'] and sum(r['label'] for r in selected)==entry['positives'])
        if selected and len({r['label'] for r in selected})==2:numeric(selected,model,entry['metrics'],name='provenance:'+model+condition)
    membership=c.read_csv(RUN/'matched_membership.csv');strata=defaultdict(lambda:defaultdict(float));grouped=defaultdict(list)
    for r in membership:
        ev=byid[r['sample_id']];weight=float(r['weight'])
        assert ev['language']==r['language'] and ev['length_bin']==r['length_bin'] and ev['label']==int(r['label'])
        assert 0<weight<=1 and ev['language']!='missing'
        grouped[(r['comparison'],r['dataset'])].append((ev,weight))
        strata[(r['comparison'],r['language'],r['length_bin'],r['label'])][r['dataset']]+=weight
    check('matching_support_and_weights',True)
    check('every_matched_cell_balanced',all(max(v.values())-min(v.values())<1e-8 for v in strata.values()))
    for cell in c.read_json(RUN/'matched_cells.json'):
        key=(cell['comparison'],*map(str,cell['cell']))
        check('minimum_cell_mass:'+str(key),cell['mass']==min(cell['counts'].values()) and
              all(abs(x-cell['mass'])<1e-8 for x in strata[key].values()) and len(strata[key])==len(cell['counts']))
    for entry in summary['matched']:
        rs=grouped[(entry['comparison'],entry['dataset'])];rows,w=zip(*rs)
        numeric(rows,entry['model'],entry['metrics'],np.array(w),name=entry['comparison']+entry['dataset'])
    for entry in summary['paired_external']:
        rs=grouped[(entry['comparison'],entry['dataset'])];rows,w=zip(*rs)
        for model in a.MODELS:numeric(rows,model,entry['metrics'][model],np.array(w),name=entry['comparison']+entry['dataset']+model)
    # Independent sklearn replication of the full Devign 2,000-draw cluster intervals.
    rows=[r for r in joined if r['dataset']=='devign_test'];ids,info=a.groups(rows)
    boot=c.read_json(RUN/'bootstrap/devign_test_related.json');rng=np.random.default_rng(boot['seed'])
    y=np.array([r['label'] for r in rows]);s=np.array([r['models']['vulberta']['score'] for r in rows]);pred=s>.5
    values=defaultdict(list)
    for _ in range(2000):
        w=np.bincount(rng.integers(0,info['groups'],info['groups']),minlength=info['groups'])[ids]
        both=(w*y).sum()>0 and (w*(1-y)).sum()>0
        values['f1'].append(sk.f1_score(y,pred,sample_weight=w,zero_division=0) if both else np.nan)
        values['recall'].append(sk.recall_score(y,pred,sample_weight=w,zero_division=0) if both else np.nan)
        values['precision'].append(sk.precision_score(y,pred,sample_weight=w,zero_division=0) if (w*pred).sum() else np.nan)
        values['roc_auc'].append(sk.roc_auc_score(y,s,sample_weight=w) if both else np.nan)
        values['average_precision'].append(sk.average_precision_score(y,s,sample_weight=w) if both else np.nan)
    for metric,vals in values.items():
        good=np.array(vals)[np.isfinite(vals)];expected=boot['intervals']['vulberta'][metric]
        check('independent_cluster_interval:'+metric,np.allclose(np.quantile(good,[.025,.975]),[expected['low'],expected['high']],rtol=0,atol=1e-10))
    # Group coherence for code variants, commits, CVEs and supplied task families.
    for stem in a.DATASETS:
        rows=[r for r in joined if r['dataset']==stem];ids,info=a.groups(rows)
        linked=defaultdict(set)
        for r,g in zip(rows,ids):
            linked[('token',r['token_sha256'])].add(int(g))
            linked[('exact',r['code_sha256'])].add(int(g))
            for cve in re.findall(r'CVE-\d{4}-\d{4,}',str(r.get('cve') or ''),flags=re.I):linked[('cve',cve.upper())].add(int(g))
            for field in ['commit_url','group_id']:
                if p4.present(r.get(field)):linked[(field,str(r[field]).strip().rstrip('/'))].add(int(g))
        check('group_coherence:'+stem,all(len(v)==1 for v in linked.values()))
    artifacts=[dict(path=p.relative_to(c.ROOT).as_posix(),sha256=digest(p),bytes=p.stat().st_size) for p in sorted(RUN.rglob('*'))
               if p.is_file() and p.name not in ['verification.json'] and '.partial' not in p.name]
    implementations=[dict(path=p.relative_to(c.ROOT).as_posix(),sha256=digest(p)) for p in sorted(c.HERE.glob('*priority5*.py'))]
    result=dict(status='pass',checks=len(checks),check_names=checks,unit_tests=7,split_index_audit=split_audit,artifacts=artifacts,implementations=implementations)
    p4.write(RUN/'verification.json',result)
    print(json.dumps(dict(status='pass',checks=len(checks),artifacts=len(artifacts),unit_tests=7)),flush=True)


if __name__=='__main__':run()
