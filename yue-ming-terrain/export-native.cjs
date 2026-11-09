// Bake the existing procedural reference into independent, standard GLB assets.
const fs=require('fs'),path=require('path');
const THREE=require('/Applications/GDevelop 5.app/Contents/Resources/GDJS/Runtime/pixi-renderers/three.js');
const ROOT=__dirname,OUT=path.join(ROOT,'native-assets');fs.mkdirSync(OUT,{recursive:true});
const data=JSON.parse(fs.readFileSync(path.join(ROOT,'terrain-data.json')));
const buildingData=JSON.parse(fs.readFileSync(path.join(ROOT,'building-data.json')));
let src=fs.readFileSync(path.join(ROOT,'terrain-runtime.js'),'utf8');
src=src.slice(src.indexOf('if (!runtimeScene.__yueTerrain) {')+'if (!runtimeScene.__yueTerrain) {'.length,src.indexOf('// PIXI interface'));
src=src.replace('TERRAIN_DATA',JSON.stringify(data)).replace('BUILDING_DATA',JSON.stringify(buildingData));
src=src.replace("ribbon([[...lake,lake[0]]],1.1,'#d9d6ae',0.14);","const shoreModel=ribbon([[...lake,lake[0]]],1.1,'#d9d6ae',0.14);");
src=src.replace('plank.position.set(deckX-1,','plank.name="BoardwalkPlank";plank.position.set(deckX-1,');
const scene=new THREE.Scene(),render={add3DRendererObject:o=>scene.add(o),getThreeScene:()=>scene};
const runtimeScene={addLayer:()=>{},setLayerIndex:()=>{},getLayer:()=>({getRenderer:()=>render})};
const S=new Function('THREE','runtimeScene',src+';return {world,terrain,water,shoreModel,building,base,pavilion,pier,deck,roads,trails,ribbon,trees,trunkG,crownG,ground,local,global,baseZ,platformZ,roofZ,player,contours,skirtPos,skirtCol};')(THREE,runtimeScene);
S.world.updateMatrixWorld(true);
const manifest={version:2,units:'meters',axes:{x:'east',y:'south',z:'up'},datumElevationMeters:240,sourceBounds:data.bounds,currentBounds:{minX:0,minY:0,maxX:data.widthMeters,maxY:data.depthMeters},tileSizeMeters:[288,245],assets:[],instances:[],walkableNames:[],solidNames:[]};
// Only positions, normals, vertex colors and PBR materials: no runtime dependencies.
function bakeMeshes(objects){
 const groups=new Map(),allBounds=new THREE.Box3();
 for(const root of objects){root.updateWorldMatrix(true,true);root.traverse(m=>{
  if(!m.isMesh||m.isInstancedMesh)return;
  const geo=m.geometry.index?m.geometry.toNonIndexed():m.geometry;
  const pos=geo.attributes.position,norm=geo.attributes.normal,col=geo.attributes.color;
  const mat=Array.isArray(m.material)?m.material[0]:m.material;
  const key=[mat.color?.getHex(),mat.roughness??1,mat.metalness??0,!!col].join(':');
  if(!groups.has(key))groups.set(key,{p:[],n:[],c:[],material:mat});
  const g=groups.get(key),v=new THREE.Vector3(),n=new THREE.Vector3(),nm=new THREE.Matrix3().getNormalMatrix(m.matrixWorld);
  for(let i=0;i<pos.count;i++){
   v.fromBufferAttribute(pos,i).applyMatrix4(m.matrixWorld);allBounds.expandByPoint(v);g.p.push(v.x,v.y,v.z);
   if(norm)n.fromBufferAttribute(norm,i).applyMatrix3(nm).normalize();else n.set(0,0,1);
   g.n.push(n.x,n.y,n.z);
   if(col)g.c.push(col.getX(i),col.getY(i),col.getZ(i));
  }
 });}
 return {groups:[...groups.values()],bounds:allBounds};
}
function writeAsset(name,objects,opts={}){
 const baked=bakeMeshes(objects),bounds=baked.bounds;
 if(bounds.isEmpty())throw new Error('No geometry: '+name);
 const anchor=bounds.min.clone(),size=bounds.getSize(new THREE.Vector3());
 const doc={asset:{version:'2.0',generator:'YueMing editable map baker'},scene:0,scenes:[{nodes:[0]}],nodes:[{mesh:0,name}],meshes:[{name,primitives:[]}],materials:[],buffers:[{byteLength:0}],bufferViews:[],accessors:[]};
 const chunks=[];let bytes=0;
 function attr(values,type,min,max){
  const arr=Float32Array.from(values),buf=Buffer.from(arr.buffer),view=doc.bufferViews.length;
  doc.bufferViews.push({buffer:0,byteOffset:bytes,byteLength:buf.length,target:34962});chunks.push(buf);bytes+=buf.length;
  const a={bufferView:view,componentType:5126,count:arr.length/(type==='VEC3'?3:4),type};if(min)a.min=min;if(max)a.max=max;
  doc.accessors.push(a);return doc.accessors.length-1;
 }
 for(const g of baked.groups){
  const pp=[],nn=[],colors=[],bb=new THREE.Box3(),v=new THREE.Vector3();
  for(let vertex=0;vertex<g.p.length/3;vertex++){
   const i=(Math.floor(vertex/3)*3+[0,2,1][vertex%3])*3;
   // GDevelop rotates +90 on X, then flips model Y: encode map-south as glTF +Z.
   v.set(g.p[i]-anchor.x,g.p[i+2]-anchor.z,g.p[i+1]-anchor.y);bb.expandByPoint(v);pp.push(v.x,v.y,v.z);
   nn.push(g.n[i],g.n[i+2],g.n[i+1]);if(g.c.length)colors.push(g.c[i],g.c[i+1],g.c[i+2]);
  }
  const mat=g.material,c=g.c.length?new THREE.Color('white'):mat.color??new THREE.Color('white');
  const mi=doc.materials.length;doc.materials.push({name:name+'-material-'+mi,pbrMetallicRoughness:{baseColorFactor:[c.r,c.g,c.b,1],metallicFactor:mat.metalness??0,roughnessFactor:mat.roughness??1},doubleSided:true});
  const attributes={POSITION:attr(pp,'VEC3',bb.min.toArray(),bb.max.toArray()),NORMAL:attr(nn,'VEC3')};
  if(g.c.length)attributes.COLOR_0=attr(colors,'VEC3');
  doc.meshes[0].primitives.push({attributes,material:mi,mode:4});
 }
 doc.buffers[0].byteLength=bytes;
 let json=Buffer.from(JSON.stringify(doc));json=Buffer.concat([json,Buffer.alloc((4-json.length%4)%4,32)]);
 let bin=Buffer.concat(chunks);bin=Buffer.concat([bin,Buffer.alloc((4-bin.length%4)%4)]);
 const head=Buffer.alloc(12);head.writeUInt32LE(0x46546c67,0);head.writeUInt32LE(2,4);head.writeUInt32LE(12+8+json.length+8+bin.length,8);
 const jh=Buffer.alloc(8);jh.writeUInt32LE(json.length,0);jh.writeUInt32LE(0x4e4f534a,4);
 const bh=Buffer.alloc(8);bh.writeUInt32LE(bin.length,0);bh.writeUInt32LE(0x004e4942,4);
 const file=name+'.glb';fs.writeFileSync(path.join(OUT,file),Buffer.concat([head,jh,json,bh,bin]));
 const asset={name,file:'native-assets/'+file,size:[size.x,size.y,Math.max(size.z,0.001)],anchor:anchor.toArray(),...opts};manifest.assets.push(asset);
 if(!opts.template)manifest.instances.push({name,x:anchor.x,y:anchor.y,z:anchor.z,width:size.x,height:size.y,depth:Math.max(size.z,0.001),angle:0});
 if(opts.walkable)manifest.walkableNames.push(name);if(opts.solid)manifest.solidNames.push(name);
 return asset;
}
// Four seam-matched terrain tiles; coordinates are permanent when expanding the map.
const pa=S.terrain.geometry.attributes.position,ca=S.terrain.geometry.attributes.color;
for(let row=0;row<2;row++)for(let column=0;column<2;column++){
 const pp=[],cc=[];
 for(let i=0;i<pa.count;i+=3){
  const cx=(pa.getX(i)+pa.getX(i+1)+pa.getX(i+2))/3,cy=(pa.getY(i)+pa.getY(i+1)+pa.getY(i+2))/3;
  if(Math.min(1,Math.floor(cx/288))!==column||Math.min(1,Math.floor(cy/245))!==row)continue;
  for(let k=0;k<3;k++){pp.push(pa.getX(i+k),pa.getY(i+k),pa.getZ(i+k));cc.push(ca.getX(i+k),ca.getY(i+k),ca.getZ(i+k));}
 }
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(pp,3));g.setAttribute('color',new THREE.Float32BufferAttribute(cc,3));g.computeVertexNormals();
 writeAsset(`Terrain_${column}_${row}`,[new THREE.Mesh(g,S.terrain.material)],{walkable:true,tile:[column,row],category:'Terrain'});
}
writeAsset('Terrain_Cutaway',[S.world.getObjectByName('EarthCutaway'),S.base],{category:'Terrain'});
writeAsset('MoonLake',[S.water],{category:'Water'});writeAsset('Lake_Shore',[S.shoreModel],{category:'Water'});
S.roads.forEach((road,i)=>{const curb=S.ribbon([road],4.8,'#d7d8be',0.55),surface=S.ribbon([road],3.5,'#657c79',0.64);writeAsset('Road_'+String(i+1).padStart(2,'0'),[curb,surface],{walkable:true,category:'Roads'});});
S.trails.forEach((trail,i)=>writeAsset('Trail_'+String(i+1).padStart(2,'0'),[S.ribbon([trail],1.75,'#e7d4a2',0.42)],{walkable:true,category:'Trails'}));
writeAsset('Lake_Boardwalk',[S.deck,...S.world.children.filter(o=>o.name==='BoardwalkPlank')],{walkable:true,category:'Lakeside'});
writeAsset('Lake_Pier',[S.pier],{walkable:true,category:'Lakeside'});writeAsset('Lake_Pavilion',[S.pavilion],{solid:true,category:'Lakeside'});
const bp={Main:[],Basement:[],Platform:[],Stairs:[],Terrace:[]};
for(const m of S.building.children){
 const n=m.name;
 if(n.startsWith('B1-'))bp.Basement.push(m);
 else if(n.startsWith('North-white-stair-')||n.startsWith('North-stair-upper-')||n.startsWith('Stair-railing-'))bp.Stairs.push(m);
 else if(n.startsWith('North-high-ground-'))bp.Terrace.push(m);
 else if(n.startsWith('1F-'))bp.Platform.push(m);
 else bp.Main.push(m);
}
for(const [key,objects]of Object.entries(bp))writeAsset('Hall_'+key,objects,{walkable:key!=='Main',solid:['Main','Basement'].includes(key),category:'Hall'});
// Three reusable tree models, with every tree remaining an individually editable instance.
for(let variant=0;variant<3;variant++){
 const group=new THREE.Group(),height=6;
 const trunk=new THREE.Mesh(S.trunkG,new THREE.MeshStandardMaterial({color:'#947956'}));trunk.position.z=height*0.27;trunk.scale.z=height*0.54;group.add(trunk);
 const color=new THREE.Color('#4d8469').lerp(new THREE.Color('#90b879'),variant/2);
 const crown=new THREE.Mesh(S.crownG,new THREE.MeshStandardMaterial({color,flatShading:true}));crown.position.z=height*0.7;crown.scale.set(1.7,1.6,height*0.48);group.add(crown);
 const tip=new THREE.Mesh(new THREE.ConeGeometry(1,2.7,6).rotateX(Math.PI/2),new THREE.MeshStandardMaterial({color:color.clone().multiplyScalar(1.07),flatShading:true}));tip.position.z=height*0.84;tip.scale.set(1.4,1.4,height*0.35);group.add(tip);
 writeAsset('Tree_'+(variant+1),[group],{template:true,category:'Trees'});
}
S.trees.forEach((tree,i)=>{
 const asset=manifest.assets.find(a=>a.name==='Tree_'+(Math.floor(tree.c*3)+1));
 const sx=tree.s,sz=tree.h/6;
 manifest.instances.push({name:asset.name,x:tree.x+asset.anchor[0]*sx,y:tree.y+asset.anchor[1]*sx,z:tree.z+asset.anchor[2]*sz,width:asset.size[0]*sx,height:asset.size[1]*sx,depth:asset.size[2]*sz,angle:0});
});
fs.writeFileSync(path.join(ROOT,'native-manifest.json'),JSON.stringify(manifest,null,2));
fs.writeFileSync(path.join(ROOT,'contour-data.json'),JSON.stringify(Array.from(S.contours.children[0].geometry.attributes.position.array)));
console.log(JSON.stringify({assets:manifest.assets.length,instances:manifest.instances.length,bytes:manifest.assets.reduce((s,a)=>s+fs.statSync(path.join(ROOT,a.file)).size,0)}));
