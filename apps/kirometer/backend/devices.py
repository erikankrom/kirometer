"""macOS USB device tools; all writes are explicit app actions."""
import asyncio
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
import uuid
import secrets
import getpass
import os
import re
import codecs

BOARD = 'waveshare-esp32-s3-touch-amoled-2.16'
_job = None
_history = []
_history_path = None
_task = None
_lock = asyncio.Lock()
_control_seq = secrets.randbits(31)
_sessions = {}
_registry_path = None

class DeviceSession:
    def __init__(self, record):
        self.record = record
        self.task = None
        self.pending_controls = None
        self.retry_deadline = None
        self.link = {'connected': False, 'port': record.get('port'),
                     'transport': record.get('transport'), 'status': None,
                     'message': 'Unavailable', 'connecting': False}

    def public(self):
        link = dict(self.link)
        if self.retry_deadline is not None:
            link['retry_in_seconds'] = max(0, int(self.retry_deadline - time.monotonic() + .999))
        return {**self.record, 'link': link}


def load_devices(ctx):
    global _registry_path, _sessions
    path = Path(ctx.data_dir) / 'configured-devices.json'
    if _registry_path == path:
        return
    _registry_path = path
    try:
        records = json.loads(path.read_text())
        if not isinstance(records, list): raise ValueError('Invalid device registry')
    except FileNotFoundError:
        records = []
    _sessions = {r['id']: DeviceSession(r) for r in records
                 if isinstance(r, dict) and isinstance(r.get('id'), str)
                 and r.get('transport') in ('bluetooth', 'usb')}


def persist_devices():
    if _registry_path is None: return
    _registry_path.parent.mkdir(parents=True, exist_ok=True)
    temp = _registry_path.with_suffix('.tmp')
    temp.write_text(json.dumps([s.record for s in _sessions.values()]))
    temp.chmod(0o600)
    temp.replace(_registry_path)


def select_device(payload):
    key = payload.get('configured_id')
    if key:
        if key not in _sessions: raise ValueError('Choose a configured device.')
        return _sessions[key]
    if len(_sessions) == 1: return next(iter(_sessions.values()))
    raise ValueError('Choose a device for this action.')


def backoff_seconds(failures):
    return min(300, 5 * 2 ** min(max(failures, 0), 6))


async def stop_session(session, pause=False):
    task = session.task
    if task and not task.done():
        task.cancel()
        try: await task
        except asyncio.CancelledError: pass
    session.task = None
    session.pending_controls = None
    session.retry_deadline = None
    session.link = {**session.link, 'connected': False, 'connecting': False,
                    'reconnecting': False, 'status': None, 'message': 'Disconnected',
                    'retry_in_seconds': None}
    if pause:
        session.record['auto_connect'] = False
        persist_devices()


async def connect_device(ctx, port, transport, name=None):
    load_devices(ctx)
    session = next((s for s in _sessions.values()
                    if s.record.get('endpoints', {}).get(transport) == port), None)
    # USB chip identity lets us switch a known device away from BLE before opening USB.
    if transport == 'usb':
        inventory = await port_inventory(ctx, [port])
        identity = next((usb_identity(i).get('device_id') for i in inventory if i['device'] == port), None)
        if identity:
            if session and session.record.get('device_id') not in (None, identity):
                session.record.get('endpoints', {}).pop('usb', None)
                session = None
            session = next((s for s in _sessions.values() if s.record.get('device_id') == identity), session)
    if session is None:
        record = {'id': uuid.uuid4().hex, 'name': str(name or 'Kirometer')[:80], 'endpoints': {}}
        session = DeviceSession(record)
        _sessions[record['id']] = session
    await stop_session(session)
    session.record.update(port=port, transport=transport, auto_connect=True)
    session.record['endpoints'][transport] = port
    persist_devices()
    session.link = {'connected': False, 'connecting': True, 'port': port,
                    'transport': transport, 'status': None, 'message': 'Connecting…'}
    session.task = asyncio.create_task(bridge(ctx, port, transport, session))
    return session


async def remember_status(session, status):
    # Store only durable identity/display settings, never pairing tokens or telemetry.
    device_id = status.get('device_id')
    if device_id:
        for key, other in list(_sessions.items()):
            if other is not session and other.record.get('device_id') == device_id:
                await stop_session(other)
                session.record['endpoints'] = {**other.record.get('endpoints', {}), **session.record['endpoints']}
                del _sessions[key]
    values = {k: status[k] for k in ('device_id', 'device_name', 'version', 'default_screen_layout') if k in status}
    changed = values != session.record.get('last_status')
    first_seen = not session.record.get('last_seen')
    session.record.update(last_status=values, last_seen=time.time())
    if device_id: session.record['device_id'] = device_id
    if status.get('device_name'): session.record['name'] = status['device_name']
    if changed or first_seen: persist_devices()


async def restore_devices(ctx):
    if not getattr(ctx, 'data_dir', None): return
    load_devices(ctx)
    if sys.platform != 'darwin': return
    for session in list(_sessions.values()):
        r = session.record
        if r.get('auto_connect') and ((r['transport'] == 'bluetooth' and bluetooth_ready(ctx)) or
                (r['transport'] == 'usb' and tools_ready(ctx) and r['port'] in ports())):
            session.link.update(connecting=True, message='Connecting…')
            session.task = asyncio.create_task(bridge(ctx, r['port'], r['transport'], session))
_inventory_cache = None
_inventory_lock = asyncio.Lock()


def validate_controls(payload):
    out={}
    if 'custom_face' in payload:
        from .custom_faces import validate
        out['custom_face']=validate(payload['custom_face'])
        out['screen_layout']='custom'
    if 'screen_layout' in payload:
        if payload['screen_layout'] not in ('ghost','usage','orbit','sidekick','ticket','big_number','custom'):raise ValueError('Choose an available screen layout.')
        out['screen_layout']=payload['screen_layout']
    if 'brightness' in payload:
        n=payload['brightness']
        if not isinstance(n,int) or isinstance(n,bool) or not 5<=n<=255:raise ValueError('Brightness must be 5–255.')
        out['brightness']=n
    if 'sleep_mode' in payload:
        if payload['sleep_mode'] not in ('awake','sleep','auto'):raise ValueError('Choose Awake, Sleep or Auto.')
        out['sleep_mode']=payload['sleep_mode']
    if 'sleep_after' in payload:
        n=payload['sleep_after']
        if not isinstance(n,int) or isinstance(n,bool) or not 30<=n<=3600:raise ValueError('Sleep timeout must be 30–3600 seconds.')
        out['sleep_after']=n
    if 'device_name' in payload:
        name=payload['device_name']
        if not isinstance(name,str) or not name.strip() or len(name.encode())>26 or any(ord(c)<32 or ord(c)==127 for c in name):raise ValueError('Device name must be 1–26 UTF-8 bytes without control characters.')
        out['device_name']=name.strip()
    if not out:raise ValueError('Choose a device setting to update.')
    return out

def pairing(ctx):
    path=Path(ctx.data_dir)/'bluetooth-pairing.json'
    if path.exists():return json.loads(path.read_text())
    data={'token':secrets.token_hex(24)}
    path.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as f:json.dump(data,f)
    return data


def python(ctx):
    return Path(ctx.data_dir) / 'device-tools/bin/python'


def tools_ready(ctx):
    return python(ctx).is_file() and (Path(ctx.data_dir) / 'device-tools/ready').is_file()


def bluetooth_ready(ctx):
    return tools_ready(ctx) and (Path(ctx.data_dir)/'device-tools/bluetooth-ready').is_file()


def default_name():
    name=getpass.getuser()+' kirometer'
    return name.encode()[:26].decode('utf-8',errors='ignore')


def ports():
    if sys.platform != 'darwin':
        return []
    return sorted(str(p) for pattern in ('cu.usbmodem*','cu.usbserial*','cu.SLAB_USBtoUART*','cu.wchusbserial*') for p in Path('/dev').glob(pattern))


def check_port(port):
    if port not in ports():
        raise ValueError('Select a currently connected USB serial device.')
    return port


async def port_inventory(ctx, current_ports, force=False):
    """Cache host metadata; enumeration never opens a serial connection."""
    global _inventory_cache
    if not current_ports or not tools_ready(ctx):
        return []
    key = (str(ctx.data_dir), tuple(current_ports))
    async with _inventory_lock:
        if not force and _inventory_cache and _inventory_cache[0] == key and time.monotonic() < _inventory_cache[1]:
            return _inventory_cache[2]
        try:
            raw = json.loads(await command([python(ctx), Path(__file__).with_name('port_inventory.py')], timeout=5))
            result = []
            for item in raw:
                if not isinstance(item, dict) or item.get('device') not in current_ports:
                    continue
                result.append({k: v for k, v in item.items()
                               if k in ('device', 'description', 'serial_number', 'manufacturer', 'vid', 'pid')
                               and (v is None or isinstance(v, (str, int))) and len(str(v)) <= 200})
                identifier = usb_identity(result[-1]).get('device_id')
                if identifier:
                    result[-1]['device_id'] = identifier
        except (ValueError, TypeError, OSError, TimeoutError):
            result = []
        _inventory_cache = (key, time.monotonic() + 15, result)
        return result


def chip_id(mac):
    # ESP.getEfuseMac() formats the six MAC bytes as a little-endian integer.
    if not isinstance(mac, str) or not re.fullmatch(r'(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}', mac):
        return None
    return ''.join(reversed(mac.lower().split(':')))


def usb_identity(item):
    serial = item.get('serial_number')
    result = {'usb_serial': serial} if serial else {}
    # Only the ESP native USB serial number is its chip MAC, not USB-UART serials.
    if item.get('vid') == 0x303A and item.get('pid') == 0x1001 and chip_id(serial):
        result.update(device_id=chip_id(serial), source='usb_serial')
    return result


def identity_from_console(job):
    match = re.search(r'^MAC:\s*((?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2})\s*$', job.get('console', ''), re.MULTILINE)
    if match:
        verified = chip_id(match.group(1))
        previous = job.get('device') or {}
        job['device'] = {**(previous if previous.get('device_id') == verified else {}),
                         'device_id': verified, 'source': 'bootloader'}


def trim_history():
    counts = {}
    kept = []
    for job in _history:
        device = job.get('device') or {}
        key = device.get('device_id') or device.get('usb_serial') or 'unidentified'
        counts[key] = counts.get(key, 0) + 1
        if counts[key] <= 8:
            kept.append(job)
    _history[:] = kept[:256]


def validate_bundle(path):
    manifest = Path(path).expanduser().resolve()
    if not manifest.is_file() or manifest.stat().st_size > 65536:
        raise ValueError('Choose a firmware bundle JSON manifest (maximum 64 KiB).')
    data = json.loads(manifest.read_text())
    if data.get('board') != BOARD or data.get('chip') != 'esp32s3':
        raise ValueError('Bundle must target the Waveshare ESP32-S3 Touch AMOLED 2.16.')
    images = data.get('images')
    if not isinstance(images,list) or not 1 <= len(images) <= 8:
        raise ValueError('Bundle needs 1–8 flash images.')
    result = []
    for item in images:
        file = (manifest.parent / item['file']).resolve()
        if not file.is_relative_to(manifest.parent) or not file.is_file():
            raise ValueError('Each image must be inside the bundle directory.')
        offset = int(str(item['offset']),0)
        size = file.stat().st_size
        if offset < 0 or offset % 4096 or size <= 0 or offset + size > 16*1024*1024:
            raise ValueError('Invalid image offset or size.')
        digest = hashlib.sha256(file.read_bytes()).hexdigest()
        if digest != item.get('sha256'):
            raise ValueError('Firmware checksum does not match the bundle.')
        result.append({'offset':offset,'file':str(file),'sha256':digest,'size':size})
    result.sort(key=lambda i:i['offset'])
    for a,b in zip(result,result[1:]):
        # Flash sectors are erased, so even unshared bytes in a sector must not overlap.
        if a['offset'] + ((a['size']+4095)//4096)*4096 > b['offset']:
            raise ValueError('Firmware image flash sectors overlap.')
    version = data.get('version')
    if not isinstance(version,str) or not 1 <= len(version) <= 80:
        raise ValueError('Bundle needs a firmware version.')
    return {'version':version,'board':BOARD,'images':result}


def load_history(ctx):
    global _history_path, _history, _job
    path = Path(ctx.data_dir) / 'firmware-updates.json'
    if _history_path == path:
        return
    _history_path = path
    try:
        stored = json.loads(path.read_text())
        _history = [job for job in stored[:256] if isinstance(job, dict)] if isinstance(stored, list) else []
    except (OSError, ValueError):
        _history = []
    for job in _history:
        identity_from_console(job)
        if job.get('state') == 'running':
            job.update(state='interrupted', message='App restarted during update. Check device status before retrying.')
    if _history:
        _job = _history[0]
    trim_history()
    persist_history()


def persist_history():
    if _history_path is None:
        return
    _history_path.parent.mkdir(parents=True, exist_ok=True)
    temp = _history_path.with_suffix('.tmp')
    temp.write_text(json.dumps(_history))
    temp.replace(_history_path)


def append_console(text):
    if not _job or _job.get('kind') != 'flash':
        return
    # Store plain console output, with bounded retention and no terminal controls.
    text = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', text).replace('\r', '\n')
    text = ''.join(c for c in text if c in '\n\t' or ord(c) >= 32)
    _job['console'] = (_job.get('console', '') + text)[-24000:]
    identity_from_console(_job)
    persist_history()


async def command(argv, timeout=180, on_output=None):
    proc = await asyncio.create_subprocess_exec(*map(str,argv), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    output = bytearray()
    decoder = codecs.getincrementaldecoder("utf-8")("replace")
    async def drain():
        while chunk := await proc.stdout.read(4096):
            if on_output: on_output(decoder.decode(chunk))
            output.extend(chunk)
            del output[:-16000]
        if on_output: on_output(decoder.decode(b"", final=True))
        return await proc.wait()
    try:
        code = await asyncio.wait_for(drain(),timeout)
    except BaseException:
        if proc.returncode is None:
            proc.kill()
            await proc.wait()
        raise
    if code:
        raise ValueError('Device tool failed. Check the cable, boot mode and that no serial monitor holds the port.')
    return output.decode(errors='replace')


async def worker(kind, ctx, port=None, bundle=None):
    global _job
    try:
        if kind in ('setup','setup_bluetooth'):
            host = sys.executable
            if not host:
                raise ValueError('Install Python 3 for macOS, then retry setup.')
            if not tools_ready(ctx):await command([host,'-m','venv','--without-pip',python(ctx).parent.parent],120)
            wheels = Path(__file__).resolve().parents[1] / 'vendor/wheels'
            expected=json.loads((wheels.parent/'checksums.json').read_text())
            for name,digest in expected.items():
                if hashlib.sha256((wheels/name).read_bytes()).hexdigest()!=digest:
                    raise ValueError('Bundled device tool checksum failed.')
            pip = next(wheels.glob('pip-*.whl'))
            await command([python(ctx),str(pip)+'/pip','install','--no-index','--find-links',wheels,'esptool==5.1.0','pyserial==3.5'],300)
            await command([python(ctx),'-c','import esptool, serial'])
            (Path(ctx.data_dir) / 'device-tools/ready').write_text('esptool 5.1.0; pyserial 3.5\n')
            await command([python(ctx),str(pip)+'/pip','install','--no-index','--find-links',wheels,'bleak==3.0.2'],300)
            await command([python(ctx),'-c','import bleak'])
            (Path(ctx.data_dir)/'device-tools/bluetooth-ready').write_text('bleak 3.0.2\n')
            _job.update(state='complete',message='USB and Bluetooth tools ready')
        else:
            check_port(port)
            # Stage validated bytes before starting esptool, preventing bundle edits mid-write.
            stage = Path(ctx.data_dir) / 'flash-staging' / _job['id']
            stage.mkdir(parents=True,exist_ok=True)
            argv = [python(ctx),'-m','esptool','--chip','esp32s3','--port',port,'--baud','460800','write-flash']
            try:
                for index,image in enumerate(bundle['images']):
                    raw = Path(image['file']).read_bytes()
                    if hashlib.sha256(raw).hexdigest() != image['sha256']:
                        raise ValueError('Firmware changed since validation; review the bundle again.')
                    file = stage / f'{index}.bin'
                    file.write_bytes(raw)
                    argv.extend([hex(image['offset']),file])
                append_console("Writing verified firmware images…\n")
                await command(argv,180,on_output=append_console)
                _job.update(state='complete',message='Flash verified by esptool. Check device status to confirm firmware boot.',version=bundle['version'])
            finally:
                shutil.rmtree(stage,ignore_errors=True)
    except asyncio.CancelledError:
        _job.update(state='interrupted',message='Operation interrupted; the device may need reflashing.')
        raise
    except Exception as exc:
        _job.update(state='failed',message=str(exc) if isinstance(exc,ValueError) else 'Device operation failed.')
    finally:
        _job['finished_at'] = time.time()
        if kind == 'flash':
            append_console('\n' + _job['message'] + '\n')
            persist_history()


async def start(kind,ctx,port=None,bundle=None):
    global _task,_job
    if sys.platform != 'darwin':
        raise ValueError('Device operations currently support macOS only.')
    async with _lock:
        load_history(ctx)
        if _task and not _task.done():
            raise ValueError('Another device operation is already running.')
        if kind == 'flash' and not tools_ready(ctx):
            raise ValueError('Set up device tools first.')
        identity = {}
        if kind == 'flash':
            check_port(port)
            inventory = await port_inventory(ctx, [port], force=True)
            target = next((item for item in inventory if item['device'] == port), {})
            identity = usb_identity(target)
            target_session = next((s for s in _sessions.values() if s.record.get('device_id') == identity.get('device_id') and identity.get('device_id')), None)
            _link = target_session.link if target_session else {}
            status = _link.get('status') or {}
            if identity.get('device_id') and identity['device_id'] == status.get('device_id'):
                identity['name'] = status.get('device_name')
            elif _link.get('connected') and _link.get('transport') == 'usb' and _link.get('port') == port and not identity.get('device_id'):
                identity.update(device_id=status.get('device_id'), name=status.get('device_name'), source='usb_status')
        # Only pause the device being flashed; other meters keep syncing.
        if kind == 'flash':
            for session in list(_sessions.values()):
                if session.record.get('endpoints', {}).get('usb') == port or (identity.get('device_id') and session.record.get('device_id') == identity['device_id']):
                    await stop_session(session, pause=True)
        _job = {'id':uuid.uuid4().hex,'kind':kind,'state':'running','port':port,'started_at':time.time(),'message':'Setting up tools…' if kind in ('setup','setup_bluetooth') else 'Flashing firmware…'}
        if kind == 'flash':
            _job.update(version=bundle['version'], device=identity, console='Preparing firmware update…\n')
            _history.insert(0, _job)
            trim_history()
            persist_history()
        _task = asyncio.create_task(worker(kind,ctx,port,bundle))
        return dict(_job)


async def stop():
    await disconnect()
    if _task and not _task.done():
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass


def bundled_firmware_version():
    try:
        manifest = json.loads((Path(__file__).resolve().parents[1] / 'firmware/firmware.json').read_text())
        return manifest.get('version') if manifest.get('board') == BOARD else None
    except (OSError, ValueError, AttributeError):
        return None


async def route(request,ctx):
    from aiohttp import web
    # Bind activity telemetry on any device request, even without opening the usage page.
    from .runtime import bind_activity_state
    bind_activity_state(request.app.get('state'))
    load_devices(ctx)
    action = request.path.rsplit('/',1)[-1]
    try:
        if request.method == 'GET':
            load_history(ctx)
            current_ports = ports()
            inventory = await port_inventory(ctx, current_ports)
            return web.json_response({'supported':sys.platform=='darwin','ports':current_ports,'port_details':inventory,'tools_ready':tools_ready(ctx),'bluetooth_ready':bluetooth_ready(ctx),'default_name':default_name(),'job':_job,'firmware_updates':_history,'devices':[s.public() for s in _sessions.values()],'link':next((s.link for s in _sessions.values() if s.link.get('connected')), {'connected':False,'status':None}),'bundled_firmware_version':bundled_firmware_version(),'bundled_firmware':str(Path(__file__).resolve().parents[1] / 'firmware/firmware.json')},headers={'Cache-Control':'no-store'})
        payload = await request.json()
        if not isinstance(payload,dict):
            raise ValueError('Device request must be a JSON object.')
        if action in ('setup','setup_bluetooth'):
            return web.json_response(await start(action,ctx),status=202)
        if action == 'disconnect':
            async with _lock:
                session = select_device(payload)
                await stop_session(session, pause=True)
            return web.json_response(session.public())
        if action == 'controls':
            global _control_seq
            session = select_device(payload)
            _link = session.link
            if not _link.get('connected'):raise ValueError('Connect a device before changing settings.')
            if not (_link.get('status') or {}).get('controls_supported'):raise ValueError('Flash Kirometer 0.5.3 to enable device controls.')
            controls=validate_controls(payload)
            if (controls.get('screen_layout')=='custom' or 'custom_face' in controls) and not (_link.get('status') or {}).get('custom_faces_supported'):
                raise ValueError('Update this device to firmware 0.9.0 for custom faces (Beta).')
            _control_seq+=1;controls['seq']=_control_seq;session.pending_controls=controls
            from .runtime import notify_update
            notify_update()
            return web.json_response({'queued':True,'control_seq':_control_seq},status=202)
        if action == 'bluetooth_scan':
            if not bluetooth_ready(ctx):raise ValueError('Set up Bluetooth tools first.')
            output=await command([python(ctx),Path(__file__).with_name('bluetooth_bridge.py'),'scan'],12)
            data=json.loads(output)
            if data.get('error'):raise ValueError(data['error'])
            return web.json_response(data)
        if action == 'bluetooth_connect':
            if not bluetooth_ready(ctx):raise ValueError('Set up Bluetooth tools first.')
            if _task and not _task.done():raise ValueError('Wait for the device operation to finish.')
            address=payload.get('address','')
            try:address=str(uuid.UUID(address))
            except (ValueError,TypeError,AttributeError):raise ValueError('Select a discovered Bluetooth device.')
            if not (Path(ctx.data_dir)/'bluetooth-pairing.json').exists():raise ValueError('Connect over USB once to provision Bluetooth pairing.')
            async with _lock:
                if _task and not _task.done(): raise ValueError('Wait for the device operation to finish.')
                session = await connect_device(ctx,address,'bluetooth',payload.get('name'))
            return web.json_response({'connecting':True,'configured_id':session.record['id']},status=202)
        if action == 'connect':
            async with _lock:
                if _task and not _task.done():
                    raise ValueError('Wait for the current operation.')
                if not tools_ready(ctx):
                    raise ValueError('Set up device tools first.')
                port = check_port(payload.get('port'))
                session = await connect_device(ctx,port,'usb')
                return web.json_response({'connecting':True,'configured_id':session.record['id']},status=202)
        if action == 'retry':
            async with _lock:
                if _task and not _task.done(): raise ValueError('Wait for the device operation to finish.')
                session = select_device(payload)
                if session.link.get('connected') or session.link.get('connecting'):
                    return web.json_response({'connecting': bool(session.link.get('connecting')), 'configured_id':session.record['id']})
                r = session.record
                if r['transport'] == 'usb':
                    if not tools_ready(ctx): raise ValueError('Set up device tools first.')
                    check_port(r['port'])
                elif not bluetooth_ready(ctx): raise ValueError('Set up Bluetooth tools first.')
                session = await connect_device(ctx,r['port'],r['transport'])
                return web.json_response({'connecting':True,'configured_id':session.record['id']},status=202)
        if action == 'bundle':
            return web.json_response(await asyncio.to_thread(validate_bundle,payload.get('path','')))
        if action == 'flash':
            if payload.get('confirm') is not True:
                raise ValueError('Confirm firmware replacement on the selected device.')
            port = check_port(payload.get('port'))
            bundle = await asyncio.to_thread(validate_bundle,payload.get('path',''))
            return web.json_response(await start('flash',ctx,port,bundle),status=202)
        if action == 'status':
            async with _lock:
                session = next((s for s in _sessions.values() if s.link.get('transport') == 'usb' and s.link.get('port') == payload.get('port') and s.task and not s.task.done()), None)
                if session:
                    _link = session.link
                    return web.json_response({'connected':_link['connected'],'firmware':'kirometer' if _link['status'] else 'unknown',**(_link['status'] or {}),'message':_link['message']})
                if _task and not _task.done():
                    raise ValueError('Wait for the device operation to finish.')
                if not tools_ready(ctx):
                    raise ValueError('Set up device tools first.')
                port = check_port(payload.get('port'))
                script = Path(__file__).with_name('serial_status.py')
                output = await command([python(ctx),script,port],8)
                return web.json_response(json.loads(output))
        raise ValueError('Unknown device operation.')
    except (ValueError, OSError, KeyError, TypeError):
        # No raw paths, tool output or exception details from untrusted firmware.
        import sys as _sys
        exc = _sys.exc_info()[1]
        return web.json_response({'error':str(exc) if isinstance(exc,ValueError) and not isinstance(exc,json.JSONDecodeError) else 'Invalid device request or bundle.'},status=400)


async def disconnect():
    for session in list(_sessions.values()):
        await stop_session(session)
    persist_devices()


async def bridge(ctx, port, transport, session):
    """Independent retry schedule; stable delivery resets exponential backoff."""
    failures = 0
    while True:
        session.retry_deadline = None
        started = time.monotonic()
        retry, delivered = await bridge_once(ctx, port, transport, session)
        if transport != 'bluetooth' or not retry: return
        # Avoid an endlessly aggressive retry loop on flapping connections.
        if delivered and time.monotonic() - started >= 30: failures = 0
        delay = backoff_seconds(failures)
        failures += 1
        session.retry_deadline = time.monotonic() + delay
        session.link.update(connected=False, connecting=False, status=None,
                            reconnecting=True, retry_in_seconds=delay, retry_attempt=failures,
                            message='Unavailable. Automatic reconnect is scheduled.')
        await asyncio.sleep(delay)


async def bridge_once(ctx,port,transport,session):
    proc=None;delivered=False;retry=True
    session.link={'connected':False,'port':port,'status':None,'transport':transport,'message':'Connecting…','connecting':True}
    try:
        proc=await asyncio.create_subprocess_exec(str(python(ctx)),str(Path(__file__).with_name('bluetooth_bridge.py' if transport=='bluetooth' else 'serial_bridge.py')),*([] if transport=='bluetooth' else [port]),stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.DEVNULL,limit=8192)
        if transport=='bluetooth':
            proc.stdin.write((json.dumps({'address':port,'token':pairing(ctx)['token']})+'\n').encode());await proc.stdin.drain()
        seq=0;provisioned=False
        while True:
            from . import runtime
            revision=runtime._revision
            seq+=1
            snapshot=runtime.current_snapshot()
            # Project only the usage contract; exclude cache paths and unrelated content.
            payload={k:snapshot.get(k) for k in ('available','stale','credits','activity','plan','session_activity')}
            payload.update(type='kirometer.usage',protocol=1,seq=seq)
            controls=session.pending_controls
            if transport=='usb' and not provisioned and (session.link.get('status') or {}).get('bluetooth_supported'):
                _control_seq_local=secrets.randbits(31) or 1
                controls={**(controls or {}),'seq':(controls or {}).get('seq',_control_seq_local),'pairing_token':pairing(ctx)['token']}
                if not (session.link.get('status') or {}).get('device_name') and 'device_name' not in controls:controls['device_name']=default_name()
            if controls:payload['controls']=controls
            sent_at=time.monotonic()
            proc.stdin.write((json.dumps(payload,allow_nan=False,separators=(',',':'))+'\n').encode())
            await proc.stdin.drain()
            raw=await asyncio.wait_for(proc.stdout.readline(),90 if seq==1 and transport=='bluetooth' else 10)
            if not raw:raise ValueError('USB connection closed.')
            answer=json.loads(raw)
            if answer.get('error_code')=='bond_removed':raise ValueError('Pairing changed. Forget only this Kirometer in macOS Bluetooth settings, then scan and reconnect.')
            connected=answer.get('acknowledged') is True and isinstance(answer.get('status'),dict)
            if not connected:raise ValueError('Device did not acknowledge usage.')
            expected = session.record.get('device_id')
            if expected and answer['status'].get('device_id') != expected:
                raise ValueError('Device identity changed. Use Add a device to connect this Kirometer.')
            delivered=True
            session.link={'connected':connected,'port':port,'status':answer.get('status') if connected else None,'last_ack_at':time.time() if connected else None,'delivery_ms':round((time.monotonic()-sent_at)*1000),'transport':transport,'message':('Wireless usage delivered · device responding' if transport=='bluetooth' else 'Usage delivered · device responding') if connected else 'USB open · no compatible firmware response'}
            await remember_status(session, answer['status'])
            if connected and controls and answer['status'].get('control_seq')==controls['seq']:
                if 'pairing_token' in controls:provisioned=True
                if session.pending_controls and session.pending_controls.get('seq')==controls['seq']:session.pending_controls=None
            await runtime.wait_for_update(revision)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        retry=not (isinstance(exc,ValueError) and str(exc).startswith(('Pairing changed.', 'Device identity changed.')))
        session.link={'connected':False,'port':port,'status':None,'transport':transport,'message':str(exc) if isinstance(exc,ValueError) and str(exc).startswith(('Pairing changed.', 'Device identity changed.')) else 'Bluetooth not responding. Check macOS Bluetooth permission, pairing and USB provisioning, then reconnect.' if transport=='bluetooth' else 'Device disconnected or not responding. Reconnect to retry.'}
    finally:
        if proc and proc.returncode is None:
            proc.kill();await proc.wait()
    persist_devices()
    return retry,delivered
