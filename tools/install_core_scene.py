"""One-time migration, run only with the saved GDevelop project CLOSED.

Copies the former overview into a new native scene, with independent assets.
The per-scene EventScript files are compiled through the GDevelop connection.
"""
from pathlib import Path
import copy
import json
import uuid

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'wolmyeongdong/project.json'
project=json.loads(P.read_text())
old=next(s for s in project['layouts'] if s['name']=='月明洞地形圖')
shell=next(s for s in project['layouts'] if s['name']=='月明洞核心區')
assert not shell['objects'], 'Migration already installed; do not overwrite edited core scene'
meta=json.loads((P.parent/'assets/core/geography.json').read_text())
x,y,_=meta['terrain_position'];width,height=meta['width_m'],meta['height_m']
core=copy.deepcopy(old);core['name']=shell['name'];core['mangledName']=shell['mangledName'];core['title']='月明洞核心區'
core['events']=[]
for obj in core['objects']:
    if 'persistentUuid' in obj:obj['persistentUuid']=str(uuid.uuid4())
for inst in core['instances']:inst['persistentUuid']=str(uuid.uuid4())
terrain=next(o for o in core['objects'] if o['name']=='WolmyeongTerrain')
terrain['content'].update(HeightmapImage='core-heightmap-rg16.png',Edits=(P.parent/'assets/core/road-edits.json').read_text(),SculptData='')
terrain['content'].update(Layer1Color='97;141;91',Layer4Color='201;181;145')
terrain_inst=next(i for i in core['instances'] if i['name']=='WolmyeongTerrain')
terrain_inst.update(x=x,y=y,z=0,width=width,height=height,depth=600)
moon=copy.deepcopy(next(o for o in core['objects'] if o['name']=='MoonLake'))
moon_inst=copy.deepcopy(next(i for i in core['instances'] if i['name']=='MoonLake'))
resources=project['resources']['resources']
resources.append({'file':'assets/core/heightmap-rg16.png','name':'core-heightmap-rg16.png','kind':'image','smoothed':False,'metadata':'','userAdded':True})
for name,data in meta['models'].items():
    if name in ('SportsGround','Lawn'):
        obj=copy.deepcopy(moon);obj['name']=name;obj['persistentUuid']=str(uuid.uuid4());core['objects'].append(obj)
        inst=copy.deepcopy(moon_inst);inst['name']=name;inst['persistentUuid']=str(uuid.uuid4());core['instances'].append(inst)
    else:
        obj=next(o for o in core['objects'] if o['name']==name);inst=next(i for i in core['instances'] if i['name']==name)
    obj['content'].update(modelResourceName=data['resource'],**dict(zip(('width','height','depth'),data['size'])))
    inst.update(**dict(zip(('x','y','z'),data['position'])),**dict(zip(('width','height','depth'),data['size'])))
    resources.append({'file':data['file'],'name':data['resource'],'kind':'model3D','metadata':'','userAdded':True})

def text(scene,name,value):
    obj=next(o for o in scene['objects'] if o['name']==name);obj['string']=value;obj['content']['text']=value

text(core,'MapTitle','月明洞｜核心區')
text(core,'ViewAll','[ 區域索引 ]')
text(core,'ViewCore','[ 核心區總覽 ]')
text(core,'LakeLabel','米色：運動場　亮綠：草坪\n藍色：月明湖')
text(core,'MapCredit','SRTM / Open Topo Data · © OpenStreetMap contributors\n核心區約630×610m；路寬為示意，依公尺固定，不隨地圖範圍放大。')
next(i for i in core['instances'] if i['name']=='MapHelp')['y']=310
button=next(o for o in core['objects'] if o['name']=='ViewCore')
button_inst=next(i for i in core['instances'] if i['name']=='ViewCore')
for name,label,bx in [('FocusSports','[ 運動場 ]',48),('FocusLawn','[ 草坪 ]',380),('FocusLake','[ 月明湖 ]',720)]:
    obj=copy.deepcopy(button);obj.update(name=name,persistentUuid=str(uuid.uuid4()));obj['string']=label;obj['content']['text']=label;core['objects'].append(obj)
    inst=copy.deepcopy(button_inst);inst.update(name=name,persistentUuid=str(uuid.uuid4()),x=bx,y=230,width=300,height=60);core['instances'].append(inst)
project['layouts'][project['layouts'].index(shell)]=core
project['firstLayout']=core['name']
text(old,'MapTitle','月明洞｜區域索引')
text(old,'ViewCore','[ 進入核心區 ]')
text(old,'ViewWalk','[ 進入核心區 F ]')
text(old,'MapHelp','全區用來查看方位與未來分區；點「進入核心區」或按 F 開始細部瀏覽。')
P.write_text(json.dumps(project,ensure_ascii=False,indent=2))

source=(ROOT/'tools/camera.events.txt').read_text()
groups=source.split('group ');groups=['group '+g for g in groups[1:]]
overview=groups[:]
overview[1]='''group "02 區域索引導航":
  if MouseButtonFromTextReleased("Left") and IsCursorOnObject(ViewAll) and NumberVariable(WasLeft, =, 1) or KeyFromTextJustPressed("Home"):
    SetNumberVariable(TargetX, =, 1778.3594455)
    SetNumberVariable(TargetY, =, 2201.6625886)
    SetNumberVariable(Distance, =, 7000)
    SetNumberVariable(Yaw, =, 45)
    SetNumberVariable(Elevation, =, 55)
  if MouseButtonFromTextReleased("Left") and IsCursorOnObject(ViewCore) and NumberVariable(WasLeft, =, 1):
    Scene("月明洞核心區", no)
  if MouseButtonFromTextReleased("Left") and IsCursorOnObject(ViewWalk) and NumberVariable(WasLeft, =, 1) or KeyFromTextJustPressed("f"):
    Scene("月明洞核心區", no)
'''
(ROOT/'tools/overview.events.txt').write_text(''.join(g for i,g in enumerate(overview) if i not in (2,7)))
source=source.replace('SetNumberVariable(Distance, =, 7000)','SetNumberVariable(Distance, =, 1100)').replace('SetNumberVariable(TargetX, =, 1778.3594455)',f'SetNumberVariable(TargetX, =, {x+width/2})').replace('SetNumberVariable(TargetY, =, 2201.6625886)',f'SetNumberVariable(TargetY, =, {y+height/2})')
source=source.replace('clamp(TargetX, 0, 3556.7188911)',f'clamp(TargetX, {x}, {x+width})').replace('clamp(TargetY, 0, 4403.3251772)',f'clamp(TargetY, {y}, {y+height})')
for var in ('TargetX','WalkX + WalkDX / WalkLength * WalkSpeed * TimeDelta()'):
    source=source.replace(f'clamp({var}, 5, 3551.7188911)',f'clamp({var}, {x+5}, {x+width-5})')
for var in ('TargetY','WalkY + WalkDY / WalkLength * WalkSpeed * TimeDelta()'):
    source=source.replace(f'clamp({var}, 5, 4398.3251772)',f'clamp({var}, {y+5}, {y+height-5})')
source=source.replace('WalkSpeed, =, 1.8','WalkSpeed, =, 8').replace('WalkSpeed, =, 4)','WalkSpeed, =, 24)')
for suffix in ('MapLakeZ - 1.8','MapRoadZ - 0.8','MapTrailZ - 0.8'):
    source=source.replace(suffix,suffix.split(' - ')[0])
new_groups=source.split('group ');new_groups=['group '+g for g in new_groups[1:]]
nav='''group "02 核心區與場地導航":
  if MouseButtonFromTextReleased("Left") and IsCursorOnObject(ViewAll) and NumberVariable(WasLeft, =, 1):
    MousePointerLock::ExitPointerLock()
    Scene("月明洞地形圖", no)
'''
for condition,cx,cy,distance in [
    ('MouseButtonFromTextReleased("Left") and IsCursorOnObject(ViewCore) and NumberVariable(WasLeft, =, 1) or KeyFromTextJustPressed("Home")',x+width/2,y+height/2,1100),
    *[(f'MouseButtonFromTextReleased("Left") and IsCursorOnObject({button}) and NumberVariable(WasLeft, =, 1)',*next(s['focus_xy'] for s in meta['sites'] if s['object']==name),distance) for button,name,distance in [('FocusSports','SportsGround',360),('FocusLawn','Lawn',330),('FocusLake','MoonLake',300)]]]:
    nav+=f'''  if {condition}:
    SetNumberVariable(WalkMode, =, 0)
    MousePointerLock::ExitPointerLock()
    SetNumberVariable(TargetX, =, {cx})
    SetNumberVariable(TargetY, =, {cy})
    SetNumberVariable(Distance, =, {distance})
    SetNumberVariable(Yaw, =, 45)
    SetNumberVariable(Elevation, =, 55)
'''
new_groups[1]=nav
(ROOT/'tools/core.events.txt').write_text(''.join(new_groups))
print(json.dumps({'first_scene':project['firstLayout'],'core_extent_m':[width,height],'native_models':list(meta['models']),'road_width_range_m':[1.2,3.5]},ensure_ascii=False))
