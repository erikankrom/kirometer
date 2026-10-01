import asyncio
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import time
import types
import unittest

ROOT = Path(__file__).parent / 'crew-app'
spec = importlib.util.spec_from_file_location('kirometer_test_backend', ROOT / 'backend/__init__.py', submodule_search_locations=[str(ROOT / 'backend')])
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
spec.loader.exec_module(package)
from kirometer_test_backend import runtime as collector

class CrewCollectorTests(unittest.IsolatedAsyncioTestCase):
    def fixture(self, used=625, limit=500):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        path = Path(temp.name) / 'state.vscdb'
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE ItemTable(key TEXT, value TEXT)')
            db.execute('INSERT INTO ItemTable VALUES(?, ?)', ('kiro.kiroAgent', json.dumps({'kiro.resourceNotifications.usageState': {'timestamp': time.time()*1000, 'usageBreakdowns': [{'type':'CREDIT','currentUsage':used,'usageLimit':limit}]}})))
        return {'db_path': str(path)}

    def test_overage_and_read_only(self):
        config = self.fixture()
        before = Path(config['db_path']).read_bytes()
        data = collector.collect(config)
        self.assertEqual(data['credits'][0]['overage_used'],125)
        self.assertEqual(data['credits'][0]['remaining_plan_credits'],0)
        self.assertFalse(data['stale'])
        self.assertEqual(data['activity'],'unknown')
        self.assertEqual(Path(config['db_path']).read_bytes(),before)

    def test_missing_never_reports_zero(self):
        data = collector.collect({'db_path':'/nonexistent/kirometer-test.db'})
        self.assertFalse(data['available'])
        self.assertEqual(data['credits'],[])
        self.assertTrue(data['stale'])

    def test_nonfinite_data_is_unknown(self):
        data = collector.collect(self.fixture(float('nan')))
        self.assertIsNone(data['credits'][0]['used'])
        self.assertIsNone(data['credits'][0]['overage_used'])

    async def test_start_stop_and_repeat_enable(self):
        ctx = types.SimpleNamespace(config=self.fixture())
        await collector.on_startup(ctx)
        first = collector._task
        await collector.on_startup(ctx)
        self.assertTrue(first.cancelled())
        self.assertIsNotNone(collector._snapshot)
        await collector.on_shutdown(ctx)
        self.assertIsNone(collector._task)
        self.assertIsNone(collector._snapshot)

class CrewBillingTests(unittest.TestCase):
    def test_crew_total_credits_and_freshness(self):
        d=collector.normalize_crew({'credits_used':625,'credits_plan':500,'plan':'KIRO PRO'},990,1000)
        self.assertEqual(d['credits'][0]['overage_used'],125)
        self.assertFalse(d['stale'])
        self.assertTrue(collector.normalize_crew({'credits_used':1,'credits_plan':500,'stale':True},990,1000)['stale'])
        self.assertIsNone(collector.normalize_crew({'credits_used':float('inf'),'credits_plan':500},990,1000))

class ActivityTests(unittest.TestCase):
    def test_activity_priority_and_completion(self):
        from kirometer_test_backend.activity import ActivityTracker
        t=ActivityTracker()
        self.assertEqual(t.classify([],0),'idle')
        self.assertEqual(t.classify(['running'],1),'working')
        self.assertEqual(t.classify(['running','waiting_permission'],2),'attention')
        self.assertEqual(t.classify(['stalled'],3),'error')
        self.assertEqual(t.classify([],4),'complete')
        self.assertEqual(t.classify([],13),'idle')
        self.assertEqual(t.classify(None,14),'unknown')
        self.assertEqual(t.classify([],15,children=1),'working')

    def test_missing_runtime_is_unknown(self):
        from kirometer_test_backend.activity import ActivityTracker
        self.assertFalse(ActivityTracker().read(None)['activity_available'])

class ActivityBindingTests(unittest.TestCase):
    def test_device_request_can_bind_activity_without_usage_page(self):
        from unittest.mock import patch
        state=object()
        with patch.object(collector,'_snapshot',{}),patch.object(collector,'_activity_state',None),patch.object(collector._activity_tracker,'read',return_value={'activity':'working'}) as read:
            collector.bind_activity_state(state)
            self.assertIs(collector._activity_state,state)
            self.assertEqual(collector._snapshot['activity'],'working')
            read.assert_called_with(state)
            collector.bind_activity_state(None)
            self.assertIs(collector._activity_state,state)
