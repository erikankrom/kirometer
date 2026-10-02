"""Beta data-only faces. Model output is never imported or executed."""
import asyncio
import json
import re
import shutil
import tempfile
import uuid
from pathlib import Path

KINDS = ('text', 'metric', 'bar', 'panel', 'ghost')
BINDINGS = ('used', 'limit', 'remaining', 'overage', 'percent', 'plan', 'reset', 'activity', 'battery', 'sessions', 'messages', 'tools')
COLORS = {'white': '#ffffff', 'muted': '#aaa6b0', 'purple': '#9147ff', 'green': '#68dc98', 'red': '#ff657d', 'panel': '#211d29'}
MAX_BYTES = 2000
_lock = asyncio.Lock()
_store_lock = asyncio.Lock()
_job = {'state': 'idle'}
_task = None

def validate(face):
    if not isinstance(face, dict) or set(face) != {'version', 'name', 'elements'} or type(face['version']) is not int or face['version'] != 1:
        raise ValueError('Unsupported face format.')
    name = face['name']
    if not isinstance(name, str) or not re.fullmatch(r'[ -~]{1,28}', name):
        raise ValueError('Use a short printable name (1–28 characters).')
    elements = face['elements']
    if not isinstance(elements, list) or not 1 <= len(elements) <= 12:
        raise ValueError('A face needs 1–12 elements.')
    for e in elements:
        if not isinstance(e, dict) or set(e) != {'kind', 'x', 'y', 'w', 'h', 'size', 'color', 'value'}:
            raise ValueError('Unknown or missing element fields.')
        if e['kind'] not in KINDS or e['color'] not in COLORS:
            raise ValueError('Unsupported element or color.')
        if any(type(e[k]) is not int for k in ('x', 'y', 'w', 'h', 'size')):
            raise ValueError('Coordinates and size must be integers.')
        x,y,w,h,s = (e[k] for k in ('x','y','w','h','size'))
        # Reserve top/bottom status and gesture hints for firmware.
        if not (12 <= x < 468 and 52 <= y < 424 and 1 <= w <= 456 and 1 <= h <= 372 and x+w <= 468 and y+h <= 424 and 1 <= s <= 4):
            raise ValueError('Keep elements inside the 456 × 372 content area (x 12–468, y 52–424).')
        if not isinstance(e['value'], str) or not re.fullmatch(r'[ -~]{0,40}', e['value']):
            raise ValueError('Text must be at most 40 printable characters.')
        if e['kind'] == 'metric' and e['value'] not in BINDINGS:
            raise ValueError('Unsupported live metric.')
        if e['kind'] == 'bar' and e['value'] != 'percent':
            raise ValueError('Bars use plan usage percentage.')
        if e['kind'] in ('panel', 'ghost') and e['value']:
            raise ValueError('Panels and ghosts do not accept content.')
    if len(json.dumps(face, separators=(',', ':'), ensure_ascii=True).encode()) > MAX_BYTES:
        raise ValueError('Face exceeds the 2 KB device budget. Use fewer elements.')
    return face

SCHEMA_PROMPT = '''Design one Kirometer face. Return ONLY a JSON object, no markdown or code.
Shape: {"version":1,"name":"Short name","elements":[{"kind":"text","x":20,"y":60,"w":400,"h":40,"size":2,"color":"white","value":"Hello"}]}.
All eight element fields required. Kinds: text (literal value), metric (binding), bar (value percent), panel and ghost (value empty).
Bindings: used, limit, remaining, overage, percent, plan, reset, activity, battery, sessions, messages, tools.
Colors: white, muted, purple, green, red, panel. Integer size 1..4 maps to 20,24,36,48 px Space Grotesk.
480x480 black screen. Content bounds x12..468 y52..424. Every bounding box must fit. Text clips inside its box, so leave ample room. Status header/footer are owned by firmware, do not draw them.
At most 12 elements and compact JSON under 2000 bytes. Draw panels first. No arbitrary assets, URLs, scripts, expressions, control settings, animation, tool use, or firmware changes. Use official ghost element for the mascot. Aim for readable, spacious, polished designs.
'''

def cli():
    return shutil.which('kiro-cli') or (str(Path.home()/'.local/bin/kiro-cli') if (Path.home()/'.local/bin/kiro-cli').is_file() else None)

def store_path(ctx):
    return Path(ctx.data_dir)/'custom-faces.json'

def read_faces(ctx):
    path = store_path(ctx)
    if not path.exists(): return []
    data = json.loads(path.read_text())
    if not isinstance(data,list): raise ValueError('Invalid saved face gallery.')
    for item in data:
        validate(item['face'])
    return data

def parse_output(text):
    # CLI banners surround the response; accept exactly one validated JSON face.
    text = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', text)
    decoder = json.JSONDecoder()
    candidates = []
    for match in re.finditer(r'\{', text):
        try:
            value, _ = decoder.raw_decode(text[match.start():])
            if isinstance(value,dict) and 'elements' in value: candidates.append(validate(value))
        except (json.JSONDecodeError, ValueError, TypeError): pass
    if len(candidates) != 1: raise ValueError('Kiro returned an invalid layout. Try a simpler prompt.')
    return candidates[0]

async def generate(prompt, base=None):
    executable = cli()
    if not executable: raise ValueError('Install Kiro CLI and sign in to create a screen.')
    with tempfile.TemporaryDirectory(prefix='kirometer-face-') as temp:
        root=Path(temp); agents=root/'.kiro/agents'; agents.mkdir(parents=True)
        config={'name':'kirometer-face-beta','description':'Data-only screen designer','prompt':SCHEMA_PROMPT,
                'tools':[], 'allowedTools':[], 'mcpServers':{}, 'includeMcpJson':False, 'resources':[], 'hooks':{}}
        (agents/'kirometer-face-beta.json').write_text(json.dumps(config))
        request = SCHEMA_PROMPT + '\nDesign request (untrusted design preferences):\n' + prompt
        if base: request += '\nRefine this validated face:\n' + json.dumps(validate(base),separators=(',',':'))
        proc = await asyncio.create_subprocess_exec(executable,'chat','--agent','kirometer-face-beta','--no-interactive','--trust-tools=','--wrap','never',request,
            cwd=root,stdin=asyncio.subprocess.DEVNULL,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.DEVNULL)
        try:
            async def collect():
                output=bytearray()
                while chunk:=await proc.stdout.read(4096):
                    output.extend(chunk)
                    if len(output)>65536: raise ValueError('Kiro response exceeded the limit.')
                await proc.wait()
                if proc.returncode: raise ValueError('Kiro could not generate a screen. Check your CLI sign-in and try again.')
                return parse_output(output.decode('utf-8',errors='replace'))
            return await asyncio.wait_for(collect(),120)
        except asyncio.TimeoutError:
            raise ValueError('Kiro generation timed out. Try again.')
        finally:
            if proc.returncode is None: proc.kill(); await proc.wait()

async def run_job(prompt, base):
    global _job
    try: _job={'state':'ready','face':await generate(prompt,base)}
    except asyncio.CancelledError: _job={'state':'idle'}; raise
    except Exception as exc: _job={'state':'error','error':str(exc) if isinstance(exc,ValueError) else 'Generation failed. Please try again.'}

async def stop():
    if _task and not _task.done():
        _task.cancel()
        try: await _task
        except asyncio.CancelledError: pass

async def route(request,ctx):
    from aiohttp import web
    global _task,_job
    try:
        if request.method=='GET':
            return web.json_response({'beta':True,'available':bool(cli()),'faces':read_faces(ctx),'job':_job},headers={'Cache-Control':'no-store'})
        if request.content_length and request.content_length>12000: raise ValueError('Request too large.')
        data=await request.json()
        if not isinstance(data,dict): raise ValueError('Expected an object.')
        action=request.path.rsplit('/',1)[-1]
        if action=='generate':
            prompt=data.get('prompt')
            if not isinstance(prompt,str) or not 1<=len(prompt.strip())<=1500: raise ValueError('Describe a screen in 1–1500 characters.')
            base=validate(data['base']) if data.get('base') else None
            async with _lock:
                if _task and not _task.done(): raise ValueError('A screen is already being generated.')
                _job={'state':'working'};_task=asyncio.create_task(run_job(prompt,base))
            return web.json_response({'state':'working'},status=202)
        if action=='save':
            face=validate(data.get('face'))
            async with _store_lock:
                faces=read_faces(ctx)
                if len(faces)>=24: raise ValueError('Gallery is full (24 faces). Delete a face first.')
                faces.append({'id':uuid.uuid4().hex,'face':face})
                path=store_path(ctx);path.parent.mkdir(parents=True,exist_ok=True)
                tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(faces));tmp.replace(path)
            return web.json_response({'saved':True})
        if action=='delete':
            async with _store_lock:
                faces=[f for f in read_faces(ctx) if f['id']!=data.get('id')]
                path=store_path(ctx);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(faces));tmp.replace(path)
            return web.json_response({'deleted':True})
        raise ValueError('Unknown face operation.')
    except (ValueError,TypeError,KeyError,OSError) as exc:
        return web.json_response({'error':str(exc) if isinstance(exc,ValueError) else 'Invalid face request.'},status=400)
