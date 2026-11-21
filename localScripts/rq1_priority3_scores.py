"""Frozen-score RQ1 diagnostics: ranking, exploratory thresholds, and prevalence.

No model fitting, calibration fitting, or deployment threshold selection occurs.
"""
from __future__ import annotations
import argparse
from collections import Counter
from importlib.metadata import version
import json
from pathlib import Path
import re
import shutil

import numpy as np
from sklearn import metrics as sk
import rq1_priority2_audit as audit

common=audit.common
METRICS=['roc_auc','average_precision','ap_lift','precision','recall','f1','fpr',
         'balanced_accuracy','mcc','predicted_positive_rate','prevalence','brier','log_loss',
         'ece_10','recall_fpr_01','recall_fpr_05','recall_fpr_10']
THRESHOLDS=[0,.00001,.00005,.0001,.0002,.0005,.001,.005,.01,.05,.1,.2,.3,.4,.5,.6,.7,.8,.9,.95,.99,.995,.999,1]
CONFIG=dict(date='2026-10-29',threshold_rule='score > threshold',baseline_threshold=.5,
    common_prevalence=.05,fpr_budgets=[.01,.05,.10],bootstrap_repetitions=2000,seed=20261029,
    intervals='95% percentile cluster bootstrap; no label stratification; row-weighted estimand',
    grouping='Connected components of exact code hash, nonempty source commit URL, valid CVE, and supplied CWEval family. Project sensitivity additionally links project names.',
    threshold_policy='Fixed grid and all distinct score boundaries; test-set exploratory upper bound only; no threshold adopted.',
    calibration='10 equal-width probability bins; 10 quantile bins as sensitivity; no calibrator fitted.',
    average_precision='Non-interpolated sum of recall increments times precision (sklearn average_precision_score).')


def jsonable(x):
    if isinstance(x,dict): return {k:jsonable(v) for k,v in x.items()}
    if isinstance(x,(list,tuple,np.ndarray)): return [jsonable(v) for v in x]
    if isinstance(x,(np.integer,)): return int(x)
    if isinstance(x,(float,np.floating)): return float(x) if np.isfinite(x) else None
    return x


def write_json(path,value):
    common.write_json(path,jsonable(value))


def safe_ratio(a,b,default=0.):
    a,b=np.broadcast_arrays(np.asarray(a,dtype=float),np.asarray(b,dtype=float))
    return np.divide(a,b,out=np.full(a.shape,default,dtype=float),where=b!=0)


def standardized(tpr,fpr,prevalence):
    p=prevalence
    return dict(prevalence=p,precision=float(safe_ratio(p*tpr,p*tpr+(1-p)*fpr)),
                f1=float(safe_ratio(2*p*tpr,p*(1+tpr)+(1-p)*fpr)))


class ScoreCurve:
    """Cache tied score boundaries so cluster-weighted metrics need no re-sort."""
    def __init__(self,y,s):
        self.y=np.asarray(y,dtype=int); self.s=np.asarray(s,dtype=float)
        assert len(y)==len(s)>0 and set(self.y)<=set([0,1]) and np.isfinite(self.s).all()
        assert ((self.s>=0)&(self.s<=1)).all()
        self.order=np.argsort(-self.s,kind='stable')
        ss=self.s[self.order]
        self.ends=np.r_[np.flatnonzero(ss[1:]!=ss[:-1]),len(ss)-1]
        self.thresholds=np.r_[1.,np.nextafter(ss[self.ends],-np.inf)]
        self.bins=np.minimum((self.s*10).astype(int),9)

    def curve(self,w=None):
        w=np.ones(len(self.y)) if w is None else np.asarray(w,dtype=float)
        assert len(w)==len(self.y) and (w>=0).all() and w.sum()>0
        pos=w*self.y; neg=w*(1-self.y)
        tp=np.r_[0.,np.cumsum(pos[self.order])[self.ends]]
        fp=np.r_[0.,np.cumsum(neg[self.order])[self.ends]]
        return tp,fp,pos.sum(),neg.sum()

    def evaluate(self,w=None,threshold=.5):
        w=np.ones(len(self.y)) if w is None else np.asarray(w,dtype=float)
        tp,fp,p,n=self.curve(w)
        valid=p>0 and n>0
        recall=safe_ratio(tp,p); fpr=safe_ratio(fp,n)
        prec=safe_ratio(tp,tp+fp)
        ap=float(np.sum(np.diff(recall)*prec[1:])) if valid else np.nan
        pred=self.s>threshold
        a=float(np.sum(w*self.y*pred)); b=float(np.sum(w*(1-self.y)*pred))
        c=p-a; d=n-b
        denom=np.sqrt((a+b)*(a+c)*(d+b)*(d+c))
        count=np.bincount(self.bins,weights=w,minlength=10)
        ps=np.bincount(self.bins,weights=w*self.s,minlength=10)
        ys=np.bincount(self.bins,weights=w*self.y,minlength=10)
        score=np.clip(self.s,1e-15,1-1e-15)
        result=dict(roc_auc=float(np.trapezoid(recall,fpr)) if valid else np.nan,
            average_precision=ap,ap_lift=ap/(p/(p+n)) if valid else np.nan,
            precision=float(safe_ratio(a,a+b)),recall=a/p if valid else np.nan,
            f1=2*a/(2*a+b+c) if valid and 2*a+b+c else (0. if valid else np.nan),
            fpr=b/n if valid else np.nan,balanced_accuracy=(a/p+d/n)/2 if valid else np.nan,
            mcc=float(safe_ratio(a*d-b*c,denom)) if valid else np.nan,
            predicted_positive_rate=(a+b)/(p+n),prevalence=p/(p+n),
            brier=float(np.average((self.s-self.y)**2,weights=w)),
            log_loss=float(np.average(-(self.y*np.log(score)+(1-self.y)*np.log(1-score)),weights=w)),
            ece_10=float(np.sum(np.abs(ps-ys))/(p+n)),
            precision_defined=bool(a+b),tp=a,fp=b,fn=c,tn=d)
        for budget,name in [(0.01,'01'),(.05,'05'),(.1,'10')]:
            result['recall_fpr_'+name]=float(np.max(recall[fpr<=budget])) if valid else np.nan
        return result

    def table(self):
        tp,fp,p,n=self.curve()
        prec=safe_ratio(tp,tp+fp); recall=tp/p; fpr=fp/n
        f1=safe_ratio(2*tp,2*tp+fp+p-tp)
        return [dict(threshold=float(t),tp=int(a),fp=int(b),fn=int(p-a),tn=int(n-b),
                     precision=float(q),recall=float(r),fpr=float(f),f1=float(v),
                     predicted_positive_rate=float((a+b)/(p+n)))
                for t,a,b,q,r,f,v in zip(self.thresholds,tp,fp,prec,recall,fpr,f1)]


def grouping(rows,project=False):
    parent=list(range(len(rows)))
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]; x=parent[x]
        return x
    seen={}
    for i,r in enumerate(rows):
        keys=[('code',r['code_sha256'])]
        for key in ['commit_url','group_id']+(['project'] if project else []):
            value=r.get(key)
            if value and str(value).lower() not in ['none','nan','null','']:
                keys.append((key,str(value).strip().rstrip('/')))
        for cve in re.findall(r'CVE-\d{4}-\d{4,}',str(r.get('cve') or ''),flags=re.I):
            keys.append(('cve',cve.upper()))
        for key in keys:
            if key in seen:
                a,b=find(i),find(seen[key])
                parent[max(a,b)]=min(a,b)
            else: seen[key]=i
    roots=[find(i) for i in range(len(rows))]
    mapping={r:i for i,r in enumerate(sorted(set(roots)))}
    ids=np.array([mapping[r] for r in roots])
    counts=np.bincount(ids)
    return ids,dict(groups=len(counts),largest_group_rows=int(max(counts)),largest_group_fraction=float(max(counts)/len(rows)),
        positive_groups=len({ids[i] for i,r in enumerate(rows) if r['label']==1}),
        group_size_quantiles=dict(zip(['min','median','p95','max'],np.quantile(counts,[0,.5,.95,1]))))


def intervals(values):
    result={}
    for i,name in enumerate(METRICS):
        v=values[:,i]; good=v[np.isfinite(v)]
        result[name]=dict(low=float(np.quantile(good,.025)) if len(good) else None,
                         high=float(np.quantile(good,.975)) if len(good) else None,
                         valid_replicates=len(good),undefined_replicates=len(v)-len(good))
    return result


def bootstrap(curves,groups,repetitions,seed):
    rng=np.random.default_rng(seed); ng=int(groups.max())+1
    values={model:np.empty((repetitions,len(METRICS))) for model in curves}
    for rep in range(repetitions):
        mult=np.bincount(rng.integers(0,ng,ng),minlength=ng)
        w=mult[groups]
        for model,curve in curves.items():
            result=curve.evaluate(w)
            values[model][rep]=[result[k] for k in METRICS]
        if (rep+1)%500==0: print(' bootstrap',rep+1,'/',repetitions,flush=True)
    return values


def reliability(y,s,strategy):
    edges=np.linspace(0,1,11) if strategy=='uniform' else np.unique(np.quantile(s,np.linspace(0,1,11)))
    if len(edges)==1: edges=np.array([0.,1.])
    bins=np.searchsorted(edges[1:-1],s,side='right')
    result=[]
    for i in range(len(edges)-1):
        mask=bins==i
        result.append(dict(bin=i,lower=float(edges[i]),upper=float(edges[i+1]),count=int(mask.sum()),
            positives=int(y[mask].sum()),mean_score=float(s[mask].mean()) if mask.any() else None,
            observed_rate=float(y[mask].mean()) if mask.any() else None))
    return result


def validate(curve):
    checks=[]
    rng=np.random.default_rng(101)
    for name,w in [('unweighted',np.ones(len(curve.y))),('weighted',rng.integers(1,4,len(curve.y)))]:
        m=curve.evaluate(w); y,s=curve.y,curve.s; pred=s>.5
        expected=dict(roc_auc=sk.roc_auc_score(y,s,sample_weight=w),average_precision=sk.average_precision_score(y,s,sample_weight=w),
            precision=sk.precision_score(y,pred,sample_weight=w,zero_division=0),recall=sk.recall_score(y,pred,sample_weight=w),
            f1=sk.f1_score(y,pred,sample_weight=w),balanced_accuracy=sk.balanced_accuracy_score(y,pred,sample_weight=w),
            mcc=sk.matthews_corrcoef(y,pred,sample_weight=w),brier=float(np.average((s-y)**2,weights=w)),
            log_loss=sk.log_loss(y,s,sample_weight=w))
        for metric,value in expected.items():
            assert abs(m[metric]-value)<1e-10,(name,metric,m[metric],value)
            checks.append(dict(check=name+'_'+metric,status='pass'))
    table=curve.table()
    for idx in sorted({0,len(table)-1,int(np.argmax([r['f1'] for r in table])),*rng.integers(0,len(table),8)}):
        row=table[idx]; pred=curve.s>row['threshold']
        tn,fp,fn,tp=sk.confusion_matrix(curve.y,pred,labels=[0,1]).ravel()
        assert (row['tn'],row['fp'],row['fn'],row['tp'])==(tn,fp,fn,tp)
    checks.append(dict(check='strict_threshold_boundary_counts',status='pass'))
    return checks


def run(source,output,repetitions):
    assert not output.exists(), 'Use a new output directory.'
    verification=common.read_json(source/'verification.json')
    assert verification['status']=='pass'
    expected={common.input_path(common.ROOT/x['path']):x['sha256'] for x in verification['artifacts']}
    for filename in ['joined_inputs.csv','input_summary.json']:
        path=source/filename
        assert common.sha(path)==expected[common.input_path(path)]
    output.mkdir(parents=True)
    shutil.copyfile(__file__,output/'score_audit.py')
    cfg=dict(CONFIG,bootstrap_repetitions=repetitions)
    write_json(output/'analysis_plan.json',cfg)
    rows=common.read_csv(source/'joined_inputs.csv')
    old=common.read_json(source/'input_summary.json')
    old_jobs={j['job']:j for j in old['jobs']}
    result=dict(status='running',config=cfg,source_run=source.relative_to(common.ROOT).as_posix(),
        source_hashes={f:common.sha(source/f) for f in ['verification.json','joined_inputs.csv','input_summary.json']},
        script_sha256=common.sha(Path(__file__)),packages={p:version(p) for p in ['numpy','scipy','scikit-learn','matplotlib']},
        datasets=[],jobs=[],model_differences=[],checks=[],documentation=[
        'https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html',
        'https://scikit-learn.org/stable/modules/calibration'])
    group_rows=[]; threshold_rows=[]; calibration_rows=[]; prevalence_rows=[]; pair_rows=[]
    for dataset_index,stem in enumerate(audit.STEMS):
        profiles=audit.jsonl(source/'profiles'/(stem+'.jsonl'))
        manifest=next(x for x in old['profile_manifest']['datasets'] if x['dataset']==stem)
        assert common.sha(source/'profiles'/(stem+'.jsonl'))==manifest['profile_sha256']
        groups,ginfo=grouping(profiles)
        project_groups,pinfo=grouping(profiles,project=True)
        dataset=dict(dataset=stem,rows=len(profiles),related_groups=ginfo,project_groups=pinfo)
        result['datasets'].append(dataset)
        for i,r in enumerate(profiles):
            group_rows.append(dict(dataset=stem,row=i,sample_id=r['sample_id'],related_group=int(groups[i]),
                project_group=int(project_groups[i]),code_sha256=r['code_sha256'],project=r['project'],commit_url=r['commit_url'],
                cve=r['cve'],cweval_family=r['group_id']))
        curves={}; job_results={}
        for model in ['linevul','vulberta']:
            selected=sorted([r for r in rows if r['dataset']==stem and r['model']==model],key=lambda r:int(r['row']))
            if not selected: continue
            assert len(selected)==len(profiles)
            for i,(r,p) in enumerate(zip(selected,profiles)):
                assert int(r['row'])==i and r['sample_id']==p['sample_id'] and int(r['label'])==p['label'] and r['code_sha256']==p['code_sha256']
            y=np.array([int(r['label']) for r in selected]); s=np.array([float(r['prob_vulnerable']) for r in selected])
            assert np.array_equal(s>.5,np.array([int(r['prediction']) for r in selected]))
            curve=curves[model]=ScoreCurve(y,s)
            result['checks']+= [dict(job=model+'/'+stem,**c) for c in validate(curve)]
            point=curve.evaluate(); old_cm=old_jobs[model+'/'+stem]['slices']['all']['metrics']['confusion_matrix']
            assert all(point[k]==old_cm[k] for k in ['tp','fp','fn','tn'])
            table=curve.table()
            common.write_csv(output/(model+'_'+stem+'_curve.csv'),table)
            # Highest threshold wins tied maxima, keeping fewer predicted positives.
            best=table[int(np.argmax([r['f1'] for r in table]))]
            rates=[]
            for budget in cfg['fpr_budgets']:
                candidates=[r for r in table if r['fpr']<=budget]
                chosen=max(candidates,key=lambda r:(r['recall'],-r['fpr'],r['threshold']))
                rates.append(dict(fpr_budget=budget,**chosen))
            quantiles={str(label):dict(rows=int((y==label).sum()),mean=float(s[y==label].mean()),
                **dict(zip(['min','p01','p05','p25','median','p75','p95','p99','max'],np.quantile(s[y==label],[0,.01,.05,.25,.5,.75,.95,.99,1])))) for label in [0,1]}
            pi=point['prevalence']
            job=dict(job=model+'/'+stem,model=model,dataset=stem,rows=len(y),point=point,quantiles=quantiles,
                baseline_always_negative=dict(precision=0,precision_defined=False,recall=0,f1=0,accuracy=1-pi,balanced_accuracy=.5),
                baseline_always_positive=dict(precision=pi,recall=1,f1=2*pi/(1+pi),accuracy=pi,balanced_accuracy=.5),
                baseline_constant_prevalence=dict(probability=pi,brier=pi*(1-pi),note='Observed-test-prevalence reference, not a fitted deployment model.'),
                exploratory_best_f1=best,recall_at_fpr=rates,
                standardized_5pct=standardized(point['recall'],point['fpr'],cfg['common_prevalence']),intervals={})
            for t in THRESHOLDS:
                threshold_rows.append(dict(model=model,dataset=stem,threshold=t,**curve.evaluate(threshold=t)))
            for strategy in ['uniform','quantile']:
                bins=reliability(y,s,strategy)
                for b in bins: calibration_rows.append(dict(model=model,dataset=stem,strategy=strategy,**b))
                job['ece_'+strategy]=sum(b['count']*abs(b['mean_score']-b['observed_rate']) for b in bins if b['count'])/len(y)
            for prevalence in [.01,.022147813458124898,.05,.08212895312250014,.1,.2,.5]:
                prevalence_rows.append(dict(model=model,dataset=stem,tpr=point['recall'],fpr=point['fpr'],**standardized(point['recall'],point['fpr'],prevalence)))
            if stem=='cweval_test':
                tasks={}
                for i,p in enumerate(profiles): tasks.setdefault(p['sample_id'].rsplit(':',1)[0],[]).append(i)
                records=[]
                for task,indices in sorted(tasks.items()):
                    assert len(indices)==2 and set(y[indices])=={0,1}
                    neg=next(i for i in indices if y[i]==0); pos=next(i for i in indices if y[i]==1)
                    assert groups[neg]==groups[pos]
                    delta=s[pos]-s[neg]
                    record=dict(model=model,task=task,family=profiles[pos]['group_id'],reference_score=s[neg],unsafe_score=s[pos],
                        delta=delta,ordering='unsafe_higher' if delta>0 else 'reference_higher' if delta<0 else 'tie',
                        both_correct=bool(s[pos]>.5 and s[neg]<=.5),both_negative=bool(s[pos]<=.5 and s[neg]<=.5),
                        both_positive=bool(s[pos]>.5 and s[neg]>.5),both_wrong=bool(s[pos]<=.5 and s[neg]>.5))
                    records.append(record); pair_rows.append(record)
                assert len(records)==29
                job['pairs']=dict(tasks=29,families=len(set(x['family'] for x in records)),
                    ordering=dict(Counter(x['ordering'] for x in records)),both_correct=sum(x['both_correct'] for x in records),
                    both_negative=sum(x['both_negative'] for x in records),both_positive=sum(x['both_positive'] for x in records),
                    both_wrong=sum(x['both_wrong'] for x in records),delta_quantiles=dict(zip(['min','median','max'],np.quantile([x['delta'] for x in records],[0,.5,1]))))
                families=sorted(set(x['family'] for x in records))
                pair_group=np.array([families.index(x['family']) for x in records])
                wins=np.array([x['delta']>0 for x in records]); correct=np.array([x['both_correct'] for x in records])
                rng=np.random.default_rng(cfg['seed']+99); pair_boot=[]
                for _ in range(repetitions):
                    w=np.bincount(rng.integers(0,len(families),len(families)),minlength=len(families))[pair_group]
                    pair_boot.append([np.average(wins,weights=w),np.average(correct,weights=w)])
                job['pairs']['family_bootstrap_95pct']=dict(zip(['unsafe_higher_fraction','both_correct_fraction'],
                    [dict(low=float(np.quantile(np.array(pair_boot)[:,i],.025)),high=float(np.quantile(np.array(pair_boot)[:,i],.975))) for i in [0,1]]))
                job['pairs']['near_ties_abs_delta_le_1e_6']=sum(abs(x['delta'])<=1e-6 for x in records)
            job_results[model]=job; result['jobs'].append(job)
            print(model,stem,'AUC',round(point['roc_auc'],4),'AP',round(point['average_precision'],4),'F1',round(point['f1'],4),'exploratory best',round(best['f1'],4),flush=True)
        for scheme,g in [('related',groups),('project',project_groups)]:
            if scheme=='project' and np.array_equal(groups,project_groups):
                for j in job_results.values(): j['intervals'][scheme]=j['intervals']['related']
                continue
            print(stem,scheme,'groups',int(g.max()+1),flush=True)
            values=bootstrap(curves,g,repetitions,cfg['seed']+dataset_index*10+(scheme=='project'))
            for model,v in values.items():
                job_results[model]['intervals'][scheme]=intervals(v)
                common.write_csv(output/(model+'_'+stem+'_'+scheme+'_bootstrap.csv'),
                    [dict(replicate=i,**{k:(float(value) if np.isfinite(value) else '') for k,value in zip(METRICS,row)}) for i,row in enumerate(v)])
            if len(values)==2:
                result['model_differences'].append(dict(dataset=stem,scheme=scheme,direction='linevul minus vulberta',
                    point={k:job_results['linevul']['point'][k]-job_results['vulberta']['point'][k] for k in METRICS},
                    intervals=intervals(values['linevul']-values['vulberta'])))
        write_json(output/'summary.json',result)
    for filename,data in [('groups.csv',group_rows),('threshold_grid.csv',threshold_rows),('reliability.csv',calibration_rows),
                           ('prevalence_sensitivity.csv',prevalence_rows),('cweval_pairs.csv',pair_rows)]:
        common.write_csv(output/filename,data)
    result['status']='pass'
    result['artifacts']=[dict(path=p.name,sha256=common.sha(p)) for p in sorted(output.iterdir()) if p.is_file() and p.name!='summary.json']
    write_json(output/'summary.json',result)
    print('Score analysis complete; independent metric checks:',len(result['checks']),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=common.input_path(common.HERE/'results/rq1_priority2_20261028'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--repetitions',type=int,default=CONFIG['bootstrap_repetitions'])
    args=parser.parse_args()
    assert args.repetitions>0
    run(args.source.resolve(),args.output.resolve(),args.repetitions)
