"""Build a self-contained detailed core from saved DEM and OSM geometry.

No project/editor writes. Widths, colors and surface offsets are illustrative.
The original research NW origin and metre coordinates are preserved.
"""
from pathlib import Path
import json
import math
import struct
from functools import lru_cache
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'source-data'
if (SOURCE/'trail-adjustments.json').exists():
    raise RuntimeError('Authored trail and terrain grading exists; do not overwrite it with the original DEM builder. See source-data/trail-adjustments.json.')
OUT = ROOT/'wolmyeongdong/assets/core'
OUT.mkdir(parents=True, exist_ok=True)
global_meta = json.loads((OUT.parent/'geography.json').read_text())
GW, GS, GE, GN = global_meta['bbox_wsen']
CW, CS, CE, CN = 127.3648, 36.1220, 127.3718, 36.1275
MX = global_meta['width_m']/(GE-GW)
MY = global_meta['height_m']/(GN-GS)
X0, Y0 = (CW-GW)*MX, (GN-CN)*MY
WIDTH, HEIGHT = (CE-CW)*MX, (CN-CS)*MY
base = Image.open(OUT.parent/'heightmap-rg16.png')

def xy(lon,lat):
    return (lon-GW)*MX, (GN-lat)*MY

def original(x,y):
    u=max(0,min(512,x/global_meta['width_m']*512))
    v=max(0,min(512,y/global_meta['height_m']*512))
    i,j=min(511,int(u)),min(511,int(v));a,b=u-i,v-j
    def pixel(c,r):
        red,green,_=base.getpixel((c,r))
        return (red*256+green)/65535*600
    return pixel(i,j)*(1-a)*(1-b)+pixel(i+1,j)*a*(1-b)+pixel(i,j+1)*(1-a)*b+pixel(i+1,j+1)*a*b

pixels=[]
for row in range(513):
    for col in range(513):
        q=round(original(X0+col/512*WIDTH,Y0+row/512*HEIGHT)/600*65535)
        pixels.append((q>>8,q&255,0))
image=Image.new('RGB',(513,513));image.putdata(pixels);image.save(OUT/'heightmap-rg16.png')

@lru_cache(maxsize=1100000)
def grid_height(i,j):
    # Native terrain bilinearly decodes the 513 image into 1024 cells.
    u=max(0,min(512,i/2));v=max(0,min(512,j/2))
    c,r=min(511,int(u)),min(511,int(v));a,b=u-c,v-r
    def z(c,r):
        red,green,_=image.getpixel((c,r));return (red*256+green)/65535*600
    return z(c,r)*(1-a)*(1-b)+z(c+1,r)*a*(1-b)+z(c,r+1)*(1-a)*b+z(c+1,r+1)*a*b

def ground(x,y):
    u=max(0,min(1024,(x-X0)/WIDTH*1024));v=max(0,min(1024,(y-Y0)/HEIGHT*1024))
    i,j=min(1023,int(u)),min(1023,int(v));a,b=u-i,v-j
    tl,tr,bl,br=grid_height(i,j),grid_height(i+1,j),grid_height(i,j+1),grid_height(i+1,j+1)
    return tl+a*(tr-tl)+b*(bl-tl) if a+b<=1 else br+(1-a)*(bl-br)+(1-b)*(tr-br)

def write_glb(name,points,color):
    vertices=[v for p in points for v in p]
    mins=[min(vertices[i::3]) for i in range(3)];maxs=[max(vertices[i::3]) for i in range(3)]
    local=[value-mins[i%3] for i,value in enumerate(vertices)]
    sizes=[maxs[i]-mins[i] for i in range(3)]
    binary=struct.pack('<'+'f'*len(local),*local)
    doc={'asset':{'version':'2.0','generator':'Wolmyeongdong core / saved OSM geometry'},'scene':0,
         'scenes':[{'nodes':[0]}],'nodes':[{'mesh':0}],
         'meshes':[{'primitives':[{'attributes':{'POSITION':0},'material':0}]}],
         'materials':[{'doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':color,'metallicFactor':0,'roughnessFactor':1},'extensions':{'KHR_materials_unlit':{}}}],
         'extensionsUsed':['KHR_materials_unlit'],'extensionsRequired':['KHR_materials_unlit'],
         'buffers':[{'byteLength':len(binary)}],
         'bufferViews':[{'buffer':0,'byteLength':len(binary),'target':34962}],
         'accessors':[{'bufferView':0,'componentType':5126,'count':len(local)//3,'type':'VEC3','min':[0,0,0],'max':sizes}]}
    kind='grass' if name=='lawn' else 'trail' if name in ('sportsground','trails') else 'road' if name=='roads' else None
    if kind:
        uv=[v for point in points for v in (point[0]/8,point[2]/8)]
        uv_bytes=struct.pack('<'+'f'*len(uv),*uv)
        doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(uv_bytes),'target':34962})
        doc['accessors'].append({'bufferView':1,'componentType':5126,'count':len(points),'type':'VEC2'})
        doc['meshes'][0]['primitives'][0]['attributes']['TEXCOORD_0']=1
        binary+=uv_bytes
        png=(OUT.parent/(kind+'-detail.png')).read_bytes()
        doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(png)})
        doc['images']=[{'bufferView':2,'mimeType':'image/png'}]
        doc['samplers']=[{'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497}]
        doc['textures']=[{'sampler':0,'source':0}]
        doc['materials'][0]['pbrMetallicRoughness']['baseColorTexture']={'index':0}
        binary+=png
        doc['buffers'][0]['byteLength']=len(binary)
    text=json.dumps(doc,separators=(',',':')).encode();text+=b' '*((-len(text))%4);binary+=b'\0'*((-len(binary))%4)
    (OUT/(name+'.glb')).write_bytes(struct.pack('<III',0x46546c67,2,28+len(text)+len(binary))+struct.pack('<II',len(text),0x4e4f534a)+text+struct.pack('<II',len(binary),0x004e4942)+binary)
    return {'resource':'core-'+name+'.glb','file':'assets/core/'+name+'.glb',
            'position':[mins[0],mins[2],mins[1]],'size':[sizes[0],sizes[2],sizes[1]],'vertices':len(local)//3}

def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def inside_triangle(p,a,b,c):return min(cross(a,b,p),cross(b,c,p),cross(c,a,p))>=-1e-8

def polygon_triangles(poly):
    if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1]))<0:poly=list(reversed(poly))
    remaining=list(range(len(poly)));result=[]
    while len(remaining)>3:
        for i,b in enumerate(remaining):
            a,c=remaining[i-1],remaining[(i+1)%len(remaining)]
            if cross(poly[a],poly[b],poly[c])<=1e-8:continue
            if any(inside_triangle(poly[j],poly[a],poly[b],poly[c]) for j in remaining if j not in (a,b,c)):continue
            result.append([poly[a],poly[b],poly[c]]);remaining.pop(i);break
        else:raise ValueError('Invalid source polygon')
    result.append([poly[i] for i in remaining]);return result

def refined(tri,output):
    a,b,c=tri
    if max(math.dist(a,b),math.dist(b,c),math.dist(c,a))<=2:
        output.extend([[x,ground(x,y)+.18,y] for x,y in tri]);return
    lengths=[math.dist(a,b),math.dist(b,c),math.dist(c,a)]
    if lengths[1]==max(lengths):a,b,c=b,c,a
    elif lengths[2]==max(lengths):a,b,c=c,a,b
    mid=[(a[i]+b[i])/2 for i in range(2)]
    for child in ([a,mid,c],[mid,b,c]):refined(child,output)

def clip(a,b):
    dx,dy=b[0]-a[0],b[1]-a[1];lo,hi=0,1
    for p,q in [(-dx,a[0]-X0),(dx,X0+WIDTH-a[0]),(-dy,a[1]-Y0),(dy,Y0+HEIGHT-a[1])]:
        if abs(p)<1e-12:
            if q<0:return None
            continue
        t=q/p
        if p<0:lo=max(lo,t)
        else:hi=min(hi,t)
        if lo>hi:return None
    return [[a[0]+lo*dx,a[1]+lo*dy],[a[0]+hi*dx,a[1]+hi*dy]]

roads={'RoadDetail':[],'TrailDetail':[]};edits=[];widths=[]
for feature in json.loads((SOURCE/'roads.geojson').read_text())['features']:
    highway=feature['properties']['highway'];walking=highway in ('footway','path','steps')
    width=1.2 if walking else (2.8 if highway in ('service','track') else 3.5)
    used=False
    for line in feature['geometry']['coordinates']:
        points=[xy(*p) for p in line]
        for a,b in zip(points,points[1:]):
            segment=clip(a,b)
            if not segment:continue
            a,b=segment;distance=math.dist(a,b)
            if distance<.01:continue
            used=True;dx,dy=(b[0]-a[0])/distance,(b[1]-a[1])/distance
            count=max(1,math.ceil(distance/1.2));across=max(1,math.ceil(width))
            rows=[]
            for j in range(count+1):
                x=a[0]+j/count*(b[0]-a[0]);y=a[1]+j/count*(b[1]-a[1]);row=[]
                for k in range(across+1):
                    offset=(k/across-.5)*width
                    px=max(X0,min(X0+WIDTH,x-dy*offset));py=max(Y0,min(Y0+HEIGHT,y+dx*offset))
                    row.append([px,ground(px,py)+.24,py])
                rows.append(row)
            out=roads['TrailDetail' if walking else 'RoadDetail']
            for r1,r2 in zip(rows,rows[1:]):
                for k in range(across):out.extend([r1[k],r2[k],r1[k+1],r1[k+1],r2[k],r2[k+1]])
            edits.append({'tool':'paint','x':(a[0]-X0)/WIDTH,'y':(a[1]-Y0)/HEIGHT,'toX':(b[0]-X0)/WIDTH,'toY':(b[1]-Y0)/HEIGHT,'radius':width/2/min(WIDTH,HEIGHT),'layer':4 if walking else 3,'strength':.08})
    if used:widths.append({'id':feature['properties'].get('id'),'highway':highway,'display_width_m':width,'measured':False})

models={key:write_glb('roads' if key=='RoadDetail' else 'trails',verts,[.70,.73,.71,1] if key=='RoadDetail' else [.64,.49,.32,1]) for key,verts in roads.items()}
context=json.loads((SOURCE/'context.geojson').read_text())['features'];sites=[]
for osm_id,key,label,color in [('OSM-313214725','MoonLake','月明湖',[.12,.57,.76,1]),('OSM-354325010','SportsGround','運動場',[.79,.71,.56,1]),('OSM-354325014','Lawn','草坪',[.37,.65,.22,1])]:
    f=next(f for f in context if f['properties']['id']==osm_id)
    poly=[xy(*p) for p in f['geometry']['coordinates'][0][:-1]];verts=[]
    for tri in polygon_triangles(poly):refined(tri,verts)
    models[key]=write_glb(key.lower(),verts,color)
    bounds=[min(p[0] for p in poly),min(p[1] for p in poly),max(p[0] for p in poly),max(p[1] for p in poly)]
    center=[sum(p[0] for p in poly)/len(poly),sum(p[1] for p in poly)/len(poly)]
    sites.append({'object':key,'label':label,'source_id':osm_id,'source_url':f['properties']['source_url'],'focus_xy':center,'world_bbox':bounds,'polygon_xy':poly,'name_status':'generic label; 陽光草皮 alias remains unconfirmed' if key=='Lawn' else 'OSM name'})
    if key=='SportsGround':
        # Light editable paint under the exact-edged polygon display.
        y=bounds[1]+.3
        while y<bounds[3]:
            intersections=[]
            for a,b in zip(poly,poly[1:]+poly[:1]):
                if (a[1]>y)!=(b[1]>y):intersections.append(a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1]))
            intersections.sort()
            for a,b in zip(intersections[::2],intersections[1::2]):edits.append({'tool':'paint','x':(a-X0)/WIDTH,'y':(y-Y0)/HEIGHT,'toX':(b-X0)/WIDTH,'toY':(y-Y0)/HEIGHT,'radius':.6/min(WIDTH,HEIGHT),'layer':4,'strength':.65})
            y+=.6

metadata={'bbox_wsen':[CW,CS,CE,CN],'global_origin_lon_lat':[GW,GN],'terrain_position':[X0,Y0,0],
          'width_m':WIDTH,'height_m':HEIGHT,'native_resolution':1024,'heightmap_size':513,'datum_m':150,'height_span_m':600,
          'models':models,'sites':sites,'road_widths':widths,'paint_edits':len(edits),
          'notice':'Core crop of saved interpolated DEM; no added survey accuracy. Fixed metre widths are illustrative, independent of scene extent. Field ground follows DEM; no invented grading or court markings.'}
(OUT/'geography.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
(OUT/'road-edits.json').write_text(json.dumps(edits,separators=(',',':')))
(SOURCE/'core-area.json').write_text(json.dumps({k:metadata[k] for k in ['bbox_wsen','global_origin_lon_lat','terrain_position','width_m','height_m','notice']},ensure_ascii=False,indent=2))
(SOURCE/'core-sites.geojson').write_text(json.dumps({'type':'FeatureCollection','features':[dict(f,properties=dict(f['properties'],display_label=('運動場' if f['properties']['id']=='OSM-354325010' else '草坪'),boundary_status='public OSM contour; not a survey')) for f in context if f['properties']['id'] in ['OSM-354325010','OSM-354325014']]},ensure_ascii=False,indent=2))
print(json.dumps({'extent_m':[WIDTH,HEIGHT],'models':{k:v['vertices'] for k,v in models.items()},'paint_edits':len(edits),'road_features':len(widths)},indent=2))
