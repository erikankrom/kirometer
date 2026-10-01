"""Explicit, bounded serial status probe. Compatible firmware must implement v1."""
import json
import sys
import time
import serial

result = {'connected':True,'firmware':'unknown','message':'No compatible Kirometer status response.'}
with serial.Serial(port=None,baudrate=115200,timeout=.2,write_timeout=1) as link:
    link.dtr = False
    link.rts = False
    link.port = sys.argv[1]
    link.open()
    link.write(b'{"type":"kirometer.status","protocol":1}\n')
    deadline = time.monotonic()+3
    while time.monotonic() < deadline:
        line = link.read_until(b'\n',4097)
        if len(line)>4096:
            continue
        try:
            data = json.loads(line)
        except (ValueError,UnicodeDecodeError):
            continue
        if isinstance(data,dict) and data.get('type')=='kirometer.status' and data.get('protocol')==1:
            # Only render a defined telemetry projection; never arbitrary device output.
            result = {'connected':True,'firmware':'kirometer','protocol':1}
            for key in ('version','device_id','screen_layout','default_screen_layout','screen_layouts_supported','screen_layouts_version','swipe_events','touch_supported','touch_events','last_wake','animation_interval_ms','animation_ticks','partial_frames','full_frames','last_render_us','max_partial_render_us','max_animation_gap_ms','ble_reply_drops','uptime_seconds','bluetooth_connected','bluetooth_supported','device_name','paired','battery_percent','charging','power_source','displayed_seq','display_usage_available','display_usage_used','display_usage_limit','display_usage_overage','sounds_supported','audio_ready','sound_enabled','sound_preset','sound_events'):
                value = data.get(key)
                if isinstance(value,(str,int,float,bool)) and len(str(value)) <= 100:
                    result[key]=value
            break
print(json.dumps(result,allow_nan=False))
