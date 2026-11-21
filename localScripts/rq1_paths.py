"""Read legacy provenance paths from the reorganized public checkout.

Use input_path only for reads. Output directories remain explicit CLI arguments.
Existing paths (including runtime caches) take precedence over bundled inputs.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RAW = ROOT / 'datasets/raw'
PRUNED = ROOT / 'datasets/pruned'
DIAGNOSTICS = ROOT / 'results/diagnostics'
SUBJECTS = {
    '1': 'evaluation_validation',
    '2': 'input_preprocessing',
    '3': 'score_analysis',
    '4': 'dataset_quality',
    '5': 'generalization_controls',
}


def raw_source(name):
    if name.startswith('primevul_'):
        return RAW / 'PrimeVul' / name
    if name == 'LLMVul_v3-Updated.csv':
        return RAW / 'LLMVul' / name
    if name.startswith('bigvul_'):
        return RAW / 'BigVul' / name
    if name == 'Devign.json' or name.startswith(('devign.', 'codexglue_')):
        return RAW / 'Devign' / name
    return None


def input_path(path):
    """Resolve a missing legacy input without changing existing or external paths."""
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    if path.exists():
        return path
    try:
        parts = path.relative_to(ROOT).parts
    except ValueError:
        return path
    if not parts:
        return path
    if parts[0] == 'prepared_datasets':
        return PRUNED.joinpath(*parts[1:])
    if len(parts) == 1:
        source = raw_source(parts[0])
        if source is not None:
            return source
        if parts[0] in ('prepare_evaluation_datasets.py', 'prepare_cweval_datasets.py'):
            return HERE / parts[0]
    if parts[:2] == ('localScripts', 'results') and len(parts) >= 3:
        name, tail = parts[2], parts[3:]
        if name.startswith('rq1_priority') and name[12:13] in SUBJECTS:
            stage = name[12]
            if stage == '5' and len(tail) >= 2:
                if tail[0] == 'inputs':
                    return PRUNED.joinpath('controls', *tail[1:])
                if tail[0] == 'sources':
                    source = raw_source(tail[1])
                    if source is not None:
                        return source
            return DIAGNOSTICS.joinpath(SUBJECTS[stage], name, *tail)
        return ROOT.joinpath('results/evaluation_runs', name, *tail)
    if parts[:2] == ('localScripts', 'reports') and len(parts) == 3:
        name = parts[2]
        if name == 'rq1_results.md':
            # Historical manifests require the captured baseline's original
            # bytes, while current findings use the consolidated rq1_answer.md.
            return DIAGNOSTICS / 'evaluation_validation/rq1_priority1_20261028_verified/evidence/32267dccb7e2_rq1_results.md'
        if name == 'rq1_diagnostics.md':
            return DIAGNOSTICS / SUBJECTS['1'] / name
        if name.startswith('rq1_priority') and name[12:13] in SUBJECTS:
            return DIAGNOSTICS / SUBJECTS[name[12]] / name
        return ROOT / 'results/findings' / name
    if parts[:2] == ('localScripts', '.cache') and len(parts) >= 3:
        kind, tail = parts[2], parts[3:]
        if kind == 'data' and tail:
            if tail[0].startswith('bigvul_test_sample_2000'):
                return PRUNED.joinpath('BigVul', *tail)
            source = raw_source(tail[0])
            return source if source is not None else path
        if kind == 'CWEval':
            candidate = RAW.joinpath('CWEval/upstream', *tail)
        elif kind == 'LineVul':
            candidate = HERE.joinpath('upstream/LineVul', *tail)
        elif kind == 'huggingface' and tail[:1] == ('hub',):
            candidate = HERE.joinpath('upstream/huggingface', *tail[1:])
        else:
            return path
        if candidate.exists():
            return candidate
    return path
