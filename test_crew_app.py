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
    def test_usage_age_is_independent_of_five_minute_polling(self):
        from kirometer_test_backend.usage import normalize
        cache={'credits_used':3.4,'credits_plan':1000}
        for age,stale in ((305,False),(3599,False),(3600,False),(3601,True)):
            with self.subTest(age=age):
                self.assertEqual(collector.normalize_crew(cache,10000-age,10000)['stale'],stale)
                self.assertEqual(normalize({'timestamp':(10000-age)*1000},now=10000)['stale'],stale)
        self.assertTrue(collector.normalize_crew(cache,0,10000)['stale'])
        self.assertTrue(collector.normalize_crew(cache,9990,10000,stale_after=5)['stale'])

    def test_billing_collection_uses_configured_threshold(self):
        from unittest.mock import patch
        sample=collector.normalize_crew({'credits_used':1,'credits_plan':1000},990,1000)
        with patch.object(collector,'crew_usage',return_value=sample) as read:
            collector.collect({'stale_after':7200})
            read.assert_called_once_with(stale_after=7200)

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

class IndependentCadenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_activity_wakes_delivery_without_another_usage_read(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as root:
            ctx=types.SimpleNamespace(config={},data_dir=root)
            sample={'available':True,'credits':[{'used':4,'limit':1000}],'age_seconds':10,'stale':False,'activity':'idle'}
            with patch.object(collector,'collect',return_value=sample.copy()) as reads,patch.object(collector._activity_tracker,'read',return_value={'activity':'idle'}):
                await collector.on_startup(ctx)
                try:
                    await asyncio.sleep(.01)
                    self.assertEqual(reads.call_count,1)
                    self.assertEqual(collector._settings['poll_seconds'],300)
                    revision=collector._revision
                    waiter=asyncio.create_task(collector.wait_for_update(revision,10))
                    await asyncio.sleep(0)
                    with patch.object(collector._activity_tracker,'read',return_value={'activity':'attention'}):
                        collector.refresh_activity()
                    await asyncio.wait_for(waiter,.1)
                    self.assertEqual(collector.current_snapshot()['activity'],'attention')
                    self.assertEqual(reads.call_count,1)
                    # A transition during a transport write must not wait for keepalive.
                    await asyncio.wait_for(collector.wait_for_update(revision,10),.1)
                finally:await collector.on_shutdown(ctx)

    def test_cached_age_advances_without_recollection(self):
        from unittest.mock import patch
        with patch.object(collector,'_snapshot',{'age_seconds':3580,'stale':False}),patch.object(collector,'_usage_collected_mono',100),patch.object(collector,'_settings',{'poll_seconds':300,'stale_after':3600}):
            self.assertFalse(collector.current_snapshot(120)['stale'])
            data=collector.current_snapshot(125)
            self.assertEqual(data['age_seconds'],3605)
            self.assertTrue(data['stale'])
            self.assertEqual(data['next_usage_poll_seconds'],275)
            self.assertEqual(collector._snapshot['age_seconds'],3580)

    async def test_settings_persist_preserve_other_config_and_reschedule(self):
        from unittest.mock import patch,AsyncMock
        with tempfile.TemporaryDirectory() as root:
            ctx=types.SimpleNamespace(config={'db_path':'example.db'},data_dir=root)
            event=asyncio.Event()
            with patch.object(collector,'_settings',{'poll_seconds':300,'stale_after':300}),patch.object(collector,'_usage_reschedule',event):
                request=types.SimpleNamespace(method='POST',json=AsyncMock(return_value={'poll_seconds':600}))
                response=await collector.settings(request,ctx)
                self.assertEqual(response.status,200)
                self.assertEqual(collector.read_settings(ctx),{'db_path':'example.db','poll_seconds':600})
                self.assertTrue(event.is_set())
                for invalid in (True,0,3601,1.5,'300',None):
                    request.json=AsyncMock(return_value={'poll_seconds':invalid})
                    self.assertEqual((await collector.settings(request,ctx)).status,400)
                self.assertEqual(collector._settings['poll_seconds'],600)
