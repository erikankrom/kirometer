"""Exercise the shipped serial bridge against a simulated device on a macOS PTY."""
import json
import sys
import importlib.util
import os
from pathlib import Path
import pty
import select
import subprocess
import threading
import unittest

TOOLS=Path(sys.executable)

@unittest.skipUnless(os.name=='posix' and importlib.util.find_spec('serial') is not None,'Requires pyserial and a POSIX PTY')
class USBProtocolTest(unittest.TestCase):
    def test_usage_ack_and_status_round_trip(self):
        master,slave=pty.openpty();port=os.ttyname(slave);quit=threading.Event()
        received=[];last_seq=0
        def device():
            nonlocal last_seq
            buffer=b''
            while not quit.is_set():
                if not select.select([master],[],[],.1)[0]:continue
                # Model the hardware's 256-byte RX queue: an unpaced burst
                # loses its tail before firmware gets another chance to read.
                try:buffer+=os.read(master,4096)[:256]
                except OSError:return
                while b'\n' in buffer:
                    line,buffer=buffer.split(b'\n',1)
                    try:message=json.loads(line)
                    except ValueError:continue
                    received.append(message)
                    if message['type']=='kirometer.usage':
                        stale={'type':'kirometer.status','protocol':1,'displayed_seq':last_seq,'display_usage_used':0}
                        os.write(master,json.dumps(stale).encode()+b'\n')
                        last_seq=message['seq']
                        response={'type':'kirometer.ack','protocol':1,'seq':message['seq'],'accepted':True}
                    else:
                        response={'type':'kirometer.status','protocol':1,'version':'0.5.8','displayed_seq':last_seq,'battery_percent':85,'display_usage_used':625,'display_usage_limit':500,'display_usage_overage':125,'wifi_connected':False,'secret':'must not leave worker'}
                    os.write(master,json.dumps(response).encode()+b'\n')
        thread=threading.Thread(target=device,daemon=True);thread.start()
        proc=subprocess.Popen([str(TOOLS),'crew-app/backend/serial_bridge.py',port],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            credit={'used':625,'limit':500,'remaining_plan_credits':0,'used_percent':125,'reset_at':'2026-11-01','overage_used':125}
            msg={'type':'kirometer.usage','protocol':1,'seq':7,'available':True,'stale':True,'credits':[credit,credit,credit],'activity':'unknown','plan':'KIRO PRO'}
            self.assertGreater(len(json.dumps(msg)),256)
            proc.stdin.write(json.dumps(msg)+'\n');proc.stdin.flush()
            self.assertTrue(select.select([proc.stdout],[],[],5)[0],'No device response')
            result=json.loads(proc.stdout.readline())
            self.assertTrue(result['acknowledged'])
            self.assertEqual(result['status']['battery_percent'],85)
            self.assertNotIn('secret',result['status'])
            self.assertEqual(result['status']['display_usage_used'],625)
            self.assertEqual(result['status']['display_usage_overage'],125)
            self.assertEqual(received[0]['credits'][0]['used'],625)
            proc.stdin.close();proc.wait(timeout=3)
            self.assertEqual(proc.returncode,0)
        finally:
            if proc.poll() is None:proc.kill();proc.wait()
            quit.set();thread.join(timeout=1);os.close(master);os.close(slave)
            proc.stdout.close();proc.stderr.close()
