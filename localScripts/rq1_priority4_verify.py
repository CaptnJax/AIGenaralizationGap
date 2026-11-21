"""Independent artifact, sampling and numerical reconciliation for Priority 4."""
import argparse
from collections import Counter, defaultdict
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys

import numpy as np
from sklearn import metrics
import rq1_priority4_audit as a


def run(out):
    checks=[]
    def check(name,ok):
        checks.append(dict(check=name,status='pass' if bool(ok) else 'fail'))
        if not ok:raise AssertionError(name)
    def sha(p):return hashlib.sha256(a.c.input_path(p).read_bytes()).hexdigest()
    s=a.c.read_json(out/'summary.json');e=a.c.read_json(out/'evidence_summary.json')
    for p,h in s['source_hashes'].items():check('unchanged:'+p,sha(a.c.ROOT/p)==h)
    check('audit_script_identity',sha(a.c.HERE/'rq1_priority4_audit.py')==s['script_sha256']==sha(out/'audit.py'))
    check('plan_identity',sha(out/'analysis_plan.json')==s['plan_sha256'])
    structure=a.p2.jsonl(out/'row_structure.jsonl');lookup={r['sample_id']:r for r in structure}
    joined=a.rows_csv(a.P2/'joined_inputs.csv');jobs=defaultdict(list)
    for r in joined:jobs[r['model']+'/'+r['dataset']].append(r)
    check('unique_source_ids',len(lookup)==len(structure)==45597)
    check('scored_records',len(joined)==89194 and len(jobs)==7)
    check('prediction_rule',all(int(r['prediction'])==int(float(r['prob_vulnerable'])>.5) for r in joined))
    check('label_hash_alignment',all(int(r['label'])==lookup[r['sample_id']]['label'] and r['code_sha256']==lookup[r['sample_id']]['code_sha256'] for r in joined))
    baseline=a.c.read_json(a.c.HERE/'reports/rq1_priority1_summary.json')
    for job in baseline['jobs']:
        rr=jobs[job['job']];cm=metrics.confusion_matrix([int(r['label']) for r in rr],[int(r['prediction']) for r in rr],labels=[0,1])
        check('historical_confusion:'+job['job'],all(int(v)==job['measured']['confusion_matrix'][k] for k,v in zip(['tn','fp','fn','tp'],cm.ravel())))
    github=a.c.read_json(out/'sources/github_sources.json')
    for source in github['llmvul_files']:
        check('llmvul_published_blob:'+source['sha'],a.blob_sha(source['content'].encode())==source['sha'])
    big=a.c.read_json(out/'sources/bigvul_source.json')
    check('bigvul_documentation_blob',a.blob_sha(big['content'].encode())==big['sha'])
    raw=a.rows_csv(a.c.ROOT/'LLMVul_v3-Updated.csv',title=True)
    check('all_llm_vote_labels',all(a.ensemble([r[k] for k in ['tool_semgrep','tool_flawfinder','pattern_match']])==r['ensemble_label'] for r in raw))
    llm_selected=[r for r in raw if r['ensemble_label']!='uncertain']
    check('llm_raw_code_and_labels',all(lookup['llmvul:'+r['unique_id']]['code_sha256']==hashlib.sha256(r['function_body'].encode()).hexdigest() and lookup['llmvul:'+r['unique_id']]['label']==int(float(r['vuln_label'])) for r in llm_selected))
    prime=a.p2.jsonl(a.c.ROOT/'primevul_test.jsonl')
    check('prime_raw_code_and_labels',all(lookup[f"primevul:{r['idx']}"]['code_sha256']==hashlib.sha256(r['func'].encode()).hexdigest() and lookup[f"primevul:{r['idx']}"]['label']==r['target'] for r in prime))
    cross=a.p2.jsonl(out/'cross_dataset_groups.jsonl')
    excluded={sid for r in cross if r['grouping']=='code_sha256' for sid in r['sample_ids']}
    for row in s['weighting']:
        rr=jobs[row['job']]
        if row.get('condition'):rr=[r for r in rr if r['sample_id'] not in excluded]
        field=row['weighting'];count=Counter(lookup[r['sample_id']].get(field) for r in rr)
        w=np.array([1/count[lookup[r['sample_id']][field]] if field!='rows' else 1 for r in rr])
        y=np.array([int(r['label']) for r in rr]);scores=np.array([float(r['prob_vulnerable']) for r in rr]);pred=scores>.5
        tag=row['job']+':'+field+':'+row.get('condition','all')
        cm=metrics.confusion_matrix(y,pred,labels=[0,1],sample_weight=w)
        for key,val in zip(['tn','fp','fn','tp'],cm.ravel()):check(tag+':'+key,abs(row[key]-val)<1e-8)
        check(tag+':f1',abs(row['f1']-metrics.f1_score(y,pred,sample_weight=w,zero_division=0))<1e-10)
        check(tag+':ap',abs(row['average_precision']-metrics.average_precision_score(y,scores,sample_weight=w))<1e-10)
        check(tag+':auc',abs(row['roc_auc']-metrics.roc_auc_score(y,scores,sample_weight=w))<1e-10)
        check(tag+':weight',abs(row['effective_weight']-sum(w))<1e-8)
    for stem,d in s['datasets'].items():
        rows=[r for r in structure if r['dataset']==stem]
        for field in ['code_sha256','token_sha256','structural_sha256']:
            counts=Counter(r[field] for r in rows)
            check(stem+':'+field+':groups',len(counts)==d[field]['groups'])
    selected=a.rows_csv(out/'review/selection.csv');strata=a.rows_csv(out/'review/strata.csv')
    for ji,(job,rr) in enumerate(sorted(jobs.items())):
        rng=random.Random(a.SEED+ji)
        for cell,quota in a.QUOTAS.items():
            pop=sorted([r for r in rr if r['error']==cell],key=lambda r:r['sample_id'])
            expected={r['sample_id'] for r in rng.sample(pop,min(quota,len(pop)))}
            actual=[r for r in selected if r['job']==job and r['error']==cell]
            check(job+':'+cell+':sample',expected=={r['sample_id'] for r in actual} and len(actual)==len(expected))
            check(job+':'+cell+':probability',all(abs(float(r['inclusion_probability'])-len(expected)/len(pop))<1e-12 for r in actual))
    packets=a.p2.jsonl(out/'review/stage1_blinded_code.jsonl');keys=a.rows_csv(out/'review/coordinator_key.csv')
    check('blinded_packet_schema',all(set(r)=={'review_id','code','declared_language'} for r in packets))
    check('review_counts',len(selected)==356 and len(keys)==len(packets)==328)
    keymap={r['review_id']:r for r in keys}
    check('blinded_code_hashes',all(hashlib.sha256(r['code'].encode()).hexdigest()==lookup[keymap[r['review_id']]['sample_id']]['code_sha256'] for r in packets))
    stratum_probs={(r['job'],r['error']):float(r['inclusion_probability']) for r in strata}
    byid=defaultdict(list)
    for job,rr in jobs.items():
        for r in rr:byid[r['sample_id']].append((job,r['error']))
    check('union_inclusion_probabilities',all(abs(float(r['merged_inclusion_probability'])-(1-np.prod([1-stratum_probs[x] for x in byid[r['sample_id']]])))<1e-12 for r in keys))
    for file in ['reviewer_1.csv','reviewer_2.csv','adjudication.csv']:
        forms=a.rows_csv(out/'review'/file)
        check('unfilled:'+file,len(forms)==328 and all(not v for r in forms for k,v in r.items() if k!='review_id'))
    review=a.rows_csv(out/'sources/llmvul_manual_review.csv',title=True)
    complete=[r for r in review if r['rater1_label'] in ('0','1') and r['rater2_label'] in ('0','1')]
    check('review_kappa_complete',abs(metrics.cohen_kappa_score([r['rater1_label'] for r in complete],[r['rater2_label'] for r in complete])-s['external_review']['complete_binary_kappa'])<1e-12)
    check('review_kappa_all',abs(metrics.cohen_kappa_score([r['rater1_label'] for r in review],[r['rater2_label'] for r in review])-s['external_review']['nominal_three_category_kappa'])<1e-12)
    llm_lookup={r['unique_id']:r for r in raw}
    agreed={f"llmvul:{r['unique_id']}":int(r['rater1_label']) for r in review if r['rater1_label']==r['rater2_label'] and r['rater1_label'] in ('0','1') and r['function_body']==llm_lookup[r['unique_id']]['function_body']}
    check('agreed_subset_support',len(agreed)==85 and sum(agreed.values())==83)
    for entry in s['external_review']['metrics']:
        rr=jobs[entry['job']]
        for variant in ['published_agreed_labels','limited_hybrid']:
            subset=rr if variant=='limited_hybrid' else [r for r in rr if r['sample_id'] in agreed]
            yy=[agreed.get(r['sample_id'],int(r['label'])) for r in subset];pp=[int(r['prediction']) for r in subset]
            check(entry['job']+':'+variant,abs(metrics.f1_score(yy,pp)-entry[variant]['f1'])<1e-12)
    # Check every pinned task/unsafe body again without running it.
    catalog=a.p2.jsonl(a.c.ROOT/'prepared_datasets/cweval/catalog.jsonl')
    lock=a.c.read_json(a.c.HERE/'cweval_upstream_lock.json');parsers=a.p2.parsers()
    for r in catalog:
        path=a.c.input_path(a.c.CACHE/'CWEval'/lock['revision']/r['upstream_path']);data=path.read_bytes()
        check('cwe_blob:'+r['sample_id'],a.blob_sha(data)==lock['files'][r['upstream_path']])
        tree=parsers[r['language']].parse(data);target=a.p2.cwe.functions(tree)[r['target_function']]
        reference=a.p2.cwe.lexical_tokens(target)
        extracted=a.p2.cwe.lexical_tokens(parsers[r['language']].parse(r['code'].encode()).root_node)
        check('cwe_target:'+r['sample_id'],reference==extracted)
    for identity in e['downloaded_file_identities']:
        check('downloaded:'+identity['path'],sha(identity['path'])==identity['sha256'] and a.blob_sha(a.c.input_path(identity['path']).read_bytes())==identity['git_blob_sha1'])
    check('new_adjudication_not_claimed',s['review']['adjudicated_cases']==0 and s['review']['independent_review_status'].startswith('pending'))
    check('security_execution_not_claimed',e['cweval']['execution']=='not_run')
    result=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(a.c.HERE),'-p','test_rq1_priority4.py','-v'],capture_output=True,text=True,cwd=a.c.ROOT)
    (out/'unit_test_log.txt').write_text(result.stdout+result.stderr,encoding='utf-8')
    check('unit_tests',result.returncode==0 and 'Ran 8 tests' in result.stderr)
    deps={p:sha(a.c.HERE/p) for p in ['rq1_priority1_audit.py','rq1_priority2_audit.py','rq1_priority3_scores.py','rq1_priority4_audit.py','rq1_priority4_evidence.py','test_rq1_priority4.py']}
    shutil.copyfile(__file__,out/'verify.py')
    artifacts={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='verification.json'}
    verification=dict(status='pass',checks=checks,passed=len(checks),unit_tests=8,dependencies=deps,
        packages={p:version(p) for p in ['numpy','scikit-learn','tree-sitter','tree-sitter-c','tree-sitter-cpp']},artifacts=artifacts)
    a.write(out/'verification.json',verification)
    print(f'{len(checks)} verification checks passed; 8 unit tests passed.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);run(p.parse_args().output.resolve())
