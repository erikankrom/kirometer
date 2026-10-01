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
         clearance_per_side=0.4, front_thickness=2.4,
         body_depth=27.5, cover_thickness=2.4, window=44.4,
         pocket_radius=6.2, pocket_wall=2.4,
         usb_width=13.0, usb_height=8.0,
         desk_tilt_degrees=15.0, rear_tail_extension=8.5, plunger_shaft_diameter=6.8,
         target_body_width=66.0, target_body_height=80.0, maximum_depth=36.0,
         ground_y=-39.3,
         closure_slide_travel=0.0, closure_clearance=-0.04,
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
GLASS = material('AMOLED glass', (.006, .004, .012))


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


def button_passage(x,r=3.8,y0=26.5,y1=72):
    z=15.3
    profile=[(x+r*math.cos(math.radians(135+i*270/48)),z+r*math.sin(math.radians(135+i*270/48))) for i in range(49)]
    profile.append((x,z+r*math.sqrt(2)))
    return along_y('Self-supporting button passage',profile,y0,y1)


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
# Retain the unchanged factory-housing clearance envelope.
boolean(body, rounded('Final housing clearance', pocket, pocket, P['pocket_radius'], 2.4, 32, y=4))
boolean(body, rounded('Glass opening', P['window'], P['window'], 5.3, -1, 3, y=4))
# Cable tunnel: oversized for connector shell, exits between the ghost tails.
boolean(body,along_y('Self-supporting USB passage',[(-6.5,7),(6.5,7),(6.5,15),(0,21.5),(-6.5,15)],-71,-15.5))
# Board buttons are on its top edge. Three straight channels accept a blunt tool.
for x in (-10,0,10):
    boolean(body,button_passage(x))
    boolean(body, button_passage(x,4.6,27.5,31.5))
assign_material(body,WHITE)

# Make the lower ghost tails solid at the back so their integral heels carry load.
tail_fill=extrude('Solid supported rear tails',outline,0,P['body_depth'])
boolean(tail_fill,box('Remove upper tail fill',(140,140,80),(0,43,14)))
boolean(body,tail_fill,'UNION')
boolean(body,along_y('USB passage through solid tails',[(-6.5,7),(6.5,7),(6.5,15),(0,21.5),(-6.5,15)],-71,-15.5))
for x in (-15,15):
    boolean(body,loft('Gradually flared rear heel',rounded_points(6,6,2,x,-32),rounded_points(14,14,5,x,-32),24,32),'UNION')
    boolean(body,rounded('Rear heel end',14,14,5,31.9,P['maximum_depth'],x=x,y=-32),'UNION')
# Open space between the heels routes the cord to the rear without a pedestal.
boolean(body,box('Rear cord exit',(15,18,42),(0,-37,25)))

cover = extrude('Removable rear cover', outline, 0, 2.4)
# Lower tails are integral solid geometry; cover closes the service cavity above.
boolean(cover,box('Tail relief',(140,80,8),(0,-67,1)))
for x in (-15,15):
    boolean(cover,rounded('Rear heel cover slide clearance',14.5,18.5,5.25,-3,4,x=x,y=-30))
# Tapered cover pegs print tip-up on the cover's exterior face, with no ledges.
for side,y in mounts:
    x=side*25.4
    boolean(body,cyl('Open vertical friction socket',1.30,6.5,(x,y,25.25)))
    bpy.ops.mesh.primitive_cone_add(vertices=64,radius1=1.15,radius2=1.32,depth=5.05,location=(x,y,-2.475))
    peg=bpy.context.object;peg.name='Tapered friction peg'
    boolean(cover,peg,'UNION')
# Printed rear stops replace the previous foam spacer, with nominal 0.2mm play.
for x in (-9,9):
    boolean(cover,rounded('Factory case retention pad',12,8,2,-2.4,.3,x=x,y=4),'UNION')
# Narrow ventilation slots above the integral heel region.
for x in (-12,-6,0,6,12):
    boolean(cover, rounded('Vent', 2.2, 6, 1.1, -1, 4, x=x, y=-22))
assign_material(cover,PURPLE)

# Three captive plungers. Insert from inside before inserting the stock unit.
plungers=[]
for index,x in enumerate((-10,0,10),1):
    plunger=cyl(f'Top button {index}',3.4,11.8,(x,34.1,15.3),'Y')
    bpy.ops.mesh.primitive_cone_add(vertices=64,radius1=4.2,radius2=3.4,depth=1,location=(x,28.4,15.3))
    flange=bpy.context.object; flange.name='45 degree plunger retaining flange'
    flange.rotation_euler.x=-math.pi/2
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    boolean(plunger,flange,'UNION')
    boolean(plunger,cyl('Contact tip',2.4,1.0,(x,27.7,15.3),'Y'),'UNION')
    boolean(plunger,cyl('Finger cap',4.4,2.4,(x,41,15.3),'Y'),'UNION')
    assign_material(plunger,PURPLE)
    plungers.append(plunger)

tilt=math.radians(P['desk_tilt_degrees'])
# Cut a common desk plane into the ghost's lobes at a 15-degree viewing angle.
# Geometry stays front-flat for printing; the cutter carries the inverse rotation.
floor=box('15 degree ground plane cutter',(180,80,180),(0,P['ground_y']-40,15))
from mathutils import Matrix
floor.matrix_world=Matrix.Rotation(-tilt,4,'X') @ floor.matrix_world
boolean(body,floor)

# A low-cost window/pocket coupon checks printer and stock-case fit before the shell.
coupon = rounded('Fit coupon', 54, 54, 9, 0, 8, y=4)
boolean(coupon, rounded('Coupon pocket', pocket,pocket,6.2,2.4,10,y=4))
boolean(coupon, rounded('Coupon window',44.4,44.4,5.3,-1,3,y=4))
boolean(coupon,rounded('Friction-fit coupon tab',12,24,2,0,8,x=31,y=4),'UNION')
for y,r in [(-4,1.28),(4,1.30),(12,1.32)]:
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
boolean(collision, rounded('Stock envelope test',46,46,5.8,2.401,24.9,y=4),'INTERSECT')
bm=bmesh.new(); bm.from_mesh(collision.data)
overlap=abs(bm.calc_volume()); bm.free()
bpy.data.objects.remove(collision,do_unlink=True)
if overlap > .01: raise RuntimeError(f'Stock housing collision: {overlap} mm3')
report['stock_envelope_overlap_mm3']=overlap
# Check the rear cover in its fully seated, unflexed position against both parts.
seated=cover.copy(); seated.data=cover.data.copy()
bpy.context.collection.objects.link(seated); seated.location.z=P['body_depth']
cover_overlaps={}
for label,tool in [('body',body),('factory_housing',rounded('Cover stock test',46,46,5.8,2.401,24.9,y=4))]:
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
    allowed=1.0 if label=='body' else .01
    if value>allowed: raise RuntimeError(f'Cover overlaps {label} beyond nominal peg interference: {value} mm3')
bpy.data.objects.remove(seated,do_unlink=True)
report['seated_cover_overlap_mm3']=cover_overlaps
# Sample the two assembly motions: straight insertion at -4mm Y, then slide up.
motion_checks=[]
for dy,dz in [(0,6),(0,4),(0,2),(0,1),(0,.5),(0,.2),(0,0)]:
    probe=cover.copy(); probe.data=cover.data.copy(); bpy.context.collection.objects.link(probe)
    probe.location=(0,dy,P['body_depth']+dz)
    cutter=body.copy(); cutter.data=body.data.copy(); bpy.context.collection.objects.link(cutter)
    boolean(probe,cutter,'INTERSECT')
    bm=bmesh.new(); bm.from_mesh(probe.data); value=abs(bm.calc_volume()); bm.free()
    bpy.data.objects.remove(probe,do_unlink=True)
    motion_checks.append({'y_offset_mm':dy,'z_offset_mm':dz,'overlap_mm3':round(value,6)})
    if value>1.0: raise RuntimeError(f'Cover motion blocked beyond nominal peg interference at {dy},{dz}: {value} mm3')
report['sampled_cover_assembly_motion']=motion_checks
parts=[(body,'kirometer-ghost-body.stl'),(cover,'kirometer-rear-cover.stl'),(coupon,'kirometer-fit-coupon.stl')]
parts += [(ob,f'kirometer-top-button-{i}.stl') for i,ob in enumerate(plungers,1)]
for ob,filename in parts:
    bm=bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=0.00001)
    bmesh.ops.dissolve_degenerate(bm,dist=0.000001,edges=list(bm.edges))
    bm.to_mesh(ob.data); bm.free()
    report['parts'][filename] = inspect(ob)
    # Export plungers cap-down with a flat surface at Z=0.
    saved_matrix=ob.matrix_world.copy()
    if ob in plungers or ob is cover:
        from mathutils import Matrix
        print_rotation=math.pi if ob is cover else -math.pi/2
        ob.matrix_world=Matrix.Rotation(print_rotation,4,'X') @ saved_matrix
        minz=min((ob.matrix_world@v.co).z for v in ob.data.vertices)
        ob.location.z-=minz
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True); bpy.context.view_layer.objects.active=ob
    bpy.ops.wm.stl_export(filepath=str(OUT/filename),export_selected_objects=True,apply_modifiers=True)
    ob.matrix_world=saved_matrix
(OUT/'geometry-validation.json').write_text(json.dumps(report,indent=2))
coupon.hide_render=True; coupon.hide_viewport=True
# Save editable assembly. The wedge key is shown with its stem seated in the seam.

# Save editable assembly. Rear cover is positioned at the rear face.
cover.location.z=P['body_depth']
stock = rounded('Reference stock unit - not printable',46,46,5.8,2.4,24.9,y=4)
stock.data.materials.append(DARK)
glass = rounded('Reference glass - not printable',43.3,43.3,5.3,1.9,2.3,y=4)
glass.data.materials.append(GLASS)

# Show mascot on glass as a small solid white silhouette. Render-only geometry.
ghost = extrude('Animated mascot reference - render only',[(x*.19,y*.19+6) for x,y in outline],1.75,1.85)
ghost.data.materials.append(WHITE)
for x in (-1.4,2.1):
    eye=cyl('Mascot eye',1, .15,(x,9,1.68)); eye.scale.y=1.6; eye.data.materials.append(GLASS)
# Render-only purple utilization bar, clearly illustrative.
bar=rounded('Illustrative meter track',31,2,1,1.7,1.8,y=-10)
bar.data.materials.append(DARK)
bar=rounded('Illustrative meter fill',23,2,1,1.6,1.7,x=4,y=-10)
bar.data.materials.append(PURPLE)

# Place the self-supporting ghost on its flat tail contact surfaces for the render.
from mathutils import Matrix
for ob in [body,cover,stock,glass,ghost,*plungers]+[ob for ob in bpy.data.objects if ob.name.startswith(('Mascot eye','Illustrative'))]:
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
camera.data.type='ORTHO'; camera.data.ortho_scale=150
bpy.context.scene.camera=camera
for loc,energy,size in [((0,130,-130),140000,110),((-110,20,-50),65000,100),((70,80,130),150000,90)]:
    bpy.ops.object.light_add(type='AREA',location=loc)
    lamp=bpy.context.object; lamp.data.energy=energy; lamp.data.shape='DISK'; lamp.data.size=size
    lamp.rotation_euler=(Vector((0,0,10))-lamp.location).to_track_quat('-Z','Y').to_euler()
scene=bpy.context.scene
scene.render.engine='CYCLES'; scene.cycles.samples=48
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
for ob in bpy.data.objects:
    if ob.name.startswith(('Mascot eye','Illustrative')): ob.hide_render=True
camera.location=(125,65,205)
camera.rotation_euler=(Vector((30,0,15))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.ortho_scale=190
scene.render.filepath=str(ROOT/'previews/kirometer-exploded.png')
bpy.ops.render.render(write_still=True)
print('Validated exports:',json.dumps(report))
