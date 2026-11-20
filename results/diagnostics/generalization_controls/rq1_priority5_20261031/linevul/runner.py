"""Frozen-checkpoint original-domain controls, with source and prediction parity guards."""
from __future__ import annotations
import argparse
from collections import Counter
import csv
from importlib.metadata import version
import json
import os
from pathlib import Path
import random
import shutil
import sys
from types import SimpleNamespace

import rq1_priority1_audit as c
from rq1_priority5_sources import RUN, digest

P2 = c.HERE / 'results/rq1_priority2_20261028'
P4 = c.HERE / 'results/rq1_priority4_20261029'
PLAN = dict(date='2026-10-31', seed=20261031, bootstrap_repetitions=2000,
    threshold='class-1 probability > 0.5; frozen weights and preprocessing',
    controls=['LineVul full official BigVul test', 'VulBERTa CodeXGLUE Devign test indices'],
    overlap='Compare evaluation to documented train and validation splits, separately: exact text, comment/whitespace-insensitive token identity, identifier-normalized structural candidates. These are bounded near-duplicate screens, not proof of absence of semantic clones.',
    matched='Common-support cells of source language x source-line bins (1-10,11-25,26-50,51-100,101+) x binary label. Cell mass is minimum count across datasets; row weight = cell mass / dataset cell count. Compare full and model-specific intact cohorts; do not pool incompatible label evidence or invent missing CWE/context.',
    inference='Batch 16; seed 42; eval/inference mode; LineVul 512 / VulBERTa 1024 tokens; safetensors for VulBERTa; verify historical parity before control inference.',
    uncertainty='2000 connected-component cluster bootstrap draws; code/token duplicates, source commits, CVEs and supplied task families stay together. Project sensitivity; same row weights for paired model differences. Matching weights fixed from observed cohorts; intervals conditional on matching.',
    limitations=['Priority 4 independent adjudication pending', 'Pretraining exposure not exhaustively available', 'Published training procedure is not an attestation of the converted checkpoint history', 'Authorship is not randomized; no causal authorship conclusion'])


def jsonl(path):
    with Path(path).open(encoding='utf-8') as f:
        for line in f:
            yield json.loads(line)


def initialize():
    RUN.mkdir(parents=True, exist_ok=True)
    path = RUN / 'analysis_plan.json'
    if path.exists():
        assert c.read_json(path) == PLAN
        return
    c.write_json(path, PLAN)
    baseline = c.read_json(c.HERE / 'reports/rq1_priority1_summary.json')
    paths = {c.ROOT / x['path'] for x in baseline['assets']}
    for j in baseline['jobs']:
        paths.update([c.ROOT/j['dataset'], c.ROOT/j['prediction_file']['path']])
    paths.update([c.CACHE/'data/bigvul_test.csv', P2/'joined_inputs.csv', P4/'row_structure.jsonl',
                  c.HERE/'reports/rq1_results.md'])
    c.write_json(RUN/'preserved_inputs.json', [dict(path=p.relative_to(c.ROOT).as_posix(), sha256=digest(p)) for p in sorted(paths)])
    print('Analysis plan and immutable-input hashes saved.', flush=True)


def prepare():
    initialize()
    destination = RUN/'inputs'; destination.mkdir(exist_ok=True)
    if (destination/'manifest.json').exists():
        for x in c.read_json(destination/'manifest.json')['datasets']:
            assert digest(destination/x['file']) == x['sha256']
        return
    manifest = dict(datasets=[], sources=[])
    csv.field_size_limit(100000000)
    big = c.CACHE/'data/bigvul_test.csv'
    expected = c.read_json(c.CACHE/'data/bigvul_test_sample_2000.selection.json')['source_sha256']
    assert digest(big) == expected
    manifest['sources'].append(dict(path=big.relative_to(c.ROOT).as_posix(), sha256=expected))
    counts = Counter()
    path = destination/'bigvul_test.jsonl'
    with big.open(encoding='utf-8', newline='') as f, path.open('w', encoding='utf-8') as out:
        for i, r in enumerate(csv.DictReader(f)):
            row = dict(sample_id='bigvul-source:'+str(i), row=i, dataset='bigvul_test', label=int(r['target']), code=r['processed_func'],
                source_language=r['lang'].lower(), project=r['project'], commit_url=r['codeLink'], commit_id=r['commit_id'],
                cwe=r['CWE ID'], cve=r['CVE ID'], file_name=r['file_name'], original_index=r['index'], group_id='',
                code_sha256=c.code_sha(r['processed_func']), source_lines=len(r['processed_func'].splitlines()),
                label_evidence='vulnerability-commit changed-line association', context_scope='unreviewed')
            out.write(json.dumps(row, ensure_ascii=False)+'\n'); counts[row['label']] += 1
    manifest['datasets'].append(dict(file=path.name, rows=sum(counts.values()), labels=dict(counts), sha256=digest(path)))
    data_path = RUN/'sources/Devign.json'
    assert digest(data_path) == c.read_json(RUN/'sources/devign.manifest.json')['sha256']
    source = c.read_json(data_path)
    splitsets = {s:set(map(int, (RUN/'sources'/('codexglue_'+s+'.txt')).read_text().split())) for s in ['train','valid','test']}
    assert [len(splitsets[s]) for s in ['train','valid','test']] == [21854,2732,2732]
    assert not any(splitsets[a] & splitsets[b] for a,b in [('train','valid'),('train','test'),('valid','test')])
    assert set.union(*splitsets.values()) == set(range(len(source)))
    for split, indices in splitsets.items():
        counts = Counter(); path = destination/('devign_'+split+'.jsonl')
        with path.open('w', encoding='utf-8') as out:
            for row_index, i in enumerate(sorted(indices)):
                r = source[i]
                row = dict(sample_id='devign:'+str(i), row=row_index, dataset='devign_'+split, label=int(r['target']), code=r['func'],
                    source_language='c', project=r['project'], commit_url=r['project'].lower()+':'+r['commit_id'], commit_id=r['commit_id'],
                    cwe='', cve='', file_name='', original_index=i, group_id='', code_sha256=c.code_sha(r['func']),
                    source_lines=len(r['func'].splitlines()), label_evidence='Devign original annotation; row-level rationale unavailable', context_scope='unreviewed')
                out.write(json.dumps(row, ensure_ascii=False)+'\n'); counts[row['label']] += 1
        manifest['datasets'].append(dict(file=path.name, rows=sum(counts.values()), labels=dict(counts), sha256=digest(path)))
    manifest.update(split_indices_disjoint=True, devign_source_sha256=digest(data_path))
    c.write_json(destination/'manifest.json', manifest)
    print(json.dumps(manifest), flush=True)


def infer(model_name):
    prepare()
    os.environ.update(HF_HOME=str(c.CACHE/'huggingface'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', USE_TF='0', TOKENIZERS_PARALLELISM='false')
    import torch
    from transformers import (AutoTokenizer, AutoModelForSequenceClassification, RobertaTokenizer,
                              RobertaConfig, RobertaForSequenceClassification, set_seed)
    set_seed(42); torch.backends.cudnn.benchmark=False; torch.backends.cudnn.deterministic=True
    device='cuda' if torch.cuda.is_available() else 'cpu'
    directory = RUN/model_name; directory.mkdir(exist_ok=True)
    checkpoint = c.LV/'saved_models/checkpoint-best-f1/12heads_linevul_model.bin' if model_name=='linevul' else c.VB/'model.safetensors'
    baseline = c.read_json(c.HERE/'reports/rq1_priority1_summary.json')
    for x in c.read_json(RUN/'preserved_inputs.json'):
        assert digest(c.ROOT/x['path']) == x['sha256'], x['path']
    signature = dict(script=digest(__file__), checkpoint=digest(checkpoint), input_manifest=digest(RUN/'inputs/manifest.json'),
        model=model_name, seed=42, batch_size=16, device=device, versions={p:version(p) for p in ['torch','transformers','tokenizers','libclang']})
    signature_path = directory/'signature.json'
    if signature_path.exists():
        assert c.read_json(signature_path) == signature, 'Inputs or implementation changed; use a new run.'
    else:
        c.write_json(signature_path, signature); shutil.copyfile(__file__, directory/'runner.py')
    if (directory/'manifest.json').exists():
        m = c.read_json(directory/'manifest.json')
        assert m['status']=='pass' and digest(directory/'predictions.jsonl')==m['predictions_sha256']
        print('Already complete:', model_name); return
    if model_name=='linevul':
        sys.path.insert(0, str(c.LV))
        line = c.load_module(c.LV/'linevul_main_local.py', 'p5_linevul')
        tokenizer = RobertaTokenizer.from_pretrained(str(c.CB), local_files_only=True)
        config = RobertaConfig.from_pretrained(str(c.CB), local_files_only=True)
        config.num_labels, config.num_attention_heads = 1, 12
        args = SimpleNamespace(use_word_level_tokenizer=False, block_size=512)
        model = line.Model(RobertaForSequenceClassification(config), config, tokenizer, args)
        line._load_local_checkpoint(model, torch.load(checkpoint, map_location='cpu', weights_only=True))
        def predict(batch):
            full = [[0]+tokenizer.convert_tokens_to_ids(tokenizer.tokenize(r['code']))+[2] for r in batch]
            ids = [v[:511]+[2] if len(v)>512 else v+[1]*(512-len(v)) for v in full]
            with torch.inference_mode():
                probs = model(input_ids=torch.tensor(ids, device=device))
            return probs, [dict(tokens=len(v), truncated=len(v)>512, input_sha256=c.code_sha(json.dumps(x))) for v,x in zip(full,ids)]
        dataset = 'bigvul_test'
    else:
        import vulberta_eval as helper
        tokenizer = AutoTokenizer.from_pretrained('claudios/VulBERTa-MLP-Devign', revision=c.VB_REV, trust_remote_code=True, local_files_only=True)
        helper.fix_clang_parser(tokenizer)
        model, loading = AutoModelForSequenceClassification.from_pretrained(str(c.VB), local_files_only=True, use_safetensors=True, output_loading_info=True)
        assert not any(loading.get(k) for k in ('missing_keys','unexpected_keys','mismatched_keys','error_msgs'))
        def predict(batch):
            clean = [helper.clean_for_vulberta(r['code']) for r in batch]
            encoded = tokenizer(clean, padding='max_length', truncation=True, max_length=1024, return_tensors='pt', return_token_type_ids=False)
            full = tokenizer(clean, padding=False, truncation=False, return_token_type_ids=False)['input_ids']
            with torch.inference_mode():
                probs = model(**{k:v.to(device) for k,v in encoded.items()}).logits.softmax(-1)
            details = [dict(tokens=len(v), truncated=len(v)>1024, cleaned_code_sha256=c.code_sha(txt),
                            input_sha256=c.code_sha(json.dumps(x))) for v,txt,x in zip(full,clean,encoded['input_ids'].tolist())]
            return probs, details
        dataset = 'devign_test'
    model.to(device).eval()
    # Exact existing examples are checked before the previously unevaluated control.
    if model_name=='linevul':
        historical = c.read_csv(P2/'linevul/bigvul_test_sample_2000.csv')
        sample_codes = c.read_csv(c.CACHE/'data/bigvul_test_sample_2000.csv')
        parity = [dict(code=r['processed_func'], label=int(r['target']), sample_id=h['sample_id'], expected=float(h['prob_vulnerable'])) for r,h in zip(sample_codes,historical)]
    else:
        import rq1_priority2_audit as p2
        _, _, datasets = p2.load_data()
        joined = c.read_csv(P2/'joined_inputs.csv'); rng = random.Random(20261031)
        parity=[]
        for stem in ['primevul_test','llmvul_test']:
            candidates=[r for r in joined if r['model']=='vulberta' and r['dataset']==stem]
            for r in rng.sample(candidates,32):
                parity.append(dict(code=datasets[stem][int(r['row'])]['processed_func'], label=int(r['label']), sample_id=r['sample_id'], expected=float(r['prob_vulnerable'])))
    parity_output=[]
    for start in range(0,len(parity),16):
        batch=parity[start:start+16]; probs,_=predict(batch)
        for r,p in zip(batch,probs[:,1].cpu().tolist()):
            parity_output.append(dict(sample_id=r['sample_id'], expected=r['expected'], probability=p,
                                      delta=abs(p-r['expected']), same_prediction=(p>.5)==(r['expected']>.5)))
    c.write_json(directory/'parity.json', parity_output)
    assert max(r['delta'] for r in parity_output)<=1e-5 and all(r['same_prediction'] for r in parity_output)
    print(model_name,'historical parity passed:',len(parity_output),'rows',flush=True)
    rows=list(jsonl(RUN/'inputs'/(dataset+'.jsonl')))
    output=directory/'predictions.jsonl'
    old=list(jsonl(output)) if output.exists() else []
    for i,r in enumerate(old):
        assert r['sample_id']==rows[i]['sample_id'] and r['label']==rows[i]['label']
    with output.open('a', encoding='utf-8') as f:
        for start in range(len(old),len(rows),16):
            batch=rows[start:start+16]; probs,details=predict(batch)
            assert torch.isfinite(probs).all() and (probs>=0).all() and (probs<=1).all()
            assert float((probs.sum(-1)-1).abs().max())<=1e-6
            for r,p,detail in zip(batch,probs[:,1].cpu().tolist(),details):
                record=dict(sample_id=r['sample_id'], row=r['row'], label=r['label'], probability=p, prediction=int(p>.5), **detail)
                f.write(json.dumps(record)+'\n')
            f.flush()
            if start%512==0: print(model_name, min(start+16,len(rows)), '/',len(rows),flush=True)
    results=list(jsonl(output))
    assert len(results)==len(rows)
    summary=dict(status='pass', dataset=dataset, rows=len(rows), signature=signature, predictions_sha256=digest(output),
                 parity_rows=len(parity_output), max_parity_delta=max(r['delta'] for r in parity_output),
                 measured=c.manual_metrics([r['label'] for r in results],[r['prediction'] for r in results]))
    if model_name=='linevul':
        scores={r['sample_id']:r['probability'] for r in results}
        summary['embedded_sample_prediction_changes']=sum((scores[r['sample_id']]>.5)!=(r['expected']>.5) for r in parity)
        summary['embedded_sample_max_score_delta']=max(abs(scores[r['sample_id']]-r['expected']) for r in parity)
        assert summary['embedded_sample_prediction_changes']==0 and summary['embedded_sample_max_score_delta']<=1e-5
    c.write_json(directory/'manifest.json', summary)
    print(json.dumps(summary),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['prepare','linevul','vulberta'])
    stage=parser.parse_args().stage
    prepare() if stage=='prepare' else infer(stage)
