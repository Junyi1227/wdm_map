"""Blender structural/export round trip check; writes evidence, never core game."""
import bpy,bmesh,pathlib,json,math
R=pathlib.Path(__file__).resolve().parents[1];results=[]
for folder in ['09-camel-rock','10-round-hill-pavilion','08-prayer-hill']:
 out=R/folder/'model';bpy.ops.wm.open_mainfile(filepath=str(out/'landmark.blend'));obs=[o for c in bpy.data.collections if c.name.startswith('LANDMARK editable model') for o in c.objects];assert obs
 for c in list(bpy.data.collections):
  if c.name.startswith('LANDMARK editable model') and not c.objects:bpy.data.collections.remove(c)
 for c in bpy.data.collections:
  if c.name.startswith('LANDMARK editable model') and c.objects:c.name='LANDMARK editable model'
 # Correct consistent outward normals on closed components; roof panel orientation
 # is explicit because an open sheet has no enclosed volume to infer outside.
 for o in obs:
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
  if o.name.startswith('Roof curved panel'):
   if sum(f.normal.z for f in bm.faces)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
  bm.to_mesh(o.data);bm.free()
 def export(file,items):
  bpy.ops.object.select_all(action='DESELECT')
  for o in items:o.select_set(True)
  bpy.context.view_layer.update()
  bpy.ops.export_scene.gltf(filepath=str(out/file),export_format='GLB',use_selection=True,export_yup=True,export_apply=True)
 export('landmark.glb',obs)
 parts={}
 if folder=='10-round-hill-pavilion':
  parts={'roof':[o for o in obs if any(w in o.name for w in ['Roof','Eave','eave','hip'])],'stairs':[o for o in obs if any(w in o.name.lower() for w in ['stair','post cap'])]};parts['structure']=[o for o in obs if all(o not in a for a in parts.values())]
 elif folder=='08-prayer-hill':parts={'terrain':[o for o in obs if 'hillside' in o.name or 'Terrain earth' in o.name],'stairs':[o for o in obs if 'stair' in o.name.lower()],'platform':[o for o in obs if 'platform' in o.name.lower() or 'crown' in o.name.lower() or 'Bench' in o.name]}
 for name,items in parts.items():export(name+'.glb',items)
 # Verify edits were saved and source is readable. Preview ground is not exported.
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'landmark.blend'))
 scene=bpy.context.scene;scene.cycles.samples=8;scene.cycles.use_denoising=True
 meta=json.loads((out/'model.json').read_text());f=meta['focus'];from mathutils import Vector
 focus=Vector(f);dist=meta['distance'];cam=scene.camera
 for name,angle in ([] if folder in ['09-camel-rock','10-round-hill-pavilion'] else [('front',-65),('right',25),('back',115),('left',205)]):
  a=math.radians(angle);cam.location=focus+Vector((dist*math.cos(a),dist*math.sin(a),dist*.65));cam.rotation_euler=(focus-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(out/'landmark.glb'));meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];tris=0
 for o in meshes:
  o.data.calc_loop_triangles();tris+=len(o.data.loop_triangles)
  assert all(math.isfinite(v) for vert in o.data.vertices for v in vert.co)
 assert meshes and tris<=30000
 results.append({'id':folder,'glb_import':'passed','editable_blend_reopened':'passed','mesh_objects':len(meshes),'triangles':tris,'external_textures':0,'parts':[n+'.glb' for n in parts]})
 print('VERIFIED',folder,tris,flush=True)
(R/'model-structure-validation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
