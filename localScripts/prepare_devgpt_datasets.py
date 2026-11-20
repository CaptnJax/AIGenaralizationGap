"""Prepare latest-snapshot DevGPT C/C++ functions with UNVERIFIED weak labels.

Run with the existing localScripts/.venv Python. Never executes source code.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime
import hashlib
from importlib.metadata import version
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile

from prepare_cweval_datasets import (
    TokenAudit, function_name, lexical_tokens, remove_comments, walk,
)

ROOT = Path(__file__).resolve().parent
LANGUAGES = {'c': 'c', 'cpp': 'cpp', 'c++': 'cpp', 'cxx': 'cpp', 'cc': 'cpp'}
PROTOCOL = 'devgpt_latest_flawfinder_weak_unverified_v1'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def write_jsonl(path, rows):
    with path.open('w', encoding='utf-8', newline='\n') as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + '\n')


def write_csv(path, fields, rows):
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def latest_snapshot(root):
    snapshots = []
    for path in root.iterdir():
        if path.is_dir() and re.fullmatch(r'snapshot_\d{8}', path.name):
            snapshots.append((datetime.strptime(path.name[9:], '%Y%m%d'), path))
    if not snapshots:
        raise ValueError(f'No dated snapshots under {root}')
    selected = max(snapshots)[1]
    files = sorted(selected.glob('*_sharings.json'))
    kinds = {p.stem.split('_')[-2] for p in files}
    if len(files) != 6 or kinds != {'pr', 'issue', 'discussion', 'commit', 'file', 'hn'}:
        raise ValueError(f'Latest snapshot is incomplete: {selected}; will not fall back to older data.')
    return selected, files


def collect_blocks(files):
    blocks, counts, languages = {}, Counter(), Counter()
    for path in files:
        data = json.loads(path.read_text(encoding='utf-8'))
        for source_index, source in enumerate(data['Sources']):
            counts['source_records'] += 1
            for sharing_index, sharing in enumerate(source.get('ChatgptSharing', [])):
                for turn_index, turn in enumerate(sharing.get('Conversations', [])):
                    for block_index, block in enumerate(turn.get('ListOfCode', [])):
                        counts['all_code_block_occurrences'] += 1
                        tag = (block.get('Type') or '').strip().lower()
                        languages[tag or '(untagged)'] += 1
                        if tag not in LANGUAGES:
                            continue
                        counts['c_cpp_tagged_block_occurrences'] += 1
                        code = block.get('Content')
                        if not isinstance(code, str) or not code.strip():
                            counts['empty_c_cpp_blocks'] += 1
                            continue
                        language = LANGUAGES[tag]
                        block_id = sha((language + '\0' + code).encode('utf-8'))
                        record = blocks.setdefault(block_id, {
                            'block_id': block_id, 'language': language, 'code': code,
                            'code_sha256': sha(code.encode('utf-8')), 'occurrences': [],
                        })
                        record['occurrences'].append({
                            'source_file': path.name,
                            'json_pointer': f'/Sources/{source_index}/ChatgptSharing/{sharing_index}/Conversations/{turn_index}/ListOfCode/{block_index}',
                            'source_url': source.get('URL'), 'conversation_url': sharing.get('URL'),
                            'source_type': source.get('Type'), 'repo': source.get('RepoName'),
                            'language_tag': block['Type'], 'conv_index': turn.get('ConvIndex'),
                            'sharing_status': sharing.get('Status'),
                        })
    return list(blocks.values()), counts, languages


def extract_functions(block, parser):
    """Conservative syntax filter; parsing is NOT semantic/security validation."""
    tree = parser.parse(block['code'].encode('utf-8'))
    if tree.root_node.has_error:
        return [], ['block_syntax_error_or_incomplete']
    nodes = [n for n in walk(tree.root_node) if n.type == 'function_definition']
    if not nodes:
        return [], ['no_function_definition']
    results, exclusions = [], []
    for node in nodes:
        ancestors, parent = [], node.parent
        while parent is not None:
            ancestors.append(parent.type)
            parent = parent.parent
        if set(ancestors) & {'class_specifier', 'struct_specifier', 'namespace_definition', 'function_definition'}:
            exclusions.append('function_requires_enclosing_scope')
            continue
        if not function_name(node):
            exclusions.append('unresolved_function_name')
            continue
        selected = node.parent if node.parent.type == 'template_declaration' else node
        if any(n.type == 'comment' and re.search(
                rb'\bTODO\b|\.\.\.|your code here|implementation here', n.text, re.I)
                for n in walk(selected)):
            exclusions.append('placeholder_comment')
            continue
        code = remove_comments(selected)
        parsed = parser.parse(code.encode('utf-8'))
        if parsed.root_node.has_error or lexical_tokens(selected) != lexical_tokens(parsed.root_node):
            exclusions.append('comment_removal_changed_tokens')
            continue
        results.append({
            'code': code, 'language': block['language'],
            'source': {'block_id': block['block_id'], 'function_name': function_name(node),
                       'start_byte': selected.start_byte, 'end_byte': selected.end_byte,
                       'start_line': selected.start_point.row + 1,
                       'end_line': selected.end_point.row + 1,
                       'raw_function_sha256': sha(selected.text)},
        })
    return results, exclusions


def weak_label(findings):
    maximum = max((int(f['Level']) for f in findings), default=0)
    if maximum >= 3:
        return 1, 'flawfinder_level_3_or_higher'
    if maximum >= 1:
        return None, 'only_level_1_or_2_findings_ambiguous'
    return 0, 'no_flawfinder_findings_at_level_1_or_higher'


def scan_functions(records, output):
    import flawfinder
    if version('flawfinder') != '2.0.19':
        raise ValueError('This labeling protocol requires flawfinder==2.0.19')
    scan_dir = output / 'audit' / 'analyzer_inputs'
    scan_dir.mkdir()
    by_filename = {}
    for row in records:
        filename = row['code_sha256'] + ('.c' if row['language'] == 'c' else '.cpp')
        (scan_dir / filename).write_bytes(row['code'].encode('utf-8'))
        by_filename[filename] = row['sample_id']
    if not records:
        raise ValueError('No parseable function candidates')
    command = [sys.executable, '-m', 'flawfinder', '--csv', '--minlevel=1', '--neverignore', str(scan_dir)]
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    run = subprocess.run(command, capture_output=True, text=True, encoding='utf-8',
                         env=env, timeout=300, check=True)
    (output / 'audit/flawfinder_raw.csv').write_text(run.stdout, encoding='utf-8')
    (output / 'audit/flawfinder_stderr.txt').write_text(run.stderr, encoding='utf-8')
    if run.stderr.strip():
        raise ValueError('Analyzer emitted diagnostics; inspect audit/flawfinder_stderr.txt before assigning labels.')
    reader = csv.DictReader(io.StringIO(run.stdout))
    if not {'File', 'Level', 'Line', 'Column', 'Name', 'CWEs'}.issubset(reader.fieldnames or []):
        raise ValueError('Unexpected analyzer CSV schema')
    grouped = defaultdict(list)
    for finding in reader:
        filename = Path(finding['File']).name
        sample_id = by_filename[filename]
        if int(finding['Level']) not in range(1, 6):
            raise ValueError('Invalid analyzer risk level')
        finding['File'] = 'analyzer_inputs/' + filename
        grouped[sample_id].append(finding)
    for row in records:
        row['findings'] = grouped[row['sample_id']]
        row['weak_label'], row['label_basis'] = weak_label(row['findings'])
        row['label_status'] = 'weak_unverified'
    return {'name': 'Flawfinder', 'version': version('flawfinder'),
            'implementation_sha256': file_sha(Path(flawfinder.__file__)),
            'arguments': command[3:-1], 'returncode': run.returncode,
            'scanned_files': len(by_filename),
            'policy': '1: any level >=3; 0: no level >=1; exclude only-level-1/2 findings. Unverified lexical heuristics, not ground truth.'}


def export_models(output, selected):
    import pandas as pd
    for name in ('linevul', 'vulberta'):
        (output / name).mkdir()
    write_csv(output / 'linevul/devgpt_weak_test.csv',
              ['sample_id', 'processed_func', 'target', 'flaw_line', 'flaw_line_index'],
              ({'sample_id': r['sample_id'], 'processed_func': r['code'], 'target': r['weak_label'],
                'flaw_line': '', 'flaw_line_index': ''} for r in selected))
    write_csv(output / 'vulberta/devgpt_weak_test.csv', ['sample_id', 'func', 'label'],
              ({'sample_id': r['sample_id'], 'func': r['code'], 'label': r['weak_label']} for r in selected))
    frame = pd.DataFrame({'sample_id': pd.Series([r['sample_id'] for r in selected], dtype=object),
                          'func': pd.Series([r['code'] for r in selected], dtype=object),
                          'label': pd.Series([r['weak_label'] for r in selected], dtype='int64')})
    frame.to_pickle(output / 'vulberta/devgpt_weak_test.pkl', protocol=4)
    for relative, code, label in [('linevul/devgpt_weak_test.csv', 'processed_func', 'target'),
                                   ('vulberta/devgpt_weak_test.csv', 'func', 'label'),
                                   ('vulberta/devgpt_weak_test.pkl', 'func', 'label')]:
        path = output / relative
        loaded = pd.read_pickle(path) if path.suffix == '.pkl' else pd.read_csv(path)
        assert loaded['sample_id'].tolist() == [r['sample_id'] for r in selected]
        assert loaded[code].tolist() == [r['code'] for r in selected]
        assert loaded[label].tolist() == [r['weak_label'] for r in selected]
        assert pd.api.types.is_integer_dtype(loaded[label])
        if label == 'target':
            assert loaded[['flaw_line', 'flaw_line_index']].isna().all().all()


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--source-root', type=Path, default=ROOT / 'DevGPT/DevGPT')
    cli.add_argument('--output', type=Path, default=ROOT / 'prepared_datasets/devgpt')
    cli.add_argument('--cache-dir', type=Path, default=ROOT / 'localScripts/.cache')
    args = cli.parse_args()
    from tree_sitter import Language, Parser
    import tree_sitter_c
    import tree_sitter_cpp
    parsers = {'c': Parser(Language(tree_sitter_c.language())),
               'cpp': Parser(Language(tree_sitter_cpp.language()))}
    snapshot, files = latest_snapshot(args.source_root)
    source_hashes = {p.name: file_sha(p) for p in files}
    auditor = TokenAudit(args.cache_dir)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / 'audit').mkdir()
    blocks, counts, languages = collect_blocks(files)
    print(f'{snapshot.name}: {counts["c_cpp_tagged_block_occurrences"]} tagged occurrences; {len(blocks)} unique language/code blocks', flush=True)
    candidates = {}
    for block in blocks:
        functions, reasons = extract_functions(block, parsers[block['language']])
        block['extraction_exclusions'] = reasons
        block['extracted_function_occurrences'] = len(functions)
        for function in functions:
            counts['extracted_function_occurrences'] += 1
            code = function['code']
            code_hash = sha(code.encode('utf-8'))
            row = candidates.setdefault(code_hash, {
                'sample_id': 'devgpt-weak:' + code_hash, 'code_sha256': code_hash,
                'code': code, 'language': function['language'], 'sources': [],
            })
            row['sources'].append(function['source'])
            # A block tagged C++ may use the same function as a block tagged C.
            if function['language'] == 'cpp':
                row['language'] = 'cpp'
    records = list(candidates.values())
    analyzer = scan_functions(records, output)
    for index, row in enumerate(records):
        checks = auditor.inspect(row['code'], parsers[row['language']])
        checks.pop('vulberta_cleaned_code')
        row['model_input_checks'] = checks
        reasons = []
        if row['weak_label'] is None:
            reasons.append('ambiguous_low_risk_findings')
        if not checks['vulberta_cleaner_preserves_lexical_tokens']:
            reasons.append('vulberta_preprocessing_changes_tokens_or_syntax')
        for model in ('linevul', 'vulberta'):
            if checks[f'{model}_would_truncate']:
                reasons.append(model + '_would_truncate')
        row['exclusion_reasons'] = reasons
        row['eligible'] = not reasons
        if (index + 1) % 100 == 0:
            print(f'Audited {index + 1}/{len(records)} functions', flush=True)
    selected = [r for r in records if r['eligible']]
    if {r['weak_label'] for r in selected} != {0, 1}:
        raise ValueError('Selected cohort does not contain both weak-label classes; inspect candidates before evaluation.')
    write_jsonl(output / 'audit/blocks.jsonl', blocks)
    write_jsonl(output / 'audit/functions.jsonl', records)
    export_models(output, selected)
    counts.update(unique_tagged_blocks=len(blocks), unique_function_candidates=len(records),
                  exported_functions=len(selected),
                  weak_non_vulnerable=sum(r['weak_label'] == 0 for r in selected),
                  weak_vulnerable=sum(r['weak_label'] == 1 for r in selected))
    assert source_hashes == {p.name: file_sha(p) for p in files}, 'Source files changed during preparation'
    manifest = {
        'protocol': PROTOCOL, 'status': 'complete', 'label_status': 'weak_unverified',
        'snapshot': snapshot.name, 'source_sha256': source_hashes,
        'source_files_unchanged': True, 'older_snapshots_used': False,
        'input_scope': 'ChatGPT answer ListOfCode only; excludes prompt text, host repository files and HTML.',
        'selection': 'Explicit C/C++ block tags, complete syntax trees, free functions, no placeholder comments, exact-code deduplication after token-preserving comment removal. Both model token limits and cleaner preservation required.',
        'counts': dict(counts), 'source_block_language_counts': dict(languages),
        'selected_languages': dict(Counter(r['language'] for r in selected)),
        'block_exclusion_counts': dict(Counter(reason for b in blocks for reason in b['extraction_exclusions'])),
        'function_exclusion_counts': dict(Counter(reason for r in records for reason in r['exclusion_reasons'])),
        'candidate_weak_labels': dict(Counter(str(r['weak_label']) for r in records)),
        'analyzer': analyzer, 'tokenizers': auditor.identity,
        'runtime': {name: version(name) for name in ('pandas', 'tree-sitter', 'tree-sitter-c', 'tree-sitter-cpp', 'flawfinder')},
        'converter_sha256': file_sha(Path(__file__)),
        'shared_conversion_helpers_sha256': file_sha(ROOT / 'prepare_cweval_datasets.py'),
        'evaluation': 'Not run. Measure agreement with unverified Flawfinder weak labels, not validated vulnerability detection accuracy.',
        'verification': 'All model rows reloaded: matching IDs, exact code and integer labels; no truncation; token-preserving cleaning; source hashes unchanged.',
    }
    (output / 'README.md').write_text(readme(manifest), encoding='utf-8')
    manifest['output_sha256'] = {p.relative_to(output).as_posix(): file_sha(p)
                                 for p in sorted(output.rglob('*')) if p.is_file()}
    write_json(output / 'manifest.json', manifest)
    archive = output.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zipped:
        for path in sorted(output.rglob('*')):
            if path.is_file():
                zipped.write(path, Path(output.name) / path.relative_to(output))
    with zipfile.ZipFile(archive) as zipped:
        assert zipped.testzip() is None
    print(json.dumps(manifest['counts'], indent=2), flush=True)
    print(f'Verified weak-label bundle: {archive}', flush=True)


def readme(manifest):
    counts = manifest['counts']
    return f'''# DevGPT C/C++ — UNVERIFIED static-analysis weak labels

Only `{manifest['snapshot']}` was read. The six JSON filenames contain collection
dates May 13–15, 2024; snapshot-directory date determines selection. Older snapshots
and the redundant link CSV are never pooled or used as fallback. The original files
are unchanged. Only generated answer code from `ListOfCode` is used.

| Selection | Count |
| --- | ---: |
| C/C++ tagged block occurrences | {counts['c_cpp_tagged_block_occurrences']} |
| Unique language/code blocks | {counts['unique_tagged_blocks']} |
| Unique parsed function candidates | {counts['unique_function_candidates']} |
| Exported functions | {counts['exported_functions']} |
| Weak vulnerable (1) | {counts['weak_vulnerable']} |
| Weak non-vulnerable (0) | {counts['weak_non_vulnerable']} |

## Label meaning

DevGPT has **no vulnerability ground truth**. The user selected static-analysis
weak labels. Every label is **unverified**, generated by Flawfinder 2.0.19:

- `1`: at least one risk-level 3–5 finding.
- `0`: no finding at risk level 1 or higher. This does **not** establish safety.
- Functions with only risk-level 1–2 findings are excluded as ambiguous.

This threshold is our preparation policy, not an official DevGPT labeling scheme.
Flawfinder is a lexical analyzer with false positives and false negatives. It does
not establish exploitability or semantic correctness. Scores measure agreement
with this heuristic; do not report them as accuracy against verified labels.
See the [analyzer documentation](https://dwheeler.com/flawfinder/).

## Extraction and model compatibility

Explicit `c`, `cpp`, `c++`, `cxx`, `cc` tags only; repository language is not used
to infer a block's language. Tree-sitter must parse the complete block without
errors. Fragments, declarations without bodies, incomplete syntax, functions inside
class/struct/namespace scopes, and placeholder comments are excluded. Parsing is
not compilation, semantic validation, or proof of complete context; external APIs,
types and helpers can still be unresolved. No source code is executed.

Only function code is exported. Comments are removed with the syntax tree to avoid
prose/security hints, while string literals and all lexical tokens are preserved.
Exact resulting function text is deduplicated across all six source categories;
all source occurrences remain in the audit. Near-duplicates may remain. There is
no training split, balancing, or claim of independence from model training data.

Both models receive the same ordered functions and labels. Functions exceeding
LineVul's 512-token limit or VulBERTa's 1024-token limit, or whose tokens/syntax change
under the existing VulBERTa cleaner, are excluded. No code is truncated to fit.

- `linevul/devgpt_weak_test.csv`: `sample_id,processed_func,target,flaw_line,flaw_line_index`.
- `vulberta/devgpt_weak_test.csv` and `.pkl`: `sample_id,func,label`.

Only `processed_func`/`func` is model input. IDs and labels are not input tokens.
The LineVul flaw columns are empty/NaN compatibility placeholders; analyzer hit
lines are not validated flaw locations. Disable all localization/ranking options.
Use frozen trained checkpoints and the existing tokenizer/preprocessing settings.
No detector evaluation or training was run during preparation.

## Audit and reproduction

`audit/blocks.jsonl` stores unique tagged blocks, original code, and all source JSON
pointers (zero-based indices), URLs, and tags. `audit/functions.jsonl` stores every
candidate, extraction byte ranges into UTF-8 blocks, hashes, findings, unverified
labels, token checks, and exclusions. `audit/analyzer_inputs/` contains the exact
code scanned. These are audit-only files, not additional evaluation samples.
`manifest.json` pins input/output hashes, tool versions, rules, tokenizer assets,
and counts. Export CSV/pickle contents were reloaded and compared row for row.

From the repository root:

```powershell
.\\localScripts\\.venv\\Scripts\\python.exe -m pip install -r .\\localScripts\\requirements-devgpt.txt
.\\localScripts\\.venv\\Scripts\\python.exe .\\prepare_devgpt_datasets.py --output .\\prepared_datasets\\devgpt_rebuild
```

Requires the tokenizer assets already cached by the local evaluation setup;
preparation never downloads checkpoints. Output and ZIP must not already exist.
The separate `devgpt.zip` includes this README and complete audit alongside both
model formats; it does not alter the legacy `prepared_datasets.zip`.
'''


if __name__ == '__main__':
    main()
