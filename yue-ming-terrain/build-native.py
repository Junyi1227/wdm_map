"""Author a native GDevelop project with placed GLB instances and camera-only code."""
from pathlib import Path
import json,uuid,copy,math
root=Path(__file__).parent
manifest=json.loads((root/'native-manifest.json').read_text())
data=json.loads((root/'terrain-data.json').read_text())
building=json.loads((root/'building-data.json').read_text())
source=(root/'terrain-runtime.js').read_text()
ui=source[source.index('  // PIXI interface'):source.index('  const S={')]
frame=source[source.index('{\n  const S=runtimeScene.__yueTerrain'):]
frame=frame.replace("  const dt=Math.min(runtimeScene.getElapsedTime()/1000,0.05);S.time+=dt;", "  S.syncWorld();\n  const dt=Math.min(runtimeScene.getElapsedTime()/1000,0.05);S.time+=dt;")
frame=frame.replace('),3,S.W-3)', '),S.bounds.minX+1,S.bounds.maxX-1)').replace('),3,S.H-3)', '),S.bounds.minY+1,S.bounds.maxY-1)')
# Exact source strings also cover older whitespace variants.
frame=frame.replace(',3,S.W-3)',',S.bounds.minX+1,S.bounds.maxX-1)').replace(',3,S.H-3)',',S.bounds.minY+1,S.bounds.maxY-1)')
frame=frame.replace('),0,S.W)', '),S.bounds.minX,S.bounds.maxX)').replace('),0,S.H)', '),S.bounds.minY,S.bounds.maxY)')
frame=frame.replace(',0,S.W)', ',S.bounds.minX,S.bounds.maxX)').replace(',0,S.H)', ',S.bounds.minY,S.bounds.maxY)')
init=r'''// Native scene objects are authored in the editor. This event only manages view, input and overlays.
if (runtimeScene.getGame().isInGameEdition()) return;
if (!runtimeScene.__yueTerrain) {
  const D = DATA_JSON;
  const B = BUILDING_JSON;
  const M = MANIFEST_JSON;
  const T=THREE,clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
  const W=D.widthMeters,H=D.depthMeters,C=D.gridColumns,R=D.gridRows;
  const xy=p=>[(p[0]-72)/1000*W,(p[1]-72)/852*H];
  const lake=D.lakePixels.map(xy),roads=D.roadPixels.map(p=>p.map(xy)),trails=D.trailPixels.map(p=>p.map(xy));
  const lakeZ=D.lakeLevelMeters-240,baseZ=lakeZ+B.basementFloorAboveLakeMeters,platformZ=baseZ+B.basementHeightMeters,roofZ=platformZ+12.6;
  const br=B.rotationDegrees*Math.PI/180,bc=Math.cos(br),bs=Math.sin(br);
  const local=(x,y)=>{const dx=x-B.centerMeters[0],dy=y-B.centerMeters[1];return [dx*bc+dy*bs,-dx*bs+dy*bc];};
  const global=(x,y)=>[B.centerMeters[0]+x*bc-y*bs,B.centerMeters[1]+x*bs+y*bc];
  const inside=(x,y,poly)=>{let b=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){const a=poly[i],c=poly[j];if((a[1]>y)!==(c[1]>y)&&x<(c[0]-a[0])*(y-a[1])/(c[1]-a[1])+a[0])b=!b;}return b;};
  const layer=runtimeScene.getLayer('Terrain3D'),renderer=layer.getRenderer(),scene=renderer.getThreeScene();
  scene.background=new T.Color('#dce8e7');scene.fog=new T.Fog('#dce8e7',6.5,15);
  const helper=new T.Group();helper.name='TourOverlay';renderer.add3DRendererObject(helper);
  const contours=new T.Group();contours.visible=false;helper.add(contours);
  const lineGeometry=new T.BufferGeometry();lineGeometry.setAttribute('position',new T.Float32BufferAttribute(CONTOUR_JSON,3));
  contours.add(new T.LineSegments(lineGeometry,new T.LineBasicMaterial({color:'#365f50',transparent:true,opacity:0.2})));
  const player=new T.Mesh(new T.ConeGeometry(2.2,6,6).rotateX(Math.PI/2),new T.MeshBasicMaterial({color:'#edaa62'}));helper.add(player);
  const ray=new T.Raycaster(),worldScale=runtimeScene.getRenderer3DWorldScale(),inverse=1/worldScale;
  let walkMeshes=[],solidMeshes=[],bounds={minX:0,minY:0,maxX:W,maxY:H},ticks=0;
  const instances=()=>runtimeScene.getAdhocListOfAllInstances();
  const syncWorld=()=>{
    scene.updateMatrixWorld(true);
    if(ticks++%30!==0)return;
    walkMeshes=[];solidMeshes=[];
    const terrainBox=new T.Box3();
    for(const o of instances()){
      const name=o.getName(),mesh=o.get3DRendererObject?.();if(!mesh)continue;
      const terrain=name.startsWith('Terrain_')&&name!=='Terrain_Cutaway';
      if(terrain||M.walkableNames.includes(name))walkMeshes.push(mesh);
      if(M.solidNames.includes(name)||name==='Hall_Platform')solidMeshes.push(mesh);
      if(terrain)terrainBox.union(new T.Box3().setFromObject(mesh));
    }
    if(!terrainBox.isEmpty())bounds={minX:terrainBox.min.x*worldScale,maxX:terrainBox.max.x*worldScale,minY:-terrainBox.max.y*worldScale,maxY:-terrainBox.min.y*worldScale};
    const state=runtimeScene.__yueTerrain;if(state)state.bounds=bounds;
  };
  syncWorld();
  const fallback=(x,y)=>{
    const i=clamp(Math.round(x/W*(C-1)),0,C-1),j=clamp(Math.round(y/H*(R-1)),0,R-1);
    return D.heightMeters[j*C+i]-240;
  };
  const ground=(x,y,ceiling=4000)=>{
    ray.set(new T.Vector3(x*inverse,-y*inverse,ceiling*inverse),new T.Vector3(0,0,-1));ray.near=0;ray.far=6000*inverse;
    const hit=ray.intersectObjects(walkMeshes,true)[0];return hit?hit.point.z*worldScale:fallback(x,y);
  };
  const walkHeight=(x,y,foot)=>ground(x,y,foot+0.62);
  const blockedAt=(x,y,foot)=>{
    const state=runtimeScene.__yueTerrain;if(!state)return false;
    const dx=x-state.x,dy=y-state.y,len=Math.hypot(dx,dy);if(len<0.0001)return false;
    for(const eye of [0.9,1.65]){
      ray.set(new T.Vector3(state.x*inverse,-state.y*inverse,(foot+eye)*inverse),new T.Vector3(dx,-dy,0).normalize());ray.near=0;ray.far=(len+0.32)*inverse;
      if(ray.intersectObjects(solidMeshes,true).length)return true;
    }
    return false;
  };
'''
state=r'''  const S={D,world:helper,layer,renderer,ground,inside,lake,W,H,building:runtimeScene.getObjects('Hall_Main')[0]?.get3DRendererObject(),buildingMeta:B,local,global,baseZ,platformZ,roofZ,walkHeight,blockedAt,syncWorld,bounds,native:true,mode:'first',x:buildingView[0],y:buildingView[1],yaw:viewYaw,pitch:0.04,footZ:ground(...buildingView),orbitYaw:0.35,orbitTilt:0.88,orbitRadius:820,targetX:W/2,targetY:H/2,targetZ:105,contours,player,hud,panel,eyebrow,title,subtitle,badge,overviewLabel,resetLabel,helpTitle,help,note,miniTitle,miniLegend,altitude,credit,crosshair,mini,locator,prevMouse:false,lastMouseX:0,lastMouseY:0,time:0};
  S.reset=()=>{S.x=buildingView[0];S.y=buildingView[1];S.yaw=viewYaw;S.pitch=0.04;S.footZ=ground(...buildingView);S.mode='first';};
  S.toggle=()=>{S.mode=S.mode==='first'?'god':'first';};
  runtimeScene.__yueTerrain=S;
}
'''
runtime=init+ui+state+frame
runtime=runtime.replace('DATA_JSON',json.dumps(data,ensure_ascii=False,separators=(',',':'))).replace('BUILDING_JSON',json.dumps(building,ensure_ascii=False,separators=(',',':'))).replace('MANIFEST_JSON',json.dumps({'walkableNames':manifest['walkableNames'],'solidNames':manifest['solidNames']},separators=(',',':'))).replace('CONTOUR_JSON',(root/'contour-data.json').read_text())
(root/'native-runtime.js').write_text(runtime)
project=json.loads((root/'project-template.json').read_text())
layout=project['layouts'][0]
project['properties']['name']='月明湖｜可編輯地圖'
project['properties']['description']='原生可編輯 3D 場景；地形分塊、建築及樓梯分離，樹木可逐棵選取。模型座標單位為公尺，可向四周擴建。'
project['properties']['projectUuid']=str(uuid.uuid4())
layout['objects']=[];layout['instances']=[]
resources=[];categories={}
for asset in manifest['assets']:
    w,h,d=asset['size'];name=asset['name']
    resources.append({'file':asset['file'],'kind':'model3D','metadata':'','name':name+'.glb','userAdded':True})
    content={'width':w,'height':h,'depth':d,'rotationX':90,'rotationY':0,'rotationZ':0,'keepAspectRatio':False,'materialType':'KeepOriginal','originLocation':'ModelOrigin','centerLocation':'ObjectCenter','isCastingShadow':False,'isReceivingShadow':False,'modelResourceName':name+'.glb','animations':[],'crossfadeDuration':0.1}
    layout['objects'].append({'name':name,'persistentUuid':str(uuid.uuid4()),'type':'Scene3D::Model3DObject','variables':[],'effects':[],'behaviors':[],'content':content})
    categories.setdefault(asset['category'],[]).append({'objectName':name})
for item in manifest['instances']:
    layout['instances'].append({**{k:item[k] for k in ['name','x','y','z','width','height','depth','angle']},'persistentUuid':str(uuid.uuid4()),'customSize':True,'keepRatio':False,'layer':'Terrain3D','zOrder':0,'numberProperties':[],'stringProperties':[],'initialVariables':[]})
labels={'Terrain':'01 地形區塊｜可向外擴建','Hall':'02 湖東主建築｜主體・地下室・樓梯・平台','Water':'03 月明湖與湖岸','Lakeside':'04 涼亭與木平台','Roads':'05 道路','Trails':'06 步道','Trees':'07 樹木｜個別實例可移動'}
layout['objectsFolderStructure']={'folderName':'__ROOT','children':[{'folderName':labels[k],'children':v} for k,v in sorted(categories.items(),key=lambda kv:labels[kv[0]])]}
project['resources']={'resources':resources}
oldLayer=copy.deepcopy(layout['layers'][0])
oldLayer.update({'name':'Terrain3D','renderingType':'3d','cameraType':'perspective','camera3DFieldOfView':67,'camera3DNearPlaneDistance':0.15,'camera3DFarPlaneDistance':4000,'followBaseLayerCamera':False})
oldLayer['effects']=[
 {'effectType':'Scene3D::HemisphereLight','name':'Soft daylight','doubleParameters':{'elevation':90,'intensity':2,'rotation':0},'stringParameters':{'skyColor':'255;248;223','groundColor':'120;148;124','top':'Z+'},'booleanParameters':{}},
 {'effectType':'Scene3D::DirectionalLight','name':'Warm sun','doubleParameters':{'elevation':54,'intensity':2.4,'rotation':230,'distanceFromCamera':1500,'shadowDistance':1000,'shadowNormalBias':1,'minimumShadowBias':0.001},'stringParameters':{'color':'255;240;206','shadowQuality':'medium','top':'Z+'},'booleanParameters':{'isCastingShadow':False}},
 {'effectType':'Scene3D::AmbientLight','name':'Gentle fill','doubleParameters':{'intensity':0.45},'stringParameters':{'color':'255;255;255'},'booleanParameters':{}}
]
uiLayer=copy.deepcopy(oldLayer);uiLayer.update({'name':'','renderingType':'2d','effects':[]})
layout['layers']=[oldLayer,uiLayer]
for effect in oldLayer['effects']:
    effect['doubleParameters']['intensity']/=math.pi
layout['events']=[{'type':'BuiltinCommonInstructions::JsCode','inlineCode':runtime.splitlines(),'parameterObjects':'','useStrict':True,'eventsSheetExpanded':False}]
layout['uiSettings'].update({'selectedLayer':'Terrain3D','gridWidth':10,'gridHeight':10,'gridDepth':10,'grid':False})
project['tests']=[];project['testsFolderStructure']={'folderName':'__ROOT','children':[]}
(root/'editable-map.json').write_text(json.dumps(project,ensure_ascii=False,indent=2))
print('Native project authored:',len(layout['objects']),'object types;',len(layout['instances']),'placed instances')
