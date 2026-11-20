"""Overlap-sensitive and matched-cohort analyses of frozen RQ1/control scores."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import shutil

import numpy as np
from sklearn import metrics as sk
import rq1_priority2_audit as p2
import rq1_priority3_scores as p3
import rq1_priority4_audit as p4
from rq1_priority5_controls import RUN, P2, P4, PLAN, jsonl
from rq1_priority5_sources import digest

c=p2.common
DATASETS=['bigvul_test','devign_test','primevul_test','llmvul_test','cweval_test']
MODELS=['linevul','vulberta']


def devign_cleaner_audit():
    path=RUN/'devign_input_audit.jsonl'
    if path.exists(): return
    from clang import cindex
    import vulberta_eval as vb
    index=cindex.Index.create(); parser_map=p2.parsers(); output=[]
    for r in jsonl(RUN/'inputs/devign_test.jsonl'):
        code=r['code'];cleaned=vb.clean_for_vulberta(code)
        tree,language,_=p2.parse_best(code,'c',parser_map)
        after=parser_map[language].parse(cleaned.encode('utf-8'))
        tree_change=p2.cwe.lexical_tokens(tree.root_node)!=p2.cwe.lexical_tokens(after.root_node)
        changed=tree_change and p2.lexical_clang(index,code)!=p2.lexical_clang(index,cleaned)
        output.append(dict(sample_id=r['sample_id'],lexical_tree_changed=tree_change,cleaner_lexical_change_confirmed=changed,
                           source_parse_error=tree.root_node.has_error,cleaned_parse_error=after.root_node.has_error))
    p4.jsonl_out(path,output)


def load_rows():
    devign_cleaner_audit()
    data={stem:list(jsonl(RUN/'profiles'/(stem+'.jsonl'))) for stem in DATASETS}
    byid={r['sample_id']:r for rows in data.values() for r in rows}
    for r in byid.values():
        r['models']={};r['overlap']={};r['external_review']='not_reviewed';r['authorship_evidence']='unavailable'
    for stem,model in [('bigvul_test','linevul'),('devign_test','vulberta')]:
        manifest=c.read_json(RUN/model/'manifest.json')
        assert manifest['status']=='pass' and digest(RUN/model/'predictions.jsonl')==manifest['predictions_sha256']
        for score in jsonl(RUN/model/'predictions.jsonl'):
            r=byid[score['sample_id']];assert r['label']==score['label']
            r['models'][model]=dict(score=score['probability'],tokens=score['tokens'],truncated=score['truncated'],lexical_tree_changed=False)
    for a in jsonl(RUN/'devign_input_audit.jsonl'):
        byid[a['sample_id']]['models']['vulberta'].update(a)
    profiles={stem:{r['sample_id']:r for r in jsonl(P2/'profiles'/(stem+'.jsonl'))} for stem in DATASETS[2:]}
    for score in c.read_csv(P2/'joined_inputs.csv'):
        if score['dataset'] not in profiles:continue
        r=byid[score['sample_id']];assert r['label']==int(score['label'])
        old=profiles[score['dataset']][r['sample_id']][score['model']]
        r['models'][score['model']]=dict(score=float(score['prob_vulnerable']),tokens=int(score['tokens']),
            truncated=old['truncated'],lexical_tree_changed=old.get('lexical_tree_changed',False),
            cleaner_lexical_change_confirmed=old.get('cleaner_lexical_change_confirmed',False))
    for hit in jsonl(RUN/'overlap.jsonl'):
        byid[hit['sample_id']]['overlap'][hit['source']]={field:hit[field]['matches']>0 for field in ['code_sha256','token_sha256','structural_sha256']}
    for review in c.read_csv(P4/'external_review_join.csv'):
        if review['code_exact']=='True' and review['rater1']==review['rater2'] and review['rater1'] in ['0','1']:
            byid[review['sample_id']]['external_review']='published_agreement_'+review['rater1']
    # Authorship signals are source-level evidence, not verified per-function authorship.
    for raw in p4.rows_csv(c.ROOT/'LLMVul_v3-Updated.csv',title=True):
        sid='llmvul:'+raw['unique_id']
        if sid in byid:
            byid[sid]['authorship_evidence']=raw['signal_strength']+':'+raw['signal_type']
            byid[sid]['ai_tool']=raw['ai_tool']
    for case in c.read_json(P4/'case_review_notes.json')['cases']:
        for sid in case['sample_ids']:
            if sid in byid:
                byid[sid]['targeted_source_assessment']=case['judgment']
    for stem,rows in data.items():
        for r in rows:
            r['cwe_categories']=sorted(set(re.findall(r'CWE-\d+',str(r.get('cwe') or ''),flags=re.I)))
            for model,detail in r['models'].items():
                detail['intact']=not r['source_parse_error'] and r['function_count']==1 and not detail['truncated'] and not detail['lexical_tree_changed']
    return data


def groups(rows, project=False):
    # Token identity includes comment/whitespace variants; task family/commit/CVE retained.
    copies=[dict(r,code_sha256=r['token_sha256']) for r in rows]
    return p3.grouping(copies,project)


def curve(rows,model):
    return p3.ScoreCurve([r['label'] for r in rows],[r['models'][model]['score'] for r in rows])


def measured(rows,model,w=None):
    cv=curve(rows,model);v=cv.evaluate(w)
    # Positive-only CWE slices have defined recall but no meaningful category precision.
    for name,fn in [('f1',sk.f1_score),('precision',sk.precision_score),('recall',sk.recall_score)]:
        v[name]=float(fn(cv.y,cv.s>.5,sample_weight=w,zero_division=0))
    v.update(rows=len(rows),positives=int(cv.y.sum()),weight_sum=float(len(rows) if w is None else sum(w)),
             effective_sample_size=float(len(rows) if w is None else sum(w)**2/sum(np.asarray(w)**2)))
    return p3.jsonable(v)


def novel(r,model,field='token_sha256'):
    prefix='bigvul' if model=='linevul' else 'devign'
    return not any(r['overlap'][prefix+'_'+split][field] for split in ['train','valid'])


def matching(cohorts, language=True):
    """Deterministic common-support weights, using labels/covariates, never scores."""
    def key(r):return tuple(([r['language']] if language else [])+[r['length_bin'],r['label']])
    counts={name:Counter(key(r) for r in rows if not language or r['language']!='missing') for name,rows in cohorts.items()}
    shared=set.intersection(*(set(x) for x in counts.values()))
    mass={cell:min(x[cell] for x in counts.values()) for cell in shared}
    weighted={}
    for name,rows in cohorts.items():
        selected=[r for r in rows if key(r) in mass]
        weighted[name]=(selected,np.array([mass[key(r)]/counts[name][key(r)] for r in selected]))
    cells=[dict(cell=list(cell),mass=mass[cell],counts={name:x[cell] for name,x in counts.items()}) for cell in sorted(shared)]
    return weighted,cells


def bootstrap(rows,models,weights,name,seed,project=False):
    ids,info=groups(rows,project);ng=info['groups']
    cache=RUN/'bootstrap';cache.mkdir(exist_ok=True)
    signature=hashlib.sha256(json.dumps(dict(ids=ids.tolist(),weights=weights.tolist(),seed=seed,
        rows=[(r['sample_id'],r['label'],[r['models'][m]['score'] for m in models]) for r in rows],reps=PLAN['bootstrap_repetitions']),sort_keys=True).encode()).hexdigest()
    target=cache/(name+('_project' if project else '_related')+'.json')
    if target.exists():
        old=c.read_json(target);assert old['signature']==signature;return old
    rng=np.random.default_rng(seed);curves={m:curve(rows,m) for m in models}
    values={m:np.full((PLAN['bootstrap_repetitions'],len(p3.METRICS)),np.nan) for m in models}
    for rep in range(PLAN['bootstrap_repetitions']):
        multiplicities=np.bincount(rng.integers(0,ng,ng),minlength=ng)
        w=weights*multiplicities[ids]
        for model,cv in curves.items():
            result=cv.evaluate(w)
            if not result['precision_defined']: result['precision']=np.nan
            values[model][rep]=[result[k] for k in p3.METRICS]
    output=dict(signature=signature,seed=seed,repetitions=PLAN['bootstrap_repetitions'],grouping=info,
        intervals={m:p3.intervals(v) for m,v in values.items()}, project=project,
        caveat='Descriptive sensitivity only: fewer than 20 independent clusters.' if ng<20 else '')
    if len(models)==2:
        output['paired_linevul_minus_vulberta']=p3.intervals(values['linevul']-values['vulberta'])
    p4.write(target,output);print('Bootstrap complete',name,'project' if project else 'related',flush=True)
    return p3.jsonable(output)


def slices(data):
    results=[];coverage=[]
    for stem,rows in data.items():
        for field in ['language','project','length_bin','context_scope','label_evidence','external_review','authorship_evidence']:
            levels=defaultdict(list)
            for r in rows:levels[str(r.get(field) or 'missing')].append(r)
            for level,rs in sorted(levels.items()):
                for model in rs[0]['models']:
                    results.append(dict(dataset=stem,field=field,level=level,model=model,**measured(rs,model)))
        for label in [0,1]:
            rs=[r for r in rows if r['label']==label]
            coverage.append(dict(dataset=stem,label=label,rows=len(rs),language_missing=sum(r['language']=='missing' for r in rs),
                cwe_missing=sum(not r['cwe_categories'] for r in rs),project_missing=sum(not p4.present(r.get('project')) for r in rs),
                context_unreviewed=sum(r['context_scope']=='unreviewed' for r in rs),independent_adjudication_missing=len(rs)))
        categories=sorted({cat for r in rows if r['label'] for cat in r['cwe_categories']})
        for category in categories:
            rs=[r for r in rows if r['label'] and category in r['cwe_categories']]
            for model in rs[0]['models']:
                results.append(dict(dataset=stem,field='positive_cwe_recall_only',level=category,model=model,rows=len(rs),positives=len(rs),
                    recall=sum(r['models'][model]['score']>.5 for r in rs)/len(rs),precision=None,f1=None,
                    caveat='Source-supplied category; not independently validated. Multi-category rows may appear in multiple slices.'))
    p4.csv_out(RUN/'slice_metrics.csv',results);p4.csv_out(RUN/'metadata_coverage.csv',coverage)
    return coverage


def provenance_sensitivity(data):
    result=[]
    def commits(r):return set(x.lower() for x in re.findall(r'[0-9a-f]{40}',str(r.get('commit_id') or r.get('commit_url') or ''),flags=re.I))
    for model,family in [('linevul','bigvul'),('vulberta','devign')]:
        train=list(jsonl(RUN/'profiles'/(family+'_train.jsonl')))
        valid=list(jsonl(RUN/'profiles'/(family+'_valid.jsonl')))
        train_commits=set().union(*(commits(r) for r in train))
        valid_commits=set().union(*(commits(r) for r in valid))
        projects={str(r['project']).lower().strip() for r in train+valid}
        rows=data[family+'_test']
        selections={
            'known_commit_shared_training':[r for r in rows if commits(r)&train_commits],
            'known_commit_absent_training':[r for r in rows if commits(r) and not commits(r)&train_commits],
            'known_commit_absent_training_validation':[r for r in rows if commits(r) and not commits(r)&(train_commits|valid_commits)],
            'project_absent_training_validation':[r for r in rows if str(r['project']).lower().strip() not in projects],
            'missing_commit':[r for r in rows if not commits(r)]}
        for ci,(condition,rs) in enumerate(selections.items()):
            metric=measured(rs,model) if rs else None
            if metric and len({r['label'] for r in rs})<2:
                metric['f1']=metric['precision']=None
            entry=dict(model=model,dataset=family+'_test',condition=condition,rows=len(rs),
                positives=sum(r['label'] for r in rs),metrics=metric,
                caveat='Observational slice; no source-project-held-out control. Single-class slices report recall only.')
            if condition in ['known_commit_shared_training','known_commit_absent_training_validation'] and rs and groups(rs)[1]['groups']>=20:
                entry['bootstrap']=bootstrap(rs,[model],np.ones(len(rs)),model+'_'+condition,PLAN['seed']+4000+ci+100*(model=='vulberta'))
            result.append(entry)
    return result


def run():
    data=load_rows();shutil.copyfile(__file__,RUN/'analysis.py')
    result=dict(status='running',config=PLAN,full=[],overlap_sensitivity=[],matched=[],paired_external=[],
                metadata_coverage=slices(data),provenance_sensitivity=provenance_sensitivity(data),limitations=PLAN['limitations'])
    membership=[];cells_all=[];seed=PLAN['seed']
    for di,(stem,rows) in enumerate(data.items()):
        models=list(rows[0]['models'])
        boot={kind:bootstrap(rows,models,np.ones(len(rows)),stem,seed+di*10+int(kind=='project'),kind=='project') for kind in ['related','project']}
        for model in models:
            result['full'].append(dict(dataset=stem,model=model,metrics=measured(rows,model),bootstrap=boot))
            for field in ['code_sha256','token_sha256','structural_sha256']:
                selected=[r for r in rows if novel(r,model,field)]
                entry=dict(dataset=stem,model=model,exclude_overlap=field,excluded_rows=len(rows)-len(selected),
                    excluded_positive=sum(r['label'] for r in rows)-sum(r['label'] for r in selected),metrics=measured(selected,model) if selected else None)
                if stem in ['bigvul_test','devign_test'] and field=='token_sha256' and selected:
                    entry['bootstrap']=bootstrap(selected,[model],np.ones(len(selected)),stem+'_novel',seed+100+di)
                result['overlap_sensitivity'].append(entry)
    for mi,model in enumerate(MODELS):
        control='bigvul_test' if model=='linevul' else 'devign_test'
        for ci,condition in enumerate(['full','intact','intact_novel']):
            cohorts={stem:[r for r in data[stem] if (condition=='full' or r['models'][model]['intact']) and
                       (condition!='intact_novel' or novel(r,model))] for stem in [control,'primevul_test','llmvul_test']}
            weighted,cells=matching(cohorts)
            name=model+'_'+condition
            cells_all.extend(dict(comparison=name,**cell) for cell in cells)
            for di,(stem,(rows,w)) in enumerate(weighted.items()):
                assert rows and len({r['label'] for r in rows})==2
                entry=dict(comparison=name,model=model,dataset=stem,eligible_rows=len(cohorts[stem]),full_rows=len(data[stem]),
                    excluded_no_common_support=len(cohorts[stem])-len(rows),metrics=measured(rows,model,w))
                entry['bootstrap']=bootstrap(rows,[model],w,name+'_'+stem,seed+1000+mi*100+ci*10+di)
                result['matched'].append(entry)
                membership.extend(dict(comparison=name,dataset=stem,sample_id=r['sample_id'],label=r['label'],language=r['language'],
                    length_bin=r['length_bin'],weight=float(weight)) for r,weight in zip(rows,w))
    # Both models scored on identical external rows, with identical matching weights.
    for ci,condition in enumerate(['full','joint_intact_novel']):
        cohorts={stem:[r for r in data[stem] if condition=='full' or all(r['models'][m]['intact'] and novel(r,m) for m in MODELS)]
                 for stem in ['primevul_test','llmvul_test']}
        weighted,cells=matching(cohorts);name='paired_external_'+condition
        cells_all.extend(dict(comparison=name,**cell) for cell in cells)
        for di,(stem,(rows,w)) in enumerate(weighted.items()):
            boot=bootstrap(rows,MODELS,w,name+'_'+stem,seed+3000+ci*10+di)
            result['paired_external'].append(dict(comparison=name,dataset=stem,metrics={m:measured(rows,m,w) for m in MODELS},bootstrap=boot))
            membership.extend(dict(comparison=name,dataset=stem,sample_id=r['sample_id'],label=r['label'],language=r['language'],
                length_bin=r['length_bin'],weight=float(weight)) for r,weight in zip(rows,w))
    review=[]
    for model in MODELS:
        for condition in ['all','intact','intact_novel']:
            rows=[r for r in data['llmvul_test'] if r['external_review']=='published_agreement_1' and
                  (condition=='all' or r['models'][model]['intact']) and (condition!='intact_novel' or novel(r,model))]
            review.append(dict(model=model,condition=condition,rows=len(rows),detected=sum(r['models'][model]['score']>.5 for r in rows),
                               recall=sum(r['models'][model]['score']>.5 for r in rows)/len(rows) if rows else None,
                               caveat='Published positive-enriched review; recall only; independent adjudication pending.'))
    result['reviewed_positive_sensitivity']=review
    p4.jsonl_out(RUN/'joined_evaluation.jsonl',[r for rows in data.values() for r in rows])
    p4.csv_out(RUN/'matched_membership.csv',membership);p4.write(RUN/'matched_cells.json',cells_all)
    result['status']='complete_pending_verification'
    p4.write(RUN/'summary.json',result)
    print('Analysis complete.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cleaner-only',action='store_true')
    args=parser.parse_args()
    devign_cleaner_audit() if args.cleaner_only else run()
