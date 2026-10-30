import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from memory_lab.evaluate import benchmark, score, CASES, MESSAGES

class EvaluationTests(unittest.TestCase):
    def test_truncated_fact_not_credited(self):
        result = score([{'source_id': 1, 'text': 'Beginning'}], {1: 'Correction'})
        self.assertEqual(result['source_recall'], 1)
        self.assertEqual(result['excerpt_recall'], 0)
        self.assertEqual(result['missing_excerpt_ids'], [1])

    def test_partial_recall_precision(self):
        result = score([{'source_id': 1, 'text': 'yes'}, {'source_id': 3, 'text': 'noise'}], {1: 'yes', 2: 'other'})
        self.assertEqual(result['source_recall'], .5)
        self.assertEqual(result['source_precision'], .5)
        self.assertEqual(result['missing_source_ids'], [2])

    def test_empty_selection(self):
        result = score([], {1: 'fact'})
        self.assertEqual(result['excerpt_recall'], 0)
        self.assertEqual(result['source_precision'], 0)

    def test_invalid_labels(self):
        for labels in ({}, {1: ''}, {'1': 'fact'}):
            with self.assertRaises(ValueError): score([], labels)

    def test_fixture_labels_exist(self):
        sources = {m['id']: m['text'] for m in MESSAGES}
        for case in CASES:
            for key, excerpt in case['expected'].items():
                self.assertIn(excerpt, sources[key])

    def test_repeatable_equal_budget_and_macro_mean(self):
        report = benchmark(450)
        self.assertEqual(report, benchmark(450))
        self.assertEqual(len(report['cases']), 20)
        for row in report['cases']:
            self.assertLessEqual(row['characters'], 450)
        for summary in report['summary']:
            rows = [r for r in report['cases'] if r['method'] == summary['method']]
            self.assertEqual(summary['excerpt_recall'], sum(r['excerpt_recall'] for r in rows)/5)

    def test_minimum_budget(self):
        self.assertTrue(all(r['excerpt_recall'] == 0 for r in benchmark(2)['cases']))

    def test_cli_json_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'report.json'
            command = [sys.executable, '-m', 'memory_lab.evaluate', '--output', str(path)]
            subprocess.run(command, check=True, capture_output=True)
            original = path.read_bytes()
            self.assertEqual(json.loads(original)['case_count'], 5)
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual(path.read_bytes(), original)
