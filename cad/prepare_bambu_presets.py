"""Resolve bundled Bambu presets, including inherited values and G-code includes."""
import json
from pathlib import Path
root=Path('/Applications/BambuStudio.app/Contents/Resources/profiles/BBL')
registry={}
for p in root.rglob('*.json'):
 try:
  d=json.loads(p.read_text());registry[p.stem]=d
  if 'name' in d:registry[d['name']]=d
 except (ValueError,OSError):pass

def resolve(name,stack=()):
 if name in stack:raise ValueError('Preset cycle')
 d=registry[name];out={}
 if d.get('inherits'):out.update(resolve(d['inherits'],stack+(name,)))
 for inc in d.get('include',[]):out.update(resolve(inc,stack+(name,)))
 out.update({k:v for k,v in d.items() if k not in ('inherits','include')})
 return out

out=Path('/tmp/kirometer-presets');out.mkdir(exist_ok=True)
for kind,name in [('machine','Bambu Lab P1S 0.4 nozzle'),('process','0.20mm Standard @BBL X1C'),('filament','Bambu PLA Basic @BBL P1S 0.4 nozzle')]:
 d=resolve(name)
 if kind=='process':d.update(layer_height='0.2',wall_loops='4',sparse_infill_density='20%',enable_support='0')
 if kind=='filament':d['filament_colour']=['#F4F0EC']
 (out/f'{kind}.json').write_text(json.dumps(d,indent=2))
 print(kind,d.get('printable_area'),len(d))
