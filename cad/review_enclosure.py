"""Render assembled rear detail and verify button/adapter reference clearances.
Run after build_enclosure.py using Blender --background --python.
The adapter is a simplified bounding reference, not a manufacturer CAD model.
"""
import bpy, bmesh, math, json
from pathlib import Path
from mathutils import Matrix, Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'cad/kirometer-enclosure.blend'))
report=json.loads((ROOT/'exports/geometry-validation.json').read_text())
P=report['parameters_mm'];tilt=math.radians(P['desk_tilt_degrees'])
body=bpy.data.objects['Kirometer ghost body'];cover=bpy.data.objects['Removable rear cover']
def volume_intersection(a,b):
 p=a.copy();p.data=a.data.copy();bpy.context.collection.objects.link(p)
 bpy.context.view_layer.objects.active=p
 m=p.modifiers.new('Clearance verification','BOOLEAN');m.operation='INTERSECT';m.solver='EXACT';m.object=b
 bpy.ops.object.modifier_apply(modifier=m.name)
 bm=bmesh.new();bm.from_mesh(p.data);value=abs(bm.calc_volume());bm.free()
 bpy.data.objects.remove(p,do_unlink=True)
 return round(value,6)
buttons=[o for o in bpy.data.objects if o.name.startswith('Factory button - reference')]
checks={o.name:{'body':volume_intersection(o,body),'cover':volume_intersection(o,cover)} for o in buttons}
# Check a generous cap envelope and a 12 mm fingertip approach corridor.
# Cap protrusion/travel is not dimensioned by Waveshare: 1.5 mm is a test allowance,
# not a manufacturer specification. Do not test against the stock case itself.
access_checks={}
for x in (-10,0,10):
 for label,radius,y0,y1 in [('cap_envelope',P['button_diameter']/2,27,28.5),('finger_approach_12mm',6,27.8,60)]:
  bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=radius,depth=y1-y0,location=(x,(y0+y1)/2,P['screen_seat']+P['button_center_from_front']))
  probe=bpy.context.object;probe.rotation_euler.x=math.pi/2
  bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
  probe.matrix_world=Matrix.Rotation(tilt,4,'X')@probe.matrix_world
  values={'body':volume_intersection(probe,body),'cover':volume_intersection(probe,cover)}
  access_checks[f'{x}_{label}']=values
  bpy.data.objects.remove(probe,do_unlink=True)
  assert all(v<.01 for v in values.values()),(x,label,values)
report['button_access']={
 'drawing_url':'https://docs.waveshare.com/assets/images/ESP32-S3-Touch-AMOLED-2.16-details-size-9be8e99d5f546b1b8ce338c394d988fd.webp',
 'center_from_factory_front_mm':P['button_center_from_front'],
 'center_from_printed_front_mm':P['screen_seat']+P['button_center_from_front'],
 'button_diameter_mm':P['button_diameter'], 'center_spacing_mm':10,
 'minimum_depth_gap_to_front_wall_mm':round(P['screen_seat']+P['button_center_from_front']-P['button_diameter']/2-P['button_wall_base_z'],2),
 'wall_slope_degrees_from_case_vertical':round(math.degrees(math.atan((P['button_wall_base_z']-P['button_wall_top_z'])/(39-27.1))),2),
 'side_gap_at_outer_buttons_mm':round(17.4-10-P['button_diameter']/2,2),
 'tested_finger_corridor_diameter_mm':12,
 'cap_height_test_allowance_mm':1.5,
 'note':'Cap height and travel are not dimensioned in the official drawing. Finger corridor is a geometric proxy; physical ergonomics remain unverified.',
 'access_overlap_mm3':access_checks}
# 21.1 x 11.9 x 6.1 mm listing envelope, orientation inferred from user photos.
# Exact plug insertion geometry and cable overmold are still physical-fit checks.
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,-22.65,16.9))
adapter=bpy.context.object;adapter.name='UGREEN adapter simplified envelope - NOT PRINTABLE'
adapter.dimensions=(11.9,6.1,21.1);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
adapter.matrix_world=Matrix.Rotation(tilt,4,'X')@adapter.matrix_world
adapter.data.materials.append(bpy.data.materials['Kiro prey 900'])
checks['adapter_approximate_envelope']={'body':volume_intersection(adapter,body),'cover':volume_intersection(adapter,cover)}
for obj,values in checks.items():
 assert all(v<.01 for v in values.values()),(obj,values)
report['button_and_adapter_clearance_checks_mm3']=checks
report['adapter_reference']={'url':'https://www.amazon.com/dp/B0FNCT8NS7','listing_dimensions_mm':[21.1,11.9,6.1],'orientation_and_inserted_position':'inferred from user photos; physical fit unverified','opening_width_mm':16}
report['physical_validation']='Pending revised coupon and assembly print'
(ROOT/'exports/geometry-validation.json').write_text(json.dumps(report,indent=2))
# Readable rear perspective with world Y as up.
scene=bpy.context.scene;camera=scene.camera
camera.location=(-95,75,210);target=Vector((0,0,17))
def aim(target):
 direction=(target-camera.location).normalized();right=direction.cross(Vector((0,1,0))).normalized();up=right.cross(direction).normalized()
 camera.rotation_euler=Matrix((right,up,-direction)).transposed().to_euler()
aim(target);camera.data.ortho_scale=115
scene.cycles.samples=48
scene.render.filepath=str(ROOT/'previews/kirometer-rear.png')
bpy.ops.render.render(write_still=True)
# Top view reveals factory-button reach without changing the actual geometry.
camera.location=(80,170,155);aim(Vector((0,9,14)));camera.data.ortho_scale=105
scene.render.filepath=str(ROOT/'previews/kirometer-button-access.png')
bpy.ops.render.render(write_still=True)
print(json.dumps(checks,indent=2))
