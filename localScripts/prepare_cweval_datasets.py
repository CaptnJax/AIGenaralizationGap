"""Convert CWEval pairs to audited function-level inputs for the frozen detectors.

Never executes benchmark code or changes model preprocessing. See
datasets/pruned/cweval/README.md for the selection protocol and limitations.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
import csv
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
from types import SimpleNamespace
from urllib.request import urlopen
from rq1_paths import input_path

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM_LOCK = ROOT / 'localScripts/cweval_upstream_lock.json'
CODEBERT_REVISION = '3b0952feddeffad0063f274080e3c23d75e7eb39'
VULBERTA_REVISION = 'fecabdee24a3ef6e804d7629d6eed03dc6b4f61e'
PROTOCOL = 'cweval_reference_pairs_function_only_v1'
METADATA = ['pair_id', 'group_id', 'language', 'cwe_id', 'source_subset', 'variant',
            'label_basis', 'code_provenance']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')


def walk(node):
    yield node
    for child in node.children:
        yield from walk(child)


def lexical_tokens(node):
    """Syntax-tree leaves, excluding comments; whitespace cannot hide changes."""
    if node.type == 'comment':
        return []
    if not node.children:
        return [node.text.decode('utf-8')]
    return [token for child in node.children for token in lexical_tokens(child)]


def declarator_name(node):
    while node is not None:
        if node.type in ('identifier', 'field_identifier', 'type_identifier', 'qualified_identifier'):
            return node.text.decode('utf-8')
        node = node.child_by_field_name('declarator')
    return None


def function_name(node):
    return declarator_name(node.child_by_field_name('declarator'))


def functions(tree):
    found = {}
    for node in walk(tree.root_node):
        if node.type == 'function_definition':
            name = function_name(node)
            if not name or name in found:
                raise ValueError('Missing or ambiguous function name; manual extraction required.')
            found[name] = node
    return found


def extract_block(payload):
    if not isinstance(payload, str):
        raise ValueError('Expected a string code response.')
    blocks = re.findall(r'<code>(.*?)</code>', payload, flags=re.DOTALL)
    if len(blocks) != 1 or not blocks[0].strip():
        raise ValueError('Expected exactly one nonempty <code> block.')
    return blocks[0].strip()


def reference_target(tree):
    matches = [name for name, node in functions(tree).items()
               if any(n.type == 'comment' and b'BEGIN SOLUTION' in n.text for n in walk(node))]
    if len(matches) != 1 or matches[0] == 'main':
        raise ValueError('Upstream BEGIN SOLUTION does not identify one target function.')
    return matches[0]


def remove_comments(node):
    """Remove benchmark hints without treating URL strings as comments."""
    data = bytearray(node.text)
    for comment in (n for n in walk(node) if n.type == 'comment'):
        start, end = comment.start_byte - node.start_byte, comment.end_byte - node.start_byte
        data[start:end] = bytes(10 if b == 10 else 32 for b in data[start:end])
    # Remove blank lines left by annotations; never join nonempty source lines.
    return '\n'.join(line.rstrip() for line in data.decode('utf-8').splitlines() if line.strip()).strip()


def referenced_context(tree, target):
    """Conservatively flag locally defined context absent from a single function."""
    func_map = functions(tree)
    node = func_map[target]
    used = {n.text.decode('utf-8') for n in walk(node)
            if n.type in ('identifier', 'type_identifier', 'field_identifier')}
    deps = {f'helper_function:{name}' for name in func_map if name != target and name in used}
    for top in tree.root_node.named_children:
        if top.type in ('preproc_def', 'preproc_function_def'):
            name = top.child_by_field_name('name')
            if name is not None and name.text.decode('utf-8') in used:
                deps.add('macro:' + name.text.decode('utf-8'))
        elif top.type in ('type_definition', 'declaration'):
            for i, child in enumerate(top.children):
                if top.field_name_for_child(i) != 'declarator':
                    continue
                # Function prototypes describe external APIs, not supplied bodies.
                if any(n.type == 'function_declarator' for n in walk(child)):
                    continue
                name = declarator_name(child)
                if name in used:
                    deps.add(('type:' if top.type == 'type_definition' else 'global:') + name)
        if top.type != 'function_definition':
            for decl in walk(top):
                if decl.type in ('struct_specifier', 'enum_specifier', 'class_specifier'):
                    name = decl.child_by_field_name('name')
                    if name is not None and name.text.decode('utf-8') in used:
                        deps.add('type:' + name.text.decode('utf-8'))
                    if decl.type == 'enum_specifier':
                        for enum in (n for n in walk(decl) if n.type == 'enumerator'):
                            name = enum.child_by_field_name('name')
                            if name is not None and name.text.decode('utf-8') in used:
                                deps.add('enum:' + name.text.decode('utf-8'))
    return sorted(deps)


def checked_upstream(relative, lock, cache, fetch):
    expected = lock['files'].get(relative)
    if expected is None:
        raise ValueError(f'No pinned upstream evidence for {relative}. Update/review the lock first.')
    path = input_path(cache / relative)
    if not path.is_file():
        if not fetch:
            raise FileNotFoundError(f'Missing {path}. Run with --fetch-upstream to download the pinned sources.')
        url = f'https://raw.githubusercontent.com/{lock["repository"]}/{lock["revision"]}/{relative}'
        with urlopen(url, timeout=60) as response:
            data = response.read()
        if git_blob_sha(data) != expected:
            raise ValueError(f'Upstream hash mismatch: {relative}')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    data = path.read_bytes()
    if git_blob_sha(data) != expected:
        raise ValueError(f'Cached upstream hash mismatch: {path}')
    return data


def load_preprocessing():
    """Use the evaluator's actual functions without importing/loading any model."""
    path = ROOT / 'localScripts/vulberta_eval.py'
    tree = ast.parse(path.read_text(encoding='utf-8'))
    tree.body = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                 and n.name in ('clean_for_vulberta', 'fix_clang_parser')]
    namespace = {'re': re}
    exec(compile(tree, str(path), 'exec'), namespace)
    return namespace


class TokenAudit:
    def __init__(self, cache):
        os.environ['TOKENIZERS_PARALLELISM'] = 'false'
        os.environ['USE_TF'] = '0'
        from transformers import RobertaTokenizer
        from tokenizers import Tokenizer
        hub = cache / 'huggingface/hub'
        lv = hub / 'models--microsoft--codebert-base/snapshots' / CODEBERT_REVISION
        vb = hub / 'models--claudios--VulBERTa-MLP-Devign/snapshots' / VULBERTA_REVISION
        assets = [lv / name for name in ('vocab.json', 'merges.txt', 'tokenizer_config.json',
                                        'special_tokens_map.json', 'config.json')]
        assets += [vb / name for name in ('tokenizer.json', 'tokenizer_config.json',
                                         'special_tokens_map.json', 'tokenization_vulberta.py', 'config.json')]
        for path in assets:
            if not input_path(path).is_file():
                raise FileNotFoundError(f'Missing cached tokenizer asset: {path}. No model downloads are performed.')
        self.lv = RobertaTokenizer.from_pretrained(str(input_path(lv)), local_files_only=True)
        self.vb = Tokenizer.from_file(str(input_path(vb / 'tokenizer.json')))
        preprocessing = load_preprocessing()
        self.clean = preprocessing['clean_for_vulberta']
        preprocessing['fix_clang_parser'](SimpleNamespace(_tokenizer=self.vb))
        self.vb.no_padding()
        self.vb.no_truncation()
        self.identity = {'linevul_revision': CODEBERT_REVISION, 'vulberta_revision': VULBERTA_REVISION,
                         'preprocessing_sha256': sha((ROOT / 'localScripts/vulberta_eval.py').read_text(encoding='utf-8').encode('utf-8')),
                         'preprocessing_hash_format': 'utf8_lf',
                         'assets_sha256': {str(p.relative_to(hub)).replace('\\', '/'): sha(input_path(p).read_bytes()) for p in assets}}

    def inspect(self, code, parser):
        cleaned = self.clean(code)
        before = parser.parse(code.encode('utf-8'))
        after = parser.parse(cleaned.encode('utf-8'))
        unchanged = lexical_tokens(before.root_node) == lexical_tokens(after.root_node) and not after.root_node.has_error
        lv_length = len(self.lv.tokenize(code)) + 2
        vb_ids = self.vb.encode(cleaned).ids
        return {'linevul_tokens_including_special': lv_length,
                'vulberta_tokens_including_special': len(vb_ids),
                'vulberta_unknown_tokens': vb_ids.count(3),
                'vulberta_cleaner_preserves_lexical_tokens': unchanged,
                'vulberta_cleaned_code': cleaned,
                'linevul_would_truncate': lv_length > 512,
                'vulberta_would_truncate': len(vb_ids) > 1024}


def assign_groups(records):
    """Join C/C++ counterparts and exact token-equivalent extracted functions."""
    parent = {r['pair_id']: r['pair_id'] for r in records}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def join(a, b):
        a, b = find(a), find(b)
        parent[max(a, b)] = min(a, b)
    seen_problem, seen_code = {}, {}
    for r in records:
        for seen, key in [(seen_problem, r['problem_id']), (seen_code, r['function_token_sha256'])]:
            if key in seen:
                join(r['pair_id'], seen[key])
            seen[key] = r['pair_id']
    members = defaultdict(list)
    for pair in parent:
        members[find(pair)].append(pair)
    names = {root: 'cweval-group:' + sha('\n'.join(sorted(pairs)).encode())[:16]
             for root, pairs in members.items()}
    for r in records:
        r['group_id'] = names[find(r['pair_id'])]


def apply_selection(records):
    by_pair, by_code = defaultdict(list), defaultdict(list)
    for r in records:
        by_pair[r['pair_id']].append(r)
        by_code[r['function_token_sha256']].append(r)
    for rows in by_code.values():
        if len({r['label'] for r in rows}) > 1:
            for r in rows:
                r['exclusion_reasons'].append('identical_function_conflicting_labels')
    for rows in by_pair.values():
        if len(rows) != 2 or {r['label'] for r in rows} != {0, 1}:
            raise ValueError('Expected a complete reference/unsafe pair.')
        reasons = sorted({reason for r in rows for reason in r['exclusion_reasons']})
        for r in rows:
            r['pair_exclusion_reasons'] = reasons
            r['eligible'] = not reasons


def write_model_csv(path, records, model):
    base = ['sample_id', 'processed_func', 'target', 'flaw_line', 'flaw_line_index'] if model == 'linevul' else ['sample_id', 'func', 'label']
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=base + METADATA, lineterminator='\n')
        writer.writeheader()
        for r in records:
            row = {'sample_id': r['sample_id'], **{k: r[k] for k in METADATA}}
            if model == 'linevul':
                row.update(processed_func=r['code'], target=r['label'], flaw_line='', flaw_line_index='')
            else:
                row.update(func=r['code'], label=r['label'])
            writer.writerow(row)


def verify_exports(output, selected):
    import pandas as pd
    sys_path = str(ROOT / 'localScripts')
    import sys
    sys.path.insert(0, sys_path)
    from pivd_local import validate_frame
    for model, code_col, label_col in [('linevul', 'processed_func', 'target'), ('vulberta', 'func', 'label')]:
        path = output / model / 'cweval_test.csv'
        frame = pd.read_csv(path)
        validate_frame(frame, model)
        if frame.sample_id.tolist() != [r['sample_id'] for r in selected] or not frame.sample_id.is_unique:
            raise ValueError('Export IDs/order changed.')
        if frame[code_col].tolist() != [r['code'] for r in selected] or frame[label_col].tolist() != [r['label'] for r in selected]:
            raise ValueError('Export code/labels changed.')
        if model == 'linevul' and not frame[['flaw_line', 'flaw_line_index']].isna().all().all():
            raise ValueError('Unexpected localization annotations.')


def write_readme(path, summary):
    subset_rows = '\n'.join(f'| {name} | {info["tasks"]} | {info["tasks"] * 2} | '
                            f'{summary["selected_subsets"].get(name.split("-00000")[0], 0)} |'
                            for name, info in summary['source_files'].items())
    exclusions = '\n'.join(f'| `{reason}` | {count} |'
                           for reason, count in summary['pair_exclusion_counts'].items())
    text = f'''# CWEval static-model evaluation bundle

Generated by `prepare_cweval_datasets.py` from every Parquet file in `CWEval/`.
All {summary['input_tasks']} tasks ({summary['candidate_records']} implementations) are converted into
`catalog.jsonl`. The two model CSVs contain the same {summary['selected_records']} eligible functions
({summary['selected_pairs']} complete reference/unsafe pairs), in the same order.

| Source file | Tasks | Catalog records | Model CSV records |
| --- | ---: | ---: | ---: |
{subset_rows}

The compatible C and C++ subsets are combined as one external evaluation set.
They remain separate from PrimeVul and LLMVul. Language, source subset, CWE,
pair and related-problem group IDs are retained for stratified reporting.

## Files and labels

- `catalog.jsonl`: every candidate, original code block, extracted function,
  provenance, source matching, token counts, cleaner checks and exclusions.
- `excluded.csv`: {summary['excluded_records']} excluded records, with each variant's own reasons and
  the union of reasons that excludes its entire pair.
- `manifest.json`: input/output hashes, pinned source and tokenizer revisions,
  software versions, selection counts and protocol identity.
- `../linevul/cweval_test.csv`: `sample_id`, `processed_func`, `target`, blank
  `flaw_line` and `flaw_line_index`, plus metadata. Function classification only.
- `../vulberta/cweval_test.csv`: `sample_id`, `func`, `label`, plus metadata.
- `UPSTREAM_LICENSE`: CWEval's Apache 2.0 license.

`completion` receives label **0** (upstream reference implementation);
`y_negative` receives label **1** (upstream intentionally unsafe implementation).
These labels are supported by comparing parsed function tokens to the official
`_task` and `_unsafe` sources, not by inferring safety from the field names.
All {summary['candidate_records']} target functions match. Reference means the benchmark's intended
solution for its specified CWE; it does not prove absence of every vulnerability.
No benchmark security tests or model inference were run during conversion.
These are benchmark implementations, not verified LLM-generated samples.

## Extraction and selection

The upstream `BEGIN SOLUTION` marker identifies the target function. C/C++ syntax
trees extract that function and remove comments, including label-bearing hints,
without treating strings as comments. Prompts, includes, surrounding helper
definitions and `main()` harnesses are not model input. Blank annotation lines
and trailing whitespace are removed; lexical token equality is checked.
Original snippets remain in the catalog.

Both variants must match upstream, parse, and have no detected dependence on
omitted local helpers, macros, types or globals. Context detection is conservative;
it is not a compiler/linker check, and standard or external library APIs remain.
Both variants must also survive the **existing** VulBERTa regex cleaner without
lexical changes, and fit LineVul's 512-token and VulBERTa's 1,024-token limits,
including special tokens. Identical functions with opposing labels are excluded.
The model implementations and preprocessing rules are unchanged. VulBERTa's
unknown-token counts are recorded, but unknown tokens do not trigger exclusion.

| Pair exclusion reason | Pairs affected |
| --- | ---: |
{exclusions}

Reasons overlap. An otherwise eligible variant is also excluded when its partner
fails a check, preserving label balance and a common comparison set for both
models. The selected set contains {len(summary['selected_cwes'])} CWEs and
{summary['selected_groups']} related-problem groups. It is a filtered diagnostic evaluation,
not a representative score for all CWEval tasks or for LLM-generated code.

Both variants, C/C++ counterparts and token-identical functions share `group_id`.
No train/validation split is created. Preserve these groups in any future split
or uncertainty analysis; rows are not independent observations. Report language
and CWE breakdowns alongside pooled metrics where sample size permits. Join
predictions back to the input CSV by `sample_id` to retrieve this metadata.
Cross-dataset overlap with PrimeVul/LLMVul or model pretraining was not audited.

## Reproduce and run

Run these commands from the repository root using the existing local environment:

```powershell
.\\localScripts\\.venv\\Scripts\\python.exe -m pip install -r .\\localScripts\\requirements-cweval.txt
# Rebuild using the supplied sources and tokenizer snapshots:
.\\localScripts\\.venv\\Scripts\\python.exe .\\localScripts\\prepare_cweval_datasets.py --output-root .\\reproductions\\cweval_rebuild\\prepared_datasets
# Stage tokenizer references for the inference runner:
New-Item -ItemType Directory -Force .\\localScripts\\.cache\\huggingface\\hub | Out-Null
Copy-Item -Path .\\localScripts\\upstream\\huggingface\\models--* -Destination .\\localScripts\\.cache\\huggingface\\hub -Recurse -Force
# Run the prepared common cohort on both frozen models:
.\\localScripts\\.venv\\Scripts\\python.exe .\\localScripts\\pivd_local.py --jobs cweval --device cuda --data-root .\\reproductions\\cweval_rebuild --run-dir .\\localScripts\\results\\rq1_cweval_rebuild
# Conversion and runner regression checks:
.\\localScripts\\.venv\\Scripts\\python.exe -m unittest discover -s localScripts -p 'test_cweval.py' -v
```

Use a fresh `--output-root` for every rebuild. Existing outputs are never silently
overwritten. `--source-dir` and `--cache-dir` can override input/cache paths.
`--fetch-upstream` downloads only missing source/license files at the locked
revision, verifies Git blob hashes, and caches them. Without it conversion is
offline using the supplied upstream snapshot or cache. New tasks need reviewed entries
in `localScripts/cweval_upstream_lock.json`; unverified labels fail conversion.

The converter requires the existing runtime dependencies plus the separate
conversion requirements. It loads tokenizer assets only, not model weights.
The pinned CodeBERT and VulBERTa tokenizer snapshots are read from the runtime cache
or `localScripts/upstream/huggingface/`; their revisions and hashes are in the
manifest. Missing assets produce an explicit error. The evaluation runner checks
the CSV, tokenizer assets and preprocessing against the audit before inference,
and uses the audited local CodeBERT tokenizer snapshot. CWEval is not in the
legacy `prepared_datasets.zip`; its manifest is independent of that archive.

## Attribution and changes

Derived from [CWEval](https://github.com/{summary['upstream_repository']}/tree/{summary['upstream_revision']}),
revision `{summary['upstream_revision']}`. See `UPSTREAM_LICENSE`.
This repository's conversion extracts functions, removes comments and surrounding
code, adds labels/metadata and applies the documented pair filters. Original
Parquet files are unchanged. The catalog preserves original code for inspection.
'''
    path.write_text(text, encoding='utf-8', newline='\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, default=ROOT / 'datasets/raw/CWEval')
    parser.add_argument('--output-root', type=Path, default=ROOT / 'reproductions/cweval/prepared_datasets')
    parser.add_argument('--cache-dir', type=Path, default=ROOT / 'localScripts/.cache')
    parser.add_argument('--fetch-upstream', action='store_true', help='Download only missing, hash-pinned upstream source files.')
    args = parser.parse_args()
    import pyarrow.parquet as pq
    from tree_sitter import Language, Parser
    import tree_sitter_c
    import tree_sitter_cpp
    parsers = {'c': Parser(Language(tree_sitter_c.language())), 'cpp': Parser(Language(tree_sitter_cpp.language()))}
    lock = json.loads(UPSTREAM_LOCK.read_text(encoding='utf-8'))
    upstream_cache = args.cache_dir / 'CWEval' / lock['revision']
    files = sorted(args.source_dir.glob('*.parquet'))
    if not files:
        raise ValueError('No source Parquet files found.')
    owned = [args.output_root / 'cweval', args.output_root / 'linevul/cweval_test.csv',
             args.output_root / 'vulberta/cweval_test.csv']
    if any(p.exists() for p in owned):
        raise FileExistsError('CWEval outputs already exist. Use a fresh --output-root for a reproducible rebuild.')
    upstream_license = checked_upstream('LICENSE', lock, upstream_cache, args.fetch_upstream)
    auditor = TokenAudit(args.cache_dir)
    records, source_info, upstream_evidence = [], {}, {}
    seen_ids = set()
    for path in files:
        rows = pq.read_table(path).to_pylist()
        source_info[path.name] = {'sha256': sha(path.read_bytes()), 'tasks': len(rows)}
        for ordinal, row in enumerate(rows, 1):
            match = re.fullmatch(r'CWEval_(core|lang)_(c|cpp)_(cwe_\d+_\d+_(?:c|cpp))', row['task_id'])
            if not match or match[3] != row['id'] or not row['id'].endswith('_' + match[2]):
                raise ValueError(f'Unrecognized task identity: {row.get("task_id")}')
            partition, language, task = match.groups()
            if row['task_id'] in seen_ids or int(task.split('_')[1]) != row['CWE_ID']:
                raise ValueError(f'Duplicate identity or inconsistent CWE: {task}')
            seen_ids.add(row['task_id'])
            syntax = parsers[language]
            ref_paths = {v: f'benchmark/{partition}/{language}/{task}_{suffix}.{language}'
                         for v, suffix in [('completion', 'task'), ('y_negative', 'unsafe')]}
            upstream = {v: checked_upstream(p, lock, upstream_cache, args.fetch_upstream) for v, p in ref_paths.items()}
            upstream_trees = {v: syntax.parse(data) for v, data in upstream.items()}
            target = reference_target(upstream_trees['completion'])
            messages = row['completion']
            if len(messages) != 1 or messages[0]['role'] != 'assistant':
                raise ValueError(f'Ambiguous completion messages for {task}')
            for variant, payload, label in [('completion', messages[0]['content'], 0), ('y_negative', row['y_negative'], 1)]:
                block = extract_block(payload)
                tree = syntax.parse(block.encode('utf-8'))
                funcs = functions(tree)
                reference = functions(upstream_trees[variant])
                if target not in funcs or target not in reference:
                    raise ValueError(f'Cannot locate upstream target {target} in {task}/{variant}.')
                node = funcs[target]
                code = remove_comments(node)
                extracted = syntax.parse(code.encode('utf-8'))
                if lexical_tokens(node) != lexical_tokens(extracted.root_node):
                    raise ValueError(f'Comment removal changed code tokens: {task}/{variant}')
                matched = lexical_tokens(node) == lexical_tokens(reference[target])
                context = referenced_context(tree, target)
                # Check supplied helpers too: the target label cannot vouch for altered helper code.
                helper_matches = {name: name in reference and lexical_tokens(fn) == lexical_tokens(reference[name])
                                  for name, fn in funcs.items() if name not in (target, 'main')}
                checks = auditor.inspect(code, syntax)
                reasons = []
                if not matched or not all(helper_matches.values()): reasons.append('upstream_code_mismatch')
                if node.has_error or extracted.root_node.has_error: reasons.append('function_parse_error')
                if context: reasons.append('requires_local_context')
                if not checks['vulberta_cleaner_preserves_lexical_tokens']: reasons.append('vulberta_cleaner_changes_code')
                if checks['linevul_would_truncate']: reasons.append('linevul_truncation')
                if checks['vulberta_would_truncate']: reasons.append('vulberta_truncation')
                record = {'sample_id': f'cweval:{task}:{variant}', 'pair_id': row['task_id'],
                          'problem_id': task.rsplit('_', 1)[0], 'source_subset': f'{partition}_{language}',
                          'source_file': path.name, 'source_row': ordinal, 'language': language,
                          'cwe_id': row['CWE_ID'], 'variant': variant, 'label': label,
                          'label_basis': 'upstream_reference' if label == 0 else 'upstream_unsafe',
                          'code_provenance': 'benchmark_implementation_not_verified_llm_generation',
                          'target_function': target, 'original_code_block': block,
                          'original_function': node.text.decode('utf-8'), 'code': code,
                          'code_sha256': sha(code.encode('utf-8')),
                          'function_token_sha256': sha(json.dumps(lexical_tokens(node), ensure_ascii=False).encode()),
                          'upstream_path': ref_paths[variant], 'upstream_target_tokens_match': matched,
                          'upstream_helpers_match': helper_matches, 'local_context_dependencies': context,
                          'original_has_main': 'main' in funcs, 'exclusion_reasons': reasons, **checks}
                records.append(record)
                upstream_evidence[ref_paths[variant]] = {'git_blob_sha1': lock['files'][ref_paths[variant]],
                                                         'sha256': sha(upstream[variant])}
            print(f'Audited {task}', flush=True)
    records.sort(key=lambda r: r['sample_id'])
    assign_groups(records)
    apply_selection(records)
    selected = [r for r in records if r['eligible']]
    if not selected:
        raise ValueError('No complete pairs are eligible; inspect the source/protocol before exporting.')
    if any(sha(path.read_bytes()) != source_info[path.name]['sha256'] for path in files):
        raise ValueError('Source files changed during conversion.')
    output = args.output_root
    audit_dir = output / 'cweval'
    audit_dir.mkdir(parents=True, exist_ok=False)
    (audit_dir / 'UPSTREAM_LICENSE').write_bytes(upstream_license)
    with (audit_dir / 'catalog.jsonl').open('w', encoding='utf-8', newline='') as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + '\n')
    with (audit_dir / 'excluded.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['sample_id', 'pair_id', 'variant', 'own_reasons', 'pair_reasons', 'context'], lineterminator='\n')
        writer.writeheader()
        for r in records:
            if not r['eligible']:
                writer.writerow({'sample_id': r['sample_id'], 'pair_id': r['pair_id'], 'variant': r['variant'],
                                 'own_reasons': ';'.join(r['exclusion_reasons']),
                                 'pair_reasons': ';'.join(r['pair_exclusion_reasons']),
                                 'context': ';'.join(r['local_context_dependencies'])})
    for model in ('linevul', 'vulberta'):
        write_model_csv(output / model / 'cweval_test.csv', selected, model)
    verify_exports(output, selected)
    summary = {'protocol': PROTOCOL, 'source_files': source_info, 'input_tasks': len(seen_ids),
               'candidate_records': len(records), 'selected_records': len(selected),
               'selected_pairs': len(selected) // 2, 'excluded_records': len(records) - len(selected),
               'candidate_cwes': sorted({r['cwe_id'] for r in records}),
               'selected_cwes': sorted({r['cwe_id'] for r in selected}),
               'selected_label_counts': dict(Counter(r['label'] for r in selected)),
               'selected_subsets': dict(Counter(r['source_subset'] for r in selected)),
               'candidate_groups': len({r['group_id'] for r in records}),
               'selected_groups': len({r['group_id'] for r in selected}),
               'pair_exclusion_counts': dict(Counter(reason for r in records if r['variant'] == 'completion' for reason in r['pair_exclusion_reasons'])),
               'all_target_token_matches': all(r['upstream_target_tokens_match'] for r in records),
               'upstream_repository': lock['repository'], 'upstream_revision': lock['revision'],
               'upstream_license_sha256': sha(upstream_license),
               'upstream_files': upstream_evidence, 'tokenizer_audit': auditor.identity,
               'converter_sha256': sha(Path(__file__).read_bytes()),
               'upstream_lock_sha256': sha(UPSTREAM_LOCK.read_bytes()),
               'packages': {p: version(p) for p in ('pyarrow', 'tree-sitter', 'tree-sitter-c', 'tree-sitter-cpp', 'transformers', 'tokenizers', 'libclang')},
               'labels_verified_against_source': True, 'security_tests_executed': False,
               'original_source_files_unchanged': True,
               'selection': 'Both variants retained only when source-matched, standalone, token-preserving under existing VulBERTa cleaning, and untruncated by both models. Not a representative full-benchmark score.',
               'split_policy': 'External evaluation only. No training split. Group C/C++ counterparts, both variants, and token-identical functions together for any future split.',
               'label_scope': 'Benchmark reference versus intentionally unsafe implementation for the task CWE; reference is not a guarantee of universal vulnerability freedom.'}
    write_readme(audit_dir / 'README.md', summary)
    summary['output_sha256'] = {str(p.relative_to(output)).replace('\\', '/'): sha(p.read_bytes())
                               for p in [audit_dir / 'catalog.jsonl', audit_dir / 'excluded.csv',
                                         audit_dir / 'README.md', audit_dir / 'UPSTREAM_LICENSE',
                                         output / 'linevul/cweval_test.csv', output / 'vulberta/cweval_test.csv']}
    write_json(audit_dir / 'manifest.json', summary)
    print(json.dumps({k: summary[k] for k in ('input_tasks', 'candidate_records', 'selected_records', 'excluded_records', 'selected_subsets', 'pair_exclusion_counts')}, indent=2))


if __name__ == '__main__':
    main()
