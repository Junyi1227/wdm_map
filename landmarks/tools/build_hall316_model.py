# -*- coding: utf-8 -*-
"""Photo-assisted local model; no service, image projection or measured dimensions.
Run in Blender: --background --python landmarks/tools/build_hall316_model.py
"""
import bpy,math,pathlib,json,sys
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import build_models as b
from mathutils import Vector
b.clear();part='main_body'
def tag(o):o['component']=part;return o
def box(n,p,s,m,bevel=0):return tag(b.box(n,p,s,m,bevel))
def beam(n,a,c,r,m,verts=8):return tag(b.beam(n,a,c,r,m,verts))
stone=b.mat('316 warm off-white stone',(.78,.77,.68));white=b.mat('316 upper white walls',(.85,.85,.78));trim=b.mat('316 pale stone trim',(.9,.89,.82));green=b.mat('316 muted jade canopy',(.15,.43,.35));under=b.mat('316 canopy underside',(.24,.49,.40));glass=b.mat('316 opaque blue-green glass',(.075,.21,.22));glass2=b.mat('316 alternate glass',(.12,.29,.28));spandrel=b.mat('316 pale jade floor bands',(.32,.53,.46));frame=b.mat('316 dark window frames',(.10,.16,.15));rail=b.mat('316 brushed railing',(.50,.56,.53));dark=b.mat('316 entrance recess',(.045,.10,.10))
for m in [glass,glass2]:
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.28;p.inputs['Metallic'].default_value=.22

def roundslab(n,cx,cy,z,w,d,h,r,m):
 points=[]
 for x,y,start in [(w/2-r,d/2-r,0),(-w/2+r,d/2-r,90),(-w/2+r,-d/2+r,180),(w/2-r,-d/2+r,270)]:
  for i in range(7):a=math.radians(start+i*15);points.append((cx+x+r*math.cos(a),cy+y+r*math.sin(a)))
 nn=len(points);v=[(x,y,z-h/2) for x,y in points]+[(x,y,z+h/2) for x,y in points];faces=[tuple(reversed(range(nn))),tuple(range(nn,2*nn))]+[(i,(i+1)%nn,(i+1)%nn+nn,i+nn) for i in range(nn)];return tag(b.mesh(n,v,faces,m))
# Lower built plinth and a genuinely open undercroft at the lake-facing side.
part='base_stairs';roundslab('Lower foundation footprint',0,.1,.12,34.8,19.8,.24,1.4,stone)
box('Lower rear service volume',(0,3.1,1.65),(29,10.7,3.05),white,.05)
for x in [-14,-7,0,7,14]:box('Undercroft structural pier',(x,-6.9,1.7),(.52,.55,3.1),stone,.025)
for i in range(9):box('Lower entrance glass %02d'%i,(-12.8+i*3.2,-2.3,1.55),(3.04,.12,2.75),glass)
roundslab('Raised portico terrace slab',0,-.2,3.32,35.4,20,.42,1.5,stone)
# Broad front staircase, separate from the open portico above.
for i in range(16):
 top=(i+1)*3.1/16;y=-15.45+(i+.5)*.34;box('Front stair tread %02d'%i,(-10.2,y,top/2),(6.0,.35,top),stone,.012)
box('Front stair upper landing',(-10.2,-9.75,3.12),(6.0,1.25,.20),stone,.025)
for x in [-13.35,-7.05]:
 beam('Stair rail sloped',(x,-15.5,.95),(x,-10.05,4.0),.038,rail)
 for i in [0,4,8,12,15]:y=-15.45+(i+.5)*.34;top=(i+1)*3.1/16;beam('Stair rail post',(x,y,top),(x,y,top+.9),.032,rail)
# Front terrace rail, leave a six metre stair opening.
for xa,xb in [(-17.1,-13.4),(-7.0,17.1)]:
 for zz in [3.9,4.3]:beam('Terrace horizontal rail',(xa,-10.1,zz),(xb,-10.1,zz),.025,rail)
 for j in range(int((xb-xa)/1.4)+1):
  xx=xa+j*(xb-xa)/max(1,int((xb-xa)/1.4));beam('Terrace rail upright',(xx,-10.1,3.55),(xx,-10.1,4.3),.025,rail)
# Three main glazed levels: facade sits behind the monumental columns.
part='main_body';box('Rear wall - provisional simple geometry',(0,7.25,9.92),(28.4,.4,12.8),white,.04)
box('Interior rear core',(0,4.3,9.92),(25.8,5.4,12.6),white,.04)
for k in range(3):
 z0=3.55+k*4.18;hh=4.12
 # opaque glass is intentional for predictable game rendering, not a transparency bug.
 box('Front recessed glass level %d'%k,(0,-6.68,z0+hh/2),(28.35,.12,hh),glass)
 for side in [-1,1]:box('Side recessed glass level %d'%k,(side*14.2,.23,z0+hh/2),(.12,13.9,hh),glass)
 for j in range(21):box('Front vertical mullion',( -14.2+j*1.42,-6.79,z0+hh/2),(.055,.09,hh),frame)
 for j in range(20):
  if (j+k)%4 in [0,1]:box('Front glass subtle color variation',(-13.49+j*1.42,-6.755,z0+2.65),(1.35,.035,1.3),glass2)
 for side in [-1,1]:
  for j in range(11):box('Side vertical mullion',(side*14.29,-6.7+j*1.35,z0+hh/2),(.075,.055,hh),frame)
 for zz in [z0+.12,z0+1.55,z0+3.0]:
  box('Front horizontal frame',(0,-6.80,zz),(28.4,.08,.055),frame)
  for side in [-1,1]:box('Side horizontal frame',(side*14.3,.25,zz),(.08,13.95,.055),frame)
 if k<2:
  box('Front jade floor band',(0,-6.83,z0+hh-.33),(28.4,.12,.69),spandrel)
  for side in [-1,1]:box('Side jade floor band',(side*14.31,.25,z0+hh-.33),(.13,13.95,.69),spandrel)
# Entry door detail behind portico, not a solid wall across columns.
for x in [-2.1,-.7,.7,2.1]:
 box('Recessed glass entrance door',(x,-6.88,4.85),(1.34,.10,2.55),dark)
 beam('Door handle',(x+.42,-6.97,4.45),(x+.42,-6.97,5.2),.023,rail)
# Exactly sixteen freestanding outer columns.
part='columns';column_positions=[(-15.6+i*31.2/7,-8.65) for i in range(8)]+[(side*15.6,y) for side in [-1,1] for y in [-4.45,-.25,3.95,8.05]]
profile=[(.66,0),(.66,.17),(.57,.30),(.52,.43),(.48,.55),(.46,12.03),(.53,12.15),(.64,12.32),(.65,12.52),(.58,12.63)]
for idx,(x,y) in enumerate(column_positions):
 v=[];f=[];n=16
 for rad,z in profile:
  for j in range(n):a=j*math.tau/n;v.append((x+rad*math.cos(a),y+rad*math.sin(a),3.55+z))
 for i in range(len(profile)-1):
  for j in range(n):a=i*n+j;c=i*n+(j+1)%n;f.append((a,c,c+n,a+n))
 f.extend([tuple(reversed(range(n))),tuple((len(profile)-1)*n+j for j in range(n))]);o=tag(b.mesh('Outer stone column %02d'%(idx+1),v,f,stone))
 for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
# Broad rounded green canopy and understated fascia seams.
part='canopy';roundslab('Green wrapping canopy',0,-.15,16.49,36.2,20.9,.65,1.65,green);roundslab('Canopy pale underside',0,-.15,16.13,35.9,20.6,.12,1.6,under)
for i in range(49):box('Green fascia standing seam',(-16.9+i*.7,-10.60,16.49),(.035,.04,.55),under)
# Upper white set-back volume, kept distinct from the three glazed main levels.
part='roof_terrace';roundslab('Upper terrace floor',0,.4,16.9,31.2,16.7,.22,1,stone)
box('Set-back white upper block',(0,1.45,18.57),(28,12.0,3.28),white,.065)
for x in [-12,-9.8,-7.6,-5.4,-3.2,-1,1.2,3.4,5.6,7.8,10,12.2]:
 box('Upper front small window',(x,-4.59,18.25),(.64,.075,1.02),glass2)
box('Upper front horizontal stone cornice',(0,-4.62,19.70),(28.15,.13,.16),stone)
for side in [-1,1]:
 for y in [-2.8,.1,3.,5.9]:box('Upper short-side small window',(side*14.055,y,18.35),(.075,.62,1.12),glass2)
box('Upper roof terrace slab',(0,1.45,20.33),(28.25,12.2,.22),stone,.04)
# Provisional rear service tower and long open rooftop shelter, visible in user winter shot.
box('Upper service tower - approximate',(-12.1,4.9,21.3),(3.4,4.2,2.0),white,.04)
for x in [-10,-6,-2,2,6,10,13]:
 for y in [-1.5,3.0]:box('Rooftop shelter thin post',(x,y,21.35),(.16,.16,1.8),stone)
roundslab('Long narrow rooftop shelter',1, .75,22.34,26.3,5.3,.22,.6,stone)
for zz in [20.8,21.2]:beam('Rooftop terrace front rail',(-14,-4.67,zz),(14,-4.67,zz),.025,rail)
for i in range(15):
 x=-14+i*2;beam('Rooftop terrace rail post',(x,-4.67,20.45),(x,-4.67,21.2),.025,rail)
# Mesh finish handles GLB, editable collection, four renders and .blend save.
meta={'id':'02-hall-316','name':'316會館／聖子愛之家','focus':[0,-.4,10.8],'distance':65,'parts':['Recessed main facade','16 outer stone columns','Green wrapping canopy','Upper white block and rooftop terrace','Foundation and front stairs'],'sources':['official-spring','official-corner-a','official-sky','official-pillar','user-winter','festival-31'],'user_identity_confirmed':'2026-11-11','built_date':'2026-11-11','estimate':'工作比例約寬36.2m、含前階梯深約26m、高22.5m；全部為照片估計，非實測。柱徑約1m用作外形比例參考。','unknown':'完整背立面、內部格局、上部退縮精確尺寸與局部基座曲線仍為簡化推定。玻璃採不透明PBR色塊；柱廊保留實際間隙。','column_count':16,'front_column_count':8,'side_column_count_each':4,'placed_in_core_map':False}
b.finish(meta)
out=b.R/'02-hall-316/model';collection=bpy.data.collections['LANDMARK editable model'];obs=list(collection.objects);parts=sorted(set(o['component'] for o in obs));paths=[]
for name in parts:
 bpy.ops.object.select_all(action='DESELECT')
 for o in obs:
  if o['component']==name:o.select_set(True)
 bpy.context.view_layer.update();bpy.ops.export_scene.gltf(filepath=str(out/(name+'.glb')),export_format='GLB',use_selection=True,export_yup=True,export_apply=True);paths.append(name+'.glb')
meta['modular_exports']=paths
# Preserve authoring structure for manual changes and source photograph traceability.
for name in parts:
 c=bpy.data.collections.new(name);collection.children.link(c)
 for o in obs:
  if o['component']==name:collection.objects.unlink(o);c.objects.link(o)
bpy.context.scene['provenance']=json.dumps(meta,ensure_ascii=False);(out/'model.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'landmark.blend'))
print('HALL COMPLETE',meta['triangles'],paths,flush=True)
