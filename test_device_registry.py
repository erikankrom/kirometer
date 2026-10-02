"""Per-device routing, persistence, cancellation and identity regression checks."""
import asyncio
import json
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch, AsyncMock
from test_devices import devices

class RegistryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.ctx=types.SimpleNamespace(data_dir=self.tmp.name)
        for key,value in [('_registry_path',None),('_sessions',{}),('_task',None)]:
            p=patch.object(devices,key,value);p.start();self.addCleanup(p.stop)
        devices.load_devices(self.ctx)

    async def asyncTearDown(self):
        await devices.disconnect()

    def request(self, action, payload):
        return types.SimpleNamespace(method='POST',path='/devices/'+action,app={},json=AsyncMock(return_value=payload))

    async def add(self, address):
        with patch.object(devices,'bridge',AsyncMock()):
            return await devices.connect_device(self.ctx,address,'bluetooth',address.title())

    async def test_registry_survives_restart_without_claiming_connected(self):
        home=await self.add('home');work=await self.add('work')
        await devices.remember_status(home,{'device_id':'chip-home','device_name':'Home','version':'0.6.0','token':'SECRET'})
        await devices.stop_session(work,pause=True)
        await devices.disconnect()
        raw=(Path(self.tmp.name)/'configured-devices.json').read_text()
        self.assertNotIn('SECRET',raw)
        devices._registry_path=None;devices.load_devices(self.ctx)
        self.assertEqual(len(devices._sessions),2)
        self.assertEqual(devices._sessions[home.record['id']].record['name'],'Home')
        self.assertTrue(devices._sessions[home.record['id']].record['auto_connect'])
        self.assertFalse(devices._sessions[work.record['id']].record['auto_connect'])
        self.assertTrue(all(not s.link['connected'] for s in devices._sessions.values()))

    async def test_retry_cancels_old_task_and_preserves_other_device(self):
        home=await self.add('home');work=await self.add('work')
        home.task=asyncio.create_task(asyncio.Event().wait())
        work.task=asyncio.create_task(asyncio.Event().wait())
        old=work.task; other=home.task
        work.link.update(connecting=False,reconnecting=True)
        await asyncio.sleep(0)
        with patch.object(devices,'bluetooth_ready',return_value=True),patch.object(devices,'bridge',AsyncMock()):
            result=await devices.route(self.request('retry',{'configured_id':work.record['id']}),self.ctx)
            self.assertEqual(result.status,202)
            await asyncio.sleep(0)
            self.assertTrue(old.cancelled());self.assertFalse(other.done())
            self.assertNotEqual(work.task,old)
            self.assertEqual(len(devices._sessions),2)

    async def test_controls_target_only_selected_device_and_ambiguous_is_rejected(self):
        home=await self.add('home');work=await self.add('work')
        for s in (home,work):s.link.update(connected=True,status={'controls_supported':True})
        result=await devices.route(self.request('controls',{'configured_id':work.record['id'],'brightness':95}),self.ctx)
        self.assertEqual(result.status,202)
        self.assertIsNone(home.pending_controls);self.assertEqual(work.pending_controls['brightness'],95)
        result=await devices.route(self.request('controls',{'brightness':100}),self.ctx)
        self.assertEqual(result.status,400)

    async def test_usb_and_ble_merge_by_chip_not_name(self):
        home=await self.add('home');other=await self.add('other')
        await devices.remember_status(home,{'device_id':'chip','device_name':'Same name'})
        await devices.remember_status(other,{'device_id':'other-chip','device_name':'Same name'})
        self.assertEqual(len(devices._sessions),2)
        home.task=asyncio.create_task(asyncio.Event().wait());await asyncio.sleep(0)
        old_task=home.task
        usb=devices.DeviceSession({'id':'usb','port':'/dev/test','transport':'usb','endpoints':{'usb':'/dev/test'}})
        devices._sessions['usb']=usb
        await devices.remember_status(usb,{'device_id':'chip','device_name':'Same name'})
        self.assertTrue(old_task.cancelled())
        self.assertEqual(len(devices._sessions),2)
        self.assertEqual(usb.record['endpoints'],{'bluetooth':'home','usb':'/dev/test'})
        self.assertIn(other.record['id'],devices._sessions)

    async def test_restore_only_enabled_devices(self):
        home=await self.add('home');work=await self.add('work')
        await devices.stop_session(work,pause=True);await devices.disconnect()
        with patch.object(devices.sys,'platform','darwin'),patch.object(devices,'bluetooth_ready',return_value=True),patch.object(devices,'bridge',AsyncMock()) as bridge:
            await devices.restore_devices(self.ctx);await asyncio.sleep(0)
            bridge.assert_awaited_once_with(self.ctx,'home','bluetooth',home)

    async def test_reused_usb_port_creates_new_device_instead_of_overwriting_old(self):
        old=await self.add('old')
        await devices.remember_status(old,{'device_id':'old-chip'})
        old.record['endpoints']['usb']='/dev/shared'
        with patch.object(devices,'port_inventory',AsyncMock(return_value=[{'device':'/dev/shared'}])),patch.object(devices,'usb_identity',return_value={'device_id':'new-chip'}),patch.object(devices,'bridge',AsyncMock()):
            new=await devices.connect_device(self.ctx,'/dev/shared','usb')
        self.assertIsNot(new,old)
        self.assertEqual(old.record['device_id'],'old-chip')
        self.assertEqual(len(devices._sessions),2)

    async def test_retry_while_connecting_does_not_duplicate_worker(self):
        device=await self.add('work')
        current=device.task
        response=await devices.route(self.request('retry',{'configured_id':device.record['id']}),self.ctx)
        self.assertEqual(response.status,200)
        self.assertIs(current,device.task)

    def test_countdown_uses_monotonic_clock(self):
        s=devices.DeviceSession({'id':'a'});s.retry_deadline=150
        with patch.object(devices.time,'monotonic',return_value=113):self.assertEqual(s.public()['link']['retry_in_seconds'],37)
        with patch.object(devices.time,'monotonic',return_value=151):self.assertEqual(s.public()['link']['retry_in_seconds'],0)

if __name__=='__main__':unittest.main()
