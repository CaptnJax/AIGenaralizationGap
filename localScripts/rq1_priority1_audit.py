"""Reproduce RQ1 priority-one checks without modifying historical evaluations.

Run artifacts first into a new output directory, then inference against that
manifest. Inference is offline, frozen, and limited to a prespecified cohort
plus the original 16-row batches containing those examples.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CACHE = HERE / '.cache'
LV = CACHE / 'LineVul' / 'linevul'
VB_REV = 'fecabdee24a3ef6e804d7629d6eed03dc6b4f61e'
CB_REV = '3b0952feddeffad0063f274080e3c23d75e7eb39'
HUB = CACHE / 'huggingface' / 'hub'
VB = HUB / 'models--claudios--VulBERTa-MLP-Devign' / 'snapshots' / VB_REV
CB = HUB / 'models--microsoft--codebert-base' / 'snapshots' / CB_REV
SELECTED = [
    ('20261009_203652_921773', 'linevul', 'bigvul_test_sample_2000'),
    ('20261009_203942_809681', 'linevul', 'primevul_test'),
    ('20261009_203942_809681', 'linevul', 'llmvul_test'),
    ('20261009_211327_299195', 'vulberta', 'primevul_test'),
    ('20261009_211327_299195', 'vulberta', 'llmvul_test'),
    ('20261015_230324_309261', 'linevul', 'cweval_test'),
    ('20261015_230324_309261', 'vulberta', 'cweval_test'),
]
csv.field_size_limit(50_000_000)


@lru_cache(None)
def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def code_sha(code):
    return hashlib.sha256(code.encode('utf-8')).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False), encoding='utf-8')


def read_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    with Path(path).open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def binary(value):
    return {'0': 0, '1': 1, 'False': 0, 'True': 1}[str(value)]


def manual_metrics(labels, predictions):
    if len(labels) != len(predictions) or not labels:
        raise ValueError('Labels/predictions must be nonempty and aligned.')
    if any(x not in (0, 1) for x in [*labels, *predictions]):
        raise ValueError('Expected binary labels and predictions.')
    counts = Counter(zip(labels, predictions))
    tn, fp, fn, tp = (counts[pair] for pair in ((0, 0), (0, 1), (1, 0), (1, 1)))
    return {
        'confusion_matrix': dict(tn=tn, fp=fp, fn=fn, tp=tp),
        'test_accuracy': (tp + tn) / len(labels),
        'test_precision': tp / (tp + fp) if tp + fp else 0.0,
        'test_recall': tp / (tp + fn) if tp + fn else 0.0,
        'test_f1': 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0,
        'precision_defined': bool(tp + fp),
    }


class Checks:
    def __init__(self):
        self.rows = []

    def check(self, name, condition, detail=None):
        self.rows.append(dict(check=name, status='pass' if condition else 'fail', detail=detail))
        if not condition:
            print('FAIL:', name, detail, flush=True)
        return condition

    @property
    def failed(self):
        return [x for x in self.rows if x['status'] == 'fail']


def freeze(path, output):
    path = Path(path)
    digest = sha(path)
    target = output / 'evidence' / (digest[:12] + '_' + path.name)
    if not target.exists():
        shutil.copyfile(path, target)
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=digest,
                snapshot=target.relative_to(output).as_posix())


def historical_source(path, wanted, output):
    """Find exact historical bytes, allowing Git LF/Windows CRLF storage."""
    path = Path(path)
    if sha(path) == wanted:
        return dict(status='exact_current_match', **freeze(path, output))
    relative = path.relative_to(ROOT).as_posix()
    commits = subprocess.check_output(
        ['git', 'log', '--format=%H', '--', relative], cwd=ROOT, text=True).splitlines()
    for commit in commits:
        blob = subprocess.check_output(['git', 'show', f'{commit}:{relative}'], cwd=ROOT)
        lf = blob.replace(b'\r\n', b'\n')
        for kind, data in [('git_blob', blob), ('lf', lf), ('crlf', lf.replace(b'\n', b'\r\n'))]:
            if hashlib.sha256(data).hexdigest() == wanted:
                target = output / 'evidence' / (wanted[:12] + '_' + path.name)
                target.write_bytes(data)
                return dict(status='recovered_from_git', commit=commit, newline_form=kind,
                            sha256=wanted, snapshot=target.relative_to(output).as_posix())
    return dict(status='unavailable', recorded_sha256=wanted, current_sha256=sha(path),
                note='No matching historical bytes found in current file or Git history.')


def source_rows(checks):
    result = {}
    manifest = read_json(ROOT / 'prepared_datasets/manifest.json')
    for name, expected in manifest['source_sha256'].items():
        checks.check('source_hash:' + name, sha(ROOT / name) == expected)
    with (ROOT / 'primevul_test.jsonl').open(encoding='utf-8') as handle:
        result['primevul_test'] = [dict(sample_id='primevul:' + str(r['idx']),
                                       code=r['func'], label=r['target'])
                                  for r in map(json.loads, handle)]
    with (ROOT / 'LLMVul_v3-Updated.csv').open(encoding='utf-8-sig', newline='') as handle:
        checks.check('llmvul_title', next(csv.reader(handle)) == ['LLMVul_v3-Updated'])
        labeled, uncertain, mapping_errors = [], 0, 0
        for r in csv.DictReader(handle):
            if r['ensemble_label'] == 'uncertain':
                uncertain += 1
                mapping_errors += r['vuln_label'] != ''
                continue
            label = {'safe': 0, 'vulnerable': 1}[r['ensemble_label']]
            mapping_errors += float(r['vuln_label']) != label
            labeled.append(dict(sample_id='llmvul:' + r['unique_id'], code=r['function_body'], label=label))
        checks.check('llmvul_label_mapping', mapping_errors == 0, dict(errors=mapping_errors, uncertain=uncertain))
        checks.check('llmvul_excluded_count', uncertain == 2679)
        result['llmvul_test'] = labeled
    with (ROOT / 'prepared_datasets/cweval/catalog.jsonl').open(encoding='utf-8') as handle:
        selected = [r for r in map(json.loads, handle) if r['eligible']]
    checks.check('cweval_reference_unsafe_mapping', all(
        r['label'] == {'upstream_reference': 0, 'upstream_unsafe': 1}[r['label_basis']] for r in selected))
    result['cweval_test'] = [dict(sample_id=r['sample_id'], code=r['code'], label=r['label']) for r in selected]
    selection = read_json(CACHE / 'data/bigvul_test_sample_2000.selection.json')
    big_path = CACHE / 'data/bigvul_test.csv'
    checks.check('bigvul_source_hash', sha(big_path) == selection['source_sha256'])
    indices = selection['source_row_indices_zero_based']
    checks.check('bigvul_selection_indices', len(indices) == len(set(indices)) == 2000 and indices == sorted(indices))
    big = read_csv(big_path)
    result['bigvul_test_sample_2000'] = [dict(sample_id='bigvul-source:' + str(i),
        code=big[i]['processed_func'], label=int(big[i]['target'])) for i in indices]
    return result


def artifacts(output):
    from importlib.metadata import version
    from sklearn.metrics import f1_score, precision_score, recall_score, accuracy_score
    import numpy as np

    output.mkdir(parents=True, exist_ok=False)
    (output / 'evidence').mkdir()
    checks = Checks()
    source = source_rows(checks)
    packages = {p: version(p) for p in ('torch', 'transformers', 'tokenizers', 'libclang', 'pandas', 'scikit-learn')}
    fixtures = [
        ('perfect', [0, 0, 1, 1], [0, 0, 1, 1], dict(tn=2, fp=0, fn=0, tp=2), 1.0),
        ('reversed', [0, 0, 1, 1], [1, 1, 0, 0], dict(tn=0, fp=2, fn=2, tp=0), 0.0),
        ('all_negative', [0, 0, 1, 1], [0, 0, 0, 0], dict(tn=2, fp=0, fn=2, tp=0), 0.0),
        ('mixed', [0, 0, 1, 1], [0, 1, 1, 1], dict(tn=1, fp=1, fn=0, tp=2), 0.8),
    ]
    for name, y, p, cm, f1 in fixtures:
        measured = manual_metrics(y, p)
        checks.check('fixture:' + name, measured['confusion_matrix'] == cm and measured['test_f1'] == f1
                     and f1_score(y, p, zero_division=0) == f1, measured)
    threshold_inputs = [np.nextafter(0.5, 0.0), 0.5, np.nextafter(0.5, 1.0)]
    checks.check('strict_threshold_fixture', [int(x > 0.5) for x in threshold_inputs] == [0, 0, 1])
    jobs, cohort = [], []
    for run, model, stem in SELECTED:
        job_id = model + '/' + stem
        print('Audit', run, job_id, flush=True)
        run_path = HERE / 'results' / run
        job_path = run_path / model / stem
        job = read_json(job_path / 'job.json')
        sig = job['signature']
        dataset = (CACHE / 'data' if stem.startswith('bigvul') else ROOT / 'prepared_datasets' / model) / (stem + '.csv')
        checks.check(job_id + ':complete', job['status'] == 'complete')
        checks.check(job_id + ':dataset_hash', sha(dataset) == sig['dataset_sha256'])
        checks.check(job_id + ':protocol', sig['threshold'] == 0.5 and sig['batch_size'] == 16 and sig['seed'] == 42)
        checks.check(job_id + ':packages_unchanged', packages == sig['packages'])
        rows = read_csv(dataset)
        code_col, label_col = ('processed_func', 'target') if model == 'linevul' else ('func', 'label')
        canonical = [dict(sample_id=r.get('sample_id', source[stem][i]['sample_id']),
                          code=r[code_col], label=int(r[label_col])) for i, r in enumerate(rows)]
        checks.check(job_id + ':source_exact', canonical == source[stem])
        ids = [r['sample_id'] for r in canonical]
        checks.check(job_id + ':unique_ids_valid_labels_code', len(ids) == len(set(ids)) and all(
            r['label'] in (0, 1) and r['code'].strip() for r in canonical))
        if not stem.startswith('bigvul') and stem != 'cweval_test':
            with (ROOT / 'prepared_datasets/audit' / (stem + '_provenance.jsonl')).open(encoding='utf-8') as handle:
                provenance = list(map(json.loads, handle))
            checks.check(job_id + ':provenance_hash_label_id', len(provenance) == len(canonical) and all(
                (a['sample_id'], a['target'], a['code_sha256']) == (b['sample_id'], b['label'], code_sha(b['code']))
                for a, b in zip(provenance, canonical)))
        prediction_path = job_path / ('results/raw_preds.csv' if model == 'linevul' else 'predictions.csv')
        raw = read_csv(prediction_path)
        checks.check(job_id + ':prediction_count', len(raw) == len(canonical))
        if len(raw) != len(canonical):
            raise ValueError('Cannot safely align predictions: ' + job_id)
        if model == 'linevul':
            checks.check(job_id + ':prediction_row_alignment', all(
                r['processed_func'] == c['code'] and int(r['target']) == c['label']
                and (r.get('sample_id', c['sample_id']) == c['sample_id']) for r, c in zip(raw, canonical)))
            predictions = [binary(r['raw_preds']) for r in raw]
            probabilities, score_audit = None, {'availability': 'not_saved_in_historical_export'}
        else:
            checks.check(job_id + ':prediction_id_label_alignment', [(r['sample_id'], int(r['label'])) for r in raw]
                         == [(c['sample_id'], c['label']) for c in canonical])
            predictions = [binary(r['prediction']) for r in raw]
            probabilities = [float(r['prob_vulnerable']) for r in raw]
            checks.check(job_id + ':finite_in_range', all(math.isfinite(x) and 0 <= x <= 1 for x in probabilities))
            checks.check(job_id + ':threshold_exact', predictions == [int(x > 0.5) for x in probabilities])
            progress = read_json(job_path / 'progress.json')
            checks.check(job_id + ':progress_alignment', progress['signature']['dataset_sha256'] == sha(dataset)
                         and len(progress['scores']) == len(probabilities)
                         and np.allclose(progress['scores'], probabilities, atol=1e-15, rtol=0))
            score_audit = dict(min=min(probabilities), max=max(probabilities), unique=len(set(probabilities)),
                               exact_zero=probabilities.count(0.0), exact_one=probabilities.count(1.0),
                               exact_threshold=probabilities.count(0.5),
                               quantiles=np.quantile(probabilities, [0, .01, .25, .5, .75, .99, 1]).tolist())
            checks.check(job_id + ':corrected_preprocessing', sig['preprocessing'] == 'original_vulberta_cleaner_v1')
        labels = [c['label'] for c in canonical]
        measured = manual_metrics(labels, predictions)
        saved = read_json(job_path / 'metrics.json')
        checks.check(job_id + ':confusion_matrix', measured['confusion_matrix'] == saved['confusion_matrix'])
        for key, fn in [('test_accuracy', accuracy_score), ('test_precision', precision_score),
                        ('test_recall', recall_score), ('test_f1', f1_score)]:
            library = float(fn(labels, predictions, **({} if key == 'test_accuracy' else {'zero_division': 0})))
            checks.check(job_id + ':' + key, abs(measured[key] - saved[key]) < 1e-12 and abs(measured[key] - library) < 1e-12)
        summaries = read_csv(run_path / 'summary.csv')
        summary = next(r for r in summaries if r['job'] == sig['job'])
        checks.check(job_id + ':summary_metrics', all(abs(float(summary[k]) - measured[k]) < 1e-12
                     for k in ('test_accuracy', 'test_precision', 'test_recall', 'test_f1')))
        impl = LV / 'linevul_main_local.py' if model == 'linevul' else HERE / 'vulberta_eval.py'
        implementation = historical_source(impl, sig['implementation_sha256'], output)
        checks.check(job_id + ':exact_inference_source_available', implementation['status'] != 'unavailable')
        runner = historical_source(HERE / 'pivd_local.py', sig['runner_sha256'], output)
        log = (job_path / 'test.log').read_text(encoding='utf-8')
        checks.check(job_id + ':trained_load_logged', ('LineVul trained checkpoint loaded successfully.' if model == 'linevul'
                     else 'Trained classifier loaded successfully.') in log)
        if model == 'linevul':
            checks.check(job_id + ':checkpoint_hash', sha(LV / 'saved_models/checkpoint-best-f1/12heads_linevul_model.bin')
                         == sig['checkpoint_sha256'])
        if stem == 'cweval_test':
            checks.check(job_id + ':cweval_manifest_hash', sha(ROOT / 'prepared_datasets/cweval/manifest.json')
                         == sig['cweval_manifest_sha256'])
        strata = Counter(('t' if y == p else 'f') + ('p' if p else 'n') for y, p in zip(labels, predictions))
        if stem == 'cweval_test':
            chosen = list(range(len(rows)))
        else:
            rng, chosen = random.Random(42), []
            for y, p in ((0, 0), (0, 1), (1, 0), (1, 1)):
                candidates = [i for i in range(len(rows)) if labels[i] == y and predictions[i] == p]
                chosen.extend(rng.sample(candidates, min(4, len(candidates))))
            chosen.sort()
        for i in chosen:
            c = canonical[i]
            cohort.append(dict(job=job_id, run=run, row=i, sample_id=c['sample_id'], label=c['label'],
                               code_sha256=code_sha(c['code']), historical_prediction=predictions[i],
                               historical_probability=probabilities[i] if probabilities is not None else None))
        jobs.append(dict(job=job_id, run=run, model=model, dataset=dataset.relative_to(ROOT).as_posix(),
                         signature=sig, rows=len(rows), measured=measured,
                         macro_f1=float(f1_score(labels, predictions, average='macro', zero_division=0)),
                         weighted_f1=float(f1_score(labels, predictions, average='weighted', zero_division=0)),
                         inverted_predictions_f1=manual_metrics(labels, [1-p for p in predictions])['test_f1'],
                         probabilities=score_audit, strata=dict(strata), cohort_rows=chosen,
                         implementation=implementation, historical_runner=runner,
                         artifacts=[freeze(p, output) for p in (job_path/'job.json', job_path/'metrics.json',
                                    run_path/'summary.csv', run_path/'environment.json')],
                         prediction_file=dict(path=prediction_path.relative_to(ROOT).as_posix(), sha256=sha(prediction_path)),
                         dataset_sha256=sha(dataset), test_log_sha256=sha(job_path/'test.log')))
    tokens = []
    for model, snapshot in [('linevul', CB), ('vulberta', VB)]:
        for path in sorted(snapshot.iterdir()):
            if path.is_file():
                item = dict(model=model, path=path.relative_to(ROOT).as_posix(), sha256=sha(path), bytes=path.stat().st_size)
                if path.suffix in ('.json', '.py', '.txt'):
                    item.update(freeze(path, output))
                tokens.append(item)
    cwe_audit = read_json(ROOT/'prepared_datasets/cweval/manifest.json')['tokenizer_audit']
    for relative, expected in cwe_audit['assets_sha256'].items():
        checks.check('cweval_tokenizer_asset:' + relative, sha(HUB / relative) == expected)
    snapshots = [freeze(p, output) for p in (Path(__file__), HERE/'vulberta_eval.py', LV/'linevul_model.py',
                 LV/'linevul_main_local.py', ROOT/'prepare_evaluation_datasets.py', ROOT/'prepare_cweval_datasets.py',
                 ROOT/'prepared_datasets/manifest.json', ROOT/'prepared_datasets/cweval/manifest.json',
                 CACHE/'data/bigvul_test_sample_2000.selection.json', HERE/'reports/rq1_results.md')]
    manifest = dict(created_utc=datetime.now(timezone.utc).isoformat(), scope='RQ1 priority 1',
                    status='fail' if checks.failed else 'pass', python=sys.version, packages=packages,
                    cohort_policy='seed 42; up to 4 per confusion-matrix cell; every selected CWEval row',
                    jobs=jobs, checks=checks.rows, assets=tokens, snapshots=snapshots,
                    limitations=['Historical LineVul scores were not exported.',
                                 'Earlier LineVul jobs did not record tokenizer revision or tokenizer hashes.',
                                 'VulBERTa recorded checkpoint revision, not a historical weights SHA-256.',
                                 'Source-label agreement does not establish source-label correctness.'])
    write_json(output/'artifact_audit.json', manifest)
    write_json(output/'cohort.json', cohort)
    write_csv(output/'checks.csv', [dict(check=r['check'], status=r['status'], detail=json.dumps(r['detail'])) for r in checks.rows])
    print(json.dumps(dict(output=str(output), checks=len(checks.rows), failures=len(checks.failed), cohort=len(cohort))), flush=True)
    return not checks.failed


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inference(output):
    # Restrict all model loading to the already available local cache.
    os.environ.update(HF_HOME=str(CACHE/'huggingface'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                      USE_TF='0', TOKENIZERS_PARALLELISM='false')
    import gc
    import numpy as np
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, RobertaConfig, RobertaForSequenceClassification, RobertaTokenizer, set_seed

    manifest = read_json(output/'artifact_audit.json')
    if manifest['status'] != 'pass':
        raise ValueError('Resolve artifact failures before running inference.')
    if (output/'inference_audit.json').exists():
        raise FileExistsError('Inference audit already exists; use a new diagnostic run.')
    for job in manifest['jobs']:
        if sha(ROOT/job['dataset']) != job['dataset_sha256']:
            raise ValueError('Dataset changed since artifact audit.')
    for item in manifest['assets']:
        if sha(ROOT/item['path']) != item['sha256']:
            raise ValueError('Model/tokenizer asset changed since artifact audit.')
    set_seed(42)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    checks, summaries, records = Checks(), [], []
    cohort = read_json(output/'cohort.json')
    helpers = load_module(HERE/'vulberta_eval.py', 'audit_vulberta')
    sys.path.insert(0, str(LV))
    line = load_module(LV/'linevul_main_local.py', 'audit_linevul')
    for model_name in ('linevul', 'vulberta'):
        print('Loading', model_name, 'on', device, flush=True)
        if model_name == 'linevul':
            tokenizer = RobertaTokenizer.from_pretrained(str(CB), local_files_only=True)
            config = RobertaConfig.from_pretrained(str(CB), local_files_only=True)
            config.num_labels, config.num_attention_heads = 1, 12
            # Every parameter is subsequently replaced by the strictly loaded trained state.
            model = line.Model(RobertaForSequenceClassification(config), config, tokenizer, SimpleNamespace())
            weight_path = LV/'saved_models/checkpoint-best-f1/12heads_linevul_model.bin'
            state = torch.load(weight_path, map_location='cpu', weights_only=True)
            loaded = line._load_local_checkpoint(model, state)
            checks.check('linevul:strict_loading', not loaded.missing_keys and not loaded.unexpected_keys)
            checks.check('linevul:trained_head_exact', torch.equal(model.classifier.out_proj.weight, state['classifier.out_proj.weight'])
                         and model.classifier.out_proj.weight.shape[0] == 2)
            del state
            length = 512
        else:
            tokenizer = AutoTokenizer.from_pretrained('claudios/VulBERTa-MLP-Devign', revision=VB_REV,
                                                      trust_remote_code=True, local_files_only=True)
            helpers.fix_clang_parser(tokenizer)
            model, loading = AutoModelForSequenceClassification.from_pretrained(
                str(VB), local_files_only=True, use_safetensors=True, output_loading_info=True)
            checks.check('vulberta:strict_loading', not any(loading.get(k) for k in
                         ('missing_keys', 'unexpected_keys', 'mismatched_keys', 'error_msgs')), loading)
            checks.check('vulberta:two_class_head', model.classifier.out_proj.weight.shape[0] == 2)
            length = 1024
        checks.check(model_name + ':padding_compatibility', tokenizer.pad_token_id == model.config.pad_token_id == 1)
        model.to(device).eval()
        checks.check(model_name + ':all_modules_eval', all(not m.training for m in model.modules()))
        head_outputs = []
        hook = model.classifier.register_forward_hook(lambda module, args, result: head_outputs.append(result.detach()))
        model_jobs = [j for j in manifest['jobs'] if j['model'] == model_name]
        for job in model_jobs:
            job_id = job['job']
            print('Inference', job_id, flush=True)
            rows = read_csv(ROOT/job['dataset'])
            selected = job['cohort_rows']
            old = {r['row']: r for r in cohort if r['job'] == job_id}
            # Recreate the exact historical batch neighbors, including final partial batches.
            batches = [list(range(start, min(start+16, len(rows)))) for start in sorted({i//16*16 for i in selected})]
            all_indices = sorted({i for batch in batches for i in batch})
            code_col = 'processed_func' if model_name == 'linevul' else 'func'
            encoded = {}
            for batch in batches:
                if model_name == 'linevul':
                    args = SimpleNamespace(use_word_level_tokenizer=False, block_size=512)
                    for i in batch:
                        ids = line.convert_examples_to_features(rows[i][code_col], 0, tokenizer, args).input_ids
                        encoded[i] = dict(input_ids=torch.tensor(ids), attention_mask=torch.tensor([int(x != 1) for x in ids]))
                else:
                    enc = tokenizer([helpers.clean_for_vulberta(rows[i][code_col]) for i in batch], padding='max_length',
                                    truncation=True, max_length=length, return_tensors='pt', return_token_type_ids=False)
                    for n, i in enumerate(batch):
                        encoded[i] = {k: enc[k][n] for k in ('input_ids', 'attention_mask')}
            checks.check(job_id + ':input_shape_mask_ids', all(
                len(e['input_ids']) == length and torch.equal(e['attention_mask'].bool(), e['input_ids'].ne(1))
                and int(e['input_ids'].min()) >= 0 and int(e['input_ids'].max()) < model.config.vocab_size
                # VulBERTa's backend inserts <s>/</s> without registering the
                # high-level bos/eos properties. Check actual checkpoint IDs.
                and int(e['input_ids'][0]) == model.config.bos_token_id
                and int(e['input_ids'][int(e['attention_mask'].sum())-1]) == model.config.eos_token_id
                for e in encoded.values()),
                dict(tokenizer_bos=tokenizer.bos_token_id, tokenizer_eos=tokenizer.eos_token_id,
                     model_bos=model.config.bos_token_id, model_eos=model.config.eos_token_id))
            if model_name == 'vulberta':
                tokenization_changes = []
                for i in selected:
                    single = tokenizer([helpers.clean_for_vulberta(rows[i][code_col])], padding='max_length',
                                       truncation=True, max_length=length, return_tensors='pt', return_token_type_ids=False)
                    if any(not torch.equal(single[k][0], encoded[i][k]) for k in ('input_ids', 'attention_mask')):
                        tokenization_changes.append(i)
                checks.check(job_id + ':single_batch_tokenization_parity', not tokenization_changes, tokenization_changes)
            sums, softmax_diffs, finite = [], [], []

            def predict(indices):
                inputs = {k: torch.stack([encoded[i][k] for i in indices]).to(device) for k in ('input_ids', 'attention_mask')}
                head_outputs.clear()
                with torch.inference_mode():
                    if model_name == 'linevul':
                        probs = model(input_ids=inputs['input_ids'])
                    else:
                        probs = model(**inputs).logits.softmax(dim=-1)
                expected = head_outputs[-1].softmax(dim=-1)
                softmax_diffs.append(float((expected-probs).abs().max().cpu()))
                sums.append(float((probs.sum(-1)-1).abs().max().cpu()))
                finite.append(bool(torch.isfinite(probs).all() and (probs >= 0).all() and (probs <= 1).all()))
                return probs[:, 1].cpu().tolist()

            batched = {}
            for batch in batches:
                batched.update(zip(batch, predict(batch)))
            singles = {i: predict([i])[0] for i in selected}
            repeated = predict([selected[0]])[0]
            checks.check(job_id + ':repeat_deterministic', abs(repeated-singles[selected[0]]) <= 1e-7)
            checks.check(job_id + ':probabilities_valid', all(finite) and max(sums) <= 1e-6,
                         dict(max_class_sum_error=max(sums)))
            checks.check(job_id + ':exactly_one_softmax', max(softmax_diffs) == 0.0)
            batch_flips = [i for i in selected if (batched[i] > .5) != (singles[i] > .5)]
            old_flips = [i for i in selected if int(batched[i] > .5) != old[i]['historical_prediction']]
            checks.check(job_id + ':batch_prediction_parity', not batch_flips, batch_flips)
            checks.check(job_id + ':historical_prediction_parity', not old_flips, old_flips)
            old_deltas = [abs(batched[i]-old[i]['historical_probability']) for i in selected
                          if old[i]['historical_probability'] is not None]
            if old_deltas:
                checks.check(job_id + ':historical_probability_parity', max(old_deltas) <= 1e-5,
                             dict(max_absolute_delta=max(old_deltas), tolerance=1e-5))
            historical = read_csv(ROOT/job['prediction_file']['path'])
            pred_col = 'raw_preds' if model_name == 'linevul' else 'prediction'
            context_flips = [i for i in all_indices if int(batched[i] > .5) != binary(historical[i][pred_col])]
            checks.check(job_id + ':original_batch_all_predictions', not context_flips, context_flips)
            context_deltas = ([abs(batched[i]-float(historical[i]['prob_vulnerable'])) for i in all_indices]
                              if model_name == 'vulberta' else [])
            if context_deltas:
                checks.check(job_id + ':original_batch_all_probabilities', max(context_deltas) <= 1e-5,
                             dict(max_absolute_delta=max(context_deltas), tolerance=1e-5))
            for i in selected:
                records.append(dict(**old[i], probability_batch16=batched[i], probability_batch1=singles[i],
                                    prediction_batch16=int(batched[i]>.5), prediction_batch1=int(singles[i]>.5),
                                    input_ids_sha256=hashlib.sha256(encoded[i]['input_ids'].numpy().tobytes()).hexdigest()))
            summaries.append(dict(job=job_id, selected_rows=len(selected), original_batch_rows=len(all_indices),
                                  batch_prediction_changes=len(batch_flips), historical_prediction_changes=len(old_flips),
                                  max_batch_probability_delta=max(abs(batched[i]-singles[i]) for i in selected),
                                  max_historical_probability_delta=max(old_deltas) if old_deltas else None,
                                  original_batch_historical_prediction_changes=len(context_flips),
                                  original_batch_max_historical_probability_delta=max(context_deltas) if context_deltas else None,
                                  max_class_sum_error=max(sums), min_probability=min(batched.values()),
                                  max_probability=max(batched.values())))
            write_csv(output/'inference_predictions.csv', records)
            write_json(output/'inference_progress.json', dict(jobs=summaries, checks=checks.rows))
        hook.remove()
        del model, tokenizer
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    report = dict(status='fail' if checks.failed else 'pass', device=device,
                  gpu=torch.cuda.get_device_name(0) if device == 'cuda' else None,
                  jobs=summaries, checks=checks.rows, audit_script_sha256=sha(Path(__file__)),
                  note='Parity uses existing evaluator functions and strictly loaded frozen weights; no training or threshold selection.')
    write_json(output/'inference_audit.json', report)
    print(json.dumps(report, indent=2), flush=True)
    return not checks.failed


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('artifacts', 'inference'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    success = (artifacts if args.stage == 'artifacts' else inference)(args.output.resolve())
    raise SystemExit(0 if success else 1)
