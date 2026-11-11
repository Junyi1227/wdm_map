# -*- coding: utf-8 -*-
"""Place the confirmed hall using the existing OSM named building footprint.
Writes native instances and a terrain-fitting plinth; never rebuilds terrain.
"""
import json,pathlib,copy,uuid,math,struct,shutil,hashlib
from PIL import Image
R=pathlib.Path(__file__).resolve().parents[2];P=R/'wolmyeongdong/project.json';project=json.loads(P.read_text());core=next(s for s in project['layouts'] if s['name']=='月明洞核心區');meta=json.loads((P.parent/'assets/core/geography.json').read_text());outer=json.loads((P.parent/'assets/geography.json').read_text());im=Image.open(P.parent/'assets/core/heightmap-rg16.png');x0,y0,_=meta['terrain_position'];W,H=meta['width_m'],meta['height_m'];terrain=next(o for o in core['objects'] if o['name']=='WolmyeongTerrain');assert not terrain['content'].get('SculptData'),'Query live sculpted terrain before running this placement tool'
terrain_before=hashlib.sha256(json.dumps(terrain,sort_keys=True).encode()).hexdigest()
def ground(x,y):
 u=max(0,min(1024,(x-x0)/W*1024));v=max(0,min(1024,(y-y0)/H*1024));i,j=min(1023,int(u)),min(1023,int(v));a,b=u-i,v-j
 def grid(c,r):
  uu,vv=c/2,r/2;ii,jj=min(511,int(uu)),min(511,int(vv));aa,bb=uu-ii,vv-jj
  def pix(i,j):red,green,_=im.getpixel((i,j));return (red*256+green)/65535*600
  return pix(ii,jj)*(1-aa)*(1-bb)+pix(ii+1,jj)*aa*(1-bb)+pix(ii,jj+1)*(1-aa)*bb+pix(ii+1,jj+1)*aa*bb
 tl,tr,bl,br=grid(i,j),grid(i+1,j),grid(i,j+1),grid(i+1,j+1)
 return tl+a*(tr-tl)+b*(bl-tl) if a+b<=1 else br+(1-a)*(bl-br)+(1-b)*(tr-br)
f=next(f for f in json.loads((R/'source-data/context.geojson').read_text())['features'] if f['properties'].get('id')=='OSM-354325017');west,south,east,north=outer['bbox_wsen'];mx=outer['width_m']/(east-west);my=outer['height_m']/(north-south);ps=[((lon-west)*mx,(north-lat)*my) for lon,lat in f['geometry']['coordinates'][0][:-1]];edges=list(zip(ps,ps[1:]+ps[:1]));area=sum(a[0]*b[1]-b[0]*a[1] for a,b in edges);x=sum((a[0]+b[0])*(a[0]*b[1]-b[0]*a[1]) for a,b in edges)/(3*area);y=sum((a[1]+b[1])*(a[0]*b[1]-b[0]*a[1]) for a,b in edges)/(3*area)
a,b=max(edges,key=lambda ab:math.dist(*ab));angle=math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]));lake=next(s for s in meta['sites'] if s['object']=='MoonLake')['focus_xy']
# Local +Y is the glazed front of the Blender-exported model in GDevelop.
if (-math.sin(math.radians(angle))*(lake[0]-x)+math.cos(math.radians(angle))*(lake[1]-y))<0:angle+=180
rad=math.radians(angle)
def world(u,v):return x+u*math.cos(rad)-v*math.sin(rad),y+u*math.sin(rad)+v*math.cos(rad)
main=[]
for cx,cy,start in [(16.5,8.9,0),(-16.5,8.9,90),(-16.5,-8.9,180),(16.5,-8.9,270)]:
 for i in range(5):t=math.radians(start+i*22.5);main.append(world(cx+1.6*math.cos(t),cy+1.6*math.sin(t)))
stairs=[world(u,v) for u,v in [(-13.55,9.9),(-6.85,9.9),(-6.85,16.15),(-13.55,16.15)]];polys=[main,stairs]
# Main terrace already rises 3.3m in the authored model: allow its lower rear
# service storey to meet the uphill terrain, rather than floating the entire hall.
upper=max(ground(*p) for p in main);originz=upper-3.3+.16;points=[]
def tri(a,b,c):points.extend([a,b,c])
for poly in polys:
 cx=sum(p[0] for p in poly)/len(poly);cy=sum(p[1] for p in poly)/len(poly);ct=(cx,originz,cy);cb=(cx,min(originz-.12,ground(cx,cy)-.12),cy)
 for a,b in zip(poly,poly[1:]+poly[:1]):
  at=(a[0],originz,a[1]);bt=(b[0],originz,b[1]);ab=(a[0],min(originz-.12,ground(*a)-.12),a[1]);bb=(b[0],min(originz-.12,ground(*b)-.12),b[1]);tri(ct,bt,at);tri(cb,ab,bb);tri(at,bt,bb);tri(at,bb,ab)
mins=[min(p[i] for p in points) for i in range(3)];maxs=[max(p[i] for p in points) for i in range(3)];sizes=[maxs[i]-mins[i] for i in range(3)];local=[p[i]-mins[i] for p in points for i in range(3)];binary=struct.pack('<'+'f'*len(local),*local)
doc={'asset':{'version':'2.0','generator':'316 hall terrain-fitting retaining base'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'mesh':0}],'meshes':[{'primitives':[{'attributes':{'POSITION':0},'material':0}]}],'materials':[{'doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':[.65,.65,.58,1],'roughnessFactor':.95,'metallicFactor':0}}],'buffers':[{'byteLength':len(binary)}],'bufferViews':[{'buffer':0,'byteLength':len(binary),'target':34962}],'accessors':[{'bufferView':0,'componentType':5126,'count':len(points),'type':'VEC3','min':[0,0,0],'max':sizes}]};js=json.dumps(doc,separators=(',',':')).encode();js+=b' '*((-len(js))%4);binary+=b'\0'*((-len(binary))%4);out=P.parent/'assets/landmarks';out.mkdir(exist_ok=True);(out/'hall316-foundation.glb').write_bytes(struct.pack('<III',0x46546c67,2,28+len(js)+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary);shutil.copy2(R/'landmarks/02-hall-316/model/landmark.glb',out/'hall316.glb')
modelmeta=json.loads((R/'landmarks/02-hall-316/model/model.json').read_text());lo,hi=modelmeta['bounds_blender_z_up'];modelsize=[hi[i]-lo[i] for i in range(3)];template=next(o for o in core['objects'] if o['name']=='MoonLake')
for name,file,position,size,rot in [('Hall316','hall316.glb',[x,y,originz],modelsize,angle),('Hall316Foundation','hall316-foundation.glb',[mins[0],mins[2],mins[1]],[sizes[0],sizes[2],sizes[1]],0)]:
 obj=next((o for o in core['objects'] if o['name']==name),None)
 if obj is None:obj=copy.deepcopy(template);obj.update(name=name,persistentUuid=str(uuid.uuid4()));core['objects'].append(obj)
 obj['content'].update(modelResourceName=file,width=size[0],height=size[1],depth=size[2],rotationX=90,rotationY=0,rotationZ=0,keepAspectRatio=False,originLocation='ModelOrigin',centerLocation='ModelOrigin',isCastingShadow=False,isReceivingShadow=False)
 inst=next((i for i in core['instances'] if i['name']==name),None)
 if inst is None:inst=copy.deepcopy(next(i for i in core['instances'] if i['name']=='MoonLake'));inst.update(name=name,persistentUuid=str(uuid.uuid4()));core['instances'].append(inst)
 inst.update(x=position[0],y=position[1],z=position[2],width=size[0],height=size[1],depth=size[2],angle=rot,customSize=True)
 res=next((r for r in project['resources']['resources'] if r['name']==file),None)
 if res is None:res={'name':file,'kind':'model3D','metadata':'','userAdded':True};project['resources']['resources'].append(res)
 res['file']='assets/landmarks/'+file
if not any(o['name']=='FocusHall316' for o in core['objects']):
 obj=copy.deepcopy(next(o for o in core['objects'] if o['name']=='FocusPavilion'));obj.update(name='FocusHall316',persistentUuid=str(uuid.uuid4()),string='[ 316會館 ]');obj['content']['text']=obj['string'];core['objects'].append(obj);inst=copy.deepcopy(next(i for i in core['instances'] if i['name']=='FocusPavilion'));inst.update(name='FocusHall316',x=1510,width=360,persistentUuid=str(uuid.uuid4()));core['instances'].append(inst)
nav=next(g for g in core['events'] if g.get('name','').startswith('02 '));oldbranch=next((e for e in nav['events'] if 'FocusHall316' in json.dumps(e)),None)
if oldbranch:nav['events'].remove(oldbranch)
branch=copy.deepcopy(next(e for e in nav['events'] if 'FocusPavilion' in json.dumps(e)))
def edit(node):
 if isinstance(node,dict):
  params=node.get('parameters',[]);typ=node.get('type',{});typ=typ.get('value') if isinstance(typ,dict) else typ
  if typ=='SetNumberVariable' and params:
   values={'TargetX':x,'TargetY':y,'TargetZ':originz+10,'Distance':90,'Yaw':angle,'Elevation':28}
   if params[0] in values:params[2]=str(values[params[0]])
  for k,v in node.items():
   if k=='parameters':node[k]=[str(p).replace('FocusPavilion','FocusHall316') for p in v]
   else:edit(v)
 elif isinstance(node,list):
  for n in node:edit(n)
edit(branch);nav['events'].append(branch)
assert terrain_before==hashlib.sha256(json.dumps(terrain,sort_keys=True).encode()).hexdigest();P.write_text(json.dumps(project,ensure_ascii=False,indent=2))
placement={'landmark':'316會館／聖子愛之家／316紀念館','object':'Hall316','scene':'月明洞核心區','user_instruction':'放進地圖','location_source':f['properties']['source_url'],'location_status':'依已存OSM聖子愛之家建築輪廓及使用者同名確認定位；不是實測建築座標。','position':[x,y,originz],'angle_deg':angle,'front_facing':'月明湖','ground_z_at_origin':ground(x,y),'ground_range_under_main':[min(ground(*p) for p in main),upper],'fixed_model_size_m':modelsize,'scaled_to_osm_footprint':False,'foundation':'山側下層與坡面相接；前側以獨立石基座補足高差。未改寫地形。','focus_button':'FocusHall316','model_sha256':hashlib.sha256((out/'hall316.glb').read_bytes()).hexdigest()};path=R/'source-data/landmark-placements.json';placements=json.loads(path.read_text()) if path.exists() else [];placements=[p for p in placements if p.get('object')!='Hall316']+[placement];path.write_text(json.dumps(placements,ensure_ascii=False,indent=2))
pending=R/'source-data/pending-locations.json';data=json.loads(pending.read_text());entry=next(p for p in data if p['name']=='316會館');entry.update(status='使用者已確認與聖子愛之家同名，並指示放入地圖；已依既有OSM輪廓配置，精確實測座標仍待核對。',source_url=f['properties']['source_url']);pending.write_text(json.dumps(data,ensure_ascii=False,indent=2));print(json.dumps(placement,ensure_ascii=False,indent=2))
