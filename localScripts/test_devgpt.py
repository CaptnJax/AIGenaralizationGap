"""Offline regression checks for snapshot isolation, extraction and weak labels."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import prepare_devgpt_datasets as prep
import pivd_local as runner
from tree_sitter import Language, Parser
import tree_sitter_c
import tree_sitter_cpp


class DevGPTTests(unittest.TestCase):
    def setUp(self):
        self.c = Parser(Language(tree_sitter_c.language()))
        self.cpp = Parser(Language(tree_sitter_cpp.language()))

    def block(self, code, language='c'):
        return {'block_id': 'b', 'code': code, 'language': language}

    def test_latest_snapshot_only_and_incomplete_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old = root / 'snapshot_20231012'
            new = root / 'snapshot_20240514'
            old.mkdir()
            new.mkdir()
            for kind in ('pr', 'issue', 'discussion', 'commit', 'file', 'hn'):
                (new / f'20240515_000000_{kind}_sharings.json').write_text('{"Sources": []}')
            self.assertEqual(prep.latest_snapshot(root)[0], new)
            (root / 'snapshot_20250101').mkdir()
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                prep.latest_snapshot(root)

    def test_language_comes_from_code_block_and_occurrences_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'file.json'
            source = {'RepoLanguage': 'C++', 'ChatgptSharing': [{'Conversations': [
                {'ListOfCode': [{'Type': None, 'Content': 'int f(){return 0;}'},
                                {'Type': 'python', 'Content': 'print(1)'},
                                {'Type': 'cpp', 'Content': 'int f(){return 0;}'}]}]}]}
            path.write_text(json.dumps({'Sources': [source, source]}))
            blocks, counts, _ = prep.collect_blocks([path])
            self.assertEqual(len(blocks), 1)
            self.assertEqual(len(blocks[0]['occurrences']), 2)
            self.assertEqual(counts['c_cpp_tagged_block_occurrences'], 2)

    def test_comments_removed_without_changing_string_literals(self):
        code = 'int f() { /* vulnerable hint */ const char *s="https://host/*x*/"; return 0; }'
        functions, reasons = prep.extract_functions(self.block(code), self.c)
        self.assertFalse(reasons)
        self.assertEqual(len(functions), 1)
        self.assertNotIn('vulnerable hint', functions[0]['code'])
        self.assertIn('"https://host/*x*/"', functions[0]['code'])
        bounds = functions[0]['source']
        raw = code.encode()[bounds['start_byte']:bounds['end_byte']]
        self.assertEqual(prep.sha(raw), bounds['raw_function_sha256'])

    def test_incomplete_fragments_placeholders_and_class_methods_excluded(self):
        for code in ('int f(){', 'int x = 1;', 'int f(){ /* TODO */ return 0;}'):
            functions, reasons = prep.extract_functions(self.block(code), self.c)
            self.assertFalse(functions)
            self.assertTrue(reasons)
        functions, reasons = prep.extract_functions(self.block('class C { int f(){return 0;} };', 'cpp'), self.cpp)
        self.assertFalse(functions)
        self.assertIn('function_requires_enclosing_scope', reasons)

    def test_template_header_preserved(self):
        code = 'template<typename T> T identity(T value) { return value; }'
        functions, reasons = prep.extract_functions(self.block(code, 'cpp'), self.cpp)
        self.assertFalse(reasons)
        self.assertEqual(functions[0]['code'], code)

    def test_label_policy_never_turns_low_risk_into_safe(self):
        self.assertEqual(prep.weak_label([])[0], 0)
        for level in (1, 2):
            self.assertIsNone(prep.weak_label([{'Level': str(level)}])[0])
        for level in (3, 4, 5):
            self.assertEqual(prep.weak_label([{'Level': str(level)}])[0], 1)

    def test_real_analyzer_and_model_exports(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / 'audit').mkdir()
            codes = ['int f(){return 0;}', 'void f(char *s){char b[8]; gets(b); /* flawfinder: ignore */}']
            rows = [{'sample_id': 'devgpt-weak:' + prep.sha(code.encode()),
                     'code_sha256': prep.sha(code.encode()), 'language': 'c', 'code': code} for code in codes]
            result = prep.scan_functions(rows, output)
            self.assertEqual(result['scanned_files'], 2)
            self.assertEqual([r['weak_label'] for r in rows], [0, 1])
            self.assertTrue(all(r['label_status'] == 'weak_unverified' for r in rows))
            self.assertTrue(rows[1]['findings'])
            prep.export_models(output, rows)

    def test_runner_opt_in_and_missing_bundle(self):
        self.assertEqual(runner.resolve_jobs(['devgpt']), ['linevul-devgpt', 'vulberta-devgpt'])
        self.assertNotIn('linevul-devgpt', runner.resolve_jobs(['all']))
        self.assertEqual(runner.prepared_relative('linevul', 'devgpt_weak_test').as_posix(),
                         'prepared_datasets/devgpt/linevul/devgpt_weak_test.csv')
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(FileNotFoundError, 'DevGPT'):
                runner.ensure_prepared(Path(directory), ['linevul-devgpt'])

    def test_runner_rejects_changed_dataset_or_tokenizer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / 'prepared_datasets/devgpt'
            (bundle / 'linevul').mkdir(parents=True)
            dataset = bundle / 'linevul/devgpt_weak_test.csv'
            dataset.write_text('sample_id,processed_func,target\nx,int f(){return 0;},0\n')
            cache = root / 'cache'
            asset = cache / 'huggingface/hub/tokenizer.json'
            asset.parent.mkdir(parents=True)
            asset.write_text('{}')
            manifest = {'protocol': prep.PROTOCOL, 'status': 'complete',
                        'label_status': 'weak_unverified', 'analyzer': {'name': 'Flawfinder'},
                        'output_sha256': {'linevul/devgpt_weak_test.csv': runner.sha(dataset)},
                        'tokenizers': {'preprocessing_sha256': prep.sha(
                            (runner.HERE / 'vulberta_eval.py').read_text(encoding='utf-8').encode()),
                            'assets_sha256': {'tokenizer.json': runner.sha(asset)},
                            'linevul_revision': 'test'}}
            prep.write_json(bundle / 'manifest.json', manifest)
            identity, _ = runner.validate_devgpt_bundle(root, cache, dataset)
            self.assertEqual(identity['label_status'], 'weak_unverified')
            asset.write_text('{"changed": true}')
            with self.assertRaisesRegex(ValueError, 'tokenizer asset'):
                runner.validate_devgpt_bundle(root, cache, dataset)
            dataset.write_text('tampered')
            with self.assertRaisesRegex(ValueError, 'CSV differs'):
                runner.validate_devgpt_bundle(root, cache, dataset)


if __name__ == '__main__':
    unittest.main()
