import asyncio
import hashlib
import importlib
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch, AsyncMock
import test_crew_app

devices = importlib.import_module('kirometer_test_backend.devices')

class DeviceTests(unittest.IsolatedAsyncioTestCase):
    async def test_flash_identity_comes_from_target_usb_not_another_bluetooth_device(self):
        with tempfile.TemporaryDirectory() as root:
            ctx = types.SimpleNamespace(data_dir=root)
            inventory = [{'device':'/dev/cu.shared','vid':0x303A,'pid':0x1001,'serial_number':'44:BD:8D:60:DA:5C'}]
            with patch.object(devices, '_history_path', None), patch.object(devices, '_history', []), patch.object(devices, '_job', None), patch.object(devices, '_task', None), patch.object(devices, '_sessions', {'other': devices.DeviceSession({'id':'other','device_id':'10da608dbd44','name':'Other device'})}), patch.object(devices.sys, 'platform', 'darwin'), patch.object(devices, 'tools_ready', return_value=True), patch.object(devices, 'check_port'), patch.object(devices, 'port_inventory', new_callable=AsyncMock, return_value=inventory), patch.object(devices, 'disconnect', new_callable=AsyncMock), patch.object(devices, 'worker', new_callable=AsyncMock):
                job = await devices.start('flash', ctx, '/dev/cu.shared', {'version':'test'})
                await devices._task
                self.assertEqual(job['device']['device_id'], '5cda608dbd44')
                self.assertEqual(job['device']['usb_serial'], '44:BD:8D:60:DA:5C')
                self.assertNotIn('name', job['device'])

    def test_old_logs_are_migrated_by_mac_never_by_reused_port(self):
        with tempfile.TemporaryDirectory() as root:
            stored = [{'id':'a','port':'/dev/cu.shared','console':'MAC:                44:bd:8d:60:da:10\n','state':'complete'},
                      {'id':'b','port':'/dev/cu.shared','console':'No serial data received.','state':'failed'}]
            path = Path(root)/'firmware-updates.json'
            path.write_text(json.dumps(stored))
            with patch.object(devices, '_history_path', None), patch.object(devices, '_history', []), patch.object(devices, '_job', None):
                devices.load_history(types.SimpleNamespace(data_dir=root))
                self.assertEqual(devices._history[0]['device']['device_id'], '10da608dbd44')
                self.assertNotIn('device', devices._history[1])
                self.assertEqual(json.loads(path.read_text())[0]['device']['source'], 'bootloader')

    def test_history_keeps_eight_updates_per_device_and_bootloader_corrects_identity(self):
        jobs = [{'device':{'device_id':'a'},'id':str(i)} for i in range(10)] + [{'device':{'device_id':'b'},'id':'b'}]
        with patch.object(devices, '_history', jobs):
            devices.trim_history()
            self.assertEqual(len(devices._history), 9)
            self.assertEqual(devices._history[-1]['id'], 'b')
        job = {'device':{'device_id':'wrong','name':'Wrong device'}, 'console':'MAC: 44:bd:8d:60:da:5c\n'}
        devices.identity_from_console(job)
        self.assertEqual(job['device'], {'device_id':'5cda608dbd44','source':'bootloader'})
        self.assertEqual(devices.usb_identity({'vid':0x10C4,'serial_number':'44:bd:8d:60:da:10'}), {'usb_serial':'44:bd:8d:60:da:10'})

    async def test_usb_inventory_filters_metadata_and_caches_without_opening_ports(self):
        ctx = types.SimpleNamespace(data_dir='/tmp/inventory-test')
        data = [{'device':'/dev/cu.usbmodem1','serial_number':'SERIAL-1','vid':123,'token':'private'},
                {'device':'/dev/cu.other','serial_number':'OTHER'}]
        with patch.object(devices, '_inventory_cache', None), patch.object(devices, 'tools_ready', return_value=True), patch.object(devices, 'command', new_callable=AsyncMock, return_value=json.dumps(data)) as command:
            result = await devices.port_inventory(ctx, ['/dev/cu.usbmodem1'])
            self.assertEqual(result, [{'device':'/dev/cu.usbmodem1','serial_number':'SERIAL-1','vid':123}])
            self.assertEqual(await devices.port_inventory(ctx, ['/dev/cu.usbmodem1']), result)
            command.assert_awaited_once()
            await devices.port_inventory(ctx, ['/dev/cu.usbmodem2'])
            self.assertEqual(command.await_count, 2)

    async def test_usb_inventory_failure_does_not_break_device_status(self):
        ctx = types.SimpleNamespace(data_dir='/tmp/inventory-test')
        with patch.object(devices, '_inventory_cache', None), patch.object(devices, 'tools_ready', return_value=True), patch.object(devices, 'command', new_callable=AsyncMock, side_effect=TimeoutError):
            self.assertEqual(await devices.port_inventory(ctx, ['/dev/cu.usbmodem1']), [])

    def bundle(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        root=Path(temp.name);raw=b'firmware fixture';(root/'firmware.bin').write_bytes(raw)
        manifest={'board':devices.BOARD,'chip':'esp32s3','version':'test','images':[{'offset':'0x10000','file':'firmware.bin','sha256':hashlib.sha256(raw).hexdigest()}]}
        path=root/'firmware.json';path.write_text(json.dumps(manifest))
        return path,manifest

    def test_bundle_requires_correct_board_hash_and_containment(self):
        path,data=self.bundle()
        self.assertEqual(devices.validate_bundle(path)['images'][0]['offset'],65536)
        for field,value in [('board','other-board'),('chip','esp32')]:
            invalid={**data,field:value};path.write_text(json.dumps(invalid))
            with self.assertRaises(ValueError):devices.validate_bundle(path)
        for file,sha in [('firmware.bin','0'*64),('../firmware.bin',data['images'][0]['sha256'])]:
            invalid={**data,'images':[{**data['images'][0],'file':file,'sha256':sha}]};path.write_text(json.dumps(invalid))
            with self.assertRaises(ValueError):devices.validate_bundle(path)

    def test_sector_overlap_refused(self):
        path,data=self.bundle();data['images'].append(dict(data['images'][0]));path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):devices.validate_bundle(path)

    def test_port_requires_current_usb_device(self):
        with patch.object(devices,'ports',return_value=['/dev/cu.usbmodem123']):
            self.assertEqual(devices.check_port('/dev/cu.usbmodem123'),'/dev/cu.usbmodem123')
            with self.assertRaises(ValueError):devices.check_port('/dev/cu.Bluetooth-Incoming-Port')

    async def test_timeout_kills_process(self):
        with self.assertRaises(asyncio.TimeoutError):
            await devices.command([__import__('sys').executable,'-c','import time; time.sleep(2)'],.02)

    async def test_flash_stages_bytes_and_does_not_claim_boot(self):
        path,_=self.bundle();bundle=devices.validate_bundle(path)
        ctx=types.SimpleNamespace(data_dir=path.parent)
        devices._job={'id':'test'}
        async def fake(argv,timeout,on_output=None):
            self.assertEqual(argv[argv.index('--chip')+1],'esp32s3')
            self.assertNotIn('--force',argv)
            self.assertNotIn('--erase-all',argv)
            self.assertEqual(Path(argv[-1]).read_bytes(),b'firmware fixture')
            return 'verified'
        with patch.object(devices,'check_port',return_value='/dev/cu.usbmodem123'),patch.object(devices,'command',side_effect=fake):
            await devices.worker('flash',ctx,'/dev/cu.usbmodem123',bundle)
        self.assertEqual(devices._job['state'],'complete')
        self.assertIn('confirm firmware boot',devices._job['message'])
        self.assertFalse((path.parent/'flash-staging/test').exists())

class ControlsTest(unittest.TestCase):
    def test_screen_layout_enum_is_validated(self):
        for layout in ('ghost','usage','orbit','sidekick','ticket','big_number'):
            self.assertEqual(devices.validate_controls({'screen_layout':layout}),{'screen_layout':layout})
        for value in ('weekly','',None,False,{},[]):
            with self.assertRaises(ValueError):devices.validate_controls({'screen_layout':value})

    def test_display_and_name_validation(self):
        self.assertEqual(devices.validate_controls({'brightness':100,'sleep_mode':'auto','sleep_after':60}),{'brightness':100,'sleep_mode':'auto','sleep_after':60})
        for payload in ({'brightness':True},{'brightness':256},{'sleep_mode':'invalid'},{'sleep_after':1},{'device_name':'x'*27},{'device_name':'bad\nname'},{'device_name':' '},{'device_name':'👻'*7}):
            with self.assertRaises(ValueError):devices.validate_controls(payload)

class ReconnectTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.session = devices.DeviceSession({'id':'test','port':'device','transport':'bluetooth'})
        self.registry_patch = patch.object(devices, '_registry_path', None)
        self.registry_patch.start()
        self.addCleanup(self.registry_patch.stop)

    async def test_backoff_caps_and_resets_after_success(self):
        from unittest.mock import AsyncMock
        waits=[]
        async def pause(seconds):
            waits.append(seconds)
            self.assertFalse(self.session.link['connected'])
            self.assertIsNone(self.session.link['status'])
            self.assertTrue(self.session.link['reconnecting'])
            if len(waits)==9:raise asyncio.CancelledError()
        clock=[0]
        async def attempt(*args):
            clock[0] += 40
            return True, len(waits) == 8
        attempts=AsyncMock(side_effect=attempt)
        with patch.object(devices,'bridge_once',attempts),patch.object(devices.asyncio,'sleep',side_effect=pause), patch.object(devices,'time',types.SimpleNamespace(monotonic=lambda:clock[0])):
            with self.assertRaises(asyncio.CancelledError):await devices.bridge(None,'device','bluetooth',self.session)
        self.assertEqual(waits,[5,10,20,40,80,160,300,300,5])

    async def test_pairing_failure_is_terminal(self):
        from unittest.mock import AsyncMock
        with patch.object(devices,'bridge_once',AsyncMock(return_value=(False,False))) as attempt,patch.object(devices.asyncio,'sleep',AsyncMock()) as pause:
            await devices.bridge(None,'device','bluetooth',self.session)
            attempt.assert_awaited_once();pause.assert_not_awaited()

    async def test_usb_does_not_reopen_missing_port(self):
        from unittest.mock import AsyncMock
        with patch.object(devices,'bridge_once',AsyncMock(return_value=(True,True))) as attempt,patch.object(devices.asyncio,'sleep',AsyncMock()) as pause:
            await devices.bridge(None,'/dev/cu.test','usb',self.session)
            attempt.assert_awaited_once();pause.assert_not_awaited()

    async def test_explicit_disconnect_cancels_pending_retry(self):
        from unittest.mock import AsyncMock
        waiting=asyncio.Event();release=asyncio.Event()
        async def pause(seconds):
            waiting.set();await release.wait()
        with patch.object(devices,'bridge_once',AsyncMock(return_value=(True,False))) as attempt,patch.object(devices.asyncio,'sleep',side_effect=pause):
            self.session.task=asyncio.create_task(devices.bridge(None,'device','bluetooth',self.session))
            await waiting.wait()
            await devices.stop_session(self.session, pause=True)
            self.assertIsNone(self.session.task)
            self.assertEqual(self.session.link['port'], 'device')
            self.assertFalse(self.session.record['auto_connect'])
            attempt.assert_awaited_once()

    async def test_worker_pairing_error_stops_and_cleans_up(self):
        from unittest.mock import AsyncMock,Mock
        ctx=types.SimpleNamespace(data_dir='/tmp/unused')
        proc=types.SimpleNamespace(stdin=types.SimpleNamespace(write=Mock(),drain=AsyncMock()),stdout=types.SimpleNamespace(readline=AsyncMock(return_value=b'{"error_code":"bond_removed"}\n')),returncode=None,kill=Mock(),wait=AsyncMock())
        with patch.object(devices.asyncio,'create_subprocess_exec',AsyncMock(return_value=proc)),patch.object(devices,'pairing',return_value={'token':'fixture'}):
            retry,delivered=await devices.bridge_once(ctx,'device','bluetooth',self.session)
        self.assertFalse(retry);self.assertFalse(delivered)
        proc.kill.assert_called_once();proc.wait.assert_awaited_once()

class FirmwareConsoleTests(unittest.IsolatedAsyncioTestCase):
    async def test_failed_command_keeps_streamed_output(self):
        chunks=[]
        with self.assertRaises(ValueError):
            await devices.command([__import__('sys').executable,'-u','-c','print("Connecting..."); print("port unavailable"); exit(1)'],on_output=chunks.append)
        self.assertIn('port unavailable',''.join(chunks))

    async def test_console_is_bounded_persisted_and_recovers_interruption(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.object(devices,'_history_path',None),patch.object(devices,'_history',[]),patch.object(devices,'_job',None):
                ctx=types.SimpleNamespace(data_dir=root)
                devices.load_history(ctx)
                devices._job={'id':'test','kind':'flash','state':'running','console':''}
                devices._history.append(devices._job)
                devices.append_console('x'*25000+'\x1b[31mError\x1b[0m\rFailed\n')
                self.assertEqual(len(devices._job['console']),24000)
                self.assertNotIn('\x1b',devices._job['console'])
                self.assertTrue(devices._job['console'].endswith('Error\nFailed\n'))
                devices._history_path=None
                devices.load_history(ctx)
                self.assertEqual(devices._job['state'],'interrupted')
                self.assertIn('Failed',devices._job['console'])
