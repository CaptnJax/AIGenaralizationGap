"""Windows/local replacement for webCopies/PIVD.ipynb. Run --help first."""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
JOBS = {
    'linevul-primevul': ('linevul', 'primevul_test'),
    'linevul-llmvul': ('linevul', 'llmvul_test'),
    'vulberta-primevul': ('vulberta', 'primevul_test'),
    'vulberta-llmvul': ('vulberta', 'llmvul_test'),
    'linevul-bigvul': ('linevul', 'bigvul_test'),
    'linevul-bigvul-sample': ('linevul', 'bigvul_test_sample_2000'),
    'linevul-cweval': ('linevul', 'cweval_test'),
    'vulberta-cweval': ('vulberta', 'cweval_test'),
}
ALIASES = {'all': list(JOBS), 'rq1': list(JOBS)[:4], 'sanity': ['linevul-bigvul-sample'],
           'cweval': ['linevul-cweval', 'vulberta-cweval']}
# Weak-label evaluations are opt-in; keep the established `all` cohort unchanged.
JOBS.update({'linevul-devgpt': ('linevul', 'devgpt_weak_test'),
             'vulberta-devgpt': ('vulberta', 'devgpt_weak_test')})
ALIASES['devgpt'] = ['linevul-devgpt', 'vulberta-devgpt']
CHECKPOINT = '12heads_linevul_model.bin'


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, indent=2), encoding='utf-8')
    temporary.replace(path)


def resolve_jobs(names):
    result = []
    for name in names:
        for job in ALIASES.get(name, [name]):
            if job not in JOBS:
                raise ValueError(f'Unknown job {job!r}. Choices: {", ".join(JOBS)}; {", ".join(ALIASES)}.')
            if job not in result:
                result.append(job)
    return result


def prepared_relative(model, stem):
    folder = Path('prepared_datasets')
    if stem == 'devgpt_weak_test':
        folder /= 'devgpt'
    return folder / model / f'{stem}.csv'


def ensure_prepared(root, selected):
    """Extract only missing requested CSVs, never replace existing datasets."""
    needed = [prepared_relative(model, stem)
              for model, stem in (JOBS[j] for j in selected) if not stem.startswith('bigvul')]
    missing = [p for p in needed if not (root / p).is_file()]
    if any(p.stem == 'devgpt_weak_test' for p in missing):
        raise FileNotFoundError('Missing DevGPT weak-label bundle. Run prepare_devgpt_datasets.py first.')
    if any(p.stem == 'cweval_test' for p in missing):
        raise FileNotFoundError('Missing prepared CWEval data. Run prepare_cweval_datasets.py first; '
                                'CWEval is not in the legacy prepared_datasets.zip.')
    if missing:
        archive = root / 'prepared_datasets.zip'
        if not archive.is_file():
            raise FileNotFoundError(f'Missing datasets and {archive}.')
        with zipfile.ZipFile(archive) as zipped:
            for relative in missing:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                with zipped.open(relative.as_posix()) as src, target.open('wb') as dest:
                    shutil.copyfileobj(src, dest)


def download(drive_id, destination):
    import gdown
    if destination.is_file() and destination.stat().st_size:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + '.part')
    result = gdown.download(id=drive_id, output=str(temporary), quiet=False)
    if result is None or not temporary.is_file() or not temporary.stat().st_size:
        raise RuntimeError(f'Download failed for {destination.name}. Retry later if Drive is rate-limited.')
    temporary.replace(destination)


def prepare_linevul(cache):
    if not shutil.which('git'):
        raise RuntimeError('Git is required. Install Git for Windows and reopen PowerShell.')
    repo = cache / 'LineVul'
    if not repo.exists():
        subprocess.run(['git', 'clone', '--depth', '1', 'https://github.com/awsm-research/LineVul.git', str(repo)], check=True)
    entry = repo / 'linevul' / 'linevul_main.py'
    if not entry.is_file():
        raise RuntimeError(f'Incomplete LineVul checkout at {repo}. Use a new --cache-dir.')
    checkpoint = entry.parent / 'saved_models' / 'checkpoint-best-f1' / CHECKPOINT
    download('1oodyQqRb9jEcvLMVVKILmu8qHyNwd-zH', checkpoint)
    if checkpoint.stat().st_size < 10_000_000:
        raise RuntimeError(f'Checkpoint is too small; inspect {checkpoint} before retrying.')
    patched = patch_linevul(entry.read_text(encoding='utf-8'))
    local_entry = entry.with_name('linevul_main_local.py')
    local_entry.write_text(patched, encoding='utf-8')
    commit = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    return local_entry, checkpoint, commit


def patch_linevul(source):
    """Generate a local copy with progress, CPU loading, and strict weight checks."""
    tree = ast.parse(source)
    test = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'test'), None)
    if test is None:
        raise RuntimeError('Unsupported LineVul source: test() is missing.')
    loops = [n for n in ast.walk(test) if isinstance(n, ast.For)
             and isinstance(n.iter, ast.Name) and n.iter.id == 'test_dataloader']
    if len(loops) != 1:
        raise RuntimeError('Unsupported LineVul test loop. Source was not modified.')
    loops[0].iter = ast.parse('tqdm(test_dataloader, total=len(test_dataloader), '
                              'desc="LineVul inference", unit="batch", mininterval=2)', mode='eval').body
    loads = 0
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == 'load_state_dict' and node.args
                and isinstance(node.args[0], ast.Call)
                and ast.unparse(node.args[0].func) == 'torch.load'):
            loads += 1
            model = node.func.value
            load = node.args[0]
            load.keywords = [k for k in load.keywords if k.arg not in ('map_location', 'weights_only')]
            load.keywords.extend([
                ast.keyword(arg='map_location', value=ast.parse('args.device', mode='eval').body),
                ast.keyword(arg='weights_only', value=ast.Constant(True)),
            ])
            node.func = ast.Name(id='_load_local_checkpoint', ctx=ast.Load())
            node.args = [model, load]
            node.keywords = []
    if loads != 1:
        raise RuntimeError('Unsupported LineVul checkpoint loader. Source was not modified.')
    helper = ast.parse('''
def _load_local_checkpoint(model, state):
    expected = model.state_dict()
    # Older Transformers saved these generated buffers; newer versions do not.
    obsolete = [k for k in state if k not in expected and
                k.endswith(('.embeddings.position_ids', '.embeddings.token_type_ids'))]
    for key in obsolete:
        del state[key]
    if obsolete:
        print('Ignoring obsolete generated embedding buffers:', obsolete, flush=True)
    result = model.load_state_dict(state, strict=True)
    print('LineVul trained checkpoint loaded successfully.', flush=True)
    return result
''').body[0]
    # Keep future imports first, and define the helper before the main() call.
    main_guard = next((i for i, n in enumerate(tree.body)
                       if isinstance(n, ast.If) and '__name__' in ast.unparse(n.test)), len(tree.body))
    tree.body.insert(main_guard, helper)
    header = source[:source.find('from __future__')] if 'from __future__' in source else ''
    result = header + ast.unparse(ast.fix_missing_locations(tree)) + '\n'
    compile(result, '<local LineVul>', 'exec')
    return result


def validate_frame(df, model):
    import pandas as pd
    code, label = ('processed_func', 'target') if model == 'linevul' else ('func', 'label')
    if not {code, label}.issubset(df.columns) or df.empty:
        raise ValueError(f'Expected nonempty {code}/{label} data.')
    if df[code].isna().any() or df[code].str.strip().eq('').any():
        raise ValueError('Dataset contains empty functions.')
    if not pd.api.types.is_integer_dtype(df[label]) or not df[label].isin([0, 1]).all():
        raise ValueError('Dataset labels must be integers 0 or 1.')
    if model == 'linevul' and not {'flaw_line', 'flaw_line_index'}.issubset(df.columns):
        raise ValueError('LineVul expects flaw_line and flaw_line_index compatibility columns.')
    if model == 'vulberta' and ('sample_id' not in df or not df.sample_id.is_unique):
        raise ValueError('VulBERTa requires unique sample_id values.')
    return label


def validate_cweval_bundle(root, cache, dataset):
    """Refuse stale/replaced audited inputs or mismatched preprocessing assets."""
    manifest_path = root / 'prepared_datasets/cweval/manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('protocol') != 'cweval_reference_pairs_function_only_v1':
        raise ValueError('Unknown CWEval preparation protocol. Rebuild/review the dataset.')
    relative = dataset.relative_to(root / 'prepared_datasets').as_posix()
    if manifest['output_sha256'].get(relative) != sha(dataset):
        raise ValueError('Prepared CWEval CSV differs from its audited manifest.')
    audit = manifest['tokenizer_audit']
    preprocessing = (HERE / 'vulberta_eval.py').read_text(encoding='utf-8').encode('utf-8')
    if audit.get('preprocessing_hash_format') != 'utf8_lf' or audit['preprocessing_sha256'] != hashlib.sha256(preprocessing).hexdigest():
        raise ValueError('VulBERTa preprocessing changed since CWEval preparation. Rebuild the dataset.')
    hub = cache / 'huggingface/hub'
    for relative, expected in audit['assets_sha256'].items():
        path = hub / relative
        if not path.is_file() or sha(path) != expected:
            raise ValueError(f'CWEval tokenizer asset missing or changed: {path}')
    tokenizer_path = hub / 'models--microsoft--codebert-base/snapshots' / audit['linevul_revision']
    return {'cweval_manifest_sha256': sha(manifest_path),
            'tokenizer_revisions': {name: audit[name] for name in ('linevul_revision', 'vulberta_revision')}}, tokenizer_path


def validate_devgpt_bundle(root, cache, dataset):
    bundle = root / 'prepared_datasets/devgpt'
    manifest_path = bundle / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if (manifest.get('protocol') != 'devgpt_latest_flawfinder_weak_unverified_v1'
            or manifest.get('label_status') != 'weak_unverified'
            or manifest.get('status') != 'complete'):
        raise ValueError('Unknown or incomplete DevGPT weak-label preparation protocol.')
    if manifest['output_sha256'].get(dataset.relative_to(bundle).as_posix()) != sha(dataset):
        raise ValueError('Prepared DevGPT CSV differs from its audited manifest.')
    audit = manifest['tokenizers']
    preprocessing = (HERE / 'vulberta_eval.py').read_text(encoding='utf-8').encode('utf-8')
    if audit.get('preprocessing_sha256') != hashlib.sha256(preprocessing).hexdigest():
        raise ValueError('VulBERTa preprocessing changed since DevGPT preparation.')
    hub = cache / 'huggingface/hub'
    for relative, expected in audit['assets_sha256'].items():
        path = hub / relative
        if not path.is_file() or sha(path) != expected:
            raise ValueError(f'DevGPT tokenizer asset missing or changed: {path}')
    print('DevGPT labels are UNVERIFIED static-analysis weak labels; metrics measure analyzer agreement.', flush=True)
    tokenizer = hub / 'models--microsoft--codebert-base/snapshots' / audit['linevul_revision']
    return {'devgpt_manifest_sha256': sha(manifest_path), 'label_status': 'weak_unverified',
            'label_analyzer': manifest['analyzer']['name'],
            'label_protocol': manifest['protocol']}, tokenizer


def sample_bigvul(frame):
    from sklearn.model_selection import train_test_split
    if len(frame) <= 2000:
        raise ValueError('Expected the full BigVul test CSV with more than 2,000 rows.')
    sample, _ = train_test_split(frame, train_size=2000, stratify=frame['target'], random_state=42)
    return sample.sort_index()


def prepare_bigvul(cache, need_sample):
    import pandas as pd
    full = cache / 'data' / 'bigvul_test.csv'
    download('1h0iFJbc5DGXCXXvvR6dru_Dms_b2zW4V', full)
    df = pd.read_csv(full)
    validate_frame(df, 'linevul')
    sample_path = full.with_name('bigvul_test_sample_2000.csv')
    if need_sample:
        sample = sample_bigvul(df)
        sample.to_csv(sample_path, index=False)
        write_json(sample_path.with_suffix('.selection.json'), {
            'source_sha256': sha(full), 'seed': 42, 'stratified_by': 'target',
            'source_row_indices_zero_based': sample.index.tolist(), 'sample_sha256': sha(sample_path),
        })
    return full, sample_path


def run_logged(command, cwd, env):
    print('Running:', subprocess.list2cmdline([str(x) for x in command]), flush=True)
    with (cwd / 'test.log').open('a', encoding='utf-8') as log:
        log.write('\nRUN ' + datetime.now(timezone.utc).isoformat() + '\n')
        process = subprocess.Popen([str(x) for x in command], cwd=cwd, env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding='utf-8', errors='replace', bufsize=1)
        try:
            for line in process.stdout:
                print(line, end='', flush=True)
                log.write(line)
                log.flush()
            code = process.wait()
            if code:
                raise RuntimeError(f'Evaluation exited with code {code}. See {cwd / "test.log"}.')
        except BaseException:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            raise
        finally:
            process.stdout.close()


def summarize_linevul(result_dir, dataset):
    import pandas as pd
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
    original = pd.read_csv(dataset)
    raw = pd.read_csv(result_dir / 'results' / 'raw_preds.csv')
    if len(raw) != len(original) or not raw.target.equals(original.target) or not raw.processed_func.equals(original.processed_func):
        raise ValueError('Saved predictions do not align with the selected test dataset.')
    mapping = {'True': 1, 'False': 0, '1': 1, '0': 0}
    predictions = raw.raw_preds.astype(str).map(mapping)
    if predictions.isna().any():
        raise ValueError('Unexpected LineVul prediction values.')
    labels = original.target
    tn, fp, fn, tp = confusion_matrix(labels, predictions, labels=[0, 1]).ravel()
    result = {
        'rows': len(raw), 'test_threshold': 0.5,
        'test_accuracy': float(accuracy_score(labels, predictions)),
        'test_precision': float(precision_score(labels, predictions, zero_division=0)),
        'test_recall': float(recall_score(labels, predictions, zero_division=0)),
        'test_f1': float(f1_score(labels, predictions, zero_division=0)),
        'confusion_matrix': {'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp)},
    }
    write_json(result_dir / 'metrics.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--jobs', nargs='+', default=['all'], help=', '.join(ALIASES) + ', or job names: ' + ', '.join(JOBS))
    parser.add_argument('--device', choices=['auto', 'cpu', 'cuda'], default='auto')
    parser.add_argument('--batch-size', type=int, help='Default: 16 on CUDA, 4 on CPU. Lower it if memory is insufficient.')
    parser.add_argument('--data-root', type=Path, default=ROOT)
    parser.add_argument('--cache-dir', type=Path, default=HERE / '.cache')
    parser.add_argument('--run-dir', type=Path, help='Default: a new timestamped folder in localScripts/results.')
    parser.add_argument('--resume', action='store_true', help='Requires --run-dir. Reuses completed jobs and VulBERTa batches.')
    parser.add_argument('--dry-run', action='store_true', help='Show jobs/paths only; no dependencies, downloads or inference.')
    args = parser.parse_args()
    jobs = resolve_jobs(args.jobs)
    if args.batch_size is not None and args.batch_size < 1:
        parser.error('--batch-size must be positive.')
    if args.resume and not args.run_dir:
        parser.error('--resume requires the previous --run-dir.')
    root, cache = args.data_root.resolve(), args.cache_dir.resolve()
    run = args.run_dir.resolve() if args.run_dir else HERE / 'results' / datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    print('Jobs:', ', '.join(jobs))
    print('Data root:', root)
    print('Results:', run)
    if args.dry_run:
        return
    missing = [name for name in ('torch', 'transformers', 'pandas', 'sklearn', 'gdown', 'captum', 'clang')
               if importlib.util.find_spec(name) is None]
    if missing:
        raise RuntimeError('Missing packages: ' + ', '.join(missing) + '. Run localScripts/setup.ps1 first and use its .venv Python.')
    import torch
    import pandas as pd
    from importlib.metadata import version
    device = ('cuda' if torch.cuda.is_available() else 'cpu') if args.device == 'auto' else args.device
    if device == 'cuda' and not torch.cuda.is_available():
        raise RuntimeError('CUDA is unavailable. Use --device cpu or install the CUDA PyTorch build.')
    batch = args.batch_size or (16 if device == 'cuda' else 4)
    if run.exists() and any(run.iterdir()) and not args.resume:
        raise ValueError('Run directory is not empty. Use --resume or a new --run-dir.')
    run.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)
    environment = {'python': sys.version, 'device': device, 'batch_size': batch,
                   'gpu': torch.cuda.get_device_name(0) if device == 'cuda' else None,
                   'packages': {p: version(p) for p in ('torch', 'transformers', 'tokenizers', 'libclang', 'pandas', 'scikit-learn')}}
    write_json(run / 'environment.json', environment)
    print('Device:', device, environment['gpu'] or '', '| batch size:', batch, flush=True)
    ensure_prepared(root, jobs)
    env = os.environ.copy()
    env.update(USE_TF='0', MPLBACKEND='Agg', TOKENIZERS_PARALLELISM='false',
               PYTHONUNBUFFERED='1', PYTHONIOENCODING='utf-8', HF_HOME=str(cache / 'huggingface'))
    if device == 'cpu':
        env['CUDA_VISIBLE_DEVICES'] = ''
    entry = checkpoint = commit = None
    if any(JOBS[j][0] == 'linevul' for j in jobs):
        entry, checkpoint, commit = prepare_linevul(cache)
    bigvul = (None, None)
    if any(JOBS[j][1].startswith('bigvul') for j in jobs):
        bigvul = prepare_bigvul(cache, 'linevul-bigvul-sample' in jobs)
    summaries = []
    for job in jobs:
        model, stem = JOBS[job]
        dataset = (bigvul[1] if 'sample' in stem else bigvul[0]) if stem.startswith('bigvul') else root / prepared_relative(model, stem)
        frame = pd.read_csv(dataset)
        label = validate_frame(frame, model)
        dataset_audit, tokenizer_path = {}, 'microsoft/codebert-base'
        if stem == 'cweval_test':
            dataset_audit, tokenizer_path = validate_cweval_bundle(root, cache, dataset)
        if stem == 'devgpt_weak_test':
            dataset_audit, tokenizer_path = validate_devgpt_bundle(root, cache, dataset)
        print(f'\n{job}: {len(frame)} rows; labels {frame[label].value_counts().to_dict()}', flush=True)
        result_dir = run / model / stem
        result_dir.mkdir(parents=True, exist_ok=True)
        signature = {'job': job, 'dataset_sha256': sha(dataset), 'device': device, 'batch_size': batch,
                     'seed': 42, 'threshold': 0.5, 'packages': environment['packages'],
                     'runner_sha256': sha(Path(__file__)),
                     'implementation_sha256': sha(entry if model == 'linevul' else HERE / 'vulberta_eval.py')}
        signature.update(dataset_audit)
        if model == 'linevul':
            signature.update(linevul_commit=commit, checkpoint_sha256=sha(checkpoint), block_size=512)
        else:
            signature.update(checkpoint_revision='fecabdee24a3ef6e804d7629d6eed03dc6b4f61e', block_size=1024,
                             tokenizer_fix='clang_skip_function_bodies_v1',
                             preprocessing='original_vulberta_cleaner_v1')
        manifest = result_dir / 'job.json'
        previous = json.loads(manifest.read_text()) if manifest.exists() else None
        if previous and previous['signature'] != signature:
            raise ValueError(f'{job}: previous run settings differ. Choose a new --run-dir.')
        if args.resume and previous and previous['status'] == 'complete' and (result_dir / 'metrics.json').is_file():
            print('Reusing completed job:', job)
        else:
            write_json(manifest, {'status': 'running', 'signature': signature})
            if model == 'linevul':
                (result_dir / 'results').mkdir(exist_ok=True)
                command = [sys.executable, '-u', str(entry), f'--model_name={CHECKPOINT}',
                           f'--output_dir={checkpoint.parent.parent}', '--model_type=roberta',
                           f'--tokenizer_name={tokenizer_path}', '--model_name_or_path=microsoft/codebert-base',
                           '--do_test', f'--test_data_file={dataset}', '--block_size=512',
                           f'--eval_batch_size={batch}', '--seed=42', '--write_raw_preds']
            else:
                command = [sys.executable, '-u', str(HERE / 'vulberta_eval.py'), f'--test_data_file={dataset}',
                           f'--output_dir={run / model}', f'--device={device}', '--block_size=1024',
                           f'--eval_batch_size={batch}', '--seed=42']
                if args.resume:
                    command.append('--resume')
            try:
                run_logged(command, result_dir, env)
                if model == 'linevul':
                    summarize_linevul(result_dir, dataset)
                if not (result_dir / 'metrics.json').is_file():
                    raise RuntimeError('Evaluation exited without metrics.json.')
                write_json(manifest, {'status': 'complete', 'signature': signature})
            except BaseException as error:
                write_json(manifest, {'status': 'interrupted_or_failed', 'signature': signature, 'error': str(error)})
                raise
        metrics = json.loads((result_dir / 'metrics.json').read_text())
        summaries.append({'job': job, **{k: metrics[k] for k in ('rows', 'test_accuracy', 'test_f1', 'test_precision', 'test_recall', 'test_threshold')}})
        pd.DataFrame(summaries).to_csv(run / 'summary.csv', index=False)
    print('\nCompleted. Results:', run)
    print(pd.DataFrame(summaries).to_string(index=False))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nStopped. Completed jobs and VulBERTa batches are saved.', file=sys.stderr)
        sys.exit(130)
    except Exception as error:
        print(f'ERROR: {error}', file=sys.stderr)
        sys.exit(1)
