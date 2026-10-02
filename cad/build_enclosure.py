"""Run with: blender --background --python cad/build_enclosure.py

All modeling coordinates are millimeters. The body prints with its front on Z=0.
The pocket fits the complete Waveshare stock housing, not the bare PCB.
"""
import bpy
import bmesh
import math
import json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'exports'
OUT.mkdir(exist_ok=True)
P = dict(stock_width=46.0, stock_height=46.0, stock_depth=22.5,
         clearance_per_side=0.4, front_thickness=2.4, screen_seat=0.8,
         body_depth=27.5, cover_thickness=2.4, window=44.4,
         pocket_radius=6.2, pocket_wall=2.4,
         usb_width=16.0, usb_height=8.0, adapter_front_offset=5.0,
         adapter_fit='UGREEN_B0FNCT8NS7_16mm_channel_physical_fit_pending',
         button_center_from_front=9.6, button_diameter=5.3,
         button_wall_base_z=3.2, button_wall_top_z=2.4,
         button_access='direct_buttons_near_vertical_wall_with_cover_tongue', revision='v9',
         desk_tilt_degrees=15.0, rear_tail_extension=8.5,
         target_body_width=66.0, target_body_height=80.0, maximum_depth=29.9,
         ground_y=-39.3,
         closure_slide_travel=0.0, closure_clearance=0.04, socket_diameter=2.68, peg_root_diameter=2.64,
         closure_type='vertical_tapered_peg_friction_fit',
         print_design='support_minimized_45_degree_roofs_and_tapers')

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)


def material(name, color):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*color, 1)
    m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .34
    return m


WHITE = material('Ghost / warm white', (.94, .93, .91))
PURPLE = material('Kiro purple 500', (.5686, .2784, 1))
DARK = material('Kiro prey 900', (.095, .085, .114))
GLASS = material('AMOLED glass', (0, 0, 0))


def extrude(name, points, z0, z1):
    n = len(points)
    verts = [(x, y, z) for z in (z0, z1) for x, y in points]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2*n))]
    faces += [(i, (i+1) % n, (i+1) % n+n, i+n) for i in range(n)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(ob)
    # Normalize winding before CSG regardless of contour direction.
    bm = bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh); bm.free()
    return ob


def rounded_points(w,h,r,x=0,y=0):
    pts = []
    for cx, cy, start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
        for j in range(17):
            a = math.radians(start+j*90/16)
            pts.append((x+cx+r*math.cos(a), y+cy+r*math.sin(a)))
    return pts


def rounded(name,w,h,r,z0,z1,x=0,y=0):
    return extrude(name,rounded_points(w,h,r,x,y),z0,z1)


def loft(name,first,last,z0,z1):
    n=len(first)
    mesh=bpy.data.meshes.new(name)
    verts=[(x,y,z0) for x,y in first]+[(x,y,z1) for x,y in last]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh.from_pydata(verts,[],faces); mesh.update()
    ob=bpy.data.objects.new(name,mesh); bpy.context.collection.objects.link(ob)
    bm=bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(mesh); bm.free()
    return ob


def box(name, size, center):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    ob = bpy.context.object; ob.name = name
    ob.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return ob


def cyl(name, radius, depth, center, axis='Z'):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=radius, depth=depth, location=center)
    ob = bpy.context.object; ob.name = name
    if axis == 'Y': ob.rotation_euler.x = math.pi/2
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return ob


def boolean(target, tool, op='DIFFERENCE'):
    bpy.context.view_layer.objects.active = target
    mod = target.modifiers.new('CSG', 'BOOLEAN')
    mod.operation = op; mod.solver = 'EXACT'; mod.object = tool
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(tool, do_unlink=True)


def assign_material(ob, mat):
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    for polygon in ob.data.polygons: polygon.material_index=0


def along_y(name, profile, y0, y1):
    ob=extrude(name,profile,y0,y1)
    for v in ob.data.vertices:
        x,z,y=v.co
        v.co=(x,y,z)
    bm=bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(ob.data); bm.free()
    return ob


def curve_outline():
    # Smooth asymmetric three-tail ghost, with two small coplanar standing flats.
    start = (0,39)
    segments = [
      ((20,39),(29,34),(29,24)),
      ((29,8),(29,-12),(25,-28)),
      ((23,-34),(20,-41),(16,-41)),
      ((14,-41),(12,-41),(10,-41)),
      ((6,-41),(3,-36),(1,-33)),
      ((-3,-36),(-6,-41),(-10,-41)),
      ((-12,-41),(-14,-41),(-16,-41)),
      ((-25,-41),(-26,-31),(-24,-25)),
      ((-31,-29),(-37,-26),(-37,-21)),
      ((-37,-15),(-30,-10),(-29,1)),
      ((-29,14),(-30,27),(-22,34)),
      ((-16,38),(-7,39),(0,39)),
    ]
    pts=[]; a=start
    for b,c,d in segments:
        for i in range(24):
            t=(i+.5)/24; u=1-t
            pts.append((u**3*a[0]+3*u*u*t*b[0]+3*u*t*t*c[0]+t**3*d[0],
                        u**3*a[1]+3*u*u*t*b[1]+3*u*t*t*c[1]+t**3*d[1]))
        a=d
    return pts


# Front is the negative-Z face; mirror X so the icon's trailing lobe appears left.
outline = [(-x,y) for x,y in curve_outline()]
body = extrude('Kirometer ghost body', outline, 0, P['body_depth'])
# Scale the ghost cavity inward; front plate remains a continuous structural web.
inner = [(x*.91, 2+(y-2)*.94) for x,y in outline]
boolean(body, extrude('Ghost interior', inner, P['front_thickness'], 31))
# Cage seats the factory housing against the front bezel.
pocket = P['stock_width']+2*P['clearance_per_side']
frame = rounded('Housing cradle', pocket+4.8, pocket+4.8, 8.6, 1.6, 25.5, y=4)
boolean(body, frame, 'UNION')
# Straight vertical sockets grow from the front plate and housing cradle.
mounts=[(side,y) for side in (-1,1) for y in (-9,14)]
for side,y in mounts:
    boolean(body,cyl('Vertical friction socket boss',1.9,25.9,(side*25.4,y,14.55)),'UNION')
# Move the complete factory housing forward to the revised seating lip.
boolean(body, rounded('Final housing clearance', pocket, pocket, P['pocket_radius'], P['screen_seat'], 32, y=4))
boolean(body, rounded('Glass opening', P['window'], P['window'], 5.3, -1, 3, y=4))
# Relieve the front window edge while retaining a 0.8mm housing seating lip.
boolean(body,loft('Screen edge chamfer',rounded_points(45.6,45.6,5.9,y=4),
                  rounded_points(P['window'],P['window'],5.3,y=4),-.01,.6))
# Close the upper shell's dead space with a continuous sloping button well.
# The stock housing is its floor: no extra moving parts or roof over the buttons.
# Official top view: 9.6 mm from the FRONT edge, not the rear edge.
button_z=P['screen_seat']+P['button_center_from_front']
upper=extrude('Closed upper cheeks',outline,0,P['body_depth'])
boolean(upper,box('Keep only above stock buttons',(150,100,80),(0,-22.9,15)))
boolean(body,upper,'UNION')
# Near-vertical inner wall: only 0.8 mm setback over 11.9 mm of height.
# Removing the previous ramp preserves fingertip space at the corrected buttons.
def across_x(name,profile,x0,x1):
    ob=extrude(name,profile,x0,x1)
    for v in ob.data.vertices:
        y,z,x=v.co;v.co=(x,y,z)
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    return ob
boolean(body,across_x('Continuous button well',[(39,P['button_wall_top_z']),(27.1,P['button_wall_base_z']),(27.1,45),(65,45),(65,P['button_wall_top_z'])],-17.4,17.4))
assign_material(body,WHITE)

# Make the lower ghost tails solid at the back so their integral heels carry load.
tail_fill=extrude('Solid supported rear tails',outline,0,P['body_depth'])
boolean(tail_fill,box('Remove upper tail fill',(140,140,80),(0,43,14)))
boolean(body,tail_fill,'UNION')

for x in (-15,15):
    boolean(body,loft('Gradually flared rear heel',rounded_points(6,6,.2,x,-32),rounded_points(14,14,.2,x,-32),22,27.5),'UNION')
    boolean(body,rounded('Flush square heel end',14,14,.2,27.4,P['maximum_depth'],x=x,y=-32),'UNION')
# Open space between the heels routes the cord to the rear without a pedestal.
boolean(body,box('Rear-open adapter clearance',(P['usb_width'],36,42),(0,-37.4,P['screen_seat']+P['adapter_front_offset']+21)))

cover = extrude('Removable rear cover', outline, 0, 2.4)
# The cover follows the full lower outline and is clipped to the same desk plane.
for x in (-15,15):
    boolean(cover,rounded('Square flush heel clearance',14.4,24,.2,-5,4,x=x,y=-36.8))
# Rear access for fingertips and the right-angle adapter.
boolean(cover,rounded('Rear button access',35.2,40,.3,-6,4,y=47.1))
boolean(cover,box('Rear adapter outlet',(P['usb_width']+.6,36,14),(0,-37.4,0)))
# Short forward tongue closes the gap behind the factory case without trapping it.
# It withdraws with the cover before the screen unit is inserted/removed.
boolean(cover,box('Button well rear closure tongue',(34.2,2.6,6.4),(0,25.75,-.8)),'UNION')
# Tapered cover pegs print tip-up on the cover's exterior face, with no ledges.
for side,y in mounts:
    x=side*25.4
    boolean(body,cyl('Open vertical friction socket',P['socket_diameter']/2,6.5,(x,y,25.25)))
    bpy.ops.mesh.primitive_cone_add(vertices=64,radius1=1.15,radius2=1.32,depth=5.05,location=(x,y,-2.475))
    peg=bpy.context.object;peg.name='Tapered friction peg'
    boolean(cover,peg,'UNION')
# Printed rear stops replace the previous foam spacer, with nominal 0.2mm play.
for x in (-9,9):
    boolean(cover,rounded('Factory case retention pad',12,8,2,-(P['body_depth']-(P['screen_seat']+P['stock_depth'])-.2),.3,x=x,y=4),'UNION')
# No decorative rear slots: retain only the necessary adapter outlet.
assign_material(cover,PURPLE)

# Factory buttons are operated directly; no separate printed plungers.

tilt=math.radians(P['desk_tilt_degrees'])
# Cut a common desk plane into the ghost's lobes at a 15-degree viewing angle.
# Geometry stays front-flat for printing; the cutter carries the inverse rotation.
floor=box('15 degree ground plane cutter',(180,80,180),(0,P['ground_y']-40,15))
from mathutils import Matrix
floor.matrix_world=Matrix.Rotation(-tilt,4,'X') @ floor.matrix_world
boolean(body,floor)
cover_floor=box('Cover common desk plane',(180,80,180),(0,P['ground_y']-40,15))
cover_floor.matrix_world=Matrix.Translation((0,0,-P['body_depth'])) @ Matrix.Rotation(-tilt,4,'X') @ cover_floor.matrix_world
boolean(cover,cover_floor)

# A low-cost window/pocket coupon checks printer and stock-case fit before the shell.
coupon = rounded('Fit coupon', 54, 54, 9, 0, 8, y=4)
boolean(coupon, rounded('Coupon pocket', pocket,pocket,6.2,P['screen_seat'],10,y=4))
boolean(coupon, rounded('Coupon window',44.4,44.4,5.3,-1,3,y=4))
boolean(coupon,rounded('Friction-fit coupon tab',12,24,2,0,8,x=31,y=4),'UNION')
for y,r in [(-4,1.32),(4,1.34),(12,1.36)]:
    boolean(coupon,cyl('Friction-fit test socket',r,10,(32,y,4)))
coupon.data.materials.append(WHITE)


def inspect(ob):
    bm=bmesh.new(); bm.from_mesh(ob.data)
    bad=sum(not e.is_manifold for e in bm.edges)
    volume=bm.calc_volume(signed=True)
    unseen=set(bm.verts); components=0
    while unseen:
        components+=1; stack=[unseen.pop()]
        while stack:
            v=stack.pop()
            for edge in v.link_edges:
                other=edge.other_vert(v)
                if other in unseen:
                    unseen.remove(other); stack.append(other)
    bm.free()
    coords=[ob.matrix_world@v.co for v in ob.data.vertices]
    bounds=[max(v[i] for v in coords)-min(v[i] for v in coords) for i in range(3)]
    if bad or volume <= 0 or components != 1:
        raise RuntimeError(f'{ob.name}: non-manifold={bad}, signed volume={volume}')
    return dict(non_manifold_edges=bad,connected_components=components,volume_mm3=round(volume,2),bounds_mm=[round(v,3) for v in bounds])


report = {'parameters_mm':P,'parts':{}}
# CSG collision check against the official factory housing envelope.
collision=body.copy(); collision.data=body.data.copy()
bpy.context.collection.objects.link(collision)
boolean(collision, rounded('Stock envelope test',46,46,5.8,P['screen_seat']+.001,P['screen_seat']+P['stock_depth'],y=4),'INTERSECT')
bm=bmesh.new(); bm.from_mesh(collision.data)
overlap=abs(bm.calc_volume()); bm.free()
bpy.data.objects.remove(collision,do_unlink=True)
if overlap > .01: raise RuntimeError(f'Stock housing collision: {overlap} mm3')
report['stock_envelope_overlap_mm3']=overlap
# Check the rear cover in its fully seated, unflexed position against both parts.
seated=cover.copy(); seated.data=cover.data.copy()
bpy.context.collection.objects.link(seated); seated.location.z=P['body_depth']
cover_overlaps={}
for label,tool in [('body',body),('factory_housing',rounded('Cover stock test',46,46,5.8,P['screen_seat']+.001,P['screen_seat']+P['stock_depth'],y=4))]:
    probe=seated.copy(); probe.data=seated.data.copy(); bpy.context.collection.objects.link(probe)
    cutter=tool.copy(); cutter.data=tool.data.copy(); bpy.context.collection.objects.link(cutter)
    boolean(probe,cutter,'INTERSECT')
    bm=bmesh.new(); bm.from_mesh(probe.data); value=abs(bm.calc_volume()); bm.free()
    if value>.01:
        bm=bmesh.new(); bm.from_mesh(probe.data)
        unseen=set(bm.verts)
        while unseen:
            component={unseen.pop()}; stack=list(component)
            while stack:
                vertex=stack.pop()
                for edge in vertex.link_edges:
                    other=edge.other_vert(vertex)
                    if other in unseen:
                        unseen.remove(other); component.add(other); stack.append(other)
            coords=[probe.matrix_world@vertex.co for vertex in component]
            print('Overlap component:',[(round(min(v[i] for v in coords),3),round(max(v[i] for v in coords),3)) for i in range(3)])
        bm.free()
    cover_overlaps[label]=round(value,6)
    bpy.data.objects.remove(probe,do_unlink=True)
    if label=='factory_housing': bpy.data.objects.remove(tool,do_unlink=True)
    allowed=.01
    if value>allowed: raise RuntimeError(f'Cover overlaps {label} beyond nominal peg interference: {value} mm3')
bpy.data.objects.remove(seated,do_unlink=True)
report['seated_cover_overlap_mm3']=cover_overlaps
# Check straight rear-cover insertion; no sliding or flexing required.
motion_checks=[]
for dy,dz in [(0,6),(0,4),(0,2),(0,1),(0,.5),(0,.2),(0,0)]:
    probe=cover.copy(); probe.data=cover.data.copy(); bpy.context.collection.objects.link(probe)
    probe.location=(0,dy,P['body_depth']+dz)
    cutter=body.copy(); cutter.data=body.data.copy(); bpy.context.collection.objects.link(cutter)
    boolean(probe,cutter,'INTERSECT')
    bm=bmesh.new(); bm.from_mesh(probe.data); value=abs(bm.calc_volume()); bm.free()
    bpy.data.objects.remove(probe,do_unlink=True)
    motion_checks.append({'y_offset_mm':dy,'z_offset_mm':dz,'overlap_mm3':round(value,6)})
    if value>.01: raise RuntimeError(f'Cover motion blocked beyond nominal peg interference at {dy},{dz}: {value} mm3')
report['sampled_cover_assembly_motion']=motion_checks
parts=[(body,'kirometer-ghost-body.stl'),(cover,'kirometer-rear-cover.stl'),(coupon,'kirometer-fit-coupon.stl')]
for ob,filename in parts:
    bm=bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=0.00001)
    bmesh.ops.dissolve_degenerate(bm,dist=0.000001,edges=list(bm.edges))
    bm.to_mesh(ob.data); bm.free()
    report['parts'][filename] = inspect(ob)
    # Export the rear cover exterior-down, with a flat surface at Z=0.
    saved_matrix=ob.matrix_world.copy()
    if ob is cover:
        from mathutils import Matrix
        print_rotation=math.pi
        ob.matrix_world=Matrix.Rotation(print_rotation,4,'X') @ saved_matrix
        minz=min((ob.matrix_world@v.co).z for v in ob.data.vertices)
        ob.location.z-=minz
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True); bpy.context.view_layer.objects.active=ob
    bpy.ops.wm.stl_export(filepath=str(OUT/filename),export_selected_objects=True,apply_modifiers=True)
    ob.matrix_world=saved_matrix
(OUT/'geometry-validation.json').write_text(json.dumps(report,indent=2))
coupon.hide_render=True; coupon.hide_viewport=True

# Save editable assembly. Rear cover is positioned at the rear face.
cover.location.z=P['body_depth']
stock = rounded('Reference stock unit - not printable',46,46,5.8,P['screen_seat'],P['screen_seat']+P['stock_depth'],y=4)
stock.data.materials.append(WHITE)
reference_buttons=[]
for x in (-10,0,10):
    cap=cyl('Factory button - reference only',P['button_diameter']/2,.8,(x,27.4,button_z),'Y')
    assign_material(cap,WHITE);reference_buttons.append(cap)
glass = rounded('Reference glass - not printable',43.3,43.3,5.3,P['screen_seat']-.15,P['screen_seat']-.01,y=4)
glass.data.materials.append(GLASS)

# Official Kiro sprite on a render-only plane, with alpha transparency.
img=bpy.data.images.load(str(ROOT/'previews/assets/kiro-ghost/south.png'))
img.pack()
mat=bpy.data.materials.new('Official Kiro ghost - render only');mat.use_nodes=True
nodes=mat.node_tree.nodes;nodes.clear()
out=nodes.new('ShaderNodeOutputMaterial');mix=nodes.new('ShaderNodeMixShader')
transparent=nodes.new('ShaderNodeBsdfTransparent');em=nodes.new('ShaderNodeEmission')
tex=nodes.new('ShaderNodeTexImage');tex.image=img
mat.node_tree.links.new(tex.outputs['Color'],em.inputs['Color'])
mat.node_tree.links.new(tex.outputs['Alpha'],mix.inputs[0])
mat.node_tree.links.new(transparent.outputs[0],mix.inputs[1]);mat.node_tree.links.new(em.outputs[0],mix.inputs[2])
mat.node_tree.links.new(mix.outputs[0],out.inputs[0])
bpy.ops.mesh.primitive_plane_add(size=20,location=(0,8,P['screen_seat']-.2))
ghost=bpy.context.object;ghost.name='Official Kiro mascot - render only'
ghost.rotation_euler.y=math.pi;ghost.data.materials.append(mat)
# Illustrative static display on a pure black screen.
bar=rounded('Illustrative meter track',31,2,1,.45,.5,y=-10);bar.data.materials.append(DARK)
bar=rounded('Illustrative meter fill',23,2,1,.4,.44,x=-4,y=-10);bar.data.materials.append(PURPLE)
# Place the self-supporting ghost on its flat tail contact surfaces for the render.
from mathutils import Matrix
for ob in [body,cover,stock,glass,ghost,*reference_buttons]+[ob for ob in bpy.data.objects if ob.name.startswith(('Mascot eye','Illustrative'))]:
    ob.matrix_world=Matrix.Rotation(tilt,4,'X') @ ob.matrix_world
desk=box('Desk surface - render only',(500,.1,400),(0,P['ground_y']-.05,20))
assign_material(desk,DARK)

bpy.ops.object.camera_add(location=(95,25,-220))
camera=bpy.context.object
camera.rotation_euler=(Vector((0,0,12))-camera.location).to_track_quat('-Z','Y').to_euler()
direction=(Vector((0,0,12))-camera.location).normalized()
right=direction.cross(Vector((0,1,0))).normalized()
up=right.cross(direction).normalized()
camera.rotation_euler=Matrix((right,up,-direction)).transposed().to_euler()
camera.data.type='ORTHO'; camera.data.ortho_scale=115
bpy.context.scene.camera=camera
for loc,energy,size in [((0,130,-130),140000,110),((-110,20,-50),65000,100),((70,80,130),150000,90)]:
    bpy.ops.object.light_add(type='AREA',location=loc)
    lamp=bpy.context.object; lamp.data.energy=energy; lamp.data.shape='DISK'; lamp.data.size=size
    lamp.rotation_euler=(Vector((0,0,10))-lamp.location).to_track_quat('-Z','Y').to_euler()
scene=bpy.context.scene
scene.render.engine='CYCLES'; scene.cycles.samples=32
scene.world.color=(.12,.10,.16)
scene.render.resolution_x=1100; scene.render.resolution_y=1100; scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
scene.render.image_settings.file_format='PNG'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'cad/kirometer-enclosure.blend'))
scene.render.filepath=str(ROOT/'previews/kirometer-enclosure.png')
bpy.ops.render.render(write_still=True)
# Rear exploded view for mechanical review.
desk.hide_render=True
cover.location.x=95

stock.hide_render=True; glass.hide_render=True; ghost.hide_render=True
for ob in reference_buttons: ob.hide_render=True
for ob in bpy.data.objects:
    if ob.name.startswith(('Mascot eye','Illustrative')): ob.hide_render=True
camera.location=(125,65,205)
camera.rotation_euler=(Vector((30,0,15))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.ortho_scale=190
scene.render.filepath=str(ROOT/'previews/kirometer-exploded.png')
bpy.ops.render.render(write_still=True)
print('Validated exports:',json.dumps(report))
