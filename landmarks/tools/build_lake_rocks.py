# -*- coding: utf-8 -*-
"""Build editable photo-assisted lake stonework. Run using Blender --background."""
import bpy,math,random,pathlib,sys,json
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import build_models as b
# Blender's Python need not have Pillow: placement configuration is authored beforehand.
cfg=json.loads((b.R/'04-god-waterfall/layout.json').read_text())
random.seed(31604);b.clear();part='upper_rocks'
stone=[b.mat('Granite %02d'%i,c) for i,c in enumerate([(.43,.45,.42),(.53,.55,.50),(.63,.64,.57),(.38,.41,.39),(.69,.69,.61),(.48,.51,.49)])]
dark=b.mat('Wet dark cascade rock',(.24,.29,.28));earth=b.mat('Mossy planted mound',(.26,.36,.22));path=b.mat('Pale rear walking path',(.69,.66,.53));white=b.mat('Light stone balustrade',(.78,.80,.70));wood=b.mat('Warm pavilion timber',(.51,.29,.12));tile=b.mat('Teal glazed roof',(.10,.31,.30));ridge=b.mat('Roof ridge trim',(.30,.48,.43));water=b.mat('Pale turquoise falling water',(.33,.72,.75));foam=b.mat('Water foam highlights',(.81,.92,.87));pool=b.mat('Turquoise collecting basin',(.19,.57,.54));pine=b.mat('Sculptural pine foliage',(.23,.41,.17));trunk=b.mat('Pine trunk',(.35,.26,.16))
for m in [water,foam,pool]:
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.32
def tag(o):o['component']=part;return o
def box(n,p,s,m,bevel=0):return tag(b.box(n,p,s,m,bevel))
def beam(n,a,c,r,m,verts=8):return tag(b.beam(n,a,c,r,m,verts))
def rock(n,p,s,m=None):
 o=tag(b.stone(n,p,s,m or random.choice(stone),1));o.rotation_euler=(random.uniform(-.15,.15),random.uniform(-.2,.2),random.random()*math.tau);return o
def ground(u,v):
 samples=cfg['ground_samples'];i=max(0,min(27,int((u+32)/2)));j=max(0,min(35,int((v+30)/2)));return samples[j][i]
# The volume is made of overlapping individual rocks, never a planar backing wedge.
# Broad lower courses and narrower upper courses support the waterfall and pavilion.
for layer,(zz,halfwidth) in enumerate([(1.8,23),(4.8,18),(7.8,13),(10.8,8.5),(13.5,4.0)]):
 front=3+zz*.55;rear=24-zz*.20
 nx=max(2,round(halfwidth*2/4.4));nv=max(1,round((rear-front)/4.8))
 for row in range(nv+1):
  vv=front+(rear-front)*row/max(1,nv)
  for j in range(nx+1):
   u=-halfwidth+halfwidth*2*j/nx+random.uniform(-.55,.55)
   if row==0:continue  # Existing smaller front stones and cascade form this face.
   rock('Stacked structural rock %d %d %d'%(layer,row,j),(u,vv+random.uniform(-.4,.4),zz+random.uniform(-.3,.3)),(random.uniform(2.2,2.8),random.uniform(2.5,3.1),random.uniform(1.8,2.2)))
for u,vv in [(-2,15.5),(2,15.5),(-2,19),(2,19)]:
 rock('Pavilion supporting capstone',(u,vv,13.65),(2.4,2.3,1.6))
# Tapering rows follow the triangular silhouette, with irregular gaps and upright slabs.
for row,(z,halfwidth) in enumerate([(1.8,23),(4.1,20),(6.4,16),(8.8,12.5),(11.2,9),(13.5,6.4)]):
 count=max(3,int(halfwidth*2/2.7))
 for j in range(count+1):
  u=-halfwidth+2*halfwidth*j/count+random.uniform(-.35,.35)
  if abs(u)<4.8:continue
  vv=3+z*.55+random.uniform(-.4,.5)
  rock('Triangular wall boulder %d %d'%(row,j),(u,vv,z+random.uniform(-.3,.4)),(random.uniform(1.35,1.9),random.uniform(1.1,1.65),random.uniform(1.15,1.7)))
for u,top in [(-23,2.6),(-19,4.5),(-15,7),(-11,9.5),(-7,13),(7,12.8),(11,10),(15,7),(19,4.8),(23,2.8)]:
 h=min(4.5,top*.65);base=top-h;vv=3+base*.55+.8
 rock('Tapered wall upright granite',(u,vv,base+h/2),(.65,.95,h/2),random.choice(stone))
 rock('Upright granite supporting boulder',(u,vv+1,base+.4),(1.5,1.4,1.2))
# Tiered central waterfall: dark stone mass and separated slender water ribbons.
part='cascade'
for k,(vv,top,width) in enumerate([(3,3.6,9.4),(6,6.8,10.5),(9,10.0,9.0),(12,15.0,8.0)]):
 bottom=0 if k==0 else [3.6,6.8,10][k-1]
 for q in range(4):
  rock('Cascade fractured rock tier %d block %d'%(k,q),(-width*.375+q*width/4,vv,(top+bottom)/2),(width/7,1.8,(top-bottom)/2+.16),dark)
 for j in range(9 if k==3 else 5):
  x=-(width/2-.35)+j*(width-.7)/(8 if k==3 else 4)+random.uniform(-.12,.12);ww=random.uniform(.12,.32) if k==3 else random.uniform(.25,.65)
  tag(b.mesh('Water ribbon upper %d %d'%(k,j),[(x-ww/2,vv-1.77,top+.07),(x+ww/2,vv-1.77,top+.07),(x+ww*.8,vv-1.85,bottom+.05),(x-ww*.8,vv-1.85,bottom+.05)],[(0,1,2,3)],water if j%3 else foam))
  box('Foam at upper tier',(x,vv-1.92,bottom+.07),(ww*1.7,.48,.08),foam,.03)
box('Upper collection pool',(0,.65,.30),(11.0,2.5,.23),pool,.16)
for u in [-5.7,5.7]:box('Collection pool coping',(u,.65,.30),(.28,2.8,.6),white,.05)
box('Pool front low coping',(0,-.75,.27),(11.6,.25,.5),white,.03)
# Front and rear roads belong to the existing map, never to this model.
# Lake shore lower stones are deliberately omitted from this revision.
# Photo shows a square viewing pavilion above the falls, distinct from hill octagon.
part='summit_pavilion';pz=15.0;cy=17
box('Pavilion summit platform',(0,cy,pz-.15),(7.2,6.4,.3),white,.12)
for x in [-2.8,2.8]:
 for y in [cy-2.3,cy+2.3]:
  box('Pavilion stone stilt',(x,y,pz+1.0),(.45,.45,2),white,.05);box('Pavilion timber column',(x,y,pz+3.5),(.26,.26,3),wood,.025)
box('Raised pavilion floor',(0,cy,pz+2),(6.3,5.5,.25),white,.06)
for y in [cy-2.45,cy+2.45]:
 beam('Timber roof beam',(-3.15,y,pz+5),(3.15,y,pz+5),.15,wood)
 for zz in [pz+2.4,pz+3.0]:
  if y<cy:continue
  beam('Pavilion rear balcony rail',(-2.8,y,zz),(2.8,y,zz),.08,white)
for side in [-1,1]:
 for zz in [pz+2.4,pz+3.0]:beam('Side balcony rail',(side*2.8,cy-2.3,zz),(side*2.8,cy+2.3,zz),.075,white)
 for j in range(9):box('Side balcony baluster',(side*2.8,cy-2.2+j*.55,pz+2.65),(.10,.10,.65),white,.015)
# Front railing around central open bay; rear approach reaches floor by short stairs.
for xa,xb in [(-2.8,-.9),(.9,2.8)]:
 for zz in [pz+2.4,pz+3.0]:beam('Front balcony railing',(xa,cy-2.3,zz),(xb,cy-2.3,zz),.07,white)
# No added pavilion stairs: access refers to the existing mapped rear road.
for side in range(4):
 # Hipped square roof with swept corners, open space below.
 a0=math.pi/4+side*math.pi/2;vs=[];fs=[]
 for j in range(9):
  t=j/8
  for k in range(13):
   a=a0+k/12*math.pi/2;r=(.3+4.1*t)*math.cos(math.pi/4)/math.cos((k/12-.5)*math.pi/2);z=pz+5.1+1.8*(1-t)**1.5+.32*t**8
   vs.append((r*math.cos(a),cy+r*math.sin(a),z))
 for j in range(8):
  for k in range(12):q=j*13+k;fs.append((q,q+1,q+14,q+13))
 o=tag(b.mesh('Swept teal roof panel',vs,fs,tile));mod=o.modifiers.new('Tile roof thickness','SOLIDIFY');mod.thickness=.12
 for k in range(13):
  pts=[vs[j*13+k] for j in range(9)]
  for aa,cc in zip(pts,pts[1:]):beam('Roof tile standing ridge',aa,cc,.035,ridge,6)
beam('Roof finial',(0,cy,pz+6.7),(0,cy,pz+7.3),.11,ridge)
# A few characteristic pruned pines rather than a complete forest.
part='planted_accents'
for u,vv,h in [(-18,5,3.5),(18,5,3.5)]:
 zz=max(0,ground(u,vv)) if vv<0 else 3
 beam('Bent pine trunk',(u,vv,zz),(u+.8,vv,zz+h),.14,trunk)
 for j in range(3):
  x=u+(-1 if j%2 else 1)*(1+j*.4);z=zz+h-j*.8;beam('Pine main branch',(u+.5,vv,z-.8),(x,vv,z),.09,trunk);tag(b.stone('Flattened pruned pine canopy',(x,vv,z),(2.2,1.6,.60),pine,2))
# Transform authored local frame into world-aligned offsets for reliable engine origin.
ac=cfg['across'];back=cfg['back']
from mathutils import Matrix
M=Matrix(((ac[0],back[0],0,0),(-ac[1],-back[1],0,0),(0,0,1,0),(0,0,0,1)))
for o in list(bpy.context.scene.objects):
 if o.get('component')=='lake_rocks':
  # Lower retaining stones belong to the lake bank and follow its downhill grade.
  # Bake object transforms before draping so water ribbons and boulders stay aligned.
  for vert in o.data.vertices:
   p=o.matrix_world@vert.co;p.z+=ground(p.x,p.y);vert.co=p
  o.matrix_world=Matrix.Identity(4)
 o.matrix_world=M@o.matrix_world
meta={'id':'04-god-waterfall','name':'月明湖對岸石頭造景與瀑布亭','focus':[0,0,8],'distance':90,'parts':['Upper rock wall','Separate cascade ribbons','Individually stacked structural rocks, no backing plane','Square summit pavilion'],'sources':['user-front-waterfall.png','user-lake-context.png'],'user_identity_confirmed':'2026-11-11','estimate':'照片輔助概略配置；岩壁底寬約50m、底部前後深約21m、頂部約8×9m，上段瀑布高約15m；均為示意估計。','unknown':'主體由獨立石塊堆疊，無平面斜坡基體；前後通路沿用原圖，不含新增坡道、樓梯或湖岸下層石景。','placed_in_core_map':True}
meta['preview_yaw']=49
b.finish(meta)
out=b.R/'04-god-waterfall/model';obs=list(bpy.data.collections['LANDMARK editable model'].objects)
groups={'upper-rocks':['upper_rocks','planted_accents'],'water':['cascade'],'summit-pavilion':['summit_pavilion']};partbounds={}
for name,components in groups.items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in obs:
  if o.get('component') in components:o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(out/(name+'.glb')),export_format='GLB',use_selection=True,export_yup=True,export_apply=True)
 partbounds[name]=b.bounds([o for o in obs if o.get('component') in components])
meta['modular_exports']=[name+'.glb' for name in groups]
meta['part_bounds_blender_z_up']=partbounds
(out/'model.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
