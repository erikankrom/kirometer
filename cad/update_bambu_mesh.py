"""Replace the body mesh while retaining Bambu plates, colors and printer settings."""
import struct,zipfile,xml.etree.ElementTree as E
from pathlib import Path
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
E.register_namespace('',ns);E.register_namespace('p','http://schemas.microsoft.com/3dmanufacturing/production/2015/06');E.register_namespace('BambuStudio','http://schemas.bambulab.com/package/2021')
with zipfile.ZipFile('exports/kirometer-bambu.3mf') as z:
 s=E.fromstring(z.read('Metadata/model_settings.config')); main=E.fromstring(z.read('3D/3dmodel.model'))
 ob=next(o for o in s.findall('object') if o.find("metadata[@key='name']").attrib['value']=='kirometer-ghost-body.stl'); part=ob.find('part')
 offset=[float(part.find(f"metadata[@key='source_offset_{a}']").attrib['value']) for a in 'xyz']
 resource=next(o for o in main.find(f'{{{ns}}}resources') if o.attrib.get('id')==ob.attrib['id']);component=resource.find(f'{{{ns}}}components')[0];path=component.attrib['{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}path'].lstrip('/')
 model=E.fromstring(z.read(path)); obj=model.find(f'{{{ns}}}resources')[0];old=obj.find(f'{{{ns}}}mesh');obj.remove(old);mesh=E.SubElement(obj,f'{{{ns}}}mesh');verts=E.SubElement(mesh,f'{{{ns}}}vertices');tris=E.SubElement(mesh,f'{{{ns}}}triangles')
 data=Path('exports/kirometer-ghost-body.stl').read_bytes();n=struct.unpack_from('<I',data,80)[0];lookup={}
 for i in range(n):
  values=struct.unpack_from('<12fH',data,84+50*i);ids=[]
  for j in (3,6,9):
   p=tuple(values[j:j+3])
   if p not in lookup:
    lookup[p]=len(lookup);E.SubElement(verts,f'{{{ns}}}vertex',**{a:format(p[k]-offset[k],'.9g') for k,a in enumerate('xyz')})
   ids.append(lookup[p])
  E.SubElement(tris,f'{{{ns}}}triangle',**{f'v{k+1}':str(v) for k,v in enumerate(ids)})
 for m in ob.findall('metadata'):
  if 'face_count' in m.attrib:m.set('face_count',str(n))
 part.find('mesh_stat').set('face_count',str(n))
 with zipfile.ZipFile('/tmp/kirometer-ridge-free-input.3mf','w',zipfile.ZIP_DEFLATED) as out:
  for info in z.infolist():
   d=z.read(info.filename)
   if info.filename==path:d=E.tostring(model,encoding='utf-8',xml_declaration=True)
   elif info.filename=='Metadata/model_settings.config':d=E.tostring(s,encoding='utf-8',xml_declaration=True)
   out.writestr(info,d)
 print('Updated body:',n,'triangles')
