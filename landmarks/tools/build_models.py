"""Photo-assisted stylized drafts, not AI reconstructions or surveyed geometry.
Run with Blender --background --python landmarks/tools/build_models.py.
"""
import bpy, bmesh, math, random, json, pathlib, sys
from mathutils import Vector
R=pathlib.Path(__file__).resolve().parents[1];random.seed(21)
def clear():
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 for d in list(bpy.data.materials):bpy.data.materials.remove(d)
 for c in list(bpy.data.collections):
  if not c.objects:bpy.data.collections.remove(c)
def mat(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=.88;return m
def mesh(n,v,f,m):
 d=bpy.data.meshes.new(n);d.from_pydata(v,[],f);d.update();o=bpy.data.objects.new(n,d);bpy.context.collection.objects.link(o);o.data.materials.append(m);return o
def box(n,loc,size,m,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=n;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if bevel:
  mod=o.modifiers.new('Soft crafted edges','BEVEL');mod.width=bevel;mod.segments=2;mod=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
 return o
def cyl(n,loc,r,depth,m,verts=12):
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=loc);o=bpy.context.object;o.name=n;o.data.materials.append(m);return o
def beam(n,a,b,r,m,verts=8):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,verts);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def stone(n,loc,scale,m,sub=2):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=1,location=loc);o=bpy.context.object;o.name=n
 for v in o.data.vertices:v.co*=random.uniform(.88,1.12)
 o.scale=scale;o.data.materials.append(m);return o
def bounds(obs):
 pts=[o.matrix_world@Vector(v) for o in obs if o.type=='MESH' for v in o.bound_box]
 return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
def roof(wood,tile,edge):
 # Octagonal swept eaves; eight open bays beneath, not a solid pavilion.
 for side in range(8):
  a0=math.pi/8+side*math.tau/8;a1=a0+math.tau/8;v=[];faces=[];nr,nt=16,12
  for j in range(nr+1):
   t=j/nr;r=.12+4.05*t;z=5.0+2.0*(1-t)**1.6+.32*t**9
   for k in range(nt+1):
    u=k/nt;a=a0+(a1-a0)*u;rr=r*(math.cos(math.pi/8)/math.cos((u-.5)*math.pi/4));v.append((rr*math.cos(a),rr*math.sin(a),z+.035*math.cos(u*math.tau*12)))
  for j in range(nr):
   for k in range(nt):i=j*(nt+1)+k;faces.append((i+nt+1,i+nt+2,i+1,i))
  o=mesh('Roof curved panel %02d'%side,v,faces,tile);so=o.modifiers.new('Roof thickness','SOLIDIFY');so.thickness=.10
  pts=[]
  for j in range(21):
   t=j/20;r=.12+4.05*t;z=5.08+2*(1-t)**1.6+.32*t**9;pts.append((r*math.cos(a0),r*math.sin(a0),z))
  for j in range(20):beam('Raised hip ridge',pts[j],pts[j+1],.065,edge)
  for k in range(13):
   u=k/12;a=a0+(a1-a0)*u;r=4.17*(math.cos(math.pi/8)/math.cos((u-.5)*math.pi/4));cyl('Eave tile end',(r*math.cos(a),r*math.sin(a),5.31),.065,.11,edge,8)
  aa=(a0+a1)/2
  for k in range(5):
   t=(k+.5)/5;a=a0+(a1-a0)*t;r=3.64
   beam('Visible eave rafter',(2.6*math.cos(a),2.6*math.sin(a),4.78),(r*math.cos(a),r*math.sin(a),5.09),.065,wood)
 cyl('Roof finial',(0,0,7.12),.12,.42,edge)
def pavilion():
 clear();wood=mat('Warm weathered timber',(.31,.18,.10));warm=mat('Golden rail edges',(.49,.32,.18));tile=mat('Blue gray roof tile',(.18,.25,.26));edge=mat('Tile ridge highlights',(.32,.40,.39));white=mat('Pale stone stairs',(.79,.82,.77));floor=mat('Timber floor',(.43,.29,.17))
 cyl('Raised octagonal floor',(0,0,2.05),3.05,.25,floor,8)
 # eight timber columns, stone stilts beneath.
 for i in range(8):
  a=math.pi/8+i*math.tau/8;x,y=2.7*math.cos(a),2.7*math.sin(a)
  cyl('Stone support %02d'%i,(x,y,1),.17,2,white,8);cyl('Timber column %02d'%i,(x,y,3.56),.13,2.8,wood)
  b=a+math.tau/8;xx,yy=2.7*math.cos(b),2.7*math.sin(b)
  beam('Upper connecting beam',(x,y,4.78),(xx,yy,4.78),.13,wood)
  # Open south bay connects stairs, no rail across entry.
  if i!=5:
   for z in [2.43,3.12]:beam('Open bay handrail',(x,y,z),(xx,yy,z),.065,warm)
   for t in [.25,.5,.75]:
    px=x*(1-t)+xx*t;py=y*(1-t)+yy*t;box('Rail baluster',(px,py,2.77),(.09,.09,.67),warm,.015)
 # White masonry stair flight approaches the south edge.
 steps=12;run=.27;rise=2.0/steps
 for i in range(steps):box('Stair tread %02d'%i,(0,-6.0+i*run,(i+1)*rise/2),(1.85,run+.02,(i+1)*rise),white,.02)
 for x in [-1.04,1.04]:
  beam('White stair handrail',(x,-6.14,.9),(x,-2.91,2.9),.075,white)
  for i in range(0,steps,2):
   y=-6+i*run;z=(i+1)*rise;cyl('Stair rail spindle',(x,y,z+.4),.055,.8,white,8)
  for y,z in [(-6.1,0),(-2.93,2)]:
   cyl('Stair endpost',(x,y,z+.48),.115,.96,white,8);stone('Post cap',(x,y,z+1.02),(.14,.14,.14),white,1)
 box('Lower stair pad',(0,-6.4,-.08),(2.65,1,.16),white,.04)
 roof(wood,tile,edge)
 return {'id':'10-round-hill-pavilion','name':'圓山八角亭','focus':[0,-1,3],'distance':18,'parts':['Raised octagonal floor','Columns and open rails','Stone supports','Stairs','Curved octagonal roof'],'sources':['round2011-00','round2011-03','round2011-06'],'estimate':'亭身直徑約6m、含屋頂高約7.3m；由照片估計，非實測。2011年外觀，未確認現況改建。','unknown':'背側梁架、屋頂頂部細節及隱藏構造為簡化推定。'}
def camel():
 clear();palette=[mat('Rock gray %d'%i,c) for i,c in enumerate([(.44,.46,.43),(.52,.54,.50),(.59,.59,.53),(.38,.41,.39),(.65,.64,.57)])]
 # Grounded elongated ridge. Station widths and height are interpreted from photos,
 # not an animal mesh and not photogrammetry.
 stations=[(-12,1.2,.6),(-10,2.1,1.7),(-7,3.0,2.7),(-3,3.35,3.2),(0,2.65,3.6),(2,2.0,2.75),(5,1.2,2.5),(8,.8,3.4),(11,1.3,4.25),(12,.9,3.95)]
 def at(x,k):
  for a,b in zip(stations,stations[1:]):
   if x<=b[0]:t=(x-a[0])/(b[0]-a[0]);return a[k]*(1-t)+b[k]*t
  return stations[-1][k]
 v=[];faces=[];nx,ny=96,32
 for i in range(nx+1):
  x=-12+24*i/nx;w=at(x,1);high=at(x,2)
  for j in range(ny+1):
   u=-1+2*j/ny;y=w*u+.12*math.sin(x*.9)*(1-u*u);ridge=max(0,1-abs(u)**1.7)
   cracks=.11*math.sin(u*21+x*.24)+.065*math.sin(x*2.2+u*11)
   z=.05+high*ridge+cracks*ridge+.1*math.sin(x*1.7)*(1-abs(u));v.append((x,y,max(.01,z)))
 for i in range(nx):
  for j in range(ny):
   a=i*(ny+1)+j
   if (i+j)%2:faces.extend([(a,a+1,a+ny+1),(a+1,a+ny+2,a+ny+1)])
   else:faces.extend([(a,a+1,a+ny+2),(a,a+ny+2,a+ny+1)])
 # Closed underside and endcaps. Buried base is provisional.
 outline=list(range(ny+1))+[i*(ny+1)+ny for i in range(1,nx+1)]+list(range(nx*(ny+1)+ny-1,nx*(ny+1)-1,-1))+[i*(ny+1) for i in range(nx-1,0,-1)]
 base=[]
 for idx in outline:x,y,z=v[idx];base.append(len(v));v.append((x,y,-.15))
 for a,b,c,d in zip(outline,outline[1:]+outline[:1],base,base[1:]+base[:1]):faces.append((a,c,d,b))
 faces.append(tuple(reversed(base)))
 o=mesh('Camel Rock continuous ridge',v,faces,palette[0])
 for m in palette[1:]:o.data.materials.append(m)
 for p in o.data.polygons:
  x=sum(o.data.vertices[i].co.x for i in p.vertices)/len(p.vertices);y=sum(o.data.vertices[i].co.y for i in p.vertices)/len(p.vertices)
  p.material_index=1 if math.sin(y*4+x*.18)>.45 else (2 if math.sin(x*.6+y*1.5)>.7 else 0)
 return {'id':'09-camel-rock','name':'駱駝石','focus':[0,0,1.8],'distance':36,'parts':['Continuous exposed bedrock ridge'],'sources':['route-12','lake-18'],'estimate':'暫定長24m、寬約6.7m、高約4.4m；未有實測，整體比例仍需現場核對。','unknown':'樹木與人群遮擋處、背面及地下基底為推定。主岩體未變成駱駝動物。'}
def hill():
 clear();grass=mat('Muted grass',(.38,.53,.26));soil=mat('Earth section',(.35,.28,.18));gravel=mat('Prayer platform gravel',(.66,.66,.53));rock=mat('Rounded gray border stone',(.44,.46,.37));light=mat('Stair pale stone',(.79,.81,.73));bench=mat('Stone benches',(.55,.60,.52))
 # Local terrain patch, independent from the surveyed map terrain.
 def z(x,y):
  base=1.8+.18*(y+6)+.45*math.sin(x*.24)*math.cos(y*.12);r=math.hypot(x-1,y);t=min(1,max(0,(r-3.7)/1.1));return 2.95*(1-t)+base*t
 n=40;v=[];f=[]
 for j in range(n+1):
  y=-12+24*j/n
  for i in range(n+1):x=-10+20*i/n;v.append((x,y,z(x,y)))
 for j in range(n):
  for i in range(n):a=j*(n+1)+i;f.extend([(a,a+1,a+n+2),(a,a+n+2,a+n+1)])
 o=mesh('Local hillside editable mesh',v,f,grass)
 # close terrain skirt separately
 edge=list(range(n+1))+[j*(n+1)+n for j in range(1,n+1)]+list(range(n*(n+1)+n-1,n*(n+1)-1,-1))+[j*(n+1) for j in range(n-1,0,-1)]
 vv=[v[i] for i in edge]+[(v[i][0],v[i][1],-.45) for i in edge];nn=len(edge);ff=[(i,(i+1)%nn,(i+1)%nn+nn,i+nn) for i in range(nn)];ff.append(tuple(range(nn,2*nn)));mesh('Terrain earth sides',vv,ff,soil)
 platformz=3.05;cyl('Round prayer platform',(1,0,platformz-.12),3.55,.28,gravel,48)
 for i in range(20):
  a=i*math.tau/20
  if 3.9<a<4.7:continue
  x,y=1+3.6*math.cos(a),3.6*math.sin(a);stone('Platform border rock %02d'%i,(x,y,platformz+.1),(.62,.43,.44),rock)
 # Larger crown-like upright rocks towards uphill rear.
 for i in range(7):
  a=.1+i*math.pi/7;x,y=1+2.95*math.cos(a),2.95*math.sin(a);stone('Upright crown stone %02d'%i,(x,y,platformz+.85),(.48,.43,1.18),rock)
 for x,y in [(-.4,-5),(1.6,-5),(3.5,-4.5),(-1.5,-6.5),(1,-6.5),(3.2,-6.2)]:
  zz=z(x,y);box('Bench seat',(x,y,zz+.55),(1.25,.37,.15),bench,.05)
  for xx in [x-.43,x+.43]:box('Bench support',(xx,y,zz+.27),(.18,.25,.55),bench,.025)
 # Left-side ascending stair in three flights, with open gravel landings.
 for start,end,base,top in [((-5.2,-10),(-5.2,-3),.7,2.7),((-5.2,-2.5),(-6,3),2.7,4.0),((-6,3.6),(-4.2,9.5),4,5.4)]:
  a,b=Vector(start),Vector(end);d=b-a;count=16
  for i in range(count):
   p=a+d*(i+.5)/count;zz=z(p.x,p.y)+.16
   o=box('Ascending stair tread',(p.x,p.y,zz-.2),(1.55,d.length/count+.025,.4),light,.015);o.rotation_euler.z=-math.atan2(d.x,d.y)
  for sign in [-1,1]:
   offset=Vector((d.y,-d.x)).normalized()*.84*sign
   beam('Low stair curb',(a.x+offset.x,a.y+offset.y,z(a.x,a.y)+.3),(b.x+offset.x,b.y+offset.y,z(b.x,b.y)+.3),.09,light)
 for x,y,zz in [(-5.2,-2.8,2.7),(-6,3.3,4)]:box('Stair landing',(x,y,z(x,y)-.02),(1.9,.9,.4),light,.02)
 return {'id':'08-prayer-hill','name':'禱告山','focus':[0,0,2],'distance':43,'parts':['Local hillside','Round prayer platform','Crown stones','Benches','Ascending stair flights'],'sources':['hill-06','hill-08','hill-09','holy-14'],'estimate':'局部示意範圍20×24m，階梯總高差約4.7m；非實測、非DEM重建。','unknown':'照片中被松樹遮住的道路連接、平台後方及石塊數量位置為簡化推定。不包含禱告奇蹟松模型。'}
def finish(meta):
 for obj in bpy.context.scene.objects:
  if obj.type=='MESH':
   bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
 bpy.context.view_layer.update();obs=[o for o in bpy.context.scene.objects if o.type=='MESH'];bb=bounds(obs)
 meta.update(status='照片輔助的簡化初稿，待風格確認',method='Blender原生網格建模；未使用Meshy/Tripo，未上傳原照片',unit='metre',bounds_blender_z_up=bb,dimensions_estimated=True,texture='solid PBR palette; no external textures')
 meta.setdefault('user_identity_confirmed','2026-11-10')
 out=R/meta['id']/'model';out.mkdir(exist_ok=True)
 bpy.ops.object.select_all(action='DESELECT')
 for o in obs:o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(out/'landmark.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=True)
 # Optional modular exports preserve independent editing/placement later.
 parts={}
 if meta['id']=='10-round-hill-pavilion':
  parts={'roof':[o for o in obs if any(w in o.name for w in ['Roof','Eave','eave','hip'])],'stairs':[o for o in obs if any(w in o.name.lower() for w in ['stair','post cap'])]}
  parts['structure']=[o for o in obs if all(o not in group for group in parts.values())]
 elif meta['id']=='08-prayer-hill':
  parts={'terrain':[o for o in obs if 'hillside' in o.name or 'Terrain earth' in o.name],'stairs':[o for o in obs if 'stair' in o.name.lower()],'platform':[o for o in obs if 'platform' in o.name.lower() or 'crown' in o.name.lower() or 'Bench' in o.name]}
 for part,items in parts.items():
  bpy.ops.object.select_all(action='DESELECT')
  for o in items:o.select_set(True)
  bpy.ops.export_scene.gltf(filepath=str(out/(part+'.glb')),export_format='GLB',use_selection=True,export_yup=True,export_apply=True)
 meta['modular_exports']=[k+'.glb' for k in parts]

 # Render-only scene collection is excluded from GLB export above.
 modelcoll=bpy.data.collections.new('LANDMARK editable model');bpy.context.scene.collection.children.link(modelcoll)
 for o in obs:
  for c in list(o.users_collection):c.objects.unlink(o)
  modelcoll.objects.link(o)
 env=bpy.data.collections.new('PREVIEW only - not exported');bpy.context.scene.collection.children.link(env)
 ground=mat('Preview ground',(.79,.81,.69));g=box('Preview floor',(0,0,bb[0][2]-.13),(200,200,.2),ground)
 for c in list(g.users_collection):c.objects.unlink(g)
 env.objects.link(g)
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.render.resolution_x=1000;scene.render.resolution_y=850;scene.render.resolution_percentage=100;scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.75,.83,.88,1);scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.65
 scene.view_settings.view_transform='AgX'
 bpy.ops.object.light_add(type='SUN',location=(0,0,20));sun=bpy.context.object;sun.rotation_euler=(.35,-.5,-.4);sun.data.energy=2;sun.data.angle=.12
 for loc,power,size in [((4,-10,22),2400,12),((-10,0,10),1700,10)]:
  bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector(meta['focus'])-o.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=max(bb[1][0]-bb[0][0],bb[1][1]-bb[0][1],bb[1][2]-bb[0][2])*1.45
 focus=Vector(meta['focus']);dist=meta['distance']
 frontangle=meta.get('preview_yaw',-65)
 for name,angle in [('front',frontangle),('right',frontangle+90),('back',frontangle+180),('left',frontangle+270)]:
  a=math.radians(angle);cam.location=focus+Vector((dist*math.cos(a),dist*math.sin(a),dist*.65));cam.rotation_euler=(focus-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
 # Save with attractive front view and meaningful object names.
 a=math.radians(frontangle);cam.location=focus+Vector((dist*math.cos(a),dist*math.sin(a),dist*.65));cam.rotation_euler=(focus-cam.location).to_track_quat('-Z','Y').to_euler()
 for area in bpy.context.screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
 deps=bpy.context.evaluated_depsgraph_get();tris=0
 for o in obs:
  me=o.evaluated_get(deps).to_mesh();me.calc_loop_triangles();tris+=len(me.loop_triangles);o.evaluated_get(deps).to_mesh_clear()
 meta['triangles']=tris;meta['files']=['landmark.glb','landmark.blend','front.png','right.png','back.png','left.png'];(out/'model.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
 bpy.context.preferences.filepaths.save_version=0;scene['provenance']=json.dumps(meta,ensure_ascii=False);bpy.ops.wm.save_as_mainfile(filepath=str(out/'landmark.blend'));print('DONE',meta['name'],tris,flush=True)
if __name__=='__main__':
 for build in [camel,pavilion,hill]:
  if '--' not in sys.argv or build.__name__ in sys.argv[sys.argv.index('--')+1:]:finish(build())
