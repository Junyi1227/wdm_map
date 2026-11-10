"""Place the confirmed pavilion on the local summit west/southwest of the lawn.
No terrain regeneration: existing sculpt/paint data and all other objects stay intact.
"""
import json,pathlib,copy,uuid,math,struct,shutil,hashlib
from PIL import Image
R=pathlib.Path(__file__).resolve().parents[2];P=R/'wolmyeongdong/project.json';project=json.loads(P.read_text());core=next(s for s in project['layouts'] if s['name']=='月明洞核心區');meta=json.loads((P.parent/'assets/core/geography.json').read_text());im=Image.open(P.parent/'assets/core/heightmap-rg16.png');x0,y0,_=meta['terrain_position'];W,H=meta['width_m'],meta['height_m']
terrain=next(o for o in core['objects'] if o['name']=='WolmyeongTerrain');assert not terrain['content'].get('SculptData'),'Use live terrain query before placement on sculpted terrain'
def ground(x,y):
 u=max(0,min(1024,(x-x0)/W*1024));v=max(0,min(1024,(y-y0)/H*1024));i,j=min(1023,int(u)),min(1023,int(v));a,b=u-i,v-j
 def grid(c,r):
  uu,vv=c/2,r/2;ii,jj=min(511,int(uu)),min(511,int(vv));aa,bb=uu-ii,vv-jj
  def pix(i,j):red,green,_=im.getpixel((i,j));return (red*256+green)/65535*600
  return pix(ii,jj)*(1-aa)*(1-bb)+pix(ii+1,jj)*aa*(1-bb)+pix(ii,jj+1)*(1-aa)*bb+pix(ii+1,jj+1)*aa*bb
 tl,tr,bl,br=grid(i,j),grid(i+1,j),grid(i,j+1),grid(i+1,j+1)
 return tl+a*(tr-tl)+b*(bl-tl) if a+b<=1 else br+(1-a)*(bl-br)+(1-b)*(tr-br)
x,y=1828.,2270.;lawn=next(s for s in meta['sites'] if s['object']=='Lawn');lx,ly=lawn['focus_xy'];angle=math.degrees(math.atan2(ly-y,lx-x))-90;theta=math.radians(angle)
def world(u,v):return x+u*math.cos(theta)-v*math.sin(theta),y+u*math.sin(theta)+v*math.cos(theta)
# Small stone plinth fills terrain variation beneath the stilts and stair approach.
polys=[[(3.3*math.cos(i*math.tau/8+math.pi/8),3.3*math.sin(i*math.tau/8+math.pi/8)) for i in range(8)],[(-1.55,2.35),(1.55,2.35),(1.55,7.35),(-1.55,7.35)]]
polys=[[world(*p) for p in poly] for poly in polys];samples=[ground(*p) for poly in polys for p in poly]+[ground(x,y)];top=max(samples)+.06;points=[]
def tri(a,b,c):points.extend([a,b,c])
for poly in polys:
 cx=sum(p[0] for p in poly)/len(poly);cy=sum(p[1] for p in poly)/len(poly);ct=(cx,top,cy);cb=(cx,ground(cx,cy)-.15,cy)
 for a,b in zip(poly,poly[1:]+poly[:1]):
  at=(a[0],top,a[1]);bt=(b[0],top,b[1]);ab=(a[0],ground(*a)-.15,a[1]);bb=(b[0],ground(*b)-.15,b[1]);tri(ct,bt,at);tri(cb,ab,bb);tri(at,bt,bb);tri(at,bb,ab)
mins=[min(p[i] for p in points) for i in range(3)];maxs=[max(p[i] for p in points) for i in range(3)];sizes=[maxs[i]-mins[i] for i in range(3)];local=[p[i]-mins[i] for p in points for i in range(3)];binary=struct.pack('<'+'f'*len(local),*local)
doc={'asset':{'version':'2.0','generator':'Pavilion terrain-fitting plinth'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'mesh':0}],'meshes':[{'primitives':[{'attributes':{'POSITION':0},'material':0}]}],'materials':[{'doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':[.61,.64,.57,1],'roughnessFactor':.95,'metallicFactor':0}}],'buffers':[{'byteLength':len(binary)}],'bufferViews':[{'buffer':0,'byteLength':len(binary),'target':34962}],'accessors':[{'bufferView':0,'componentType':5126,'count':len(points),'type':'VEC3','min':[0,0,0],'max':sizes}]};js=json.dumps(doc,separators=(',',':')).encode();js+=b' '*((-len(js))%4);binary+=b'\0'*((-len(binary))%4)
out=P.parent/'assets/landmarks';out.mkdir(exist_ok=True);(out/'round-hill-pavilion-base.glb').write_bytes(struct.pack('<III',0x46546c67,2,28+len(js)+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary);shutil.copy2(R/'landmarks/10-round-hill-pavilion/model/landmark.glb',out/'round-hill-pavilion.glb')
modelmeta=json.loads((R/'landmarks/10-round-hill-pavilion/model/model.json').read_text());lo,hi=modelmeta['bounds_blender_z_up'];modelsize=[hi[i]-lo[i] for i in range(3)];template=next(o for o in core['objects'] if o['name']=='MoonLake')
for name,file,position,size,rot in [('RoundHillPavilion','round-hill-pavilion.glb',[x,y,top],modelsize,angle),('RoundHillPavilionBase','round-hill-pavilion-base.glb',[mins[0],mins[2],mins[1]],[sizes[0],sizes[2],sizes[1]],0)]:
 obj=next((o for o in core['objects'] if o['name']==name),None)
 if obj is None:obj=copy.deepcopy(template);obj.update(name=name,persistentUuid=str(uuid.uuid4()));core['objects'].append(obj)
 obj['content'].update(modelResourceName=file,width=size[0],height=size[1],depth=size[2],rotationX=90,rotationY=0,rotationZ=0,keepAspectRatio=False,originLocation='ModelOrigin',centerLocation='ModelOrigin' if name=='RoundHillPavilion' else 'ObjectCenter',isCastingShadow=False,isReceivingShadow=False)
 inst=next((i for i in core['instances'] if i['name']==name),None)
 if inst is None:inst=copy.deepcopy(next(i for i in core['instances'] if i['name']=='MoonLake'));inst.update(name=name,persistentUuid=str(uuid.uuid4()));core['instances'].append(inst)
 inst.update(x=position[0],y=position[1],z=position[2],width=size[0],height=size[1],depth=size[2],angle=rot,customSize=True)
 res=next((r for r in project['resources']['resources'] if r['name']==file),None)
 if res is None:res={'name':file,'kind':'model3D','metadata':'','userAdded':True};project['resources']['resources'].append(res)
 res['file']='assets/landmarks/'+file
# A native focus button makes the newly placed landmark easy to find.
if not any(o['name']=='FocusPavilion' for o in core['objects']):
 obj=copy.deepcopy(next(o for o in core['objects'] if o['name']=='FocusLawn'));obj.update(name='FocusPavilion',persistentUuid=str(uuid.uuid4()),string='[ 圓山八角亭 ]');obj['content']['text']=obj['string'];core['objects'].append(obj)
 inst=copy.deepcopy(next(i for i in core['instances'] if i['name']=='FocusLawn'));inst.update(name='FocusPavilion',x=1060,persistentUuid=str(uuid.uuid4()),width=420);core['instances'].append(inst)
 nav=next(g for g in core['events'] if g.get('name','').startswith('02 '));branch=copy.deepcopy(next(e for e in nav['events'] if 'FocusLawn' in json.dumps(e)))
 def edit(node):
  if isinstance(node,dict):
   params=node.get('parameters',[]);typ=node.get('type',{});typ=typ.get('value') if isinstance(typ,dict) else typ
   if typ=='SetNumberVariable' and params:
    values={'TargetX':x,'TargetY':y,'TargetZ':top+3,'Distance':52,'Yaw':30,'Elevation':32}
    if params[0] in values:params[2]=str(values[params[0]])
   for k,v in node.items():
    if k=='parameters':node[k]=[str(p).replace('FocusLawn','FocusPavilion') for p in v]
    else:edit(v)
  elif isinstance(node,list):
   for e in node:edit(e)
 edit(branch);nav['events'].append(branch)
P.write_text(json.dumps(project,ensure_ascii=False,indent=2))
placement={'landmark':'圓山八角亭','object':'RoundHillPavilion','scene':'月明洞核心區','user_instruction':'草皮西側的山頂','location_status':'依使用者方位指示，選用現有DEM草皮西南側局部高點；非實測地標GPS。','position':[x,y,top],'ground_z_at_origin':ground(x,y),'approx_elevation_m':ground(x,y)+150,'angle_deg':angle,'stairs_facing':'toward lawn','fixed_model_size_m':modelsize,'foundation':'獨立貼地石基座；未改寫地形高度或筆刷資料。','focus_button':'FocusPavilion','source_model_sha256':hashlib.sha256((out/'round-hill-pavilion.glb').read_bytes()).hexdigest()};(R/'source-data/landmark-placements.json').write_text(json.dumps([placement],ensure_ascii=False,indent=2));print(json.dumps(placement,ensure_ascii=False,indent=2))
