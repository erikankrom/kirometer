import sqlite3
import tempfile
from pathlib import Path
import unittest
import json
from kirometer import normalize, read_usage


class UsageTests(unittest.TestCase):
    def test_expired_snapshot_remains_stale(self):
        result = normalize({'timestamp': 1000, 'usageBreakdowns': [{'type': 'CREDIT', 'currentUsage': 12.5, 'usageLimit': 50}]}, now=4000)
        self.assertTrue(result['stale'])
        self.assertEqual(result['credits'][0]['remaining_plan_credits'], 37.5)
        self.assertEqual(result['activity'], 'unknown')

    def test_zero_and_missing_limits_are_not_full_capacity(self):
        for limit in (0, None):
            result = normalize({'usageBreakdowns': [{'type': 'CREDIT', 'currentUsage': 0, 'usageLimit': limit}]})
            self.assertIsNone(result['credits'][0]['used_percent'])
            self.assertTrue(result['stale'])

    def test_reads_cache_without_changing_database(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.vscdb'
            with sqlite3.connect(path) as db:
                db.execute('CREATE TABLE ItemTable (key TEXT, value TEXT)')
                db.execute('INSERT INTO ItemTable VALUES (?, ?)', ('kiro.kiroAgent', json.dumps({'kiro.resourceNotifications.usageState': {'timestamp': 1000, 'usageBreakdowns': []}})))
            before = path.read_bytes()
            self.assertEqual(read_usage(path)['credits'], [])
            self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
