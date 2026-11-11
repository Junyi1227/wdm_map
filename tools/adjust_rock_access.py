# -*- coding: utf-8 -*-
"""Authored game placement and trail grading; raw public research remains unchanged."""
import pathlib,json,math,copy,hashlib,struct,ast,sys
from PIL import Image
R=pathlib.Path(__file__).resolve().parents[1]
if (R/'source-data/trail-adjustments.json').exists():raise SystemExit('Authored adjustment already applied; edit its configuration before a new grading pass.')
P=R/'wolmyeongdong/project.json';p=json.loads(P.read_text());s=next(x for x in p['layouts'] if x['name']=='月明洞核心區');out=P.parent/'assets/core';meta=json.loads((out/'geography.json').read_text());outer=json.loads((out.parent/'geography.json').read_text());W,S,E,N=outer['bbox_wsen'];MX=outer['width_m']/(E-W);MY=outer['height_m']/(N-S)
def xy(c):return ((c[0]-W)*MX,(N-c[1])*MY)
def digest(f):return hashlib.sha256(f.read_bytes()).hexdigest()
model_files=list((P.parent/'assets/landmarks').glob('lake-rocks-*.glb'));model_hashes={f.name:digest(f) for f in model_files}
terrain=next(o for o in s['objects'] if o['name']=='WolmyeongTerrain');assert not terrain['content'].get('SculptData'),'Check authored sculpting before updating heightmap'
original_objects=copy.deepcopy({o['name']:o for o in s['objects'] if o['name'] in ['WolmyeongTerrain','MoonLake','Hall316','RoadDetail']})
old=(2078.,2271.);origin=(2068.0313732,2270.2084976);angle=8.;rad=math.radians(angle);C,SN=math.cos(rad),math.sin(rad);base=191.01877395625166
parts=json.loads((R/'landmarks/04-god-waterfall/model/map-parts.json').read_text())
for file,name in [('upper-rocks','LakeUpperRocks'),('water','LakeRockWater'),('summit-pavilion','LakeRockPavilion')]:
 off=parts[file]['offset_native'];i=next(i for i in s['instances'] if i['name']==name);i.update(x=origin[0]+C*off[0]-SN*off[1],y=origin[1]+SN*off[0]+C*off[1],angle=angle)
def camera(n):
 if isinstance(n,dict):
  if n.get('type',{}).__class__ is dict and n.get('type',{}).get('value')=='SetNumberVariable':
   a=n['parameters'];v={'TargetX':origin[0],'TargetY':origin[1],'Yaw':230}
   if a[0] in v:a[2]=str(v[a[0]])
  for e in n.get('events',[])+n.get('actions',[]):camera(e)
nav=next(g for g in s['events'] if g.get('name','').startswith('02 '))
for e in nav['events']:
 if 'FocusLakeRocks' in json.dumps(e):camera(e)
# Existing rear trail segment is rerouted near the back of the pavilion, then right.
# Heights are intentional game grading, not newly measured elevations.
route=[(2038.4130788,2260.0177667,None),(2033,2267,None),(2034,2275,200),(2040,2283,204),(2048,2287,207.8),(2053,2284,208.143773956),(2058,2289,206),(2068,2300,201),(2080,2309,196),(2093.9194494,2314.3143244,None)]
roads=json.loads((R/'source-data/roads.geojson').read_text())['features'];road_lines=[]
for f in roads:
 if f['properties']['highway'] not in ('footway','path','steps'):
  for l in f['geometry']['coordinates']:
   ps=[xy(c) for c in l]
   for a,b in zip(ps,ps[1:]):
    if min(a[0],b[0])<2120 and max(a[0],b[0])>2000 and min(a[1],b[1])<2330 and max(a[1],b[1])>2230:road_lines.append((a,b))
image=Image.open(out/'heightmap-rg16.png');X0,Y0,_=meta['terrain_position'];width,height=meta['width_m'],meta['height_m']
def pixelz(im,c,r):red,green,_=im.getpixel((c,r));return (red*256+green)/65535*600
def imageground(x,y):
 u=max(0,min(512,(x-X0)/width*512));v=max(0,min(512,(y-Y0)/height*512));i,j=min(511,int(u)),min(511,int(v));a,b=u-i,v-j
 return pixelz(image,i,j)*(1-a)*(1-b)+pixelz(image,i+1,j)*a*(1-b)+pixelz(image,i,j+1)*(1-a)*b+pixelz(image,i+1,j+1)*a*b
route=[(x,y,imageground(x,y)+.24 if z is None else z) for x,y,z in route]
def projection(x,y,a,b):
 dx,dy=b[0]-a[0],b[1]-a[1];t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy)));return math.hypot(x-a[0]-t*dx,y-a[1]-t*dy),t
height_hash_before=digest(out/'heightmap-rg16.png');changed=0;lake_road_max_delta=0
for row in range(513):
 y=Y0+row/512*height
 if not 2248<y<2327:continue
 for col in range(513):
  x=X0+col/512*width
  if not 2018<x<2110:continue
  nearest=min(((*projection(x,y,a,b),a,b) for a,b in zip(route,route[1:])),key=lambda q:q[0]);dist,t,a,b=nearest
  if dist>=9:continue
  rd=min((projection(x,y,a,b)[0] for a,b in road_lines),default=100)
  if rd<=2.8:continue  # Preserve the entire fixed-width lakeside road corridor.
  current=pixelz(image,col,row);target=a[2]*(1-t)+b[2]*t-.24
  smooth=lambda q:q*q*(3-2*q)
  weight=1 if dist<=1.8 else 1-smooth((dist-1.8)/7.2)
  protect=smooth(min(1,max(0,(rd-2.8)/3.2)))
  z=current+max(0,target-current)*weight*protect
  if z-current>.005:
   value=round(z/600*65535);image.putpixel((col,row),(value>>8,value&255,0));changed+=1
# Fit the existing ground beneath the moved lower stones without editing their geometry.
# The front apron follows the original body-local terrain samples; rear path grade stays.
foot_samples=json.loads((R/'landmarks/04-god-waterfall/layout.json').read_text())['ground_samples'];foot_count=0
for row in range(513):
 y=Y0+row/512*height
 if not 2230<y<2300:continue
 for col in range(513):
  x=X0+col/512*width
  if not 2025<x<2110:continue
  dx,dy=x-origin[0],y-origin[1];ox=C*dx+SN*dy;oy=-SN*dx+C*dy;u=ox*.75+oy*.6614378277661477;v=ox*(-.6614378277661477)+oy*.75
  if abs(u)>=29 or v<=-6 or v>=11:continue
  rd=min((projection(x,y,a,b)[0] for a,b in road_lines),default=100)
  if rd<=2.8:continue
  su=(u+32)/2;sv=(v+30)/2;i,j=min(27,max(0,int(su))),min(35,max(0,int(sv)));a,b=su-i,sv-j
  target=base+foot_samples[j][i]*(1-a)*(1-b)+foot_samples[j][i+1]*a*(1-b)+foot_samples[j+1][i]*(1-a)*b+foot_samples[j+1][i+1]*a*b
  wU=min(1,max(0,(29-abs(u))/5));wV=min(1,max(0,(v+6)/5),max(0,(11-v)/5));w=wU*wV;current=pixelz(image,col,row);z=current+min(0,target-current)*w
  if current-z>.005:
   q=round(z/600*65535);image.putpixel((col,row),(q>>8,q&255,0));foot_count+=1

image.save(out/'heightmap-rg16.png')
# Query the same triangle interpolation used by native terrain (1024 cells).
from functools import lru_cache
@lru_cache(maxsize=100000)
def grid(i,j):
 u,v=i/2,j/2;c,r=min(511,int(u)),min(511,int(v));a,b=u-c,v-r
 return pixelz(image,c,r)*(1-a)*(1-b)+pixelz(image,c+1,r)*a*(1-b)+pixelz(image,c,r+1)*(1-a)*b+pixelz(image,c+1,r+1)*a*b
def ground(x,y):
 u=max(0,min(1024,(x-X0)/width*1024));v=max(0,min(1024,(y-Y0)/height*1024));i,j=min(1023,int(u)),min(1023,int(v));a,b=u-i,v-j;tl,tr,bl,br=grid(i,j),grid(i+1,j),grid(i,j+1),grid(i+1,j+1)
 return tl+a*(tr-tl)+b*(bl-tl) if a+b<=1 else br+(1-a)*(bl-br)+(1-b)*(tr-br)
# Reuse only the pure mesh writer and clipping functions, never execute build_core.py.
tree=ast.parse((R/'tools/build_core.py').read_text());pure=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('write_glb','clip')],type_ignores=[]);env={'math':math,'json':json,'struct':struct,'OUT':out,'X0':X0,'Y0':Y0,'WIDTH':width,'HEIGHT':height};exec(compile(pure,'build_core pure helpers','exec'),env)
triangles=[];route_feature=120371436
for feature in roads:
 if feature['properties']['highway'] not in ('footway','path','steps'):continue
 for l in feature['geometry']['coordinates']:
  ps=[xy(c) for c in l]
  if feature['properties']['osm_id']==route_feature:
   ia=min(range(len(ps)),key=lambda i:math.dist(ps[i],route[-1][:2]));ib=min(range(len(ps)),key=lambda i:math.dist(ps[i],route[0][:2]));assert ia<ib
   ps=ps[:ia]+[(x,y) for x,y,z in reversed(route)]+ps[ib+1:]
  for a,b in zip(ps,ps[1:]):
   clipped=env['clip'](a,b)
   if not clipped:continue
   a,b=clipped;le=math.dist(a,b)
   if le<.01:continue
   dx,dy=(b[0]-a[0])/le,(b[1]-a[1])/le;count=max(1,math.ceil(le/1.2));rows=[]
   for j in range(count+1):
    x=a[0]+j/count*(b[0]-a[0]);y=a[1]+j/count*(b[1]-a[1]);row=[]
    for k in range(3):
     off=(k/2-.5)*1.2;xx=max(X0,min(X0+width,x-dy*off));yy=max(Y0,min(Y0+height,y+dx*off));row.append([xx,ground(xx,yy)+.24,yy])
    rows.append(row)
   for a,b in zip(rows,rows[1:]):
    for k in range(2):triangles.extend([a[k],b[k],a[k+1],a[k+1],b[k],b[k+1]])
data=env['write_glb']('trails',triangles,[.64,.49,.32,1]);meta['models']['TrailDetail']=data
for o in s['objects']:
 if o['name']=='TrailDetail':o['content'].update(width=data['size'][0],height=data['size'][1],depth=data['size'][2])
for i in s['instances']:
 if i['name']=='TrailDetail':i.update(**dict(zip(['x','y','z'],data['position'])),**dict(zip(['width','height','depth'],data['size'])))
for name,obj in original_objects.items():assert next(o for o in s['objects'] if o['name']==name)==obj,name
assert all(digest(P.parent/'assets/landmarks'/name)==sha for name,sha in model_hashes.items())
P.write_text(json.dumps(p,ensure_ascii=False,indent=2));(out/'geography.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
pose={'origin_xy':origin,'angle_deg':angle,'base_z':base,'reason':'左移並略往山側退，整組旋轉8度避開湖邊道路；模型幾何未修改。'}
(R/'source-data/lake-rocks-map-pose.json').write_text(json.dumps(pose,ensure_ascii=False,indent=2))
report={'source_feature':route_feature,'status':'使用者要求的遊戲步道調整，非原始OSM或實測路線','waypoints_xyz':route,'width_m':1.2,'native_heightmap_local_grading':True,'protected_lakeside_road_half_width_m':2.8,'changed_heightmap_pixels':changed,'heightmap_sha_before':height_hash_before,'heightmap_sha_after':digest(out/'heightmap-rg16.png'),'model_file_hashes_unchanged':model_hashes,'model_pose':pose,'pavilion_nearby_path_height':ground(2053,2284)+.24}
(R/'source-data/trail-adjustments.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));(R/'validation/rock-access-adjustment.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
placements=R/'source-data/landmark-placements.json';d=json.loads(placements.read_text())
for entry in d:
 if entry.get('object')=='LakeUpperRocks':entry.update(position=[*origin,base],angle_deg=angle,access='山側原步道改線至亭後附近，再接回右側；高差為局部遊戲地形整平。模型本體未改。')
placements.write_text(json.dumps(d,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
