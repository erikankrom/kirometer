import asyncio
import importlib.util
from pathlib import Path
import json
import unittest
from unittest.mock import patch
import types
import test_devices

spec=importlib.util.spec_from_file_location('bluetooth_bridge',Path(__file__).parent/'crew-app/backend/bluetooth_bridge.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

class BluetoothTests(unittest.IsolatedAsyncioTestCase):
    async def test_fragmented_messages_require_matching_ack_and_display(self):
        lines=b.Lines()
        messages=[{'type':'kirometer.ack','protocol':1,'seq':1,'accepted':True},{'type':'kirometer.status','protocol':1,'displayed_seq':1}, {'type':'kirometer.ack','protocol':1,'seq':2,'accepted':True},{'type':'kirometer.status','protocol':1,'displayed_seq':2,'device_name':'test kirometer','brightness':90,'screen_layout':'usage','screen_layouts_supported':True,'default_screen_layout':'orbit','screen_layouts_version':2,'swipe_events':3,'sounds_supported':True,'audio_ready':True,'sound_enabled':False,'sound_preset':'pulse','sound_events':2,'token':'must-not-return'}]
        raw=''.join(json.dumps(m)+'\n' for m in messages).encode()
        for i in range(0,len(raw),7):lines.receive(None,raw[i:i+7])
        answer=await lines.response(2,.1)
        self.assertEqual(answer['status']['brightness'],90)
        self.assertEqual(answer['status']['screen_layout'],'usage')
        self.assertTrue(answer['status']['screen_layouts_supported'])
        self.assertEqual(answer['status']['default_screen_layout'],'orbit')
        self.assertEqual(answer['status']['screen_layouts_version'],2)
        self.assertEqual(answer['status']['swipe_events'],3)
        self.assertNotIn('token',answer['status'])
        self.assertTrue(answer['status']['sounds_supported'])
        self.assertEqual(answer['status']['sound_preset'],'pulse')
        self.assertEqual(answer['status']['sound_events'],2)
    async def test_overflow_recovers_at_next_line_and_timeout_not_success(self):
        lines=b.Lines();lines.receive(None,b'x'*5000+b'\n')
        self.assertTrue(lines.queue.empty())
        with self.assertRaises(TimeoutError):await lines.response(1,.01)
        lines.receive(None,b'{"protocol":1,"type":"kirometer.ack","seq":1,"accepted":true}\n')
        with self.assertRaises(TimeoutError):await lines.response(1,.01)
    def test_default_name_and_unicode_bytes(self):
        with patch.object(test_devices.devices.getpass,'getuser',return_value='alice'):
            self.assertEqual(test_devices.devices.default_name(),'alice kirometer')
        self.assertEqual(test_devices.devices.validate_controls({'device_name':' My ghost '})['device_name'],'My ghost')
        with self.assertRaises(ValueError):test_devices.devices.validate_controls({'device_name':'👻'*7})

if __name__=='__main__':unittest.main()

class SoundControlTests(unittest.TestCase):
    def test_sound_choices_and_strict_enable_validation(self):
        validate=test_devices.devices.validate_controls
        for preset in ('chime','ding','blip','pop','pulse'):
            self.assertEqual(validate({'sound_enabled':True,'sound_preset':preset}),{'sound_enabled':True,'sound_preset':preset})
        for value in (1,'true',None,[]):
            with self.assertRaises(ValueError):validate({'sound_enabled':value})
        for value in ('none','unknown',1,None):
            with self.assertRaises(ValueError):validate({'sound_preset':value})

class TestSoundRequestTests(unittest.IsolatedAsyncioTestCase):
    def test_preview_validation_is_separate_from_saved_settings(self):
        validate=test_devices.devices.validate_controls
        self.assertEqual(validate({'test_sound':'pop'}),{'test_sound':'pop'})
        for payload in ({'test_sound':'invalid'},{'test_sound':True},{'test_sound':'chime','sound_enabled':True}):
            with self.assertRaises(ValueError):validate(payload)

    async def test_preview_requires_audio_capability_and_preserves_other_commands(self):
        from unittest.mock import AsyncMock
        d=test_devices.devices
        status={'controls_supported':True,'test_sound_supported':True,'audio_ready':True,'sound_enabled':False,'sound_preset':'chime'}
        request=types.SimpleNamespace(app={},method='POST',path='/devices/controls',json=AsyncMock(return_value={'test_sound':'pulse'}))
        with patch.object(d,'_link',{'connected':True,'status':status}),patch.object(d,'_pending_controls',None),patch.object(d,'_control_seq',100):
            for key in ('test_sound_supported','audio_ready'):
                status[key]=False
                self.assertEqual((await d.route(request,None)).status,400)
                self.assertIsNone(d._pending_controls)
                status[key]=True
            reply=await d.route(request,None)
            self.assertEqual(reply.status,202)
            self.assertEqual(d._pending_controls,{'test_sound':'pulse','seq':101})
            self.assertFalse(status['sound_enabled'])
            self.assertEqual(status['sound_preset'],'chime')
            self.assertEqual((await d.route(request,None)).status,400)
            self.assertEqual(d._pending_controls['seq'],101)
