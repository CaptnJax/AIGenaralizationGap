"""Reconcile retrieved source evidence without executing benchmark/source code."""
import argparse
import ast
from collections import Counter, defaultdict
import difflib
import hashlib
from pathlib import Path
import re

import rq1_priority4_audit as a


def save_source(folder, path, structured):
    data=structured['content'].encode('utf-8')
    assert a.blob_sha(data)==structured['sha'], path
    target=folder/path
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(data)
    return dict(path=str(target),git_blob_sha1=structured['sha'],sha256=hashlib.sha256(data).hexdigest())


def run(output):
    src=output/'sources'; catalog=a.p2.jsonl(a.c.ROOT/'prepared_datasets/cweval/catalog.jsonl')
    cwe_files=a.c.read_json(src/'cweval_sources.json'); tests={}; identities=[]
    for r in cwe_files:
        assert r['result']['status']=='fulfilled' and not r['result']['value']['isError']
        data=r['result']['value']['structuredContent']
        identities.append(save_source(src/'cweval',r['path'],data))
        tests[r['path']]=data['content']
    mapping=[]
    for pair in sorted({r['pair_id'] for r in catalog}):
        rows=[r for r in catalog if r['pair_id']==pair]
        reference=next(r for r in rows if r['label']==0)
        test_path=re.sub(r'_task\.(c|cpp)$','_test.py',reference['upstream_path'])
        code=tests[test_path]; tree=ast.parse(code)
        defs=Counter(n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)))
        duplicates=[name for name,count in defs.items() if count>1]
        mapping.append(dict(pair_id=pair,eligible=reference['eligible'],sample_ids=[r['sample_id'] for r in rows],
            target_function=reference['target_function'],source_test=test_path,
            security_marker_present='pytest.mark.security' in code,
            compiled_reference_mentioned='compiled_path' in code,
            compiled_unsafe_mentioned='compiled_unsafe_path' in code,
            duplicate_top_level_function_names=duplicates,
            source_task_tokens_match=all(r['upstream_target_tokens_match'] for r in rows),
            execution='not_run'))
    a.csv_out(output/'cweval_test_map.csv',mapping)
    raw=a.rows_csv(a.c.ROOT/'LLMVul_v3-Updated.csv',title=True);lookup={r['unique_id']:r for r in raw}
    included=[r for r in raw if r['ensemble_label']!='uncertain']
    flags=[]
    for r in raw:
        path=r['file_name'].lower().replace('\\','/')
        flags.append(dict(sample_id='llmvul:'+r['unique_id'],included=r['ensemble_label']!='uncertain',
            source_label=r['ensemble_label'],vendor_path_hint=bool(re.search(r'(^|/)(3rdparty|third_party|thirdparty|vendor|vendors|external|extern)(/|$)',path)),
            test_path_hint=bool(re.search(r'(^|/)(test|tests|testing)(/|$)',path)),
            generated_text_hint=bool(re.search(r'auto.?generated|automatically generated|do not edit',r['function_body'],re.I)),
            actual_lines=len(r['function_body'].splitlines()),declared_lines=int(r['function_lines']),
            declared_span=int(r['function_end_line'])-int(r['function_start_line'])+1,
            nonascii=not r['function_body'].isascii()))
    a.csv_out(output/'llmvul_construction_flags.csv',flags)
    construction={}
    for included_flag in (True,False):
        rr=[r for r in flags if r['included']==included_flag]
        construction['included' if included_flag else 'excluded_uncertain']=dict(rows=len(rr),
            **{f:sum(r[f] for r in rr) for f in ['vendor_path_hint','test_path_hint','generated_text_hint','nonascii']},
            line_count_mismatch=sum(r['actual_lines']!=r['declared_lines'] for r in rr),
            declared_span_mismatch=sum(r['declared_lines']!=r['declared_span'] for r in rr))
    flagmap={r['sample_id']:r for r in flags}
    scored=defaultdict(list)
    for r in a.rows_csv(a.P2/'joined_inputs.csv'):
        if r['dataset']=='llmvul_test':
            scored[r['model']].append(dict(sample_id=r['sample_id'],label=int(r['label']),score=float(r['prob_vulnerable'])))
    construction_metrics=[]
    for model,rows in scored.items():
        for flag in ['test_path_hint','vendor_path_hint','generated_text_hint','nonascii']:
            for value in (False,True):
                subset=[r for r in rows if flagmap[r['sample_id']][flag]==value]
                if subset:construction_metrics.append(dict(model=model,flag=flag,value=value,**a.weighted_metrics(subset)))
    a.csv_out(output/'construction_cohort_metrics.csv',construction_metrics)
    all_exact=defaultdict(list)
    for r in raw:all_exact[a.c.code_sha(r['function_body'])].append(r)
    full_label_conflicts=[dict(code_sha256=k,sample_ids=[r['unique_id'] for r in rs],
                              labels=[r['ensemble_label'] for r in rs]) for k,rs in all_exact.items()
                         if len({r['ensemble_label'] for r in rs})>1]
    a.write(output/'llmvul_all_exact_label_conflicts.json',full_label_conflicts)
    # Source snippets are fixed purposive evidence; they do not estimate defect rates.
    cases=a.c.read_json(src/'case_sources.json')
    extra=a.c.read_json(src/'additional_case_sources.json')
    ids=['ID_289E72EB6D827C0D','ID_9D80D1E3ECA38FE1','ID_1FD8CA7AD4F7A7A6',
         'ID_9D4C3136460C9399','ID_64E05D7C322FB0BB','ID_F486991D843C2E5D']
    names=['main','p256_transparent_import_key','cmd_plan','_ebpf_copy_program_entry','dns_select_test_srv','ACLCheckAllPerm']
    parser_map=a.p2.parsers();matches=[]
    for sid,name,item in zip(ids,names,cases['llm']+extra):
        data=item['result']['value']['structuredContent'];source=data['content'];rawrow=lookup[sid]
        identities.append(save_source(src/'case_files',sid+Path(item['request']['path']).suffix,data))
        tree,lang,errors=a.p2.parse_best(source,rawrow['language'],parser_map)
        nodes=[n for n in a.p2.nodes(tree.root_node) if n.type=='function_definition' and a.p2.cwe.function_name(n)==name]
        exact_func=nodes[0].text.decode('utf-8') if len(nodes)==1 else None
        start=source.find(rawrow['function_body'])
        diff=list(difflib.unified_diff((exact_func or '').splitlines(),rawrow['function_body'].splitlines(),fromfile='upstream_function',tofile='dataset_fragment',lineterm=''))
        matches.append(dict(sample_id='llmvul:'+sid,source_request=item['request'],function=name,
            source_url=data['display_url'],source_sha256=hashlib.sha256(source.encode()).hexdigest(),
            source_file_hash_matches=rawrow['file_hash']=='sha256:'+hashlib.sha256(source.encode()).hexdigest(),
            target_candidates=len(nodes),exact_target_function_match=exact_func==rawrow['function_body'],
            exact_substring=start>=0,source_start_line=source[:start].count('\n')+1 if start>=0 else None,
            stored_start_line=int(rawrow['function_start_line']),stored_end_line=int(rawrow['function_end_line']),
            target_diff=diff,source_parser_errors=errors))
    a.write(output/'source_case_matches.json',matches)
    prime_commits=[]
    for item in cases['prime']:
        data=item['result']['value']['structuredContent'];commit=data['commit']
        path=src/'case_files'/(commit['sha']+'.patch')
        path.write_text(commit['diff'],encoding='utf-8')
        prime_commits.append(dict(repository=item['request']['repo_full_name'],sha=commit['sha'],
            url=data['display_url'],patch_path=str(path),patch_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            filenames=[r['filename'] for r in commit['files']]))
    # Save compact comment-only conflict evidence with source provenance.
    prime={f"primevul:{r['idx']}":r for r in a.p2.jsonl(a.c.ROOT/'primevul_test.jsonl')}
    conflicts=[]
    for g in a.rows_csv(output/'duplicate_groups.csv'):
        if g['dataset']=='primevul_test' and g['grouping']=='token_sha256' and len(a.json.loads(g['labels']))>1:
            sids=a.json.loads(g['sample_ids']);x,y=[prime[s] for s in sids]
            conflicts.append(dict(sample_ids=sids,labels=[x['target'],y['target']],
                commits=[x['commit_url'],y['commit_url']],cves=[x['cve'],y['cve']],
                token_sha256=g['group'],diff=list(difflib.unified_diff(x['func'].splitlines(),y['func'].splitlines(),lineterm='')),
                judgment='context_or_label_incompatibility_candidate; not independently adjudicated'))
    a.write(output/'primevul_token_label_conflicts.json',conflicts)
    summary=dict(status='source_evidence_reconciled_no_security_execution',retrieved_cweval_files=len(cwe_files),
        cweval=dict(candidate_pairs=len(mapping),eligible_pairs=sum(r['eligible'] for r in mapping),
            eligible_security_marker_pairs=sum(r['eligible'] and r['security_marker_present'] for r in mapping),
            duplicate_definitions=[r for r in mapping if r['duplicate_top_level_function_names']],
            execution='not_run', limitation='Presence of tests and markers is not a passed test. Duplicate top-level Python definitions can shadow compiled-unsafe wrappers; inspect before execution.'),
        llmvul_construction=construction,construction_metrics=construction_metrics,
        llmvul_full_exact_conflicting_groups=len(full_label_conflicts),
        source_case_matches=matches,prime_patch_evidence=prime_commits,
        prime_token_conflicts=conflicts,downloaded_file_identities=identities,
        source_attribution='LLMVul upstream https://github.com/Wahed08/LLMVul-Dataset/tree/29313663fe2a575123adf552fd339c93c345e43d; CWEval upstream pinned e9a2a124c8c53679b6d8d27adfd2f6c40e7576d7')
    a.write(output/'evidence_summary.json',summary)
    print('Reconciled source files, task tests, and targeted cases.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);run(p.parse_args().output.resolve())
