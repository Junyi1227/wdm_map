// Portable terrain renderer. TERRAIN_DATA is embedded by build.py.
// Coordinates: X east, Y south, Z elevation above the 240 m datum.
if (!runtimeScene.__yueTerrain) {
  const D = TERRAIN_DATA;
  const T = THREE;
  const clamp = (v,a,b) => Math.max(a,Math.min(b,v));
  const W=D.widthMeters, H=D.depthMeters, C=D.gridColumns, R=D.gridRows;
  const xy = p => [(p[0]-72)/1000*W,(p[1]-72)/852*H];
  const lake = D.lakePixels.map(xy), lakeZ=D.lakeLevelMeters-240;
  const roads=D.roadPixels.map(p=>p.map(xy)), trails=D.trailPixels.map(p=>p.map(xy));
  const B=BUILDING_DATA,br=B.rotationDegrees*Math.PI/180,bc=Math.cos(br),bs=Math.sin(br);
  const baseZ=lakeZ+B.basementFloorAboveLakeMeters,platformZ=baseZ+B.basementHeightMeters;
  const roofZ=platformZ+B.aboveGroundFloors*B.floorHeightMeters;
  const local=(x,y)=>{const dx=x-B.centerMeters[0],dy=y-B.centerMeters[1];return [dx*bc+dy*bs,-dx*bs+dy*bc];};
  const global=(x,y)=>[B.centerMeters[0]+x*bc-y*bs,B.centerMeters[1]+x*bs+y*bc];
  const rectDistance=(x,y,x1,y1,x2,y2)=>Math.hypot(Math.max(x1-x,0,x-x2),Math.max(y1-y,0,y-y2));
  const smooth=t=>{t=clamp(t,0,1);return t*t*(3-2*t);};
  const inside=(x,y,poly)=>{
    let b=false;
    for(let i=0,j=poly.length-1;i<poly.length;j=i++) {
      const a=poly[i],c=poly[j];
      if((a[1]>y)!==(c[1]>y)&&x<(c[0]-a[0])*(y-a[1])/(c[1]-a[1])+a[0]) b=!b;
    }
    return b;
  };
  const segDist=(x,y,a,b)=>{
    const dx=b[0]-a[0],dy=b[1]-a[1];
    const t=clamp(((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy||1),0,1);
    return Math.hypot(x-a[0]-t*dx,y-a[1]-t*dy);
  };
  const pathDist=(x,y,paths)=>{
    let d=1e9;
    for(const p of paths)for(let i=1;i<p.length;i++)d=Math.min(d,segDist(x,y,p[i-1],p[i]));
    return d;
  };
  const rawHeight=(x,y)=>{
    const gx=clamp(x/W*(C-1),0,C-1.001),gy=clamp(y/H*(R-1),0,R-1.001);
    const i=Math.floor(gx),j=Math.floor(gy),u=gx-i,v=gy-j,a=j*C+i;
    return (D.heightMeters[a]*(1-u)*(1-v)+D.heightMeters[a+1]*u*(1-v)+D.heightMeters[a+C]*(1-u)*v+D.heightMeters[a+C+1]*u*v)-240;
  };
  const reconstructedHeight=(x,y)=>{
    let shore=1e9;
    for(let i=0;i<lake.length;i++) shore=Math.min(shore,segDist(x,y,lake[i],lake[(i+1)%lake.length]));
    if(inside(x,y,lake)) return lakeZ-1.5-Math.min(shore*0.25,4);
    const t=clamp(shore/13,0,1),s=t*t*(3-2*t);
    let h=(lakeZ+0.6)*(1-s)+rawHeight(x,y)*s;
    const p=local(x,y),u=p[0],v=p[1];
    // Replace the misread depression by a flat basement apron. Keep the lake intact.
    const basementD=rectDistance(u,v,-22,-29,18,30);
    h=h+(baseZ-h)*(1-smooth(basementD/12));
    // The facade's left/north end joins the existing higher land at 1F level.
    const terraceD=rectDistance(u,v,B.upperTerrace.minX,B.upperTerrace.minY,B.upperTerrace.maxX,B.upperTerrace.maxY);
    const terraceBlend=(1-smooth(terraceD/10))*smooth((-v-23)/6);
    return h+(platformZ-h)*terraceBlend;
  };
  const vertexHeights=[];
  for(let j=0;j<R;j++)for(let i=0;i<C;i++)vertexHeights.push(reconstructedHeight(i/(C-1)*W,j/(R-1)*H));
  const ground=(x,y)=>{
    const gx=clamp(x/W*(C-1),0,C-1.001),gy=clamp(y/H*(R-1),0,R-1.001);
    const i=Math.floor(gx),j=Math.floor(gy),u=gx-i,v=gy-j,a=j*C+i;
    if(u+v<=1)return vertexHeights[a]*(1-u-v)+vertexHeights[a+1]*u+vertexHeights[a+C]*v;
    return vertexHeights[a+C+1]*(u+v-1)+vertexHeights[a+1]*(1-v)+vertexHeights[a+C]*(1-u);
  };
  runtimeScene.addLayer({name:'Terrain3D',renderingType:'3d',cameraType:'perspective',defaultCameraBehavior:'do-nothing',visibility:true,cameras:[],effects:[],ambientLightColorR:255,ambientLightColorG:255,ambientLightColorB:255,camera3DFieldOfView:67,camera3DNearPlaneDistance:0.15,camera3DFarPlaneDistance:4000,isLightingLayer:false,followBaseLayerCamera:false});
  runtimeScene.setLayerIndex('Terrain3D',0);
  const layer=runtimeScene.getLayer('Terrain3D'), renderer=layer.getRenderer();
  const world=new T.Group(); world.name='YueMingLake_Terrain';
  renderer.add3DRendererObject(world);
  const scene=renderer.getThreeScene();
  scene.background=new T.Color('#dce8e7');
  scene.fog=new T.Fog('#dce8e7',650,1500);
  const hemi=new T.HemisphereLight('#fff8df','#78947c',2.0);hemi.position.set(0,0,800);scene.add(hemi);
  const sun=new T.DirectionalLight('#fff0ce',2.4);sun.position.set(-300,-350,650);scene.add(sun);
  const fill=new T.AmbientLight('#ffffff',0.45);scene.add(fill);
  const mesh=(positions,colors,material)=>{
    const g=new T.BufferGeometry();g.setAttribute('position',new T.Float32BufferAttribute(positions,3));
    if(colors)g.setAttribute('color',new T.Float32BufferAttribute(colors,3));
    g.computeVertexNormals();const m=new T.Mesh(g,material);world.add(m);return m;
  };
  const landMat=new T.MeshStandardMaterial({vertexColors:true,flatShading:true,roughness:1,side:T.DoubleSide});
  const positions=[],colors=[];
  let seed=8073;const rand=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
  for(let j=0;j<R-1;j++)for(let i=0;i<C-1;i++) {
    const x=i/(C-1)*W,y=j/(R-1)*H,dx=W/(C-1),dy=H/(R-1);
    const ps=[[x,y],[x+dx,y],[x,y+dy],[x+dx,y+dy]];
    for(const ids of [[0,1,2],[1,3,2]]) {
      const z=ids.reduce((s,k)=>s+ground(...ps[k]),0)/3;
      const c=new T.Color('#79a47d').lerp(new T.Color('#bdc18b'),clamp((z-75)/90,0,1));
      c.multiplyScalar(0.94+rand()*0.1);
      for(const k of ids){positions.push(...ps[k],ground(...ps[k]));colors.push(c.r,c.g,c.b);}
    }
  }
  const terrain=mesh(positions,colors,landMat);terrain.name='ElevationMesh';
  // Cutaway edge gives the landscape a physical, tabletop model silhouette.
  const skirtPos=[],skirtCol=[];const border=[];
  for(let i=0;i<C;i++)border.push([i/(C-1)*W,0]);
  for(let j=1;j<R;j++)border.push([W,j/(R-1)*H]);
  for(let i=C-2;i>=0;i--)border.push([i/(C-1)*W,H]);
  for(let j=R-2;j>0;j--)border.push([0,j/(R-1)*H]);
  for(let i=0;i<border.length;i++) {
    const a=border[i],b=border[(i+1)%border.length],za=ground(...a),zb=ground(...b);
    for(const p of [[...a,za],[...b,zb],[...a,23],[...b,zb],[...b,23],[...a,23]]){
      skirtPos.push(...p);const c=new T.Color(p[2]===23?'#b4a084':'#c6b697');skirtCol.push(c.r,c.g,c.b);
    }
  }
  mesh(skirtPos,skirtCol,landMat).name='EarthCutaway';
  const base=new T.Mesh(new T.BoxGeometry(W+4,H+4,9),new T.MeshStandardMaterial({color:'#bca98c',roughness:1}));
  base.position.set(W/2,H/2,19);world.add(base);
  const shape=new T.Shape();lake.forEach((p,i)=>i?shape.lineTo(...p):shape.moveTo(...p));shape.closePath();
  const water=new T.Mesh(new T.ShapeGeometry(shape),new T.MeshStandardMaterial({color:'#67bfc5',roughness:0.3,metalness:0.08,side:T.DoubleSide}));
  water.position.z=lakeZ;water.name='MoonLake';world.add(water);
  const ripples=new T.Group();world.add(ripples);
  for(let i=0;i<18;i++) {
    const x=347+rand()*28,y=286+rand()*40;
    if(!inside(x,y,lake))continue;
    const z=lakeZ+0.05,pp=[x,y,z,x+2+rand()*4,y+0.2,z];
    const g=new T.BufferGeometry();g.setAttribute('position',new T.Float32BufferAttribute(pp,3));
    const l=new T.Line(g,new T.LineBasicMaterial({color:'#b7e7d9',transparent:true,opacity:0.7}));ripples.add(l);
  }
  // Ribbons follow the same sampled ground as the walking camera.
  const ribbon=(paths,width,color,offset)=>{
    const pp=[];
    for(const path of paths)for(let i=1;i<path.length;i++){
      const a=path[i-1],b=path[i],len=Math.hypot(b[0]-a[0],b[1]-a[1]),n=Math.max(1,Math.ceil(len/0.7));
      const nx=-(b[1]-a[1])/len*width/2,ny=(b[0]-a[0])/len*width/2;
      for(let k=0;k<n;k++){
        const u=k/n,v=(k+1)/n,ax=a[0]+(b[0]-a[0])*u,ay=a[1]+(b[1]-a[1])*u,bx=a[0]+(b[0]-a[0])*v,by=a[1]+(b[1]-a[1])*v;
        const q=[[ax+nx,ay+ny],[bx+nx,by+ny],[ax-nx,ay-ny],[bx-nx,by-ny]];
        for(const t of [0,1,2,1,3,2]) pp.push(...q[t],ground(...q[t])+offset);
      }
    }
    return mesh(pp,null,new T.MeshStandardMaterial({color,roughness:1,side:T.DoubleSide,polygonOffset:true,polygonOffsetFactor:-2,polygonOffsetUnits:-2}));
  };
  const roadsGroup=new T.Group(),trailsGroup=new T.Group();world.add(roadsGroup,trailsGroup);
  for(const [paths,w,color,z,parent] of [[roads,4.8,'#d7d8be',0.55,roadsGroup],[roads,3.5,'#657c79',0.61,roadsGroup],[trails,1.75,'#e7d4a2',0.42,trailsGroup]]){
    const obj=ribbon(paths,w,color,z);world.remove(obj);parent.add(obj);
  }
  // Light shoreline edge, with an east-bank promenade and observation deck.
  ribbon([[...lake,lake[0]]],1.1,'#d9d6ae',0.14);
  const deckX=xy([760,600])[0],deckY=xy([760,600])[1],deckZ=ground(deckX,deckY)+0.3;
  const plankMat=new T.MeshStandardMaterial({color:'#d5af79',roughness:1});
  const deck=new T.Mesh(new T.BoxGeometry(9,18,0.45),plankMat);deck.position.set(deckX-1,deckY,deckZ);world.add(deck);
  for(let i=0;i<15;i++){
    const plank=new T.Mesh(new T.BoxGeometry(9.1,0.08,0.03),new T.MeshBasicMaterial({color:'#a47e53'}));
    plank.position.set(deckX-1,deckY-8.4+i*1.2,deckZ+0.25);world.add(plank);
  }
  const pierA=xy([712,586]),pierB=xy([758,586]);
  const pier=new T.Mesh(new T.BoxGeometry(pierB[0]-pierA[0],1.8,0.4),plankMat);pier.position.set((pierA[0]+pierB[0])/2,pierA[1],lakeZ+0.75);world.add(pier);
  const pavilion=new T.Group();pavilion.position.set(pierA[0],pierA[1],lakeZ+0.7);
  const disk=new T.Mesh(new T.CylinderGeometry(5.1,5.1,0.6,8),plankMat);disk.rotation.x=Math.PI/2;disk.position.z=0.2;pavilion.add(disk);
  for(let i=0;i<4;i++){
    const pole=new T.Mesh(new T.CylinderGeometry(0.15,0.19,3.7,5),new T.MeshStandardMaterial({color:'#886e50'}));
    pole.rotation.x=Math.PI/2;pole.position.set(Math.cos(i*Math.PI/2+Math.PI/4)*3.5,Math.sin(i*Math.PI/2+Math.PI/4)*3.5,2);pavilion.add(pole);
  }
  const roof=new T.Mesh(new T.ConeGeometry(6.3,2.6,8),new T.MeshStandardMaterial({color:'#6c857b',flatShading:true}));roof.rotation.x=Math.PI/2;roof.position.z=5.1;pavilion.add(roof);world.add(pavilion);
  // East-bank hall: three floors over an open, lake-facing basement.
  const building=new T.Group();building.name=B.id;building.position.set(...B.centerMeters,0);building.rotation.z=br;world.add(building);
  const ivory=new T.MeshStandardMaterial({color:'#f1f0df',roughness:0.85});
  const concrete=new T.MeshStandardMaterial({color:'#d2d5c9',roughness:1});
  const shaded=new T.MeshStandardMaterial({color:'#8fa59a',roughness:1});
  const greenGlass=new T.MeshStandardMaterial({color:'#548e82',roughness:0.27,metalness:0.25});
  const darkGlass=new T.MeshStandardMaterial({color:'#335f59',roughness:0.23,metalness:0.2});
  const windowGlow=new T.MeshStandardMaterial({color:'#93b9a0',roughness:0.3,metalness:0.12});
  const teal=new T.MeshStandardMaterial({color:'#58a79b',roughness:0.65,side:T.DoubleSide});
  const roofWhite=new T.MeshStandardMaterial({color:'#e0e3d6',roughness:0.85,side:T.DoubleSide});
  const box=(name,x,y,z,w,d,h,material)=>{const m=new T.Mesh(new T.BoxGeometry(w,d,h),material);m.position.set(x,y,z);m.name=name;building.add(m);return m;};
  const halfL=B.lengthMeters/2,halfW=B.widthMeters/2;
  box('B1-floor',0,0,baseZ-0.07,36,60,0.3,concrete);
  box('B1-rear-retaining-wall',halfW-0.3,0,baseZ+2.1,0.6,52,4.2,concrete);
  box('B1-recessed-back-wall',halfW-2.2,0,baseZ+2,0.3,51,3.7,shaded);
  const columnYs=Array.from({length:9},(_,i)=>-24+i*6);
  for(const [i,y]of columnYs.entries()){
    box('B1-open-column-'+i,-12.9,y,baseZ+2.1,0.9,0.9,4.2,ivory);
    box('B1-inner-column-'+i,3,y,baseZ+2.1,0.7,0.7,4.2,concrete);
  }
  box('1F-platform',0,0,platformZ-0.28,35,58,0.56,ivory);
  box('1F-platform-surface',0,0,platformZ+0.02,35,58,0.04,concrete);
  // Glazing is set back behind the tall white colonnade.
  for(let floor=0;floor<3;floor++){
    const fz=platformZ+floor*B.floorHeightMeters;
    box('Floor-'+(floor+1)+'-slab',1,0,fz+0.12,26,52,0.24,ivory);
    box('Floor-'+(floor+1)+'-rear',halfW-0.5,0,fz+2.1,0.7,52,3.9,ivory);
    for(let bay=0;bay<8;bay++){
      const y=-21+bay*6;
      box('Floor-'+(floor+1)+'-window-'+bay,-11.7,y,fz+2.1,0.24,5.8,3.8,(floor+bay)%3===0?windowGlow:greenGlass);
      for(let m=0;m<3;m++)box('Window-mullion',-11.86,y-2.9+m*1.93,fz+2.1,0.12,0.10,3.8,ivory);
      box('Window-transom',-11.86,y,fz+1.3,0.12,5.8,0.09,ivory);
    }
    for(const end of [-1,1]){
      box('Floor-end-glass',0,end*(halfL-0.12),fz+2.1,23.5,0.25,3.8,greenGlass);
      for(let k=0;k<7;k++)box('End-mullion',-10+k*3.7,end*(halfL+0.03),fz+2.1,0.12,0.12,3.8,ivory);
    }
    box('Lake-facade-floor-band',-11.85,0,fz+4.08,0.3,52,0.2,ivory);
  }
  box('Lake-facing-glass-backplane',-11.6,0,(platformZ+roofZ)/2,0.12,52,roofZ-platformZ-0.25,greenGlass);
  for(const [i,y]of columnYs.entries()){
    box('Tall-white-facade-column-'+i,-14.1,y,(platformZ+roofZ)/2,1.0,0.85,roofZ-platformZ,ivory);
    box('Column-capital-'+i,-14.1,y,roofZ-0.18,1.5,1.4,0.38,ivory);
    box('Column-base-'+i,-14.1,y,platformZ+0.14,1.4,1.3,0.28,ivory);
  }
  box('Main-entrance-doors',-11.96,0,platformZ+1.5,0.2,4.0,3,darkGlass);
  box('Door-center-frame',-12.1,0,platformZ+1.5,0.08,0.08,3,ivory);
  // Gently bowed roof with green eaves and a pale upper surface.
  const roofGeometry=(zOffset)=>{
    const pp=[];
    const rz=x=>roofZ+0.65+1.45*(1-(x/17.4)**2)+0.55*(Math.abs(x)/17.4)**10+zOffset;
    for(let i=0;i<24;i++){
      const a=-17.4+i*34.8/24,b=-17.4+(i+1)*34.8/24;
      for(const p of [[a,-29.5],[b,-29.5],[a,29.5],[b,-29.5],[b,29.5],[a,29.5]])pp.push(...p,rz(p[0]));
    }
    const g=new T.BufferGeometry();g.setAttribute('position',new T.Float32BufferAttribute(pp,3));g.computeVertexNormals();return g;
  };
  const roofUnder=new T.Mesh(roofGeometry(0),teal);roofUnder.name='Curved-green-eaves';building.add(roofUnder);
  const roofTop=new T.Mesh(roofGeometry(0.38),roofWhite);roofTop.name='Pale-curved-roof';building.add(roofTop);
  for(const side of [-1,1])box('Green-eave-fascia',side*17.4,0,roofZ+1.22,0.22,59,0.72,teal);
  // White stairs at the facade's left/north end, rising from the lower lake apron.
  const stair=B.stairs,stairW=stair.maxX-stair.minX,stairRun=stair.bottomY-stair.topY;
  for(let i=0;i<stair.steps;i++){
    const h=(i+1)/stair.steps*B.basementHeightMeters;
    const y=stair.bottomY-(i+0.5)/stair.steps*stairRun;
    box('North-white-stair-'+String(i+1).padStart(2,'0'),(stair.minX+stair.maxX)/2,y,baseZ+h/2,stairW,stairRun/stair.steps+0.02,h,ivory);
  }
  box('North-stair-upper-landing',-17,-26,platformZ-0.18,10,6,0.36,ivory);
  box('North-high-ground-terrace',-2.5,-36,platformZ+0.01,41,14,0.06,new T.MeshStandardMaterial({color:'#b9c898',roughness:1}));
  box('North-high-ground-paved-connection',-17,-32.8,platformZ+0.07,10,7.6,0.08,concrete);
  // Low parapets frame the exterior first-floor balcony, leaving the stairs open.
  box('1F-balcony-front-parapet',-17.1,4,platformZ+0.5,0.25,48,1,ivory);
  box('1F-balcony-south-parapet',0,28.7,platformZ+0.5,34,0.25,1,ivory);
  for(let i=0;i<7;i++){
    const y=stair.bottomY-(i+0.25)/6*stairRun;
    const h=clamp((stair.bottomY-y)/stairRun,0,1)*B.basementHeightMeters;
    box('Stair-railing-post',stair.minX+0.15,y,baseZ+h+0.45,0.15,0.15,0.9,ivory);
  }
  // First-person floor support and collision are independent of decorative geometry.
  const walkHeight=(x,y,currentFoot)=>{
    const p=local(x,y),u=p[0],v=p[1];
    if(u>=stair.minX&&u<=stair.maxX&&v>=stair.topY&&v<=stair.bottomY){
      const step=clamp(Math.ceil((stair.bottomY-v)/stairRun*stair.steps),0,stair.steps);
      return baseZ+step/stair.steps*B.basementHeightMeters;
    }
    if(u>=-22&&u<=-12&&v>=-29&&v<=-23)return platformZ;
    if(u>=-17.5&&u<=17.5&&v>=-29&&v<=29){
      if(currentFoot>=platformZ-0.65)return platformZ+0.04;
      return baseZ+0.08;
    }
    if(u>=-23&&u<=18&&v>=-43&&v<=-29)return platformZ+0.08;
    return ground(x,y);
  };
  const blockedAt=(x,y,foot)=>{
    const p=local(x,y),u=p[0],v=p[1];
    if(v>-26.5&&v<26.5){
      if(foot>platformZ-0.65&&u>-12.3&&u<14.7)return true;
      if(foot<platformZ-0.65&&u>11.3&&u<15)return true;
      for(const cy of columnYs){if(Math.abs(v-cy)<0.85&&(Math.abs(u+12.9)<0.85||(foot<platformZ-0.65&&Math.abs(u-3)<0.75)||(foot>=platformZ-0.65&&Math.abs(u+14.1)<0.9)))return true;}
    }
    if(foot>platformZ-0.65&&Math.abs(u+17.1)<0.5&&v>-20&&v<28.5)return true;
    if(foot>platformZ-0.65&&Math.abs(v-28.7)<0.5&&Math.abs(u)<17)return true;
    return false;
  };
  // Decorative trees are illustrative; their locations are not surveyed.
  const trees=[];
  for(let i=0;i<3200&&trees.length<1150;i++){
    const x=6+rand()*(W-12),y=6+rand()*(H-12);
    const q=local(x,y);
    if((q[0]>-26&&q[0]<23&&q[1]>-47&&q[1]<36)||inside(x,y,lake)||pathDist(x,y,[lake])<6||pathDist(x,y,roads)<5.5||pathDist(x,y,trails)<2.5||Math.hypot(x-deckX,y-deckY)<17)continue;
    trees.push({x,y,z:ground(x,y),h:3+rand()*4.8,s:0.8+rand()*0.7,c:rand()});
  }
  const trunkG=new T.CylinderGeometry(0.2,0.32,1,5);trunkG.rotateX(Math.PI/2);
  const crownG=new T.IcosahedronGeometry(1,0);
  const trunk=new T.InstancedMesh(trunkG,new T.MeshStandardMaterial({color:'#947956'}),trees.length);
  const crown=new T.InstancedMesh(crownG,new T.MeshStandardMaterial({color:'#ffffff',flatShading:true,roughness:1}),trees.length);
  const crown2=new T.InstancedMesh(new T.ConeGeometry(1,2.7,6).rotateX(Math.PI/2),new T.MeshStandardMaterial({color:'#ffffff',flatShading:true,roughness:1}),trees.length);
  const dummy=new T.Object3D();
  trees.forEach((p,i)=>{
    dummy.position.set(p.x,p.y,p.z+p.h*0.27);dummy.scale.set(1,1,p.h*0.54);dummy.rotation.set(0,0,0);dummy.updateMatrix();trunk.setMatrixAt(i,dummy.matrix);
    dummy.position.z=p.z+p.h*0.7;dummy.scale.set(p.s*1.7,p.s*1.6,p.h*0.48);dummy.rotation.z=rand()*6.28;dummy.updateMatrix();crown.setMatrixAt(i,dummy.matrix);
    const col=new T.Color('#4d8469').lerp(new T.Color('#90b879'),p.c);crown.setColorAt(i,col);
    dummy.position.z=p.z+p.h*0.84;dummy.scale.set(p.s*1.4,p.s*1.4,p.h*0.35);dummy.updateMatrix();crown2.setMatrixAt(i,dummy.matrix);crown2.setColorAt(i,col.clone().multiplyScalar(1.07));
  });world.add(trunk,crown,crown2);
  const contours=new T.Group();world.add(contours);
  const lines=[];
  for(let level=60;level<180;level+=10){
    for(let j=0;j<R-1;j++)for(let i=0;i<C-1;i++){
      const q=[[i/(C-1)*W,j/(R-1)*H],[(i+1)/(C-1)*W,j/(R-1)*H],[(i+1)/(C-1)*W,(j+1)/(R-1)*H],[i/(C-1)*W,(j+1)/(R-1)*H]];
      const zz=q.map(p=>ground(...p)),hits=[];
      for(let k=0;k<4;k++){const n=(k+1)%4;if((zz[k]<level)!==(zz[n]<level)){const t=(level-zz[k])/(zz[n]-zz[k]);hits.push([q[k][0]+(q[n][0]-q[k][0])*t,q[k][1]+(q[n][1]-q[k][1])*t,level+0.27]);}}
      if(hits.length>=2)lines.push(...hits[0],...hits[1]);
    }
  }
  const cg=new T.BufferGeometry();cg.setAttribute('position',new T.Float32BufferAttribute(lines,3));
  contours.add(new T.LineSegments(cg,new T.LineBasicMaterial({color:'#365f50',transparent:true,opacity:0.20})));contours.visible=false;
  const player=new T.Mesh(new T.ConeGeometry(2.2,6,6),new T.MeshBasicMaterial({color:'#edaa62'}));player.rotation.x=Math.PI/2;world.add(player);
  // PIXI interface stays inside the exported game and in preview screenshots.
  const hud=new PIXI.Container();runtimeScene.getLayer('').getRenderer().addRendererObject(hud,100000);
  const panel=new PIXI.Graphics();hud.addChild(panel);
  const text=(value,size,color,weight='400')=>{const p=new PIXI.Text(value,{fontFamily:'PingFang TC, Noto Sans TC, Microsoft JhengHei, sans-serif',fontSize:size,fill:color,fontWeight:weight,letterSpacing:0.5});hud.addChild(p);return p;};
  const eyebrow=text('FIELD ATLAS  /  月明洞',11,0x56716a,'600');
  const title=text('月明湖・山林漫遊',27,0x25443a,'600');
  const subtitle=text('湖東主建築 · 地上三層＋開放式地下室',11,0x6b8077);
  const badge=text('第一人稱',12,0x36594c,'600');
  const overviewLabel=text('上帝視角  V',12,0x36594c,'600');
  const resetLabel=text('回到湖畔  R',12,0x36594c,'500');
  const helpTitle=text('沿著湖岸，走進山林',16,0x29483e,'600');
  const help=text('W A S D  移動   ·   Shift  加速\n拖曳滑鼠 / 方向鍵  環顧   ·   V  切換視角\nC  等高線   ·   R  回到湖畔',12,0x587066);
  help.style.lineHeight=23;
  const note=text('近似地形 · 色階推估高程；樹木與涼亭為示意',10,0x587066);
  const miniTitle=text('區域導覽',12,0x36594c,'600');
  const miniLegend=text('道路      步道      月明湖',10,0x587066);
  const altitude=text('',12,0x36594c,'500');
  const credit=text('地圖參考 © OpenStreetMap contributors · SRTM / OpenTopoData',9,0x5a746c);
  const crosshair=new PIXI.Graphics();hud.addChild(crosshair);
  const mapCanvas=document.createElement('canvas');mapCanvas.width=260;mapCanvas.height=221;
  const ctx=mapCanvas.getContext('2d');
  ctx.fillStyle='#afc0a0';ctx.fillRect(0,0,260,221);
  for(let j=0;j<R-1;j++)for(let i=0;i<C-1;i++){
    const h=D.heightMeters[j*C+i],f=clamp((h-300)/100,0,1);
    ctx.fillStyle=`rgb(${Math.round(130+f*50)},${Math.round(167+f*5)},${Math.round(133-f*13)})`;ctx.fillRect(i*260/(C-1),j*221/(R-1),3.6,3.6);
  }
  const miniPath=(paths,color,width)=>{ctx.strokeStyle=color;ctx.lineWidth=width;ctx.lineCap='round';for(const p of paths){ctx.beginPath();p.forEach((q,i)=>i?ctx.lineTo(q[0]/W*260,q[1]/H*221):ctx.moveTo(q[0]/W*260,q[1]/H*221));ctx.stroke();}};
  miniPath(trails,'#eed8a4',0.8);miniPath(roads,'#5a7776',1.8);
  ctx.fillStyle='#79c3c8';ctx.beginPath();lake.forEach((p,i)=>i?ctx.lineTo(p[0]/W*260,p[1]/H*221):ctx.moveTo(p[0]/W*260,p[1]/H*221));ctx.closePath();ctx.fill();
  ctx.fillStyle='#e9eee0';ctx.strokeStyle='#4f8f82';ctx.lineWidth=1;
  ctx.beginPath();B.footprintPixels.map(xy).forEach((p,i)=>i?ctx.lineTo(p[0]/W*260,p[1]/H*221):ctx.moveTo(p[0]/W*260,p[1]/H*221));ctx.closePath();ctx.fill();ctx.stroke();
  const buildingView=[332,312],viewYaw=Math.atan2(B.centerMeters[0]-buildingView[0],-(B.centerMeters[1]-buildingView[1]));
  const mini=new PIXI.Sprite(PIXI.Texture.from(mapCanvas));hud.addChild(mini);
  const locator=new PIXI.Graphics();hud.addChild(locator);
  const S={D,world,terrain,water,trees,layer,renderer,ground,inside,lake,W,H,building,buildingMeta:B,local,global,baseZ,platformZ,roofZ,walkHeight,blockedAt,mode:'first',x:buildingView[0],y:buildingView[1],yaw:viewYaw,pitch:0.04,footZ:ground(...buildingView),orbitYaw:0.35,orbitTilt:0.88,orbitRadius:820,targetX:W/2,targetY:H/2,targetZ:105,contours,player,hud,panel,eyebrow,title,subtitle,badge,overviewLabel,resetLabel,helpTitle,help,note,miniTitle,miniLegend,altitude,credit,crosshair,mini,locator,prevMouse:false,dragged:false,lastMouseX:0,lastMouseY:0,time:0,seed,roadCount:roads.length,trailCount:trails.length};
  S.reset=()=>{S.x=buildingView[0];S.y=buildingView[1];S.yaw=viewYaw;S.pitch=0.04;S.footZ=ground(...buildingView);S.mode='first';};
  S.toggle=()=>{S.mode=S.mode==='first'?'god':'first';};
  runtimeScene.__yueTerrain=S;
}
{
  const S=runtimeScene.__yueTerrain,clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
  const input=runtimeScene.getGame().getInputManager(),key=k=>gdjs.evtTools.input.isKeyPressed(runtimeScene,k),just=k=>gdjs.evtTools.input.wasKeyJustPressed(runtimeScene,k);
  const dt=Math.min(runtimeScene.getElapsedTime()/1000,0.05);S.time+=dt;
  if(just('v')||just('Tab'))S.toggle();if(just('r')||just('b'))S.reset();if(just('c'))S.contours.visible=!S.contours.visible;
  const width=runtimeScene.getGame().getGameResolutionWidth(),height=runtimeScene.getGame().getGameResolutionHeight();
  const uiScale=Math.min(width/1100,height/650,1.25),uw=width/uiScale,uh=height/uiScale;
  S.hud.scale.set(uiScale);
  const mx=input.getMouseX(),my=input.getMouseY(),ux=mx/uiScale,uy=my/uiScale;
  const mouse=input.isMouseButtonPressed(0),newClick=mouse&&!S.prevMouse;
  const overMode=ux>uw-306&&ux<uw-166&&uy>28&&uy<68;
  const overReset=ux>uw-154&&ux<uw-24&&uy>28&&uy<68;
  const overMini=ux>uw-302&&uy>uh-309;
  const overPanel=ux<395&&uy>uh-155;
  const uiHit=overMode||overReset||overMini||overPanel||(ux<360&&uy<130);
  if(newClick&&overMode)S.toggle();if(newClick&&overReset)S.reset();
  if(newClick&&overMini){const nx=(ux-(uw-286))/260,ny=(uy-(uh-272))/221;if(nx>=0&&nx<=1&&ny>=0&&ny<=1){S.targetX=nx*S.W;S.targetY=ny*S.H;S.mode='god';}}
  if(mouse&&S.prevMouse&&!uiHit){
    let dx=mx-S.lastMouseX,dy=my-S.lastMouseY;
    if(S.mode==='first'){S.yaw+=dx*0.004;S.pitch=clamp(S.pitch-dy*0.003,-1.15,1.0);}
    else{S.orbitYaw-=dx*0.006;S.orbitTilt=clamp(S.orbitTilt+dy*0.004,0.2,1.48);}
  }
  S.prevMouse=mouse;S.lastMouseX=mx;S.lastMouseY=my;
  if(S.mode==='first'){
    S.yaw+=((key('Right')?1:0)-(key('Left')?1:0))*dt*1.4;
    S.pitch=clamp(S.pitch+((key('Up')?1:0)-(key('Down')?1:0))*dt,-1.15,1.0);
    const f=(key('w')?1:0)-(key('s')?1:0),r=(key('d')?1:0)-(key('a')?1:0),speed=(key('LShift')?22:8)*dt/Math.max(1,Math.hypot(f,r));
    const nx=clamp(S.x+(Math.sin(S.yaw)*f+Math.cos(S.yaw)*r)*speed,3,S.W-3),ny=clamp(S.y+(-Math.cos(S.yaw)*f+Math.sin(S.yaw)*r)*speed,3,S.H-3);
    if(!S.inside(nx,ny,S.lake)&&!S.blockedAt(nx,ny,S.footZ)){S.x=nx;S.y=ny;}
    S.footZ=S.walkHeight(S.x,S.y,S.footZ);
    const z=S.footZ+1.85;
    S.layer.setCameraX(S.x);S.layer.setCameraY(S.y);S.layer.setCameraZ(z,67);
    S.layer.setCameraRotation(S.yaw*180/Math.PI);S.layer.setCameraRotationX(90+S.pitch*180/Math.PI);S.layer.setCameraRotationY(0);
  }else{
    S.orbitYaw+=((key('Right')?1:0)-(key('Left')?1:0))*dt*0.7;
    S.orbitTilt=clamp(S.orbitTilt+((key('Up')?1:0)-(key('Down')?1:0))*dt*0.6,0.2,1.48);
    const speed=dt*90;S.targetX=clamp(S.targetX+((key('d')?1:0)-(key('a')?1:0))*speed,0,S.W);S.targetY=clamp(S.targetY+((key('s')?1:0)-(key('w')?1:0))*speed,0,S.H);
    const wheel=input.getMouseWheelDelta();
    if(wheel)S.orbitRadius=clamp(S.orbitRadius*Math.exp(-wheel*0.001),100,1300);
    if(key('q'))S.orbitRadius=clamp(S.orbitRadius+dt*190,100,1300);if(key('e'))S.orbitRadius=clamp(S.orbitRadius-dt*190,100,1300);
    const h=Math.cos(S.orbitTilt)*S.orbitRadius;
    S.layer.setCameraX(S.targetX+Math.sin(S.orbitYaw)*h);S.layer.setCameraY(S.targetY+Math.cos(S.orbitYaw)*h);S.layer.setCameraZ(S.targetZ+Math.sin(S.orbitTilt)*S.orbitRadius,67);
    S.layer.setCameraRotation(-S.orbitYaw*180/Math.PI);S.layer.setCameraRotationX(90-S.orbitTilt*180/Math.PI);S.layer.setCameraRotationY(0);
  }
  S.player.visible=S.mode==='god';S.player.position.set(S.x,S.y,S.footZ+4);
  // Interface layout adapts to the preview window without obscuring the lake.
  const p=S.panel;p.clear();
  const box=(x,y,w,h,c,a=0.94)=>{p.beginFill(c,a);p.drawRoundedRect(x,y,w,h,14);p.endFill();};
  box(24,24,330,104,0xf8faf1);box(uw-306,28,140,40,0xf8faf1);box(uw-154,28,130,40,0xf8faf1);
  box(24,uh-155,370,125,0xf8faf1);box(uw-302,uh-309,278,279,0xf8faf1);
  p.beginFill(0x74a88b);p.drawCircle(41,43,3);p.endFill();
  S.eyebrow.position.set(52,36);S.title.position.set(40,57);S.subtitle.position.set(41,100);
  S.overviewLabel.position.set(uw-286,40);S.overviewLabel.text=S.mode==='first'?'上帝視角  V':'第一人稱  V';S.resetLabel.position.set(uw-136,40);
  S.helpTitle.position.set(41,uh-138);S.help.position.set(41,uh-108);
  if(S.mode==='first'){S.helpTitle.text='沿著湖岸，走進山林';S.help.text='W A S D  移動   ·   Shift  加速\n拖曳滑鼠 / 方向鍵  環顧   ·   V  切換視角\nB  建築導覽   ·   C  等高線   ·   R  湖畔';}
  else{S.helpTitle.text='俯瞰山脊與湖泊';S.help.text='拖曳滑鼠  環繞   ·   滾輪 / Q E  縮放\nW A S D  平移   ·   點導覽圖  移動中心\nC  等高線   ·   V  返回第一人稱';}
  S.note.visible=false;S.miniTitle.position.set(uw-286,uh-295);S.miniLegend.position.set(uw-286,uh-43);
  S.mini.position.set(uw-293,uh-272);S.mini.width=260;S.mini.height=221;
  S.altitude.text=(S.mode==='first'?'步行視角':'上帝視角')+'   /   '+Math.round(S.footZ+240)+' m';S.altitude.position.set(uw-274,82);
  S.credit.position.set(24,uh-6);S.credit.anchor.set(0,1);
  S.badge.visible=false;
  const l=S.locator;l.clear();const lx=uw-293+S.x/S.W*260,ly=uh-272+S.y/S.H*221;
  l.lineStyle(2,0xf8faf1);l.beginFill(0xeaa466);l.drawCircle(lx,ly,4);l.endFill();
  l.lineStyle(2,0xffedbf);l.moveTo(lx,ly);l.lineTo(lx+Math.sin(S.yaw)*11,ly-Math.cos(S.yaw)*11);
  l.lineStyle(1,0x345e51);l.moveTo(uw-47,uh-257);l.lineTo(uw-47,uh-241);l.moveTo(uw-51,uh-251);l.lineTo(uw-47,uh-257);l.lineTo(uw-43,uh-251);
  const cross=S.crosshair;cross.clear();cross.visible=S.mode==='first';cross.lineStyle(1,0xffffff,0.75);cross.drawCircle(uw/2,uh/2,3);cross.moveTo(uw/2-8,uh/2);cross.lineTo(uw/2-4,uh/2);cross.moveTo(uw/2+4,uh/2);cross.lineTo(uw/2+8,uh/2);
}
