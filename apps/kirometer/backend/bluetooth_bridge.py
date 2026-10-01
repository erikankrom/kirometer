"""CoreBluetooth worker: bounded JSON lines over encrypted Kirometer GATT."""
import asyncio
import json
import sys

SERVICE='f3641400-00b0-4240-ba50-05ca45bf8abc'
RX='f3641401-00b0-4240-ba50-05ca45bf8abc'
TX='f3641402-00b0-4240-ba50-05ca45bf8abc'
PAIR='f3641403-00b0-4240-ba50-05ca45bf8abc'
STATUS_KEYS=('version','device_id','touch_supported','touch_events','last_wake','animation_interval_ms','animation_ticks','partial_frames','full_frames','last_render_us','max_partial_render_us','max_animation_gap_ms','ble_reply_drops','device_name','bluetooth_supported','bluetooth_connected','paired','uptime_seconds','battery_percent','charging','power_source','displayed_seq','display_usage_available','display_usage_used','display_usage_limit','display_usage_overage','usage_connected','usage_available','usage_stale','activity','brightness','sleep_mode','sleeping','sleep_after','control_seq','controls_supported')

def project(data):
    return {k:data[k] for k in STATUS_KEYS if k in data and (data[k] is None or isinstance(data[k],(str,int,float,bool))) and len(str(data[k]))<=100}

class Lines:
    def __init__(self):self.buffer=bytearray();self.drop=False;self.queue=asyncio.Queue(maxsize=8)
    def receive(self,_,value):
        for c in value:
            if c==10:
                if not self.drop:
                    try:
                        data=json.loads(self.buffer)
                        if isinstance(data,dict) and data.get('protocol')==1:self.queue.put_nowait(data)
                    except (ValueError,UnicodeDecodeError,asyncio.QueueFull):pass
                self.buffer.clear();self.drop=False
            elif not self.drop:
                if len(self.buffer)<4096:self.buffer.append(c)
                else:self.buffer.clear();self.drop=True
    async def response(self,seq,timeout=5):
        ack=False;status=None
        async with asyncio.timeout(timeout):
            while True:
                data=await self.queue.get()
                if data.get('type')=='kirometer.ack' and data.get('seq')==seq and data.get('accepted') is True:ack=True
                if data.get('type')=='kirometer.status' and data.get('displayed_seq')==seq:status=project(data)
                if ack and status is not None:return {'acknowledged':True,'status':status}

async def scan():
    from bleak import BleakScanner
    found=await BleakScanner.discover(timeout=5,return_adv=True,service_uuids=[SERVICE])
    return [{'address':device.address,'name':adv.local_name or device.name or 'Kirometer','rssi':adv.rssi} for device,adv in found.values() if SERVICE in [s.lower() for s in adv.service_uuids]]

async def run():
    if len(sys.argv)>1 and sys.argv[1]=='scan':
        try:print(json.dumps({'devices':await scan()}),flush=True)
        except Exception:print(json.dumps({'error':'Bluetooth scan unavailable. Enable Bluetooth and allow Kiro Crew in macOS Privacy & Security → Bluetooth.'}),flush=True)
        return
    from bleak import BleakClient,BleakScanner
    config=json.loads(await asyncio.to_thread(sys.stdin.readline))
    device=await BleakScanner.find_device_by_address(config['address'],timeout=10,service_uuids=[SERVICE])
    if device is None:raise ValueError('Device not found')
    lines=Lines()
    async with BleakClient(device,timeout=20) as client:
        await client.start_notify(TX,lines.receive)
        # macOS starts its pairing flow on an encrypted characteristic read.
        await client.read_gatt_char(PAIR)
        await client.write_gatt_char(RX,b'\n',response=True)
        while raw:=await asyncio.to_thread(sys.stdin.readline):
            data=json.loads(raw);data['token']=config['token']
            packet=json.dumps(data,allow_nan=False).encode()+b'\n'
            if len(packet)>4096:raise ValueError('Packet too large')
            while not lines.queue.empty():lines.queue.get_nowait()
            for start in range(0,len(packet),20):await client.write_gatt_char(RX,packet[start:start+20],response=True)
            answer=await lines.response(data['seq'])
            print(json.dumps(answer,allow_nan=False),flush=True)

if __name__=='__main__':
    try:asyncio.run(run())
    except Exception as exc:
        code='bond_removed' if 'Peer removed pairing information' in str(exc) else 'bluetooth_unavailable'
        print(json.dumps({'error_code':code}),flush=True)

