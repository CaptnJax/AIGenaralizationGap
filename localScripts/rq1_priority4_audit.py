"""Read-only label/construction audit of frozen RQ1 datasets and predictions.

Creates review materials, not independent reviewer judgments. Run sources must be
retrieved separately; no untrusted downloaded Python is imported or executed.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import random
import re
import shutil

import numpy as np
from sklearn import metrics
import rq1_priority2_audit as p2
from rq1_priority3_scores import ScoreCurve, jsonable

c = p2.common
P2 = c.input_path(c.HERE / 'results/rq1_priority2_20261028')
P3 = c.input_path(c.HERE / 'results/rq1_priority3_20261029')
SEED = 20261029
QUOTAS = {'fn': 20, 'fp': 20, 'tp': 10, 'tn': 10}
MISSING = {'', 'none', 'null', 'nan', 'n/a'}


def write(path, data):
    c.write_json(path, jsonable(data))


def rows_csv(path, title=False):
    csv.field_size_limit(10**8)
    with c.input_path(path).open(encoding='utf-8-sig', newline='') as f:
        if title:
            next(csv.reader(f))
        return list(csv.DictReader(f))


def csv_out(path, rows, fields=None):
    if not fields:
        fields = list(dict.fromkeys(k for r in rows for k in r))
    with Path(path).open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in r.items()})


def jsonl_out(path, rows):
    with Path(path).open('w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(jsonable(r), ensure_ascii=False) + '\n')


def present(value):
    return value is not None and str(value).strip().lower() not in MISSING and value != []


def blob_sha(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def ensemble(votes):
    n = sum(int(v) for v in votes)
    return 'safe' if n == 0 else 'uncertain' if n == 1 else 'vulnerable'


def token_profile(code, lang, parser_map):
    tree, chosen, errors = p2.parse_best(code, lang, parser_map)
    allnodes = list(p2.nodes(tree.root_node))
    funcs = [n for n in allnodes if n.type == 'function_definition']
    leaves, structural = [], []
    def walk(n):
        if n.type == 'comment':
            return
        # Treat entire literals as units; never normalize their internal spaces.
        if n.type in ('string_literal', 'raw_string_literal', 'char_literal'):
            leaves.append(n.text.decode('utf-8')); structural.append(leaves[-1]); return
        if n.child_count:
            for ch in n.children:
                walk(ch)
        else:
            value = n.text.decode('utf-8')
            if value:
                leaves.append(value)
                structural.append('<identifier>' if n.type.endswith('identifier') else value)
    walk(tree.root_node)
    names = []
    for n in funcs:
        dec = n.child_by_field_name('declarator')
        if dec:
            ids = [x.text.decode('utf-8') for x in p2.nodes(dec) if x.type in ('identifier', 'field_identifier')]
            names.append(ids[0] if ids else '')
    body = funcs[0].child_by_field_name('body') if len(funcs) == 1 else None
    statements = [ch for ch in body.named_children if ch.type != 'comment'] if body else []
    return dict(token_sha256=p2.digest_tokens(leaves), structural_sha256=p2.digest_tokens(structural),
                token_count=len(leaves), parser_language=chosen, parser_error_count=errors,
                source_parse_error=tree.root_node.has_error, function_count=len(funcs),
                function_names=names, empty_body=body is not None and not statements,
                trivial_return_body=bool(len(statements) == 1 and statements[0].type == 'return_statement'),
                source_lines=len(code.splitlines()), source_chars=len(code))


def profile_groups(rows, field):
    groups = defaultdict(list)
    for r in rows:
        groups[r[field]].append(r)
    duplicate = [rs for rs in groups.values() if len(rs) > 1]
    conflict = [rs for rs in groups.values() if len({r['label'] for r in rs}) > 1]
    return dict(rows=len(rows), groups=len(groups), extra_rows=len(rows)-len(groups),
                duplicate_groups=len(duplicate), rows_in_duplicate_groups=sum(map(len, duplicate)),
                conflicting_groups=len(conflict), conflicting_rows=sum(map(len, conflict)),
                largest_group=max(map(len, groups.values()), default=0)), groups


def weighted_metrics(rows, field=None):
    count = Counter(r[field] for r in rows) if field else None
    w = np.array([1/count[r[field]] if field else 1 for r in rows])
    y = np.array([r['label'] for r in rows]); s = np.array([r['score'] for r in rows])
    m = ScoreCurve(y, s).evaluate(w)
    # Independent weighted F1/precision/recall including one-class slices.
    for name, fn in [('f1', metrics.f1_score), ('precision', metrics.precision_score), ('recall', metrics.recall_score)]:
        v = fn(y, s > .5, sample_weight=w, zero_division=0)
        if np.isfinite(m[name]):
            assert abs(v - m[name]) < 1e-10, (name, v, m[name])
        m[name] = float(v)
    m.update(rows=len(rows), original_positives=int(y.sum()), effective_weight=float(w.sum()), weighting=field or 'rows')
    return m


def select_sample(rows, seed):
    rng = random.Random(seed)
    selected, strata = [], []
    for cell, quota in QUOTAS.items():
        pool = sorted([r for r in rows if r['error'] == cell], key=lambda r: r['sample_id'])
        chosen = rng.sample(pool, min(quota, len(pool)))
        prob = len(chosen)/len(pool) if pool else 0
        strata.append(dict(error=cell, population=len(pool), selected=len(chosen), inclusion_probability=prob))
        for r in chosen:
            selected.append(dict(sample_id=r['sample_id'], error=cell, population=len(pool), selected=len(chosen),
                                 inclusion_probability=prob, inverse_probability=1/prob, seed=seed))
    return selected, strata


def cohort_profile(rows):
    result = dict(rows=len(rows), projects=len({r['project_name'] for r in rows}),
                  commits=len({(r['project_name'], r['commit_id']) for r in rows}),
                  exact_code_groups=len({c.code_sha(r['function_body']) for r in rows}))
    for field in ['language', 'project_name', 'ai_tool', 'signal_strength', 'signal_type', 'ensemble_label', 'semgrep_rule', 'cwe_id']:
        result[field] = dict(Counter(r[field] or '(missing)' for r in rows).most_common())
    for field, vals in [('lines', [len(r['function_body'].splitlines()) for r in rows]),
                        ('chars', [len(r['function_body']) for r in rows])]:
        result[field] = dict(zip(['min', 'median', 'p90', 'max'], np.quantile(vals, [0, .5, .9, 1])))
    result['analyzer_patterns'] = dict(Counter(''.join(r[k] for k in ['tool_semgrep','tool_flawfinder','pattern_match']) for r in rows))
    return result


def review_package(output, byjob, rowmap, rawmap):
    review = output/'review'; review.mkdir(exist_ok=False)
    selections, strata, purposive = [], [], []
    for ji, (job, rows) in enumerate(sorted(byjob.items())):
        chosen, ss = select_sample(rows, SEED + ji)
        selections.extend(dict(job=job, **r) for r in chosen)
        strata.extend(dict(job=job, **r) for r in ss)
        for cell, high in [('fn', False), ('fp', True)]:
            pool = sorted([r for r in rows if r['error'] == cell], key=lambda r:(r['score'], r['sample_id']), reverse=high)
            if pool:
                purposive.append(dict(job=job, sample_id=pool[0]['sample_id'], reason='highest_score_fp' if high else 'lowest_score_fn'))
        worst = max(rows, key=lambda r:(rowmap[r['sample_id']]['parser_error_count'], r['sample_id']))
        if rowmap[worst['sample_id']]['parser_error_count']:
            purposive.append(dict(job=job, sample_id=worst['sample_id'], reason='largest_parser_error_count'))
    ids = sorted({r['sample_id'] for r in selections}); random.Random(SEED+1000).shuffle(ids)
    key = {sid:'R%04d' % (i+1) for i, sid in enumerate(ids)}
    for r in selections:
        r['review_id'] = key[r['sample_id']]
    packets, evidence, keys = [], [], []
    for sid in ids:
        r, raw = rowmap[sid], rawmap[sid]
        packets.append(dict(review_id=key[sid], code=r['code'], declared_language=r['language']))
        ev = {k:v for k,v in raw.items() if k not in ['target','vuln_label','ensemble_label','label','function_body','func','processed_func']}
        # Predictions are never provided to either review stage. Evidence can imply labels.
        evidence.append(dict(review_id=key[sid], source_evidence=ev))
        probs = [s['inclusion_probability'] for s in selections if s['sample_id']==sid]
        keys.append(dict(review_id=key[sid], sample_id=sid, dataset=r['dataset'], original_label=r['label'],
                         merged_inclusion_probability=1-float(np.prod([1-p for p in probs])),
                         probability_note='Union over all jobs for this dataset, computed below'))
    # Union probabilities must include every model's eligible stratum, even if not selected by it.
    strata_map = {(r['job'], r['error']):r['inclusion_probability'] for r in strata}
    jobs_lookup = {j:{r['sample_id']:r for r in rs} for j,rs in byjob.items()}
    for k in keys:
        pp = [strata_map[j, lookup[k['sample_id']]['error']] for j,lookup in jobs_lookup.items() if k['sample_id'] in lookup]
        k['merged_inclusion_probability'] = 1-float(np.prod([1-p for p in pp]))
        k['probability_note'] = '1-product(1-n_h/N_h) over independent model-specific stratum samples; use per-job weights for per-job estimates'
    csv_out(review/'selection.csv', selections); csv_out(review/'strata.csv', strata)
    csv_out(review/'coordinator_key.csv', keys); csv_out(review/'purposive_selection.csv', purposive)
    jsonl_out(review/'stage1_blinded_code.jsonl', packets)
    jsonl_out(review/'stage2_source_evidence.jsonl', evidence)
    jsonl_out(review/'purposive_cases.jsonl', [dict(**r, source=rawmap[r['sample_id']], code=rowmap[r['sample_id']]['code']) for r in purposive])
    fields=['review_id','reviewer_id','judgment','scope','evidence_url_or_path','code_lines','cwe','confidence','tags','explanation']
    for reviewer in (1,2):
        csv_out(review/f'reviewer_{reviewer}.csv', [{k:p['review_id'] if k=='review_id' else '' for k in fields} for p in packets], fields)
    csv_out(review/'adjudication.csv', [dict(review_id=p['review_id'], final_judgment='', evidence='', rationale='', adjudicator='') for p in packets])
    (review/'README.md').write_text('''# Priority 4 independent review package

Status: prepared; independent reviews and adjudication have not been performed.
Give each qualified reviewer only stage1_blinded_code.jsonl and their own blank
reviewer form. Do not give the coordinator key, selections, this audit report,
or model predictions. Code comments/identifiers may themselves reveal provenance;
blinding is therefore best effort, not guaranteed. Then release stage2 evidence,
retaining both initial and evidence-informed judgments separately. Source metadata
can reveal intended labels; record when that happens. Never run untrusted source
on the host. Test evidence needs an isolated environment.

Allowed judgments: vulnerable; non_vulnerable_scoped; uncertain;
insufficient_context. A scoped negative must name the assessed vulnerability
and assumptions; it does not certify universal safety. Provide line references,
patch/test/source evidence, CWE only if justified, confidence, and rationale.
Tags can include label_disagreement, confirmed_label_error, missing_context,
preprocessing_damage, lost_span, unsupported_language, model_miss,
spurious_model_positive. Do not use model-miss tags until predictions are revealed.

Two reviewers work independently before the adjudicator resolves disagreements
with evidence. Blank forms are not negative judgments. Preserve uncertain and
insufficient-context decisions; do not silently coerce them to binary labels.

selection.csv preserves each model/stratum sample probability n/N and weight N/n.
coordinator_key.csv also gives merged-sample union probabilities. For per-job
estimates use that job's selections and weights, not the union or the raw review
fraction. Report unresolved weighted mass separately; use design-aware uncertainty
before estimating population label-error rates. Purposive cases and the external
authors' 100-case sample are separate, with no probability weights invented.

Original source labels and benchmark predictions remain unchanged. No corrected
whole-dataset metrics should be presented before defensible adjudication.
''', encoding='utf-8')
    return dict(selections=len(selections), unique_cases=len(ids), strata=strata,
                principal_selections=sum('primevul' in r['job'] or 'llmvul' in r['job'] for r in selections),
                purposive_selections=len(purposive), purposive_unique_cases=len({r['sample_id'] for r in purposive}),
                independent_review_status='pending_two_qualified_reviewers', adjudicated_cases=0)


def external_review(output, raw_llm, byjob):
    review = rows_csv(output/'sources/llmvul_manual_review.csv', title=True)
    lookup = {r['unique_id']:r for r in raw_llm}
    rating = Counter((r['rater1_label'],r['rater2_label']) for r in review)
    complete = [r for r in review if r['rater1_label'] in ('0','1') and r['rater2_label'] in ('0','1')]
    joined = []
    for r in review:
        original = lookup.get(r['unique_id'])
        assert original is not None
        joined.append(dict(sample_id='llmvul:'+r['unique_id'], rater1=r['rater1_label'], rater2=r['rater2_label'],
                           original_label=int(float(original['vuln_label'])), code_exact=r['function_body']==original['function_body'],
                           review_code_sha256=c.code_sha(r['function_body']), source_code_sha256=c.code_sha(original['function_body']),
                           notes=r['notes']))
    csv_out(output/'external_review_join.csv', joined)
    out = dict(rows=len(review), unique_ids=len({r['unique_id'] for r in review}), exact_code_matches=sum(r['code_exact'] for r in joined),
               rating_pairs={','.join(k):v for k,v in rating.items()},
               nominal_three_category_kappa=metrics.cohen_kappa_score([r['rater1_label'] for r in review],[r['rater2_label'] for r in review]),
               complete_binary_rows=len(complete), complete_binary_kappa=metrics.cohen_kappa_score([r['rater1_label'] for r in complete],[r['rater2_label'] for r in complete]),
               undocumented_minus_one_rows=len(review)-len(complete), consensus_field_present=False,
               interpretation='Published rater agreement is source evidence, not our independent adjudication. -1 is undocumented and not recoded. Binary kappa is conditional on omitting incomplete rows.',
               agreed_zero_ids=[r['sample_id'] for r in joined if r['rater1']==r['rater2']=='0'], metrics=[])
    agreed = {r['sample_id']:int(r['rater1']) for r in joined if r['code_exact'] and r['rater1']==r['rater2'] and r['rater1'] in ('0','1')}
    out['agreed_binary_exact_rows']=len(agreed)
    for job, rs in byjob.items():
        if not job.endswith('/llmvul_test'): continue
        original=[r for r in rs if r['sample_id'] in agreed]
        adjud=[dict(r, label=agreed[r['sample_id']]) for r in original]
        out['metrics'].append(dict(job=job, original_selected_labels=weighted_metrics(original),
                                    published_agreed_labels=weighted_metrics(adjud)))
        # Explicitly limited hybrid, replacing only two documented agreed-zero judgments.
        hybrid=[dict(r, label=agreed.get(r['sample_id'],r['label'])) for r in rs]
        out['metrics'][-1]['limited_hybrid']=weighted_metrics(hybrid)
    return out


def run(output):
    assert (output/'analysis_plan.json').is_file(), 'Freeze the analysis plan first.'
    assert not (output/'summary.json').exists(), 'Use a new output directory.'
    baseline, jobs, datasets = p2.load_data()
    p3summary=c.read_json(P3/'summary.json')
    joined_path=P2/'joined_inputs.csv'
    assert c.sha(joined_path)==p3summary['source_hashes']['joined_inputs.csv']
    source_paths=[c.ROOT/'LLMVul_v3-Updated.csv', c.ROOT/'primevul_test.jsonl', c.ROOT/'primevul_valid.jsonl',
                  c.ROOT/'prepared_datasets/cweval/catalog.jsonl', joined_path]
    source_paths += [c.ROOT/j['prediction_file']['path'] for j in jobs.values()]
    source_paths = [c.input_path(p) for p in source_paths]
    before={str(p.relative_to(c.ROOT)):c.sha(p) for p in source_paths}
    sources=c.read_json(output/'sources/github_sources.json')
    raw_llm=rows_csv(source_paths[0],title=True)
    raw_prime=p2.jsonl(source_paths[1]); raw_cwe=p2.jsonl(source_paths[3])
    raw_big=rows_csv(c.CACHE/'data/bigvul_test_sample_2000.csv')
    rawsets={'llmvul_test':[r for r in raw_llm if r['ensemble_label']!='uncertain'], 'primevul_test':raw_prime,
             'cweval_test':[r for r in raw_cwe if r['eligible']], 'bigvul_test_sample_2000':raw_big}
    assert blob_sha(source_paths[0].read_bytes())==next(x['sha'] for x in sources['llmvul_tree']['tree'] if x['path']=='data/LLMVul_v3-Updated.csv')
    parser_map=p2.parsers(); rowmap={}; rawmap={}; allrows=[]
    for stem in p2.STEMS:
        print('Structure and provenance:', stem, flush=True)
        profiles=p2.jsonl(P2/'profiles'/(stem+'.jsonl'))
        assert len(datasets[stem])==len(profiles)==len(rawsets[stem])
        for row, profile, raw in zip(datasets[stem], profiles, rawsets[stem]):
            sid=row['sample_id']; code=row['processed_func']
            assert c.code_sha(code)==profile['code_sha256']
            lang=raw.get('language') or profile['source_language'] or 'unknown'
            info=token_profile(code,lang,parser_map)
            rec=dict(sample_id=sid, dataset=stem,label=int(row['target']),code=code,code_sha256=c.code_sha(code),language=lang,
                     project=profile['project'], file_name=profile['file_name'],**info)
            rowmap[sid]=rec; rawmap[sid]=raw; allrows.append(rec)
    included=rawsets['llmvul_test']; excluded=[r for r in raw_llm if r['ensemble_label']=='uncertain']
    uncertain=[]
    for raw in excluded:
        uncertain.append(dict(sample_id='llmvul:'+raw['unique_id'], label=None, language=raw['language'],
                              project=raw['project_name'], code_sha256=c.code_sha(raw['function_body']),
                              **token_profile(raw['function_body'],raw['language'],parser_map)))
    csv_out(output/'uncertain_structure.csv', uncertain)
    jsonl_out(output/'row_structure.jsonl',[{k:v for k,v in r.items() if k!='code'} for r in allrows])
    byjob=defaultdict(list)
    for r in rows_csv(joined_path):
        profile=rowmap[r['sample_id']]
        assert int(r['label'])==profile['label'] and r['code_sha256']==profile['code_sha256']
        rec={k:v for k,v in profile.items() if k!='code'}
        rec.update(score=float(r['prob_vulnerable']), prediction=int(r['prediction']), error=r['error'])
        assert rec['prediction']==int(rec['score']>.5)
        byjob[r['model']+'/'+r['dataset']].append(rec)
    summaries={}; groupdetails=[]; sensitivity=[]; slices=[]
    group_fields=['code_sha256','token_sha256','structural_sha256']
    for stem in p2.STEMS:
        rr=[r for r in allrows if r['dataset']==stem]
        summaries[stem]={}
        for field in group_fields:
            summary, groups=profile_groups(rr,field);summaries[stem][field]=summary
            for key,rs in groups.items():
                if len(rs)>1:
                    groupdetails.append(dict(dataset=stem,grouping=field,group=key,rows=len(rs),labels=sorted({r['label'] for r in rs}),sample_ids=[r['sample_id'] for r in rs]))
        summaries[stem]['structure']=dict(language=dict(Counter(r['language'] for r in rr)),
            parse_errors=sum(r['source_parse_error'] for r in rr),function_counts=dict(Counter(r['function_count'] for r in rr)),
            empty_bodies=sum(r['empty_body'] for r in rr),trivial_return_bodies=sum(r['trivial_return_body'] for r in rr))
    cross=[]; overlap_ids=set()
    for field in group_fields:
        groups=defaultdict(list)
        for r in allrows: groups[r[field]].append(r)
        for key,rs in groups.items():
            if len({r['dataset'] for r in rs})>1:
                cross.append(dict(grouping=field,group=key,datasets=sorted({r['dataset'] for r in rs}),
                    sample_ids=[r['sample_id'] for r in rs],labels=[r['label'] for r in rs],conflicting=len({r['label'] for r in rs})>1))
                if field=='code_sha256':overlap_ids.update(r['sample_id'] for r in rs)
    csv_out(output/'duplicate_groups.csv',groupdetails)
    jsonl_out(output/'cross_dataset_groups.jsonl',cross)
    for job,rr in byjob.items():
        for field in [None]+group_fields:
            sensitivity.append(dict(job=job,**weighted_metrics(rr,field)))
        noover=[r for r in rr if r['sample_id'] not in overlap_ids]
        sensitivity.append(dict(job=job,**weighted_metrics(noover),condition='exclude_cross_dataset_exact_matches'))
        for field in ['language','source_parse_error','function_count','empty_body','trivial_return_body','project']:
            groups=defaultdict(list)
            for r in rr:groups[str(r[field])].append(r)
            for value, group in sorted(groups.items()):
                slices.append(dict(job=job,field=field,value=value,**weighted_metrics(group)))
        if job.endswith('/llmvul_test'):
            for field in ['signal_strength','signal_type','ai_tool','semgrep_rule','cwe_id','analyzer_votes']:
                groups=defaultdict(list)
                for r in rr:
                    raw=rawmap[r['sample_id']]
                    value=str(sum(int(raw[k]) for k in ['tool_semgrep','tool_flawfinder','pattern_match'])) if field=='analyzer_votes' else raw[field] or '(missing)'
                    groups[value].append(r)
                for value,group in sorted(groups.items()):
                    slices.append(dict(job=job,field=field,value=value,**weighted_metrics(group)))
    csv_out(output/'weighting_sensitivity.csv',sensitivity); csv_out(output/'cohort_metrics.csv',slices)
    votechecks=[]
    for r in raw_llm:
        expected=ensemble([r[k] for k in ['tool_semgrep','tool_flawfinder','pattern_match']])
        numeric={'safe':'0.0','uncertain':'','vulnerable':'1.0'}[expected]
        if expected!=r['ensemble_label'] or numeric!=r['vuln_label']:
            votechecks.append(r['unique_id'])
    commits=defaultdict(list)
    for r in raw_llm:commits[(r['project_name'],r['commit_id'])].append(r)
    llm=dict(source_rows=len(raw_llm), published_git_blob_matches=True, vote_rule_mismatches=votechecks,
        included=cohort_profile(included), excluded_uncertain=cohort_profile(excluded),
        full_exact_groups=len({c.code_sha(r['function_body']) for r in raw_llm}),
        uncertain_structure=dict(parse_errors=sum(r['source_parse_error'] for r in uncertain), function_counts=dict(Counter(r['function_count'] for r in uncertain))),
        attribution=dict(scope='commit metadata, not independently verified function authorship',commits=len(commits),
            commits_with_multiple_functions=sum(len(rs)>1 for rs in commits.values()),largest_commit_functions=max(map(len,commits.values())),
            mixed_signal_commits=sum(len({(r['ai_tool'],r['signal_type'],r['signal_strength']) for r in rs})>1 for rs in commits.values()),
            strong_without_visible_coauthor_trailer=sum(r['signal_strength']=='strong' and 'co-authored-by:' not in r['commit_message'].lower() for r in raw_llm),
            warning='Messages may be truncated at 1000 characters by the published representative miner; missing visible trailer is not disproof.'),
        rule_counts=dict(Counter(r['semgrep_rule'] or '(missing)' for r in included if r['ensemble_label']=='vulnerable')),
        raw_analyzer_locations_available=False,
        construction='Published representative miner parses concatenated added diff lines, not complete checked-out files; executed original labeling rules/versions and run logs are unavailable in the retrieved tree.')
    prime={}
    for label in (0,1):
        rr=[r for r in raw_prime if r['target']==label]
        prime[str(label)]=dict(rows=len(rr), **{k+'_present':sum(present(r.get(k)) for r in rr) for k in ['commit_url','commit_message','file_name','file_hash','cve','cve_desc','cwe']})
    prime['limitations']='No row-level OneFunc/NVDCheck decision field or local file_info/file_contents package; a CVE or commit link is supporting provenance, not independent function-level validation.'
    cwe=dict(candidate_rows=len(raw_cwe),selected_rows=sum(r['eligible'] for r in raw_cwe),
        selected_pairs=len({r['pair_id'] for r in raw_cwe if r['eligible']}),
        all_target_tokens_match=all(r['upstream_target_tokens_match'] for r in raw_cwe),
        excluded_reasons=dict(Counter(x for r in raw_cwe for x in r['pair_exclusion_reasons'])),
        security_execution='not_run: no Docker executable, no GCC/Clang executable on PATH, and WSL reports not installed; static test mapping is separate evidence',
        label_scope='reference versus intentionally unsafe for the specified task/CWE; no universal safety or verified LLM authorship claim')
    reviews=review_package(output,byjob,rowmap,rawmap)
    external=external_review(output,raw_llm,byjob)
    after={str(p.relative_to(c.ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    assert before==after
    manifest=dict(status='automated_audit_complete_independent_adjudication_pending',plan_sha256=c.sha(output/'analysis_plan.json'),
        script_sha256=c.sha(Path(__file__)),source_hashes=before,source_files_unchanged=True,
        datasets=summaries,weighting=sensitivity,cross_dataset=dict(groups_by_type=dict(Counter(r['grouping'] for r in cross)),
            conflicting_groups_by_type=dict(Counter(r['grouping'] for r in cross if r['conflicting'])),exact_overlap_rows=len(overlap_ids)),
        llmvul=llm,primevul=prime,cweval=cwe,review=reviews,external_review=external,
        limitations=['No independent new label adjudication; no population label-error estimate.',
                     'Structural grouping is a candidate similarity screen, not semantic equivalence or exhaustive fuzzy search.',
                     'Sensitivity metrics are descriptive, not causal and not replacement RQ1 scores.',
                     'Uncertain LLMVul records have no binary labels or predictions in these analyses.'])
    shutil.copyfile(__file__,output/'audit.py')
    write(output/'summary.json',manifest)
    print('Completed',output,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args().output.resolve())
