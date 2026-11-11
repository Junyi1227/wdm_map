"""Bake each map part at its own southwest-bottom origin for native model sizing."""
import bpy,pathlib,json,bmesh
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2];out=ROOT/'landmarks/04-god-waterfall/model'
bpy.ops.wm.open_mainfile(filepath=str(out/'landmark.blend'))
obs=list(bpy.data.collections['LANDMARK editable model'].objects);deps=bpy.context.evaluated_depsgraph_get()
assert not any('backing' in o.name.lower() for o in obs),'A continuous backing surface must not be reintroduced'
structural=[o for o in obs if o.name.startswith('Stacked structural rock') or o.name.startswith('Pavilion supporting capstone')]
assert len(structural)>40,'Stonework needs genuine individual support rocks'
(out/'stacked-rock-validation.json').write_text(json.dumps({'continuous_backing_mesh':False,'individual_support_rocks':len(structural),'structural_rocks_are_editable':True,'added_stairs':any('stair' in o.name.lower() for o in obs),'added_ramp':any('ramp' in o.name.lower() for o in obs)},indent=2))
groups={'upper-rocks':['upper_rocks','planted_accents'],'water':['cascade'],'summit-pavilion':['summit_pavilion']};report={}
for name,components in groups.items():
 verts=[];faces=[];indices=[];materials=[]
 for o in obs:
  if o.get('component') not in components:continue
  ev=o.evaluated_get(deps);me=ev.to_mesh();offset=len(verts)
  verts.extend([tuple(o.matrix_world@v.co) for v in me.vertices])
  matmap=[]
  for m in me.materials:
   if m not in materials:materials.append(m)
   matmap.append(materials.index(m))
  for p in me.polygons:faces.append(tuple(offset+i for i in p.vertices));indices.append(matmap[p.material_index] if matmap else 0)
  ev.to_mesh_clear()
 lo=[min(v[i] for v in verts) for i in range(3)];hi=[max(v[i] for v in verts) for i in range(3)]
 # Native scene +Y equals Blender -Y: give all three native axes a zero minimum.
 normalized=[(x-lo[0],y-hi[1],z-lo[2]) for x,y,z in verts]
 me=bpy.data.meshes.new('Map '+name);me.from_pydata(normalized,[],faces);me.update()
 for m in materials:me.materials.append(m)
 for p,i in zip(me.polygons,indices):p.material_index=i
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 obj=bpy.data.objects.new('Map '+name,me);bpy.context.scene.collection.objects.link(obj);bpy.ops.object.select_all(action='DESELECT');obj.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(out/('map-'+name+'.glb')),export_format='GLB',use_selection=True,export_yup=True,export_apply=True)
 report[name]={'offset_native':[lo[0],-hi[1],lo[2]],'size':[hi[i]-lo[i] for i in range(3)]}
 bpy.data.objects.remove(obj,do_unlink=True)
(out/'map-parts.json').write_text(json.dumps(report,indent=2));print('Normalized native map parts exported')
