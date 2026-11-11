# -*- coding: utf-8 -*-
"""One-time native scene authoring. Run after exporting the Blender model."""
import json,copy,uuid,shutil,math,hashlib,pathlib
from lake_rock_layout import ROOT,ORIGIN,ACROSS,BACK,BASE,world
P=ROOT/'wolmyeongdong/project.json';project=json.loads(P.read_text());core=next(s for s in project['layouts'] if s['name']=='月明洞核心區')
out=ROOT/'landmarks/04-god-waterfall/model';meta=json.loads((out/'model.json').read_text());cfg=json.loads((out.parent/'layout.json').read_text())
map_parts=json.loads((out/'map-parts.json').read_text())
pose_path=ROOT/'source-data/lake-rocks-map-pose.json'
pose=json.loads(pose_path.read_text()) if pose_path.exists() else {}
ORIGIN=tuple(pose.get('origin_xy',ORIGIN));rotation=pose.get('angle_deg',0);rr=math.radians(rotation);cc,ss=math.cos(rr),math.sin(rr)
assert not next(o for o in core['objects'] if o['name']=='WolmyeongTerrain')['content'].get('SculptData'),'Query live terrain before placing after sculpting'
names=['WolmyeongTerrain','MoonLake','RoadDetail','TrailDetail','Hall316','Hall316Foundation','RoundHillPavilion','RoundHillPavilionBase','SportsGround','Lawn']
preserved={key:{n:[o for o in core[key] if o['name']==n] for n in names} for key in ['objects','instances']};before=copy.deepcopy(preserved)
def uid():return str(uuid.uuid4())
def instr(name,parameters):return {'type':{'value':name},'parameters':[str(p) for p in parameters]}
def setvar(n,v):return instr('SetNumberVariable',[n,'=',v])
def event(conditions,actions,events=None):
 d={'type':'BuiltinCommonInstructions::Standard','conditions':conditions,'actions':actions}
 if events is not None:d['events']=events
 return d
parts={'upper-rocks':'LakeUpperRocks','water':'LakeRockWater','summit-pavilion':'LakeRockPavilion'}
for file,name in parts.items():
 size=map_parts[file]['size'];offset=map_parts[file]['offset_native'];resource='lake-rocks-'+file+'.glb';dest=P.parent/'assets/landmarks'/resource;shutil.copy2(out/('map-'+file+'.glb'),dest)
 obj=next((o for o in core['objects'] if o['name']==name),None)
 if obj is None:obj=copy.deepcopy(next(o for o in core['objects'] if o['name']=='Hall316'));obj.update(name=name,persistentUuid=uid());core['objects'].append(obj)
 obj['content'].update(modelResourceName=resource,width=size[0],height=size[1],depth=size[2],originLocation='ModelOrigin',centerLocation='ModelOrigin',rotationX=90,rotationY=0,rotationZ=0)
 inst=next((o for o in core['instances'] if o['name']==name),None)
 if inst is None:inst=copy.deepcopy(next(o for o in core['instances'] if o['name']=='Hall316'));inst.update(name=name,persistentUuid=uid());core['instances'].append(inst)
 inst.update(x=ORIGIN[0]+cc*offset[0]-ss*offset[1],y=ORIGIN[1]+ss*offset[0]+cc*offset[1],z=BASE+offset[2],angle=rotation,width=size[0],height=size[1],depth=size[2],customSize=True)
 res=next((r for r in project['resources']['resources'] if r['name']==resource),None)
 if res is None:res={'name':resource,'kind':'model3D','metadata':'','userAdded':True};project['resources']['resources'].append(res)
 res['file']='assets/landmarks/'+resource
def button(name,text,x,y,width):
 if not any(o['name']==name for o in core['objects']):
  o=copy.deepcopy(next(o for o in core['objects'] if o['name']=='FocusHall316'));o.update(name=name,persistentUuid=uid(),string=text);o['content']['text']=text;core['objects'].append(o)
  i=copy.deepcopy(next(i for i in core['instances'] if i['name']=='FocusHall316'));i.update(name=name,persistentUuid=uid(),x=x,y=y,width=width);core['instances'].append(i)
button('FocusLakeRocks','[ 湖畔石景 ]',1900,230,480)
nav=next(g for g in core['events'] if g.get('name','').startswith('02 '));nav['events']=[e for e in nav['events'] if not any(n in json.dumps(e) for n in ['FocusLakeRocks','EnterLakeRamp'])]
template=next(e for e in nav['events'] if 'FocusHall316' in json.dumps(e))
branch=copy.deepcopy(template)
def replace(n):
 if isinstance(n,dict):
  if isinstance(n.get('type'),dict) and n['type'].get('value')=='SetNumberVariable':
   values={'TargetX':ORIGIN[0],'TargetY':ORIGIN[1],'TargetZ':BASE+8,'Distance':112,'Yaw':222+rotation,'Elevation':24}
   p=n['parameters']
   if p[0] in values:p[2]=str(values[p[0]])
  for k,v in n.items():
   if k=='parameters':n[k]=[p.replace('FocusHall316','FocusLakeRocks') for p in v]
   else:replace(v)
 elif isinstance(n,list):
  for v in n:replace(v)
replace(branch);nav['events'].append(branch)
# Remove the superseded added access structures and their synthetic walking surfaces.
removed=['LakeShoreRocks','LakeRearRamp','EnterLakeRamp']
for key in ['objects','instances']:core[key]=[o for o in core[key] if o['name'] not in removed]
core['variables']=[v for v in core['variables'] if v['name'] not in ['RockLocalU','RockLocalV','RockRampT']]
def restore_ground_walk(n):
 if not isinstance(n,dict):return
 acts=n.get('actions',[])
 if any(a.get('parameters',[''])[0]=='RockLocalU' for a in acts):
  tail=next(e['actions'] for e in reversed(n.get('events',[])) if any(a.get('type',{}).get('value')=='Scene3D::SetCameraZ' for a in e.get('actions',[])))
  n['actions']=[a for a in acts if a.get('parameters',[''])[0] not in ['RockLocalU','RockLocalV','RockRampT']]+tail
  n.pop('events',None);n.pop('lakeRockWalkSurface',None);return
 for e in n.get('events',[]):restore_ground_walk(e)
for group in core['events']:restore_ground_walk(group)
project['resources']['resources']=[r for r in project['resources']['resources'] if r['name'] not in ['lake-rocks-lake-rocks.glb','lake-rocks-rear-ramp.glb']]
for key in ['objects','instances']:
 for name in names:assert [o for o in core[key] if o['name']==name]==before[key][name],(key,name)
P.write_text(json.dumps(project,ensure_ascii=False,indent=2))
placements=ROOT/'source-data/landmark-placements.json';data=json.loads(placements.read_text());data=[p for p in data if p.get('object')!='LakeUpperRocks'];data.append({'object':'LakeUpperRocks','landmark':'月明湖對岸石頭造景／瀑布亭','scene':core['name'],'position':[ORIGIN[0],ORIGIN[1],BASE],'parts':parts,'status':cfg['status'],'reference_photos':cfg['sources'],'road_separation':'前後石景分開，中間保留湖岸道路，不合併成實心牆。','access':'前後通路皆沿用原地圖，不包含新增坡道、樓梯或人工高度補丁。','focus_button':'FocusLakeRocks'});placements.write_text(json.dumps(data,ensure_ascii=False,indent=2))
report={'preserved_objects':names,'native_events':True,'runtime_js_added':False,'relative_resources':True,'origin_xy':ORIGIN,'base_z':BASE,'model_parts':parts,'triangles':meta['triangles'],'position_is_approximate':True}
(ROOT/'validation/lake-rocks-placement.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
