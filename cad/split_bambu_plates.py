"""Arrange the existing Bambu project on coupon, white-body, and purple-accent plates."""
from pathlib import Path
import copy,json,zipfile,sys,xml.etree.ElementTree as E
src=Path(sys.argv[1]) if len(sys.argv)>1 else Path('exports/kirometer-bambu.3mf')
dst=Path(sys.argv[2]) if len(sys.argv)>2 else Path('/tmp/kirometer-three-plates.3mf')
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
E.register_namespace('',ns);E.register_namespace('p','http://schemas.microsoft.com/3dmanufacturing/production/2015/06');E.register_namespace('BambuStudio','http://schemas.bambulab.com/package/2021')
with zipfile.ZipFile(src) as z:
 cfg=json.loads(z.read('Metadata/project_settings.config')); model=E.fromstring(z.read('3D/3dmodel.model')); settings=E.fromstring(z.read('Metadata/model_settings.config'))
 names={o.attrib['id']:o.find("metadata[@key='name']").attrib['value'] for o in settings.findall('object')}
 groups=[('01 Fit coupon — white',lambda n:'coupon' in n,(0,0)),('02 Body — white',lambda n:'ghost-body' in n,(307.2,0)),('03 Accents — purple',lambda n:'coupon' not in n and 'ghost-body' not in n,(0,-307.2))]
 old_plates=settings.findall('plate');instances={i.find("metadata[@key='object_id']").attrib['value']:copy.deepcopy(i) for p in old_plates for i in p.findall('model_instance')}
 for old in old_plates:settings.remove(old)
 for index,(label,test,origin) in enumerate(groups,1):
  plate=E.SubElement(settings,'plate')
  for key,value in [('plater_id',str(index)),('plater_name',label),('locked','false'),('filament_map_mode','Auto For Flush'),('gcode_file',''),('thumbnail_file',f'Metadata/plate_{index}.png'),('thumbnail_no_light_file',f'Metadata/plate_no_light_{index}.png'),('top_file',f'Metadata/top_{index}.png'),('pick_file',f'Metadata/pick_{index}.png')]:E.SubElement(plate,'metadata',key=key,value=value)
  ids=[oid for oid,n in names.items() if test(n)]
  for oid in ids:plate.append(instances[oid])
  for item in model.find(f'{{{ns}}}build'):
   oid=item.attrib['objectid']
   if oid not in ids:continue
   n=names[oid];x,y=(128,128)
   if index==3:
    if 'cover' in n:x,y=128,160
    elif 'key' in n:x,y=128,60
    elif 'button-1' in n:x,y=100,60
    elif 'button-2' in n:x,y=112,60
    else:x,y=145,60
   # Mesh components are already centered, in their validated print orientations.
   item.set('transform',f'1 0 0 0 1 0 0 0 1 {x+origin[0]} {y+origin[1]} 0')
 for o in settings.findall('object'):
  o.find("metadata[@key='extruder']").set('value','1' if ('body' in names[o.attrib['id']] or 'coupon' in names[o.attrib['id']]) else '2')
 cfg['filament_colour']=['#FFFFFF','#9147FF'];cfg['filament_type']=['PLA','PLA'];cfg['filament_settings_id']=['Bambu PLA Basic @BBL P1S 0.4 nozzle']*2
 # Duplicate each one-slot filament option, not machine/extruder options.
 preset=json.loads(Path('/tmp/kirometer-presets/filament.json').read_text())
 for key in preset:
  if isinstance(cfg.get(key),list) and len(cfg[key])==1:cfg[key]=cfg[key]*2
 cfg['filament_colour']=['#FFFFFF','#9147FF']
 cfg['filament_ids']=['GFA00','GFA00']
 for key,value in list(cfg.items()):
  if key.startswith('filament_') and isinstance(value,list) and len(value)==1:cfg[key]=value*2
 cfg['filament_extruder_variant']=['Direct Drive Standard','Direct Drive High Flow']*2
 cfg['flush_volumes_matrix']=['0','140','140','0']
 cfg['flush_volumes_vector']=['140','140','140','140']
 data={'Metadata/project_settings.config':json.dumps(cfg,indent=2).encode(),'Metadata/model_settings.config':E.tostring(settings,encoding='utf-8',xml_declaration=True),'3D/3dmodel.model':E.tostring(model,encoding='utf-8',xml_declaration=True),'Metadata/filament_sequence.json':json.dumps({f'plate_{i}':{'nozzle_sequence':[],'optimal_assignment':[],'sequence':[]} for i in range(1,4)}).encode()}
 with zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED) as out:
  for info in z.infolist():out.writestr(info,data.get(info.filename,z.read(info.filename)))
print('Prepared three plates with white/purple PLA assignments')
