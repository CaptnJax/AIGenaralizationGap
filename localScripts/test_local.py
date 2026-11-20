"""Offline contract checks; no model weights or GPU needed."""
import ast
import contextlib
import io
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
import zipfile

import pandas as pd
import pivd_local as runner


class LocalRunnerTests(unittest.TestCase):
    def test_original_vulberta_cleaner(self):
        tree = ast.parse((runner.HERE / 'vulberta_eval.py').read_text(encoding='utf-8'))
        tree.body = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'clean_for_vulberta']
        namespace = {'re': re}
        exec(compile(tree, '<cleaner>', 'exec'), namespace)
        clean = namespace['clean_for_vulberta']
        self.assertEqual(clean('int f() { /* block\n comment */\n\treturn 0; // tail\n}'),
                         'int f() { return 0; }')
        self.assertEqual(clean('int x = a / b; /* ** stars ** */'), 'int x = a / b; ')
        self.assertEqual(clean('int f() { return 0; }'), 'int f() { return 0; }')
        # Document the upstream regex's behavior, rather than silently improving it.
        self.assertEqual(clean('char *s = "/*text*/";'), 'char *s = "";')

    def test_cached_vulberta_comment_token_regression(self):
        from tokenizers import Tokenizer, normalizers
        path = (runner.HERE / '.cache/huggingface/hub/models--claudios--VulBERTa-MLP-Devign/snapshots'
                / 'fecabdee24a3ef6e804d7629d6eed03dc6b4f61e/tokenizer.json')
        if not path.is_file():
            self.skipTest('Download the VulBERTa tokenizer with an evaluation first; tests never download it.')
        tree = ast.parse((runner.HERE / 'vulberta_eval.py').read_text(encoding='utf-8'))
        tree.body = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                     and n.name in ('clean_for_vulberta', 'fix_clang_parser')]
        namespace = {'re': re}
        exec(compile(tree, '<preprocessing>', 'exec'), namespace)
        actual, reference = Tokenizer.from_file(str(path)), Tokenizer.from_file(str(path))
        reference.normalizer = normalizers.Sequence([normalizers.StripAccents(), normalizers.Replace(' ', '\u00c4')])
        for tokenizer in (actual, reference):
            namespace['fix_clang_parser'](SimpleNamespace(_tokenizer=tokenizer))
            tokenizer.no_padding()
            tokenizer.no_truncation()
        plain = 'int f() { return 0; }'
        commented = 'int f() { /* AUDIT_COMMENT */\n\treturn 0; // tail\n}'
        self.assertNotEqual(actual.encode(commented).ids, actual.encode(plain).ids)
        cleaned = namespace['clean_for_vulberta'](commented)
        self.assertEqual(actual.encode(cleaned).ids, reference.encode(plain).ids)
        self.assertNotIn(3, actual.encode(cleaned).ids)  # No comment-introduced <unk>.
        self.assertEqual(actual.encode(cleaned).ids[0], 0)
        self.assertEqual(actual.encode(cleaned).ids[-1], 2)

    def test_job_aliases_and_dry_run_outside_repository(self):
        self.assertEqual(len(runner.resolve_jobs(['all'])), 8)
        self.assertEqual(runner.resolve_jobs(['cweval']), ['linevul-cweval', 'vulberta-cweval'])
        self.assertEqual(len(runner.resolve_jobs(['rq1', 'vulberta-llmvul'])), 4)
        with self.assertRaises(ValueError):
            runner.resolve_jobs(['typo'])
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, str(runner.HERE / 'pivd_local.py'),
                                     '--jobs', 'all', '--dry-run'], cwd=directory,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(str(runner.ROOT), result.stdout)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_extract_missing_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            relative = Path('prepared_datasets/linevul/primevul_test.csv')
            with zipfile.ZipFile(root / 'prepared_datasets.zip', 'w') as archive:
                archive.writestr(relative.as_posix(), 'target,processed_func\n1,code\n')
                archive.writestr('../outside.txt', 'must not extract')
            runner.ensure_prepared(root, ['linevul-primevul'])
            self.assertIn('1,code', (root / relative).read_text())
            (root / relative).write_text('existing data')
            runner.ensure_prepared(root, ['linevul-primevul'])
            self.assertEqual((root / relative).read_text(), 'existing data')
            self.assertEqual(len(list(root.rglob('*.csv'))), 1)

    def test_stratified_sample_reproducible_and_ordered(self):
        frame = pd.DataFrame({'target': [0] * 9000 + [1] * 1000,
                              'processed_func': [f'fn{i}' for i in range(10000)]})
        first, second = runner.sample_bigvul(frame), runner.sample_bigvul(frame)
        pd.testing.assert_frame_equal(first, second)
        self.assertEqual(len(first), 2000)
        self.assertEqual(first.target.value_counts().to_dict(), {0: 1800, 1: 200})
        self.assertTrue(first.index.is_monotonic_increasing)
        self.assertTrue(first.index.is_unique)
        pd.testing.assert_frame_equal(first, frame.loc[first.index])

    def test_data_validation_rejects_wrong_labels(self):
        frame = pd.DataFrame({'sample_id': ['a', 'b'], 'func': ['a()', 'b()'], 'label': [0, 1]})
        runner.validate_frame(frame, 'vulberta')
        frame.loc[1, 'label'] = 2
        with self.assertRaises(ValueError):
            runner.validate_frame(frame, 'vulberta')
        frame.loc[1, 'label'] = 1
        frame.loc[1, 'sample_id'] = 'a'
        with self.assertRaises(ValueError):
            runner.validate_frame(frame, 'vulberta')

    def test_linevul_patch_checks_weights_and_keeps_batch_order(self):
        source = '''# license preserved
from __future__ import annotations
def test(test_dataloader):
    seen = []
    for batch in test_dataloader:
        seen.append(batch)
    return seen
def main(model, args):
    model.load_state_dict(torch.load('weights'), strict=False)
'''
        patched = runner.patch_linevul(source)
        self.assertTrue(patched.startswith('# license preserved'))
        calls = []
        def load(path, **kwargs):
            calls.append(kwargs)
            return {'weight': 1, 'encoder.embeddings.position_ids': 2}
        class Model:
            def state_dict(self):
                return {'weight': 0}
            def load_state_dict(self, state, strict):
                if not strict or set(state) != {'weight'}:
                    raise ValueError('bad weights')
                return state
        namespace = {'tqdm': lambda rows, **kwargs: rows, 'torch': SimpleNamespace(load=load)}
        exec(patched, namespace)
        self.assertEqual(namespace['test']([1, 2, 3]), [1, 2, 3])
        with contextlib.redirect_stdout(io.StringIO()):
            namespace['main'](Model(), SimpleNamespace(device='cpu'))
        self.assertEqual(calls, [{'map_location': 'cpu', 'weights_only': True}])
        with self.assertRaises(ValueError):
            namespace['_load_local_checkpoint'](Model(), {'wrong.weight': 1})
        with self.assertRaises(RuntimeError):
            runner.patch_linevul('def test(): pass')

    def test_metrics_and_prediction_alignment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'results').mkdir()
            data = pd.DataFrame({'processed_func': ['a', 'b', 'c', 'd'], 'target': [0, 0, 1, 1]})
            dataset = root / 'data.csv'
            data.to_csv(dataset, index=False)
            raw = data.assign(raw_preds=[False, True, True, True])
            raw.to_csv(root / 'results/raw_preds.csv', index=False)
            result = runner.summarize_linevul(root, dataset)
            self.assertAlmostEqual(result['test_f1'], 0.8)
            self.assertEqual(result['confusion_matrix'], {'tn': 1, 'fp': 1, 'fn': 0, 'tp': 2})
            raw.iloc[::-1].to_csv(root / 'results/raw_preds.csv', index=False)
            with self.assertRaises(ValueError):
                runner.summarize_linevul(root, dataset)

    def test_child_error_is_logged_and_propagated(self):
        with tempfile.TemporaryDirectory(prefix='pivd space ') as directory:
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(RuntimeError):
                runner.run_logged([sys.executable, '-c', 'print("diagnostic"); raise SystemExit(3)'],
                                  Path(directory), os.environ.copy())
            self.assertIn('diagnostic', (Path(directory) / 'test.log').read_text())

    def test_vulberta_resume_rejects_mismatched_or_partial_batches(self):
        # Load only the independent progress functions, without importing ML libraries.
        tree = ast.parse((runner.HERE / 'vulberta_eval.py').read_text())
        tree.body = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                     and n.name in ('load_progress', 'save_progress')]
        namespace = {'os': os, 'json': json}
        exec(compile(tree, '<progress>', 'exec'), namespace)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'progress.json'
            signature = {'device': 'cpu', 'batch_size': 2}
            namespace['save_progress'](path, signature, [0.2, 0.7])
            self.assertEqual(namespace['load_progress'](path, signature, 5), [0.2, 0.7])
            with self.assertRaises(ValueError):
                namespace['load_progress'](path, dict(signature, device='cuda'), 5)
            with self.assertRaises(ValueError):
                namespace['load_progress'](path, dict(signature, preprocessing='original_vulberta_cleaner_v1'), 5)
            namespace['save_progress'](path, signature, [0.2])
            with self.assertRaises(ValueError):
                namespace['load_progress'](path, signature, 5)


if __name__ == '__main__':
    unittest.main()
