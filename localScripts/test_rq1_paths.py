"""Path relocation must preserve input identity and explicit output destinations."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import rq1_paths as paths
import rq1_priority1_audit as audit


class PublicPaths(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name, value in {
            'ROOT': self.root, 'HERE': self.root/'localScripts',
            'RAW': self.root/'datasets/raw', 'PRUNED': self.root/'datasets/pruned',
            'DIAGNOSTICS': self.root/'results/diagnostics',
        }.items():
            context = patch.object(paths, name, value)
            context.start()
            self.addCleanup(context.stop)
        context = patch.object(audit, 'ROOT', self.root)
        context.start()
        self.addCleanup(context.stop)
        audit.sha.cache_clear()

    def test_manifest_inputs_and_relocated_controls(self):
        pairs = {
            'prepared_datasets/linevul/primevul_test.csv': 'datasets/pruned/linevul/primevul_test.csv',
            'primevul_test.jsonl': 'datasets/raw/PrimeVul/primevul_test.jsonl',
            'LLMVul_v3-Updated.csv': 'datasets/raw/LLMVul/LLMVul_v3-Updated.csv',
            'localScripts/results/20261009_203942_809681/summary.csv':
                'results/evaluation_runs/20261009_203942_809681/summary.csv',
            'localScripts/results/rq1_priority2_20261028/joined_inputs.csv':
                'results/diagnostics/input_preprocessing/rq1_priority2_20261028/joined_inputs.csv',
            'localScripts/reports/rq1_priority1_summary.json':
                'results/diagnostics/evaluation_validation/rq1_priority1_summary.json',
            'localScripts/reports/rq1_results.md':
                'results/diagnostics/evaluation_validation/rq1_priority1_20261028_verified/evidence/32267dccb7e2_rq1_results.md',
            'localScripts/.cache/data/bigvul_test.csv': 'datasets/raw/BigVul/bigvul_test.csv',
            'localScripts/.cache/data/bigvul_test_sample_2000.csv': 'datasets/pruned/BigVul/bigvul_test_sample_2000.csv',
            'localScripts/results/rq1_priority5_20261031/inputs/devign_test.jsonl':
                'datasets/pruned/controls/devign_test.jsonl',
            'localScripts/results/rq1_priority5_20261031/sources/Devign.json':
                'datasets/raw/Devign/Devign.json',
        }
        for old, new in pairs.items():
            with self.subTest(old=old):
                self.assertEqual(paths.input_path(self.root/old), self.root/new)

    def test_legacy_report_reads_captured_bytes_after_consolidation(self):
        legacy = self.root/'localScripts/reports/rq1_results.md'
        captured = paths.input_path(legacy)
        captured.parent.mkdir(parents=True)
        captured.write_bytes(b'original baseline')
        current = self.root/'results/findings/rq1_answer.md'
        current.parent.mkdir(parents=True)
        current.write_bytes(b'consolidated findings')
        self.assertEqual(audit.sha(legacy), hashlib.sha256(b'original baseline').hexdigest())
        self.assertNotEqual(audit.sha(legacy), audit.sha(current))

    def test_existing_and_external_inputs_are_not_substituted(self):
        path = self.root/'primevul_test.jsonl'
        path.write_text('different bytes', encoding='utf-8')
        self.assertEqual(paths.input_path(path), path)
        self.assertEqual(audit.sha(path), hashlib.sha256(path.read_bytes()).hexdigest())
        outside = self.root.parent/'external/primevul_test.jsonl'
        self.assertEqual(paths.input_path(outside), outside)

    def test_bundled_assets_do_not_invent_missing_weights(self):
        source = self.root/'localScripts/upstream/LineVul/linevul/linevul_model.py'
        source.parent.mkdir(parents=True)
        source.write_text('# reference', encoding='utf-8')
        legacy = self.root/'localScripts/.cache/LineVul/linevul/linevul_model.py'
        self.assertEqual(paths.input_path(legacy), source)
        missing = legacy.parent/'saved_models/checkpoint-best-f1/model.bin'
        self.assertEqual(paths.input_path(missing), missing)

    def test_writes_stay_at_explicit_destination(self):
        path = self.root/'localScripts/reports/rq1_priority1_summary.json'
        path.parent.mkdir(parents=True)
        audit.write_json(path, {'new': True})
        self.assertTrue(path.is_file())
        self.assertFalse((self.root/'results/diagnostics/evaluation_validation/rq1_priority1_summary.json').exists())

    def test_captured_source_requires_the_complete_hash(self):
        current = self.root/'runner.py'
        current.write_bytes(b'updated implementation')
        original = b'original implementation'
        wanted = hashlib.sha256(original).hexdigest()
        captured = self.root/'results/diagnostics/evaluation_validation/rq1_priority1_verified/evidence'
        captured.mkdir(parents=True)
        source = captured/(wanted[:12] + '_runner.py')
        source.write_bytes(original)
        output = self.root/'reproduction'
        (output/'evidence').mkdir(parents=True)
        found = audit.historical_source(current, wanted, output)
        self.assertEqual(found['status'], 'recovered_from_evidence')
        self.assertEqual((output/found['snapshot']).read_bytes(), original)
        source.write_bytes(b'corrupted capture')
        audit.sha.cache_clear()
        with patch.object(audit.subprocess, 'check_output', return_value=''):
            self.assertEqual(audit.historical_source(current, wanted, output)['status'], 'unavailable')


if __name__ == '__main__':
    unittest.main()
