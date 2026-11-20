"""CWEval extraction, label-evidence, and matched-cohort regression checks."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import prepare_cweval_datasets as conversion
import pivd_local as runner
try:
    from tree_sitter import Language, Parser
    import tree_sitter_c
    import tree_sitter_cpp
    HAS_PARSERS = True
except ImportError:
    HAS_PARSERS = False


@unittest.skipUnless(HAS_PARSERS, 'Install localScripts/requirements-cweval.txt for conversion tests.')
class CWEvalTests(unittest.TestCase):
    def setUp(self):
        self.parser = Parser(Language(tree_sitter_c.language()))

    def test_extract_function_ignores_harness_and_preserves_literals(self):
        source = b'''#define SIZE 8
int helper() { return 1; }
// BEGIN PROMPT
int target() {
 // BEGIN SOLUTION -- unsafe
 const char *url = "https://example.com/*path*/";
 /* remove annotation */ return helper();
}
// BEGIN ENTRYPOINT
int main() { return target(); }
'''
        tree = self.parser.parse(source)
        self.assertEqual(conversion.reference_target(tree), 'target')
        node = conversion.functions(tree)['target']
        extracted = conversion.remove_comments(node)
        self.assertIn('"https://example.com/*path*/"', extracted)
        self.assertNotIn('unsafe', extracted)
        self.assertNotIn('main', extracted)
        self.assertNotIn('#define', extracted)
        self.assertEqual(conversion.lexical_tokens(node), conversion.lexical_tokens(self.parser.parse(extracted.encode()).root_node))
        self.assertEqual(conversion.referenced_context(tree, 'target'), ['helper_function:helper'])

    def test_macro_type_and_global_context_is_not_silently_lost(self):
        source = b'''#define LIMIT 8
typedef struct { int value; } Item;
int shared = 1;
int target(Item *p) { return p->value + LIMIT + shared; }
'''
        deps = conversion.referenced_context(self.parser.parse(source), 'target')
        self.assertEqual(set(deps), {'macro:LIMIT', 'type:Item', 'global:shared'})

    def test_cpp_raw_string_and_lambda_comment_handling(self):
        parser = Parser(Language(tree_sitter_cpp.language()))
        source = b'''int target() {
 auto text = R"tag(https://host/*x*/)tag";
 auto f = []() { return 2; }; // annotation
 return f();
}'''
        node = conversion.functions(parser.parse(source))['target']
        result = conversion.remove_comments(node)
        self.assertIn('R"tag(https://host/*x*/)tag"', result)
        self.assertEqual(conversion.lexical_tokens(node), conversion.lexical_tokens(parser.parse(result.encode()).root_node))

    def test_multiple_code_blocks_are_rejected(self):
        with self.assertRaises(ValueError):
            conversion.extract_block('<code>one</code><code>two</code>')

    def test_source_evidence_rejects_tampered_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = b'int f() { return 0; }\n'
            (root / 'ref.c').write_bytes(data)
            lock = {'files': {'ref.c': conversion.git_blob_sha(data)}}
            self.assertEqual(conversion.checked_upstream('ref.c', lock, root, False), data)
            (root / 'ref.c').write_bytes(data + b'//changed')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                conversion.checked_upstream('ref.c', lock, root, False)

    def test_pair_exclusions_and_language_duplicate_grouping(self):
        records = []
        for pair, problem in [('c', 'cwe_020_0'), ('cpp', 'cwe_020_0'), ('other', 'cwe_918_0')]:
            for label in (0, 1):
                records.append({'pair_id': pair, 'problem_id': problem, 'label': label,
                                'function_token_sha256': 'shared' if label == 0 else pair + '-unsafe',
                                'exclusion_reasons': ['requires_local_context'] if pair == 'c' and label == 0 else []})
        conversion.assign_groups(records)
        self.assertEqual(len({r['group_id'] for r in records}), 1)
        conversion.apply_selection(records)
        self.assertFalse(records[1]['eligible'])
        self.assertEqual(records[1]['exclusion_reasons'], [])
        self.assertEqual(records[1]['pair_exclusion_reasons'], ['requires_local_context'])
        self.assertTrue(records[2]['eligible'])

    def test_conflicting_identical_functions_exclude_whole_pairs(self):
        records = [{'pair_id': 'one', 'label': label, 'function_token_sha256': 'same', 'exclusion_reasons': []}
                   for label in (0, 1)]
        conversion.apply_selection(records)
        self.assertTrue(all(not r['eligible'] for r in records))
        self.assertIn('identical_function_conflicting_labels', records[0]['pair_exclusion_reasons'])

    def test_cleaner_hazard_is_observable_without_changing_runtime(self):
        clean = conversion.load_preprocessing()['clean_for_vulberta']
        original = 'const char *f() { return "https://example.com"; }'
        self.assertNotEqual(conversion.lexical_tokens(self.parser.parse(original.encode()).root_node),
                            conversion.lexical_tokens(self.parser.parse(clean(original).encode()).root_node))

    def test_missing_cweval_does_not_fall_back_to_old_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(FileNotFoundError, 'prepare_cweval_datasets.py'):
                runner.ensure_prepared(Path(directory), ['linevul-cweval'])

    def test_prepared_bundle_contract_and_tamper_guard(self):
        root = conversion.ROOT
        manifest_path = root / 'prepared_datasets/cweval/manifest.json'
        if not manifest_path.is_file():
            self.skipTest('Run the converter for the optional generated-bundle integration check.')
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        records = [json.loads(line) for line in (manifest_path.parent / 'catalog.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertEqual(len(records), manifest['candidate_records'])
        self.assertTrue(all(r['upstream_target_tokens_match'] for r in records))
        selected = [r for r in records if r['eligible']]
        self.assertEqual(len(selected), manifest['selected_records'])
        self.assertEqual({r['variant'] for r in selected}, {'completion', 'y_negative'})
        self.assertTrue(all(not r['local_context_dependencies'] and r['vulberta_cleaner_preserves_lexical_tokens']
                            and not r['linevul_would_truncate'] and not r['vulberta_would_truncate'] for r in selected))
        conversion.verify_exports(root / 'prepared_datasets', selected)
        for relative, expected in manifest['output_sha256'].items():
            self.assertEqual(conversion.sha((root / 'prepared_datasets' / relative).read_bytes()), expected)
        dataset = root / 'prepared_datasets/linevul/cweval_test.csv'
        cache = root / 'localScripts/.cache'
        if all((cache / 'huggingface/hub' / relative).is_file()
               for relative in manifest['tokenizer_audit']['assets_sha256']):
            runner.validate_cweval_bundle(root, cache, dataset)
        with tempfile.TemporaryDirectory() as directory:
            alternate = Path(directory)
            (alternate / 'prepared_datasets/cweval').mkdir(parents=True)
            conversion.write_json(alternate / 'prepared_datasets/cweval/manifest.json', manifest)
            target = alternate / 'prepared_datasets/linevul/cweval_test.csv'
            target.parent.mkdir()
            target.write_bytes(dataset.read_bytes() + b'\n')
            with self.assertRaisesRegex(ValueError, 'differs from its audited manifest'):
                runner.validate_cweval_bundle(alternate, root / 'localScripts/.cache', target)


if __name__ == '__main__':
    unittest.main()
