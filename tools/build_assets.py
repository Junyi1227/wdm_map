"""Build initial geographic assets. Never rewrites the editable GDevelop project."""
from pathlib import Path
import json
import math
import struct
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'source-data'
OUT = ROOT / 'wolmyeongdong/assets'
OUT.mkdir(parents=True, exist_ok=True)
outer = json.loads((SOURCE/'elevation-dense.json').read_text())
core = json.loads((SOURCE/'elevation-core.json').read_text())
W,S,E,N = outer['metadata']['bbox_wsen']
CW,CS,CE,CN = core['metadata']['bbox_wsen']
MX = math.pi/180*6371008.8*math.cos(math.radians((S+N)/2))
MY = math.pi/180*6371008.8
WIDTH,HEIGHT = (E-W)*MX,(N-S)*MY
DATUM,SPAN,SIZE = 150,600,513

def sample(data,lon,lat):
    m=data['metadata'];w,s,_,_=m['bbox_wsen'];cols,rows=m['columns'],m['rows'];step=m['step_degrees']
    fx=max(0,min(cols-1,(lon-w)/step));fy=max(0,min(rows-1,(lat-s)/step))
    c,r=min(cols-2,int(fx)),min(rows-2,int(fy));a,b=fx-c,fy-r
    def v(j,i): return data['results'][j*cols+i]['elevation']
    return v(r,c)*(1-a)*(1-b)+v(r,c+1)*a*(1-b)+v(r+1,c)*(1-a)*b+v(r+1,c+1)*a*b

def elevation(lon,lat):
    coarse=sample(outer,lon,lat)
    if not CW<=lon<=CE or not CS<=lat<=CN:return coarse
    edge=min((lon-CW)*MX,(CE-lon)*MX,(lat-CS)*MY,(CN-lat)*MY)
    t=max(0,min(1,edge/100));t=t*t*(3-2*t)
    return coarse*(1-t)+sample(core,lon,lat)*t

def xy(lon,lat):return [(lon-W)*MX,(N-lat)*MY]

encoded=[];highres=[]
for row in range(SIZE):
    for col in range(SIZE):
        h=elevation(W+(E-W)*col/(SIZE-1),N-(N-S)*row/(SIZE-1))
        q=round((h-DATUM)/SPAN*65535)
        assert 0<=q<=65535
        encoded.append((q>>8,q&255,0));highres.append(q/65535*SPAN)
im=Image.new('RGB',(SIZE,SIZE));im.putdata(encoded);im.save(OUT/'heightmap-rg16.png')

# Lake footprint uses a 256-cell reference surface; native terrain uses 1024 cells.
# The display offset keeps this approximate independent footprint above the terrain.
native=[[highres[(r*2)*SIZE+c*2] for c in range(257)] for r in range(257)]
def surface(x,y):
    fx=max(0,min(256,x/WIDTH*256));fy=max(0,min(256,y/HEIGHT*256))
    c,r=min(255,int(fx)),min(255,int(fy));a,b=fx-c,fy-r
    return native[r][c]*(1-a)*(1-b)+native[r][c+1]*a*(1-b)+native[r+1][c]*(1-a)*b+native[r+1][c+1]*a*b

def simplify(points,tol=3):
    if len(points)<=2:return points
    a,b=points[0],points[-1];dx,dy=b[0]-a[0],b[1]-a[1];den=dx*dx+dy*dy
    best,index=0,0
    for i,p in enumerate(points[1:-1],1):
        t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den)) if den else 0
        d=math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)
        if d>best:best,index=d,i
    return simplify(points[:index+1],tol)[:-1]+simplify(points[index:],tol) if best>tol else [a,b]

roads=json.loads((SOURCE/'roads.geojson').read_text())['features'];edits=[]
for f in roads:
    walking=f['properties']['highway'] in ['footway','path','steps']
    for line in f['geometry']['coordinates']:
        points=simplify([xy(*p) for p in line])
        for a,b in zip(points,points[1:]):
            edits.append({'tool':'paint','x':round(a[0]/WIDTH,7),'y':round(a[1]/HEIGHT,7),
                          'toX':round(b[0]/WIDTH,7),'toY':round(b[1]/HEIGHT,7),
                          'radius':round((3 if walking else 6)/min(WIDTH,HEIGHT),7),
                          'layer':4 if walking else 3,'strength':0.15})
(OUT/'road-edits.json').write_text(json.dumps(edits,separators=(',',':')))

context=json.loads((SOURCE/'context.geojson').read_text())['features']
lake=next(f['geometry']['coordinates'][0] for f in context if f['properties'].get('name')=='월명호')
poly=[xy(*p) for p in lake[:-1]]
area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1]))
if area<0:poly.reverse()
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def in_tri(p,a,b,c):return min(cross(a,b,p),cross(b,c,p),cross(c,a,p))>=-1e-8
remaining=list(range(len(poly)));triangles=[]
while len(remaining)>3:
    for i,b in enumerate(remaining):
        a,c=remaining[i-1],remaining[(i+1)%len(remaining)]
        if cross(poly[a],poly[b],poly[c])<=1e-8:continue
        if any(in_tri(poly[j],poly[a],poly[b],poly[c]) for j in remaining if j not in [a,b,c]):continue
        triangles.append([poly[a],poly[b],poly[c]]);remaining.pop(i);break
    else:raise ValueError('Invalid lake polygon')
triangles.append([poly[i] for i in remaining])
refined=[]
def subdivide(tri):
    a,b,c=tri
    if max(math.dist(a,b),math.dist(b,c),math.dist(c,a))<=4:
        refined.append(tri);return
    ab=[(a[i]+b[i])/2 for i in range(2)];bc=[(b[i]+c[i])/2 for i in range(2)];ca=[(c[i]+a[i])/2 for i in range(2)]
    for t in [[a,ab,ca],[ab,b,bc],[ca,bc,c],[ab,bc,ca]]:subdivide(t)
for tri in triangles:subdivide(tri)
anchor=[min(p[0] for p in poly),min(p[1] for p in poly),min(surface(*p) for p in poly)]
vertices=[]
for tri in refined:
    for x,y in tri:
        vertices.extend([x-anchor[0],surface(x,y)+1.2-anchor[2],y-anchor[1]])
mins=[min(vertices[i::3]) for i in range(3)];maxs=[max(vertices[i::3]) for i in range(3)]
binary=struct.pack('<'+'f'*len(vertices),*vertices)
doc={'asset':{'version':'2.0','generator':'Wolmyeongdong DEM lake footprint'},'scene':0,'scenes':[{'nodes':[0]}],
     'nodes':[{'mesh':0,'name':'MoonLakeFootprint'}],'meshes':[{'primitives':[{'attributes':{'POSITION':0},'material':0}]}],
     'materials':[{'name':'Lake footprint blue','doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':[.12,.55,.76,1],'metallicFactor':0,'roughnessFactor':1},'extensions':{'KHR_materials_unlit':{}}}],
     'extensionsUsed':['KHR_materials_unlit'],'extensionsRequired':['KHR_materials_unlit'],
     'buffers':[{'byteLength':len(binary)}],'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':len(binary),'target':34962}],
     'accessors':[{'bufferView':0,'componentType':5126,'count':len(vertices)//3,'type':'VEC3','min':mins,'max':maxs}]}
js=json.dumps(doc,separators=(',',':')).encode();js+=b' '*((-len(js))%4);binary+=b'\0'*((-len(binary))%4)
(OUT/'moon-lake.glb').write_bytes(struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary)
meta={'bbox_wsen':[W,S,E,N],'origin_lon_lat':[W,N],'width_m':WIDTH,'height_m':HEIGHT,'datum_m_egm96':DATUM,'height_span_m':SPAN,
      'axes':{'x':'east','y':'south','z':'up'},'heightmap_size':SIZE,'terrain_resolution':1024,'core_blend_width_m':100,
      'heightmap_encoding':'16-bit normalized height: R=MSB, G=LSB, B=0; no grayscale or gamma conversion',
      'road_edit_count':len(edits),'road_display_radius_m':6,'trail_display_radius_m':3,
      'lake_anchor':[anchor[0],anchor[1],anchor[2]+2],'lake_display_offset_m':3.2,
      'lake_size':[maxs[0]-mins[0],maxs[2]-mins[2],maxs[1]-mins[1]],'lake_vertex_min':mins,
      'lake_label':xy(127.36898,36.12418),'lake_triangles':len(refined),
      'notice':'Approximate terrain; interpolation does not add survey accuracy. Lake is a draped footprint, not surveyed water level.'}
(OUT/'geography.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
print(json.dumps(meta,ensure_ascii=False,indent=2))
