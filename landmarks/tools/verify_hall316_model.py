import bpy,pathlib,json,math,struct
from mathutils import Vector
R=pathlib.Path(__file__).resolve().parents[1];O=R/'02-hall-316/model';meta=json.loads((O/'model.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(O/'landmark.blend'));obs=list(bpy.data.collections['LANDMARK editable model'].all_objects);columns=[o for o in obs if o.name.startswith('Outer stone column')];assert len(columns)==16
# Read the mesh coordinates to check actual clearance, not just the intended count.
front=[o for o in columns if abs(sum(v.co.y for v in o.data.vertices)/len(o.data.vertices)+8.65)<.001];assert len(front)==8
clearance=-6.84-max(v.co.y for o in front for v in o.data.vertices)
assert clearance > 1.0,'Portico gap must remain open'
scene=bpy.context.scene;cam=scene.camera;scene.cycles.samples=12;scene.cycles.use_denoising=True;cam.location=Vector((44,-70,34));focus=Vector((0,-1,10.4));cam.rotation_euler=(focus-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(O/'perspective.png')
if not (O/'perspective.png').exists():bpy.ops.render.render(write_still=True)
# Reset saved source camera to this readable front 3/4 view, retaining editable components.
scene['model_notes']='316 hall draft; 16 real outer columns; unmeasured dimensions; provisional rear; five editable component collections.';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(O/'landmark.blend'))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(O/'landmark.glb'));meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];tris=0
for o in meshes:
 o.data.calc_loop_triangles();tris+=len(o.data.loop_triangles)
 assert all(math.isfinite(c) for v in o.data.vertices for c in v.co)
assert 5000<=tris<=30000
counts={}
for name in meta['modular_exports']+['landmark.glb']:
 raw=(O/name).read_bytes();length=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+length]);assert g.get('meshes');assert not g.get('images');assert all('uri' not in b for b in g.get('buffers',[]));counts[name]=sum(g['accessors'][p['indices']]['count']//3 for m in g['meshes'] for p in m['primitives'])
assert sum(n for k,n in counts.items() if k!='landmark.glb')==counts['landmark.glb']
report={'date':'2026-11-11','editable_blend_reopened':True,'glb_reimported':True,'triangles':tris,'mesh_objects':len(meshes),'columns':16,'front_columns':8,'open_front_portico_clearance_m':round(clearance,3),'part_triangle_counts':counts,'external_textures':0,'measured_dimensions':False,'rear_geometry':'provisional','core_map_modified':False}
(O/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False),flush=True)
