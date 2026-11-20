"""Controlled cleaning and tail-window diagnostics; never changes RQ1 defaults."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import random
import shutil
import sys
from types import SimpleNamespace

import rq1_priority1_audit as common
import rq1_priority2_audit as audit


def pack(full_ids, limit, tail=False):
    assert full_ids[0] == 0 and full_ids[-1] == 2
    body = full_ids[1:-1]
    body = body[-(limit-2):] if tail else body[:limit-2]
    ids = [0]+body+[2]
    return ids+[1]*(limit-len(ids))


def choose_rows(rows, predicate, per_cell=16):
    """Sample only from a predefined input condition and confusion-matrix cell."""
    rng, chosen = random.Random(42), []
    for cell in ('tn','fp','fn','tp'):
        candidates=[r for r in rows if predicate(r) and r['_error']==cell]
        chosen.extend(rng.sample(candidates,min(per_cell,len(candidates))))
    return sorted(chosen,key=lambda r:r['row'])


def run(output):
    import torch
    from transformers import AutoTokenizer,AutoModelForSequenceClassification,RobertaConfig,RobertaTokenizer,RobertaForSequenceClassification,set_seed
    _, jobs, datasets = audit.load_data()
    assert common.read_json(output/'profiles/manifest.json')['status']=='complete'
    assert common.read_json(output/'linevul/manifest.json')['status']=='pass'
    directory=output/'ablations'
    directory.mkdir(exist_ok=False)
    shutil.copyfile(__file__,directory/'ablation_runner.py')
    profiles={stem:audit.jsonl(output/'profiles'/(stem+'.jsonl')) for stem in audit.STEMS}
    parser_map=audit.parsers()
    from clang import cindex
    clang_index=cindex.Index.create()
    auditor=audit.cwe.TokenAudit(common.CACHE)
    selected=[]
    for model in ('linevul','vulberta'):
        for stem, profile in profiles.items():
            if model+'/'+stem not in jobs:
                continue
            active=[dict(r,_error=r[model]['error']) for r in profile]
            for r in choose_rows(active,lambda r:r[model]['truncated']):
                selected.append(dict(model=model,dataset=stem,row=r['row'],sample_id=r['sample_id'],condition='tail_window',
                                     label=r['label'],historical_prediction=r[model]['prediction']))
            for r in choose_rows(active,lambda r:not r[model]['truncated'],per_cell=4):
                selected.append(dict(model=model,dataset=stem,row=r['row'],sample_id=r['sample_id'],condition='tail_untruncated_control',
                                     label=r['label'],historical_prediction=r[model]['prediction']))
            if model=='vulberta':
                for r in active:
                    p=r[model]
                    if p['cleaner_lexical_change_confirmed'] and p['alternative_lexical_preservation'] and p['cleaner_changes_retained_input']:
                        condition=('cleaner_untruncated' if not p['truncated'] and p['alternative_tokens_including_special']<=1024
                                   else 'cleaner_with_truncation')
                        selected.append(dict(model=model,dataset=stem,row=r['row'],sample_id=r['sample_id'],condition=condition,
                                             label=r['label'],historical_prediction=p['prediction']))
                for r in choose_rows(active,lambda r:not r['source_parse_error'] and not r[model]['lexical_tree_changed'] and not r[model]['truncated'],per_cell=8):
                    selected.append(dict(model=model,dataset=stem,row=r['row'],sample_id=r['sample_id'],condition='cleaner_unchanged_control',
                                         label=r['label'],historical_prediction=r[model]['prediction']))
    common.write_json(directory/'selection.json',selected)
    print('Fixed intervention selection:',dict(Counter(r['condition'] for r in selected)),flush=True)
    set_seed(42)
    torch.backends.cudnn.benchmark=False
    torch.backends.cudnn.deterministic=True
    device='cuda' if torch.cuda.is_available() else 'cpu'
    helpers=common.load_module(common.HERE/'vulberta_eval.py','ablation_vulberta')
    summaries,results=[],[]
    for model_name in ('linevul','vulberta'):
        limit=512 if model_name=='linevul' else 1024
        if model_name=='linevul':
            sys.path.insert(0,str(common.LV))
            line=common.load_module(common.LV/'linevul_main_local.py','ablation_linevul')
            tokenizer=RobertaTokenizer.from_pretrained(str(common.CB),local_files_only=True)
            config=RobertaConfig.from_pretrained(str(common.CB),local_files_only=True)
            config.num_labels,config.num_attention_heads=1,12
            model=line.Model(RobertaForSequenceClassification(config),config,tokenizer,SimpleNamespace())
            state=torch.load(common.LV/'saved_models/checkpoint-best-f1/12heads_linevul_model.bin',map_location='cpu',weights_only=True)
            line._load_local_checkpoint(model,state)
            del state
        else:
            tokenizer=AutoTokenizer.from_pretrained('claudios/VulBERTa-MLP-Devign',revision=common.VB_REV,
                                                   trust_remote_code=True,local_files_only=True)
            helpers.fix_clang_parser(tokenizer)
            model,loading=AutoModelForSequenceClassification.from_pretrained(str(common.VB),local_files_only=True,
                                                                            use_safetensors=True,output_loading_info=True)
            assert not any(loading.get(k) for k in ('missing_keys','unexpected_keys','mismatched_keys','error_msgs'))
        model.to(device).eval()
        candidates=[r for r in selected if r['model']==model_name]
        for start in range(0,len(candidates),16):
            batch=candidates[start:start+16]
            originals,variants,original_masks,variant_masks,details=[],[],[],[],[]
            for choice in batch:
                stem,i=choice['dataset'],choice['row']
                code=datasets[stem][i]['processed_func']
                profile=profiles[stem][i]
                if model_name=='linevul':
                    body=tokenizer.convert_tokens_to_ids(tokenizer.tokenize(code))
                    full=[0]+body+[2]
                    original=pack(full,limit)
                    exact=line.convert_examples_to_features(code,choice['label'],tokenizer,
                        SimpleNamespace(use_word_level_tokenizer=False,block_size=512)).input_ids
                    assert exact==original
                else:
                    cleaned=helpers.clean_for_vulberta(code)
                    full=auditor.vb.encode(cleaned).ids
                    original=pack(full,limit)
                    exact=tokenizer(cleaned,padding='max_length',truncation=True,max_length=limit,return_token_type_ids=False)
                    assert exact['input_ids']==original
                if choice['condition'].startswith('tail_'):
                    variant=pack(full,limit,tail=True)
                    extra=dict(source_tokens=len(full),variant_tokens=min(len(full),limit),lexical_preservation=None)
                else:
                    tree=parser_map[profile['parser_language']].parse(code.encode('utf-8'))
                    alternative=audit.preserve_lexical_code(code,tree)
                    preserved=audit.lexical_clang(clang_index,code)==audit.lexical_clang(clang_index,alternative)
                    assert preserved
                    alternate_ids=auditor.vb.encode(alternative).ids
                    variant=pack(alternate_ids,limit)
                    extra=dict(source_tokens=len(full),variant_tokens=len(alternate_ids),lexical_preservation=preserved)
                if choice['condition']=='tail_untruncated_control':
                    assert original==variant
                originals.append(original)
                variants.append(variant)
                original_masks.append([1]*min(len(full),limit)+[0]*max(0,limit-len(full)))
                variant_length=min(len(full) if choice['condition'].startswith('tail_') else len(alternate_ids),limit)
                variant_masks.append([1]*variant_length+[0]*(limit-variant_length))
                if model_name=='vulberta':
                    assert exact['attention_mask']==original_masks[-1]
                details.append(dict(**extra,input_changed=original!=variant,
                                    baseline_input_sha256=common.code_sha(json.dumps(original)),
                                    variant_input_sha256=common.code_sha(json.dumps(variant))))
            def score(ids,masks):
                inputs=torch.tensor(ids,device=device)
                with torch.inference_mode():
                    p=(model(input_ids=inputs) if model_name=='linevul' else
                       model(input_ids=inputs,attention_mask=torch.tensor(masks,device=device)).logits.softmax(dim=-1))
                assert torch.isfinite(p).all()
                return p[:,1].cpu().tolist()
            before,after=score(originals,original_masks),score(variants,variant_masks)
            for choice,p0,p1,detail in zip(batch,before,after,details):
                result=dict(**choice,**detail,baseline_probability=p0,variant_probability=p1,
                            baseline_prediction=int(p0>.5),variant_prediction=int(p1>.5),
                            baseline_correct=int(p0>.5)==choice['label'],variant_correct=int(p1>.5)==choice['label'])
                result['baseline_matches_history']=result['baseline_prediction']==choice['historical_prediction']
                results.append(result)
            common.write_csv(directory/'predictions.csv',results)
            if start%128==0:
                print(model_name,start+len(batch),'/',len(candidates),'ablations',flush=True)
        del model,tokenizer
        import gc
        gc.collect()
        if device=='cuda':
            torch.cuda.empty_cache()
    for model in ('linevul','vulberta'):
        for stem in audit.STEMS:
            for condition in sorted({r['condition'] for r in results}):
                group=[r for r in results if r['model']==model and r['dataset']==stem and r['condition']==condition]
                if not group:
                    continue
                summaries.append(dict(model=model,dataset=stem,condition=condition,rows=len(group),
                    positives=sum(r['label'] for r in group),input_changed=sum(r['input_changed'] for r in group),
                    recovered_errors=sum(not r['baseline_correct'] and r['variant_correct'] for r in group),
                    introduced_errors=sum(r['baseline_correct'] and not r['variant_correct'] for r in group),
                    unchanged_errors=sum(not r['baseline_correct'] and not r['variant_correct'] for r in group),
                    baseline=common.manual_metrics([r['label'] for r in group],[r['baseline_prediction'] for r in group]),
                    variant=common.manual_metrics([r['label'] for r in group],[r['variant_prediction'] for r in group])))
    historical_changes=sum(not r['baseline_matches_history'] for r in results)
    summary=dict(status='pass' if historical_changes==0 else 'review_required',device=device,threshold=0.5,
                 selection_seed=42,script_sha256=common.sha(Path(__file__)),historical_prediction_changes=historical_changes,
                 selection_policy='All confirmed, lexical-preserving cleaner changes visible in retained input; seed-42 stratified tail and unchanged controls.',
                 conditions=summaries)
    common.write_json(directory/'summary.json',summary)
    print('Ablations complete; historical prediction changes:',historical_changes,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    run(args.output.resolve())
