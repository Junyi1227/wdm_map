"""Build a separate native GDevelop model review project. Never writes core game."""
import pathlib,json,copy,uuid
R=pathlib.Path(__file__).resolve().parents[1];P=json.loads((R.parent/'wolmyeongdong/project.json').read_text());base=P['layouts'][0]
def uid():return str(uuid.uuid4())
def instruction(t,p):return {'type':{'value':t},'parameters':[str(x) for x in p]}
def event(cond,acts):return {'type':'BuiltinCommonInstructions::Standard','conditions':cond,'actions':acts}
def setvar(k,v):return instruction('SetNumberVariable',[k,'=',v])
def key(k):return instruction('KeyFromTextJustPressed',['','"'+k+'"'])
P['properties'].update(name='月明洞｜地標模型檢視',description='三個照片輔助的簡化初稿；估計尺寸；未整合到核心區。',projectUuid=uid(),latestCompilationDirectory='')
P['resources']={'resources':[],'resourceFolders':[]};P['objects']=[];P['variables']=[];P['externalEvents']=[];P['externalLayouts']=[];P['eventsFunctionsExtensions']=[e for e in P['eventsFunctionsExtensions'] if e['name']=='ThirdPersonCamera'];P['layouts']=[]
folders=['09-camel-rock','10-round-hill-pavilion','08-prayer-hill'];names=['駱駝石','圓山八角亭','禱告山']
for idx,(folder,name) in enumerate(zip(folders,names)):
 meta=json.loads((R/folder/'model/model.json').read_text());s=copy.deepcopy(base);s.update(name=name,title=name,mangledName='Landmark'+str(idx),instances=[],objects=[],objectsGroups=[],objectsFolderStructure={'folderName':'__ROOT','children':[]},events=[],behaviorsSharedData=[])
 # Same metre convention as the main game; models retain their own origin.
 lo,hi=meta['bounds_blender_z_up'];sizes=[hi[i]-lo[i] for i in range(3)];model=copy.deepcopy(next(o for o in base['objects'] if o['name']=='MoonLake'));model.update(name='Landmark',persistentUuid=uid());model['content'].update(modelResourceName=folder+'.glb',width=sizes[0],height=sizes[1],depth=sizes[2],rotationX=90,isCastingShadow=False,isReceivingShadow=False)
 s['objects'].append(model);s['instances'].append({'name':'Landmark','persistentUuid':uid(),'x':0,'y':0,'z':0,'angle':0,'zOrder':0,'layer':'','customSize':True,'width':sizes[0],'height':sizes[1],'depth':sizes[2],'numberProperties':[],'stringProperties':[],'initialVariables':[]})
 P['resources']['resources'].append({'name':folder+'.glb','file':'../'+folder+'/model/landmark.glb','kind':'model3D','metadata':'','userAdded':True})
 for objname,text,x,y,size in [('MapTitle',name+'｜簡化初稿',48,35,56),('MapHelp','左鍵拖曳旋轉 · 右鍵／Shift＋左鍵平移 · 滾輪縮放 · WASD平移 · Home重設',48,120,32),('MapCredit','照片輔助建模，尺寸與隱藏處為估計；未放入核心區地圖。\n1 駱駝石　2 圓山八角亭　3 禱告山',48,1460,30),('RotateLeft','[ 左轉 ]',48,220,34),('RotateRight','[ 右轉 ]',270,220,34),('ZoomIn','[ 拉近 ]',490,220,34),('ZoomOut','[ 拉遠 ]',710,220,34)]:
  o=copy.deepcopy(next(o for o in base['objects'] if o['name']=='MapTitle'));o.update(name=objname,string=text,characterSize=size);o['content'].update(text=text,characterSize=size);s['objects'].append(o)
  s['instances'].append({'name':objname,'persistentUuid':uid(),'x':x,'y':y,'zOrder':5,'angle':0,'layer':'UI','customSize':False,'width':1800,'height':90,'numberProperties':[],'stringProperties':[],'initialVariables':[]})
 focus=[meta['focus'][0],-meta['focus'][1],meta['focus'][2]];distance=22 if folder=='10-round-hill-pavilion' else meta['distance'];s['r']=239;s['v']=241;s['b']=228;s['layers'][0]['camera3DNearPlaneDistance']=.05;s['layers'][0]['camera3DFarPlaneDistance']=1000
 for effect in s['layers'][0]['effects']:
  if 'intensity' in effect['doubleParameters']:effect['doubleParameters']['intensity']=.9
 init=[setvar('WalkMode',0),setvar('TargetX',focus[0]),setvar('TargetY',focus[1]),setvar('TargetZ',focus[2]),setvar('Distance',distance),setvar('Yaw',30),setvar('Elevation',35),instruction('ZoomCamera',['','1','"UI"','0']),instruction('SetCameraCenterX',['','=','1280','"UI"','0']),instruction('SetCameraCenterY',['','=','800','"UI"','0'])]
 s['events'].append(event([instruction('SceneJustBegins',[''])],init));s['events'].append(event([key('Home')],init[:8]))
 for k,dest in enumerate(names,1):s['events'].append(event([key('Num'+str(k))],[instruction('Scene',['','"'+dest+'"','no'])]))
 for i in [2,3,4,5,6]:
  e=copy.deepcopy(base['events'][i])
  def visit(node):
   if isinstance(node,dict):
    # Remove the terrain height dependency: the target is the model's centre.
    if node.get('type',{}).__class__ is dict and node.get('type',{}).get('value')=='SetNumberVariable' and node.get('parameters',[''])[0]=='TargetZ':node['parameters']=['TargetZ','=',str(focus[2])]
    for k,v in node.items():
     if k=='parameters':
      node[k]=[str(x).replace('clamp(Distance, 2500, 14000)','clamp(Distance, 2, 160)').replace('clamp(TargetX, 0, 3556.7188911)','clamp(TargetX, -60, 60)').replace('clamp(TargetY, 0, 4403.3251772)','clamp(TargetY, -60, 60)').replace('14000','160') for x in v]
     else:visit(v)
   elif isinstance(node,list):
    for item in node:visit(item)
  visit(e);s['events'].append(e)
 s['variables']=[{'name':v,'type':'number','value':0,'persistentUuid':uid()} for v in ['WalkMode','TargetX','TargetY','TargetZ','Distance','Yaw','Elevation','PrevX','PrevY','WasLeft','WasRight']]
 P['layouts'].append(s)
P['firstLayout']=names[0];P['layoutsFolderStructure']={'folderName':'__ROOT','children':[{'type':'Layout','name':n} for n in names]};P['externalEventsFolderStructure']={'folderName':'__ROOT','children':[]};P['externalLayoutsFolderStructure']={'folderName':'__ROOT','children':[]};P['objectsFolderStructure']={'folderName':'__ROOT','children':[]};P['testsFolderStructure']={'folderName':'__ROOT','children':[]}
out=R/'preview';out.mkdir(exist_ok=True);(out/'project.json').write_text(json.dumps(P,ensure_ascii=False,indent=2));print('Created separate GDevelop viewer with',len(P['layouts']),'scenes')
