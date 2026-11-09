await harness.goToScene('月明湖地形');
await harness.stepFrames(4);
const s=harness.getCurrentRuntimeScene().__yueTerrain;
harness.assert(s?.native===true,'Native editor-authored scene controller initialized');
const terrainNames=['Terrain_0_0','Terrain_1_0','Terrain_0_1','Terrain_1_1'];
for(const name of terrainNames)harness.assert(harness.getObjects(name).length===1,'Placed editable tile '+name);
harness.assert(['Tree_1','Tree_2','Tree_3'].reduce((n,name)=>n+harness.getObjects(name).length,0)===1150,'Trees exist as 1150 editable instances');
for(const name of ['Hall_Main','Hall_Basement','Hall_Platform','Hall_Stairs','Hall_Terrace'])harness.assert(harness.getObjects(name).length===1,'Placed editable building part '+name);
const b=s.buildingMeta;
console.log(JSON.stringify({bounds:s.bounds,hall:harness.getRenderedBounds(harness.getObjects('Hall_Main')[0].id),stairs:harness.getRenderedBounds(harness.getObjects('Hall_Stairs')[0].id),camera:harness.getCameraState('Terrain3D')}));
await harness.takeScreenshot('原生場景・第一人稱',{width:1440});
const hero=s.global(-80,-8);
harness.lookAt({from:{x:hero[0],y:hero[1],z:s.platformZ+15},to:{x:b.centerMeters[0],y:b.centerMeters[1],z:s.platformZ+5},layer:'Terrain3D'});
await harness.takeScreenshot('原生模型・建築與樓梯',{width:1440});
// Follow actual player input around the north shore and up the staircase.
const angleDiff=(a,b)=>Math.atan2(Math.sin(a-b),Math.cos(a-b));
async function aimAt(x,y){
  const desired=Math.atan2(x-s.x,-(y-s.y));
  let count=0;
  while(Math.abs(angleDiff(desired,s.yaw))>0.018&&count++<150){
    const right=angleDiff(desired,s.yaw)>0;
    harness.setKeyPressed(right?'Right':'Left',true);await harness.stepFrames(1);harness.releaseAllInputs();
  }
  await harness.stepFrames(1);
}
async function walkTo(x,y,radius=0.7){
  let previous=1e9,stalls=0;
  for(let chunk=0;chunk<170;chunk++){
    const distance=Math.hypot(x-s.x,y-s.y);
    if(distance<radius)return true;
    await aimAt(x,y);
    harness.setKeyPressed('w',true);
    await harness.stepFrames(Math.min(18,Math.max(1,Math.floor(distance/0.14))));
    harness.releaseAllInputs();await harness.stepFrames(1);
    if(Math.abs(previous-distance)<0.08)stalls++;else stalls=0;
    if(stalls>=4){console.log('Movement stalled near '+JSON.stringify({x:s.x,y:s.y,target:[x,y],local:s.local(s.x,s.y),foot:s.footZ}));return false;}
    previous=distance;
  }
  return false;
}
for(const p of [[327,256],[397,256],[397,288],s.global(-18.75,-10)]){
  harness.assert(await walkTo(...p),'Reach staircase approach '+p.map(v=>v.toFixed(1)).join(','));
}
const bottomZ=s.footZ;
harness.assert(await walkTo(...s.global(-18.75,-25)),'Walk up white staircase to upper landing');
harness.assert(s.footZ>bottomZ+3.7,'Staircase raises the walking camera to 1F');
harness.assert(Math.abs(s.footZ-s.platformZ)<0.15,'Upper landing is level with the first-floor platform');
await harness.takeScreenshot('第一人稱・白色樓梯上方',{width:1440});
harness.assert(await walkTo(...s.global(-18.75,-36)),'Upper landing connects to higher northern flat ground');
harness.assert(Math.abs(s.footZ-s.platformZ)<0.15,'Higher ground is level with platform');
harness.assert(await walkTo(...s.global(-18.75,-25)),'Return from higher ground to landing');
harness.assert(await walkTo(...s.global(-15,-25)),'Step onto the exterior 1F platform');
await aimAt(...s.global(-5,-25));harness.setKeyPressed('w',true);await harness.stepFrames(100);harness.releaseAllInputs();await harness.stepFrames(1);
console.log('Facade stop: '+JSON.stringify({local:s.local(s.x,s.y),foot:s.footZ}));
harness.assert(s.local(s.x,s.y)[0]<-11.9,'Actual model facade stops the first-person camera with clearance');

harness.setKeyPressed('v',true);await harness.stepFrames(1);harness.releaseAllInputs();await harness.stepFrames(1);
harness.assert(s.mode==='god','God-view toggle still works');
const v=s.global(-100,140);
harness.lookAt({from:{x:v[0],y:v[1],z:s.platformZ+145},to:{x:b.centerMeters[0]-15,y:b.centerMeters[1]-5,z:s.platformZ},layer:'Terrain3D'});
await harness.takeScreenshot('上帝視角・湖東建築與地形銜接',{width:1440});
harness.setKeyPressed('b',true);await harness.stepFrames(1);harness.releaseAllInputs();await harness.stepFrames(1);
harness.assert(s.mode==='first'&&Math.hypot(s.x-332,s.y-312)<0.1,'B returns to lakeside building view');
const eastTile=harness.getObjects('Terrain_1_0')[0];
harness.spawn('Terrain_1_0',576,0,eastTile.z,'Terrain3D');await harness.stepFrames(31);
harness.assert(s.bounds.maxX>863,'Adding an eastern tile expands map bounds automatically');
harness.setKeyPressed('v',true);await harness.stepFrames(1);harness.releaseAllInputs();await harness.stepFrames(1);
harness.setKeyPressed('d',true);await harness.stepFrames(300);harness.releaseAllInputs();await harness.stepFrames(1);
harness.assert(s.targetX>576,'God camera can pan beyond the original map boundary');
await harness.goToScene('月明湖地形');await harness.stepFrames(2);
console.log(JSON.stringify({buildingCenter:b.centerMeters,rotation:b.rotationDegrees,basementElevation:s.baseZ+240,firstFloorElevation:s.platformZ+240,stairSteps:b.stairs.steps}));
