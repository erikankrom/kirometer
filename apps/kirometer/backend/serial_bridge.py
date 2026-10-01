"""One persistent USB owner, driven by collector snapshots on stdin."""
import json
import sys
import time
import serial

with serial.Serial(port=None,baudrate=115200,timeout=.15,write_timeout=1) as link:
    link.dtr=False;link.rts=False;link.port=sys.argv[1];link.open()
    # Opening macOS USB-JTAG serial can restart the S3. Drain startup output
    # before sending the first usage packet, which would otherwise be lost.
    startup=time.monotonic()+1
    while time.monotonic()<startup:
        link.read_until(b'\n',4097)
    for line in sys.stdin:
        outgoing=json.loads(line)
        # HWCDC defaults to a 256-byte RX queue. A usage snapshot exceeds it;
        # pace USB packets so a frame transfer cannot cause dropped JSON bytes.
        packet=json.dumps(outgoing,allow_nan=False).encode()+b'\n'
        for offset in range(0,len(packet),64):
            link.write(packet[offset:offset+64])
            link.flush()
            time.sleep(.025)
        link.write(b'{"type":"kirometer.status","protocol":1}\n')
        deadline=time.monotonic()+2
        status=None;ack=False
        while time.monotonic()<deadline:
            raw=link.read_until(b'\n',4097)
            if len(raw)>4096:continue
            try:data=json.loads(raw)
            except (ValueError,UnicodeDecodeError):continue
            if not isinstance(data,dict) or data.get('protocol')!=1:continue
            if data.get('type')=='kirometer.ack' and data.get('seq')==outgoing['seq'] and data.get('accepted') is True:ack=True
            if data.get('type')=='kirometer.status' and data.get('displayed_seq')==outgoing['seq']:
                status={key:data[key] for key in ('version','device_id','screen_layout','screen_layouts_supported','touch_supported','touch_events','last_wake','animation_interval_ms','animation_ticks','partial_frames','full_frames','last_render_us','max_partial_render_us','max_animation_gap_ms','ble_reply_drops','uptime_seconds','bluetooth_connected','bluetooth_supported','device_name','paired','battery_percent','charging','power_source','displayed_seq','display_usage_available','display_usage_used','display_usage_limit','display_usage_overage','usage_connected','usage_available','usage_stale','activity','brightness','sleep_mode','sleeping','sleep_after','control_seq','controls_supported') if key in data and (data[key] is None or isinstance(data[key],(str,int,float,bool))) and len(str(data[key]))<=100}
            if ack and status is not None:break
        print(json.dumps({'acknowledged':ack,'status':status},allow_nan=False),flush=True)
