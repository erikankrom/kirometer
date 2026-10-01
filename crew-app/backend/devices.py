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
_link_task = None
_pending_controls = None
_control_seq = secrets.randbits(31)
_link = {"connected": False, "port": None, "status": None, "message": "No device linked"}


def validate_controls(payload):
    out={}
    if 'sound_enabled' in payload:
        if not isinstance(payload['sound_enabled'],bool):raise ValueError('Sound enabled must be true or false.')
        out['sound_enabled']=payload['sound_enabled']
    if 'sound_preset' in payload:
        if payload['sound_preset'] not in ('chime','ding','blip','pop','pulse'):raise ValueError('Choose a supported notification sound.')
        out['sound_preset']=payload['sound_preset']
    if 'screen_layout' in payload:
        if payload['screen_layout'] not in ('ghost','usage','orbit','sidekick','ticket','big_number'):raise ValueError('Choose an available screen layout.')
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
        _history = stored[:8] if isinstance(stored, list) else []
    except (OSError, ValueError):
        _history = []
    for job in _history:
        if job.get('state') == 'running':
            job.update(state='interrupted', message='App restarted during update. Check device status before retrying.')
    if _history:
        _job = _history[0]


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
        await disconnect()
        if _task and not _task.done():
            raise ValueError('Another device operation is already running.')
        if kind == 'flash' and not tools_ready(ctx):
            raise ValueError('Set up device tools first.')
        _job = {'id':uuid.uuid4().hex,'kind':kind,'state':'running','port':port,'started_at':time.time(),'message':'Setting up tools…' if kind in ('setup','setup_bluetooth') else 'Flashing firmware…'}
        if kind == 'flash':
            _job.update(version=bundle['version'], console='Preparing firmware update…\n')
            _history.insert(0, _job)
            del _history[8:]
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


async def route(request,ctx):
    from aiohttp import web
    global _link_task
    # Bind activity telemetry on any device request, even without opening the usage page.
    from .runtime import bind_activity_state
    bind_activity_state(request.app.get('state'))
    action = request.path.rsplit('/',1)[-1]
    try:
        if request.method == 'GET':
            load_history(ctx)
            return web.json_response({'supported':sys.platform=='darwin','ports':ports(),'tools_ready':tools_ready(ctx),'bluetooth_ready':bluetooth_ready(ctx),'default_name':default_name(),'job':_job,'firmware_updates':_history,'link':_link,'bundled_firmware':str(Path(__file__).resolve().parents[1] / 'firmware/firmware.json')},headers={'Cache-Control':'no-store'})
        payload = await request.json()
        if not isinstance(payload,dict):
            raise ValueError('Device request must be a JSON object.')
        if action in ('setup','setup_bluetooth'):
            return web.json_response(await start(action,ctx),status=202)
        if action == 'disconnect':
            await disconnect()
            return web.json_response(_link)
        if action == 'controls':
            global _pending_controls, _control_seq
            if not _link.get('connected'):raise ValueError('Connect a device before changing settings.')
            if not (_link.get('status') or {}).get('controls_supported'):raise ValueError('Flash Kirometer 0.5.3 to enable device controls.')
            controls=validate_controls(payload)
            if any(k in controls for k in ('sound_enabled','sound_preset')) and not (_link.get('status') or {}).get('sounds_supported'):
                raise ValueError('Update to firmware 0.7.0 or later for notification sounds.')
            _control_seq+=1;controls['seq']=_control_seq;_pending_controls=controls
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
            await disconnect()
            _link_task=asyncio.create_task(bridge(ctx,address,transport='bluetooth'))
            return web.json_response({'connecting':True},status=202)
        if action == 'connect':
            async with _lock:
                if _task and not _task.done():
                    raise ValueError('Wait for the current operation.')
                if not tools_ready(ctx):
                    raise ValueError('Set up device tools first.')
                port = check_port(payload.get('port'))
                await disconnect()
                _link_task = asyncio.create_task(bridge(ctx,port))
                return web.json_response({'connecting':True},status=202)
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
                if _link_task and not _link_task.done():
                    if payload.get('port') != _link.get('port'):
                        raise ValueError('Disconnect the current USB link before checking another device.')
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
    global _link_task, _link
    if _link_task and not _link_task.done():
        _link_task.cancel()
        try:
            await _link_task
        except asyncio.CancelledError:
            pass
    _link_task=None
    _link={'connected':False,'port':None,'status':None,'message':'No device linked'}


async def bridge(ctx,port,transport='usb'):
    """Keep the user-selected BLE link alive until explicitly disconnected."""
    global _link
    failures=0
    while True:
        retry,delivered=await bridge_once(ctx,port,transport)
        if transport!='bluetooth' or not retry:return
        if delivered:failures=0
        delay=min(30,5*2**min(failures,3));failures+=1
        _link={'connected':False,'port':port,'status':None,'transport':transport,
               'reconnecting':True,'retry_in_seconds':delay,'retry_attempt':failures,
               'message':f'Bluetooth connection interrupted. Retrying automatically in {delay} seconds. Keep your Kirometer powered on and nearby.'}
        await asyncio.sleep(delay)


async def bridge_once(ctx,port,transport='usb'):
    global _link, _pending_controls
    proc=None;delivered=False;retry=True
    _link={'connected':False,'port':port,'status':None,'transport':transport,'message':'Connecting…'}
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
            payload={k:snapshot.get(k) for k in ('available','stale','credits','activity','plan','needs_response','response_event')}
            payload.update(type='kirometer.usage',protocol=1,seq=seq,notification_baseline=seq==1)
            controls=_pending_controls
            if transport=='usb' and not provisioned and (_link.get('status') or {}).get('bluetooth_supported'):
                _control_seq_local=secrets.randbits(31) or 1
                controls={**(controls or {}),'seq':(controls or {}).get('seq',_control_seq_local),'pairing_token':pairing(ctx)['token']}
                if not (_link.get('status') or {}).get('device_name') and 'device_name' not in controls:controls['device_name']=default_name()
            if controls:payload['controls']=controls
            sent_at=time.monotonic()
            proc.stdin.write((json.dumps(payload,allow_nan=False)+'\n').encode())
            await proc.stdin.drain()
            raw=await asyncio.wait_for(proc.stdout.readline(),90 if seq==1 and transport=='bluetooth' else 10)
            if not raw:raise ValueError('USB connection closed.')
            answer=json.loads(raw)
            if answer.get('error_code')=='bond_removed':raise ValueError('Pairing changed. Forget only this Kirometer in macOS Bluetooth settings, then scan and reconnect.')
            connected=answer.get('acknowledged') is True and isinstance(answer.get('status'),dict)
            if not connected:raise ValueError('Device did not acknowledge usage.')
            delivered=True
            _link={'connected':connected,'port':port,'status':answer.get('status') if connected else None,'last_ack_at':time.time() if connected else None,'delivery_ms':round((time.monotonic()-sent_at)*1000),'transport':transport,'message':('Wireless usage delivered · device responding' if transport=='bluetooth' else 'Usage delivered · device responding') if connected else 'USB open · no compatible firmware response'}
            if connected and controls and answer['status'].get('control_seq')==controls['seq']:
                if 'pairing_token' in controls:provisioned=True
                if _pending_controls and _pending_controls.get('seq')==controls['seq']:_pending_controls=None
            await runtime.wait_for_update(revision)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        retry=not (isinstance(exc,ValueError) and str(exc).startswith('Pairing changed.'))
        _link={'connected':False,'port':port,'status':None,'transport':transport,'message':str(exc) if isinstance(exc,ValueError) and str(exc).startswith('Pairing changed.') else 'Bluetooth not responding. Check macOS Bluetooth permission, pairing and USB provisioning, then reconnect.' if transport=='bluetooth' else 'Device disconnected or not responding. Reconnect to retry.'}
    finally:
        if proc and proc.returncode is None:
            proc.kill();await proc.wait()
    return retry,delivered
