"""Join priority-two evidence and produce descriptive, non-causal input slices."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import sys
import numpy as np

import rq1_priority2_audit as audit
common=audit.common


def stats(values):
    return dict(zip(['min','p25','median','p75','p90','p95','p99','max'],
                    map(float,np.quantile(values,[0,.25,.5,.75,.9,.95,.99,1])))) if values else None


def group_metrics(rows,model):
    if not rows:
        return dict(rows=0,positives=0,metrics=None)
    return dict(rows=len(rows),positives=sum(r['label'] for r in rows),
                positive_prevalence=sum(r['label'] for r in rows)/len(rows),
                metrics=common.manual_metrics([r['label'] for r in rows],[r[model]['prediction'] for r in rows]))


def run(output):
    _,jobs,datasets=audit.load_data()
    pm=common.read_json(output/'profiles/manifest.json')
    lm=common.read_json(output/'linevul/manifest.json')
    assert pm['status']=='complete' and lm['status']=='pass'
    ablation=common.read_json(output/'ablations/summary.json')
    assert ablation['status']=='pass'
    interventions=common.read_csv(output/'ablations/predictions.csv')
    for dataset in pm['datasets']:
        stem=dataset['dataset']
        assert common.sha(output/'profiles'/(stem+'.jsonl'))==dataset['profile_sha256']
        assert common.sha(output/'profiles'/(stem+'_lexical.jsonl.gz'))==dataset['lexical_sha256']
    controls=[r for r in interventions if r['condition'].endswith('_control')]
    assert all(r['input_changed']=='False' for r in controls)
    control_delta=max(abs(float(r['baseline_probability'])-float(r['variant_probability'])) for r in controls)
    assert control_delta==0
    for condition in ablation['conditions']:
        group=[r for r in interventions if all(r[k]==condition[k] for k in ('model','dataset','condition'))]
        condition['transitions']=dict(Counter(
            audit.error_cell(int(r['label']),int(r['baseline_prediction']))+'->'+
            audit.error_cell(int(r['label']),int(r['variant_prediction'])) for r in group))
    report=dict(scope='RQ1 priority 2',date='2026-10-29',started='2026-10-28',run_directory=output.relative_to(common.ROOT).as_posix(),
                profile_manifest=pm,linevul_export=lm,ablation=ablation,
                unchanged_controls=dict(rows=len(controls),input_changes=0,max_probability_delta=control_delta),
                clang=common.read_json(output/'clang_checks/summary.json'),jobs=[],source_cohorts=[],
                limitations=['Source labels remain unverified. Input slices differ in label prevalence and code difficulty.',
                             'Parse errors in standalone functions do not prove malformed or invalid source code.',
                             'Clang comparisons cover 36 cases, not all functions.',
                             'PrimeVul/LLMVul verified vulnerability spans and full calling context are unavailable locally.',
                             'BigVul line annotations are patch-derived and are not independently adjudicated vulnerability locations.',
                             'Cleaner and truncation flags overlap; counts must not be added as independent causes.',
                             'Tail windows are a context-sensitivity experiment and discard the function prefix.',
                             'CWEval benchmark_checked denotes the prior static dependency audit, not execution of its security tests.',
                             'Diagnostic cleaner variants may differ from the model training preprocessing.'],
                script_sha256=common.sha(Path(__file__)))
    if (output/'context_review_notes.json').exists():
        review=common.read_json(output/'context_review_notes.json')
        selection=common.read_json(output/'context_review_selection.json')
        assert {r['sample_id'] for r in review['cases']}=={r['sample_id'] for r in selection['cases']}
        report['context_review']=dict(**review,selection_policy=selection['policy'],seed=selection['seed'],
            notes_sha256=common.sha(output/'context_review_notes.json'),
            selection_sha256=common.sha(output/'context_review_selection.json'))
    flattened=[]
    examples=[]
    for stem in audit.STEMS:
        profile=audit.jsonl(output/'profiles'/(stem+'.jsonl'))
        scores=common.read_csv(output/'linevul'/(stem+'.csv'))
        assert len(profile)==len(scores)==len(datasets[stem])
        for i,(r,s) in enumerate(zip(profile,scores)):
            assert r['row']==i==int(s['row'])
            assert r['sample_id']==s['sample_id'] and r['code_sha256']==common.code_sha(datasets[stem][i]['processed_func'])
            assert r['label']==int(s['label']) and r['linevul']['prediction']==int(s['prediction'])
            r['linevul']['prob_vulnerable']=float(s['prob_vulnerable'])
        report['source_cohorts'].append(dict(dataset=stem,rows=len(profile),
            declared_languages=dict(Counter(str(r['source_language']) for r in profile)),
            parser_languages=dict(Counter(r['parser_language'] for r in profile)),
            source_parse_errors=sum(r['source_parse_error'] for r in profile),
            non_single_function_parses=sum(r['function_definition_count']!=1 for r in profile),
            rows_with_calls=sum(bool(r['call_expressions']) for r in profile),
            rows_with_preprocessor=sum(r['preprocessor_directives']>0 for r in profile),
            source_chars=stats([r['source_chars'] for r in profile]),source_lines=stats([r['source_lines'] for r in profile])))
        for model in ('linevul','vulberta'):
            if model+'/'+stem not in jobs:
                continue
            fn=[r for r in profile if r[model]['error']=='fn']
            fp=[r for r in profile if r[model]['error']=='fp']
            subsets={'all':profile,'truncated':[r for r in profile if r[model]['truncated']],
                     'untruncated':[r for r in profile if not r[model]['truncated']],
                     'source_parse_error':[r for r in profile if r['source_parse_error']],
                     'source_parse_clean':[r for r in profile if not r['source_parse_error']],
                     'unknown_fraction_ge_20pct':[r for r in profile if r[model]['unknown_fraction']>=.2]}
            details=dict(tokens=stats([r[model]['tokens_including_special'] for r in profile]),
                removed_fraction=stats([r[model]['truncation_fraction'] for r in profile]),
                unknown_fraction=stats([r[model]['unknown_fraction'] for r in profile]),
                weighted_unknown_fraction=sum(r[model]['unknown_tokens'] for r in profile)/max(1,sum(r[model]['tokens_including_special']-2 for r in profile)),
                retained_weighted_unknown_fraction=sum(r[model]['retained_unknown_tokens'] for r in profile)/max(1,sum(r[model]['retained_tokens_including_special']-2 for r in profile)),
                degenerate=sum(r[model]['degenerate'] for r in profile),fn=len(fn),fp=len(fp),
                fn_truncated=sum(r[model]['truncated'] for r in fn),fp_truncated=sum(r[model]['truncated'] for r in fp))
            if model=='vulberta':
                for name,predicate in {
                    'cleaner_lexical_change':lambda r:r[model]['cleaner_lexical_change_confirmed'],
                    'cleaner_retained_input_change':lambda r:r[model]['cleaner_changes_retained_input'] is True,
                    'confirmed_cleaner_retained_input_change':lambda r:r[model]['cleaner_lexical_change_confirmed'] and r[model]['cleaner_changes_retained_input'] is True,
                    'cleaner_introduced_parse_error':lambda r:r[model]['introduced_parse_error'],
                    'preprocessor_line_structure_changed':lambda r:r[model]['preprocessor_line_structure_changed'],
                    'untruncated_no_confirmed_cleaner_change':lambda r:not r[model]['truncated'] and not r[model]['cleaner_lexical_change_confirmed'],
                    'parse_clean_untruncated_lexically_unchanged':lambda r:not r['source_parse_error'] and not r[model]['truncated'] and not r[model]['lexical_tree_changed'],
                    'lexical_change_but_no_retained_input_change':lambda r:r[model]['cleaner_lexical_change_confirmed'] and r[model]['cleaner_changes_retained_input'] is False,
                    'lexical_change_visibility_unresolved':lambda r:r[model]['cleaner_lexical_change_confirmed'] and r[model]['cleaner_changes_retained_input'] is None,
                }.items():
                    subsets[name]=[r for r in profile if predicate(r)]
                details.update(fn_cleaner_lexical_change=sum(r[model]['cleaner_lexical_change_confirmed'] for r in fn),
                    fp_cleaner_lexical_change=sum(r[model]['cleaner_lexical_change_confirmed'] for r in fp),
                    fn_retained_input_change=sum(r[model]['cleaner_changes_retained_input'] is True for r in fn),
                    fp_retained_input_change=sum(r[model]['cleaner_changes_retained_input'] is True for r in fp),
                    fn_either_truncated_or_changed=sum(r[model]['truncated'] or r[model]['cleaner_changes_retained_input'] is True for r in fn),
                    fp_either_truncated_or_changed=sum(r[model]['truncated'] or r[model]['cleaner_changes_retained_input'] is True for r in fp))
                replacements={int(r['row']):int(r['variant_prediction']) for r in interventions
                              if r['model']==model and r['dataset']==stem and r['condition'].startswith('cleaner_') and r['condition']!='cleaner_unchanged_control'}
                details['tested_cleaner_replacement']=dict(rows_replaced=len(replacements),
                    note='Diagnostic replacement of tested cleaner cases only; not a new official RQ1 result or all-row alternative-cleaner run.',
                    metrics=common.manual_metrics([r['label'] for r in profile],
                        [replacements.get(r['row'],r[model]['prediction']) for r in profile]))
            else:
                annotations=[r for r in profile if r['label']==1]
                details['annotation_audit']=dict(status_counts=dict(Counter(r[model]['annotated_line_visibility']['status'] for r in annotations)),
                    fn_status_counts=dict(Counter(r[model]['annotated_line_visibility']['status'] for r in fn)),
                    positive_rows_losing_some_annotated_lines=sum(r[model]['annotated_line_visibility']['partly_or_fully_removed_lines']>0 for r in annotations),
                    fn_losing_some_annotated_lines=sum(r[model]['annotated_line_visibility']['partly_or_fully_removed_lines']>0 for r in fn))
            report['jobs'].append(dict(job=model+'/'+stem,model=model,dataset=stem,rows=len(profile),details=details,
                                      slices={name:group_metrics(rows,model) for name,rows in subsets.items()}))
            for r in profile:
                p=r[model]
                flattened.append(dict(model=model,dataset=stem,row=r['row'],sample_id=r['sample_id'],label=r['label'],
                    prediction=p['prediction'],prob_vulnerable=p['prob_vulnerable'],error=p['error'],project=r['project'],
                    source_language=r['source_language'],parser_language=r['parser_language'],source_parse_error=r['source_parse_error'],
                    code_sha256=r['code_sha256'],duplicate_group=r['duplicate_group'],duplicate_group_rows=r['duplicate_group_rows'],
                    source_chars=r['source_chars'],source_lines=r['source_lines'],tokens=p['tokens_including_special'],
                    retained_tokens=p['retained_tokens_including_special'],truncated=p['truncated'],removed_fraction=p['truncation_fraction'],
                    unknown_fraction=p['unknown_fraction'],degenerate=p['degenerate'],cleaned_code_sha256=p['cleaned_code_sha256'],
                    cleaner_lexical_change=p.get('cleaner_lexical_change_confirmed',False),
                    cleaner_retained_input_change=p.get('cleaner_changes_retained_input',False),
                    cleaner_introduced_parse_error=p.get('introduced_parse_error',False),
                    context_assessment=r['context_assessment'],vulnerability_span_status=r['vulnerability_span_status']))
        # Save transparent examples of improvements, regressions and persistent errors.
        source_lookup={r['row']:r for r in profile}
        for category,predicate in {
            'cleaner_recovered':lambda r:r['condition']=='cleaner_untruncated' and r['baseline_correct']=='False' and r['variant_correct']=='True',
            'cleaner_regressed':lambda r:r['condition']=='cleaner_untruncated' and r['baseline_correct']=='True' and r['variant_correct']=='False',
            'tail_recovered':lambda r:r['condition']=='tail_window' and r['baseline_correct']=='False' and r['variant_correct']=='True',
            'tail_regressed':lambda r:r['condition']=='tail_window' and r['baseline_correct']=='True' and r['variant_correct']=='False',
        }.items():
            choices=[r for r in interventions if r['dataset']==stem and predicate(r)]
            choices=sorted(choices,key=lambda r:(len(datasets[stem][int(r['row'])]['processed_func']),r['sample_id']))[:3]
            for item in choices:
                i=int(item['row']); code=datasets[stem][i]['processed_func']
                examples.append(dict(category=category,intervention=item,metadata=source_lookup[i],
                                     source=code,historical_cleaned=audit.cwe.load_preprocessing()['clean_for_vulberta'](code)))
    common.write_csv(output/'joined_inputs.csv',flattened)
    common.write_json(output/'examples.json',examples)
    common.write_json(output/'input_summary.json',report)
    print(json.dumps([dict(job=j['job'],rows=j['rows'],truncated=j['slices']['truncated']['rows'],
                          token_median=j['details']['tokens']['median'],fn=j['details']['fn'],fn_truncated=j['details']['fn_truncated'],
                          cleaner_changed=j['slices'].get('cleaner_lexical_change',{}).get('rows'),
                          cleaner_visible=j['slices'].get('cleaner_retained_input_change',{}).get('rows'),
                          fn_cleaner_visible=j['details'].get('fn_retained_input_change')) for j in report['jobs']],indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output',type=Path,required=True)
    run(p.parse_args().output.resolve())
