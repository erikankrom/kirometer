"""Validate stored Bambu geometry, plate assignments, and support-free slice output."""
import json,zipfile,xml.etree.ElementTree as E
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'exports'
ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
r=json.loads((OUT/'bambu-slice-validation.json').read_text());assert r['return_code']==0
geometry=json.loads((OUT/'geometry-validation.json').read_text())
with zipfile.ZipFile(OUT/'kirometer-bambu.3mf') as z:
 assert z.testzip() is None
 c=json.loads(z.read('Metadata/project_settings.config'));s=E.fromstring(z.read('Metadata/model_settings.config'))
 assert c['filament_colour']==['#FFFFFF','#9147FF'] and c['enable_support']=='0'
 assert c['printer_model']=='Bambu Lab P1S'
 objects={o.attrib['id']:o.find("metadata[@key='name']").attrib['value'] for o in s.findall('object')}
 assert len(objects)==3 and not any('button' in n for n in objects.values())
 plates=[]
 for i,plate in enumerate(s.findall('plate'),1):
  ids=[item.find("metadata[@key='object_id']").attrib['value'] for item in plate.findall('model_instance')]
  assert len(ids)==1
  sliced=r['sliced_plates'][i-1];assert sliced['warning_message']==''
  assert not any('support' in k.lower() and v>0 for k,v in sliced['feature_type_times'].items())
  assert '; FEATURE: Support' not in z.read(f'Metadata/plate_{i}.gcode').decode()
  slot=sliced['filaments'][0]['id'];assert slot==(2 if i==3 else 1)
  plates.append({'name':plate.find("metadata[@key='plater_name']").attrib['value'],'objects':[objects[oid] for oid in ids],'filament_slot':slot,'estimated_seconds':round(sliced['total_predication'],1),'estimated_grams':round(sum(f['total_used_g'] for f in sliced['filaments']),2),'slice_warnings':sliced['warning_message']})
 assert len(plates)==3
 counts=[]
 for n in z.namelist():
  if n.startswith('3D/Objects/') and n.endswith('.model'):
   counts += [len(t) for t in E.fromstring(z.read(n)).findall('.//m:triangles',ns)]
 expected=[v['triangles'] for v in json.loads((OUT/'stl-validation.json').read_text()).values()]
 assert sorted(counts)==sorted(expected),(counts,expected)
 output={'revision':geometry['parameters_mm'].get('revision','v7'),'producer':'Bambu Studio 02.08.02.61','printer':'P1S','nozzle_mm':.4,'filament_colors':c['filament_colour'],'supports':c['enable_support'],'physically_print_tested':False,'stored_mesh_triangle_counts':counts,'plates':plates}
 (OUT/'3mf-validation.json').write_text(json.dumps(output,indent=2));print(json.dumps(output,indent=2))
