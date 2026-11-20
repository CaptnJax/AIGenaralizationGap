"""Audit effective RQ1 inputs and run controlled, frozen input ablations.

All results are diagnostic variants. Historical datasets/evaluators are read-only.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import difflib
import gzip
import hashlib
import json
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys
from types import SimpleNamespace

import rq1_priority1_audit as common
sys.path.insert(0, str(common.ROOT))
import prepare_cweval_datasets as cwe

os.environ.update(HF_HOME=str(common.CACHE/'huggingface'), HF_HUB_OFFLINE='1',
                  TRANSFORMERS_OFFLINE='1', USE_TF='0', TOKENIZERS_PARALLELISM='false')
STEMS = ['bigvul_test_sample_2000', 'primevul_test', 'llmvul_test', 'cweval_test']


def jsonl(path):
    with Path(path).open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle]


def digest_tokens(tokens):
    return common.code_sha(json.dumps(tokens, ensure_ascii=False))


def error_cell(label, prediction):
    return ('t' if label == prediction else 'f') + ('p' if prediction else 'n')


def metadata():
    prime = jsonl(common.ROOT/'primevul_test.jsonl')
    with (common.ROOT/'LLMVul_v3-Updated.csv').open(encoding='utf-8-sig', newline='') as handle:
        next(csv.reader(handle))
        llm = [r for r in csv.DictReader(handle) if r['ensemble_label'] != 'uncertain']
    big = common.read_csv(common.CACHE/'data/bigvul_test_sample_2000.csv')
    selected = [r for r in jsonl(common.ROOT/'prepared_datasets/cweval/catalog.jsonl') if r['eligible']]
    source = dict(zip(STEMS, [big, prime, llm, selected]))
    result = {}
    for stem in STEMS:
        result[stem] = []
        for r in source[stem]:
            result[stem].append(dict(
                source_language=r.get('language', r.get('lang')),
                project=r.get('project_name', r.get('project')),
                file_name=r.get('file_name'), cwe=r.get('cwe', r.get('cwe_id', r.get('CWE ID'))),
                cve=r.get('cve', r.get('CVE ID')), cve_desc=r.get('cve_desc', r.get('Summary')),
                commit_url=r.get('commit_url', r.get('codeLink')), group_id=r.get('group_id'),
                local_context_dependencies=r.get('local_context_dependencies'),
                flaw_line_index=r.get('flaw_line_index'), flaw_line=r.get('flaw_line')))
    return result


def load_data():
    baseline = common.read_json(common.HERE/'reports/rq1_priority1_summary.json')
    jobs, datasets = {}, {}
    for j in baseline['jobs']:
        assert common.sha(common.ROOT/j['dataset']) == j['dataset_sha256']
        assert common.sha(common.ROOT/j['prediction_file']['path']) == j['prediction_file']['sha256']
        jobs[j['job']] = j
        if j['model'] == 'linevul':
            stem = Path(j['dataset']).stem
            rows = common.read_csv(common.ROOT/j['dataset'])
            if stem.startswith('bigvul'):
                indices = common.read_json(common.CACHE/'data/bigvul_test_sample_2000.selection.json')['source_row_indices_zero_based']
                for i, row in enumerate(rows):
                    row['sample_id'] = 'bigvul-source:' + str(indices[i])
            datasets[stem] = rows
    return baseline, jobs, datasets


def parsers():
    from tree_sitter import Language, Parser
    import tree_sitter_c, tree_sitter_cpp
    return {'c': Parser(Language(tree_sitter_c.language())), 'cpp': Parser(Language(tree_sitter_cpp.language()))}


def nodes(root):
    stack = [root]
    while stack:
        node = stack.pop()
        yield node
        stack.extend(reversed(node.children))


def parse_best(code, source_language, parser_map):
    raw = code.encode('utf-8')
    language = str(source_language or '').lower()
    preferred = 'c' if language == 'c' else 'cpp'
    tree = parser_map[preferred].parse(raw)
    errors = sum(n.is_error or n.is_missing for n in nodes(tree.root_node))
    if tree.root_node.has_error:
        alternate = 'cpp' if preferred == 'c' else 'c'
        other = parser_map[alternate].parse(raw)
        other_errors = sum(n.is_error or n.is_missing for n in nodes(other.root_node))
        if other_errors < errors:
            return other, alternate, other_errors
    return tree, preferred, errors


def preserve_lexical_code(code, tree):
    """Blank only parser-identified comments; preserve newlines and token gaps."""
    raw = bytearray(code.encode('utf-8'))
    for n in nodes(tree.root_node):
        if n.type == 'comment':
            raw[n.start_byte:n.end_byte] = bytes(10 if b == 10 else 13 if b == 13 else 32
                                                for b in raw[n.start_byte:n.end_byte])
    return raw.decode('utf-8')


def lexical_clang(index, code, language='c', skip=True):
    from clang import cindex
    filename = 'tmp.cpp' if language == 'cpp' else 'tmp.c'
    tu = index.parse(filename, args=[''], unsaved_files=[(filename, code)],
                     options=cindex.TranslationUnit.PARSE_SKIP_FUNCTION_BODIES if skip else 0)
    tokens = list(tu.get_tokens(extent=tu.cursor.extent))
    spells = [t.spelling.strip() for t in tokens if t.kind != cindex.TokenKind.COMMENT and t.spelling.strip()]
    return spells


def linevul_ids(auditor, code):
    tokens = auditor.lv.tokenize(code)
    ids = auditor.lv.convert_tokens_to_ids(tokens)
    rebuilt = bytes(auditor.lv.byte_decoder[ch] for token in tokens for ch in token)
    if rebuilt != code.encode('utf-8'):
        raise ValueError('CodeBERT token bytes do not reconstruct source.')
    retained_bytes = sum(len(t) for t in tokens[:510])
    return ids, retained_bytes


def flaw_visibility(code, meta, end_byte):
    """Audit supplied BigVul annotations without treating patch lines as verified flaws."""
    indices = meta.get('flaw_line_index')
    snippets = meta.get('flaw_line')
    if not indices or not snippets:
        return dict(status='unavailable', verified_lines=0, fully_visible_lines=0, partly_or_fully_removed_lines=0)
    try:
        line_ids = [int(x) for x in indices.split(',')]
    except ValueError:
        return dict(status='invalid_indices', verified_lines=0, fully_visible_lines=0, partly_or_fully_removed_lines=0)
    parts = snippets.split('/~/')
    lines = code.splitlines(keepends=True)
    if len(parts) != len(line_ids) or any(i<0 or i>=len(lines) or lines[i].strip()!=s.strip() for i,s in zip(line_ids,parts)):
        return dict(status='annotation_text_mismatch', verified_lines=0, fully_visible_lines=0, partly_or_fully_removed_lines=0)
    ends, offset = [], 0
    for line in lines:
        ends.append(offset+len(line.rstrip('\r\n').encode('utf-8')))
        offset += len(line.encode('utf-8'))
    visible = sum(ends[i] <= end_byte for i in line_ids)
    return dict(status='source_text_matched', verified_lines=len(line_ids), fully_visible_lines=visible,
                partly_or_fully_removed_lines=len(line_ids)-visible)


def profile(output):
    from clang import cindex
    from importlib.metadata import version
    baseline, jobs, datasets = load_data()
    for a in baseline['assets']:
        assert common.sha(common.ROOT/a['path']) == a['sha256']
    directory = output/'profiles'
    directory.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, directory/'profiler.py')
    parser_map, index = parsers(), cindex.Index.create()
    auditor = cwe.TokenAudit(common.CACHE)
    meta = metadata()
    counts = Counter(common.code_sha(r['processed_func']) for rs in datasets.values() for r in rs)
    manifest = dict(status='running', script_sha256=common.sha(Path(__file__)), tokenizer_identity=auditor.identity,
                    packages={p:version(p) for p in ('tree-sitter','tree-sitter-c','tree-sitter-cpp','libclang','tokenizers')}, datasets=[])
    common.write_json(directory/'manifest.json', manifest)
    for stem, rows in datasets.items():
        print('Profiling', stem, len(rows), flush=True)
        historical = {}
        for model in ('linevul','vulberta'):
            if model+'/'+stem in jobs:
                historical[model] = common.read_csv(common.ROOT/jobs[model+'/'+stem]['prediction_file']['path'])
        totals = Counter()
        with (directory/(stem+'.jsonl')).open('w',encoding='utf-8') as dest, gzip.open(
                directory/(stem+'_lexical.jsonl.gz'),'wt',encoding='utf-8') as lexout:
            for i, r in enumerate(rows):
                code = r['processed_func']
                m = meta[stem][i]
                tree, language, error_count = parse_best(code,m['source_language'],parser_map)
                tree_nodes = list(nodes(tree.root_node))
                before = cwe.lexical_tokens(tree.root_node)
                lv_ids, end_byte = linevul_ids(auditor,code)
                nlv = len(lv_ids)
                calls = sorted({n.child_by_field_name('function').text.decode('utf-8')
                                for n in tree_nodes if n.type=='call_expression' and n.child_by_field_name('function') is not None})
                rec = dict(sample_id=r['sample_id'], row=i, dataset=stem, label=int(r['target']),
                           **m, parser_language=language, parser_error_count=error_count,
                           source_parse_error=tree.root_node.has_error, code_sha256=common.code_sha(code),
                           duplicate_group=common.code_sha(code), duplicate_group_rows=counts[common.code_sha(code)],
                           source_chars=len(code), source_bytes=len(code.encode('utf-8')),
                           source_lines=len(code.splitlines()), lexical_source_count=len(before),
                           lexical_source_sha256=digest_tokens(before),
                           function_definition_count=sum(n.type=='function_definition' for n in tree_nodes),
                           preprocessor_directives=sum(n.type.startswith('preproc_') for n in tree_nodes),
                           call_expressions=calls, source_type_references=sorted({n.text.decode('utf-8') for n in tree_nodes if n.type=='type_identifier'}),
                           context_assessment='benchmark_checked' if stem=='cweval_test' else 'function_only_context_not_verified',
                           vulnerability_span_status='unavailable' if stem!='bigvul_test_sample_2000' else 'dataset_annotation_not_independently_validated')
                pred = common.binary(historical['linevul'][i]['raw_preds'])
                rec['linevul'] = dict(tokens_including_special=nlv+2, retained_tokens_including_special=min(nlv,510)+2,
                    truncated=nlv>510, removed_code_tokens=max(0,nlv-510), truncation_fraction=max(0,nlv-510)/max(1,nlv),
                    unknown_tokens=lv_ids.count(auditor.lv.unk_token_id), unknown_fraction=lv_ids.count(auditor.lv.unk_token_id)/max(1,nlv),
                    retained_unknown_tokens=lv_ids[:510].count(auditor.lv.unk_token_id), degenerate=nlv==0,
                    retained_end_byte=end_byte, original_code_sha256=rec['code_sha256'], cleaned_code_sha256=rec['code_sha256'],
                    prediction=pred, error=error_cell(rec['label'],pred), prob_vulnerable=None,
                    annotated_line_visibility=flaw_visibility(code,m,end_byte))
                lexical_record = dict(sample_id=r['sample_id'], source=before)
                if 'vulberta' in historical:
                    cleaned = auditor.clean(code)
                    after_tree = parser_map[language].parse(cleaned.encode('utf-8'))
                    after = cwe.lexical_tokens(after_tree.root_node)
                    tree_changed = before != after
                    vb_ids = auditor.vb.encode(cleaned).ids
                    assert vb_ids[0]==0 and vb_ids[-1]==2
                    nvb = len(vb_ids)-2
                    original_clang = cleaned_clang = None
                    changed, alternate_valid, alternate_ids = False, None, None
                    if tree_changed:
                        original_clang = lexical_clang(index,code)
                        cleaned_clang = lexical_clang(index,cleaned)
                        changed = original_clang != cleaned_clang
                        alternate = preserve_lexical_code(code,tree)
                        alternate_clang = lexical_clang(index,alternate)
                        alternate_valid = original_clang == alternate_clang and bool(original_clang)
                        if alternate_valid:
                            alternate_ids = auditor.vb.encode(alternate).ids
                    pred = int(historical['vulberta'][i]['prediction'])
                    rec['vulberta'] = dict(tokens_including_special=len(vb_ids),retained_tokens_including_special=min(nvb,1022)+2,
                        truncated=nvb>1022, removed_code_tokens=max(0,nvb-1022), truncation_fraction=max(0,nvb-1022)/max(1,nvb),
                        unknown_tokens=vb_ids[1:-1].count(3), unknown_fraction=vb_ids[1:-1].count(3)/max(1,nvb),
                        retained_unknown_tokens=vb_ids[1:1023].count(3), degenerate=nvb==0,
                        cleaned_code_sha256=common.code_sha(cleaned), cleaned_chars=len(cleaned),
                        lexical_cleaned_count=len(after), lexical_cleaned_sha256=digest_tokens(after),
                        lexical_tree_changed=tree_changed, cleaner_lexical_change_confirmed=changed,
                        source_parse_error=tree.root_node.has_error, cleaned_parse_error=after_tree.root_node.has_error,
                        introduced_parse_error=not tree.root_node.has_error and after_tree.root_node.has_error,
                        preprocessor_line_structure_changed=rec['preprocessor_directives']>0 and '\n' in code and '\n' not in cleaned,
                        alternative_lexical_preservation=alternate_valid,
                        alternative_tokens_including_special=len(alternate_ids) if alternate_ids is not None else None,
                        cleaner_changes_retained_input=(vb_ids[1:1023] != alternate_ids[1:1023]) if alternate_ids is not None else None,
                        prediction=pred, error=error_cell(rec['label'],pred),prob_vulnerable=float(historical['vulberta'][i]['prob_vulnerable']),
                        vulnerability_span_visibility='unknown_without_verified_source_span')
                    lexical_record.update(cleaned=after, original_clang=original_clang, cleaned_clang=cleaned_clang)
                    totals['cleaner_lexical_change_confirmed'] += changed
                    totals['vulberta_truncated'] += nvb>1022
                dest.write(json.dumps(rec,ensure_ascii=False)+'\n')
                lexout.write(json.dumps(lexical_record,ensure_ascii=False)+'\n')
                totals['linevul_truncated'] += nlv>510
                if i%500==0:
                    dest.flush()
                    print(stem,i+1,'/',len(rows),dict(totals),flush=True)
        manifest['datasets'].append(dict(dataset=stem,rows=len(rows),counts=dict(totals),
                                         profile_sha256=common.sha(directory/(stem+'.jsonl')),
                                         lexical_sha256=common.sha(directory/(stem+'_lexical.jsonl.gz'))))
        common.write_json(directory/'manifest.json',manifest)
    manifest['status']='complete'
    common.write_json(directory/'manifest.json',manifest)
    print('Profile complete',flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['profile'])
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    profile(args.output.resolve())
