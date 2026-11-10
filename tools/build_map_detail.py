"""Build local repeating ground textures and draped vector route ribbons.

Only writes assets. Never overwrites the native terrain or its sculpt data.
Route widths and the 1m display offset are graphic conventions, not surveys.
"""
from pathlib import Path
import json
import math
import random
import struct
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'wolmyeongdong/assets'
meta = json.loads((OUT / 'geography.json').read_text())
W, S, E, N = meta['bbox_wsen']
WIDTH, HEIGHT = meta['width_m'], meta['height_m']
heightmap = Image.open(OUT / 'heightmap-rg16.png')

def xy(lon, lat):
    return (lon-W)/(E-W)*WIDTH, (N-lat)/(N-S)*HEIGHT

def ground(x, y):
    u = max(0, min(512, x/WIDTH*512))
    v = max(0, min(512, y/HEIGHT*512))
    i, j = min(511, int(u)), min(511, int(v))
    a, b = u-i, v-j
    def z(c, r):
        red, green, _ = heightmap.getpixel((c, r))
        return (red*256+green)/65535*600
    return z(i,j)*(1-a)*(1-b)+z(i+1,j)*a*(1-b)+z(i,j+1)*(1-a)*b+z(i+1,j+1)*a*b

# Neutral textures are tinted by the four editable terrain layer colors.
# A tile spans 8m, independent of the 4km map extent.
for kind in ('grass', 'rock', 'road', 'trail'):
    rng = random.Random('wolmyeongdong-'+kind)
    image = Image.new('RGB', (256, 256))
    pixels = []
    for _ in range(256*256):
        shade = max(160, min(255, round(rng.gauss(237, 5))))
        pixels.append((shade, shade, shade))
    image.putdata(pixels)
    draw = ImageDraw.Draw(image)
    for _ in range(800 if kind == 'grass' else 320):
        x, y = rng.randrange(256), rng.randrange(256)
        shade = rng.randrange(185, 228)
        if kind == 'grass':
            draw.line([(x,y),(x+1,y-3)], fill=(shade,)*3, width=1)
        else:
            draw.ellipse((x,y,x+1,y+1), fill=(shade,)*3)
    image.save(OUT / (kind+'-detail.png'))

def write_model(name, walking, half_width, color):
    vertices = []
    features = json.loads((ROOT/'source-data/roads.geojson').read_text())['features']
    def vertex(point):
        x, y = point
        return [x, ground(x,y)+1.0+(0.05 if walking else 0), y]
    for feature in features:
        is_walk = feature['properties']['highway'] in ('footway', 'path', 'steps')
        if is_walk != walking:
            continue
        for line in feature['geometry']['coordinates']:
            original = [xy(*p) for p in line]
            points = []
            for a,b in zip(original, original[1:]):
                count = max(1, math.ceil(math.dist(a,b)/2))
                points.extend([(a[0]+(b[0]-a[0])*i/count,a[1]+(b[1]-a[1])*i/count) for i in range(count)])
            if not points:
                continue
            points.append(original[-1])
            rows=[]
            for index, point in enumerate(points):
                before, after = points[max(0,index-1)], points[min(len(points)-1,index+1)]
                dx,dy = after[0]-before[0], after[1]-before[1]
                length = math.hypot(dx,dy)
                nx,ny = (-dy/length,dx/length) if length else (0,1)
                rows.append([vertex((point[0]+nx*half_width*t,point[1]+ny*half_width*t)) for t in (-1,-.5,0,.5,1)])
            for a,b in zip(rows,rows[1:]):
                for col in range(4):
                    for v in (a[col],b[col],a[col+1],a[col+1],b[col],b[col+1]):
                        vertices.extend(v)
    mins=[min(vertices[i::3]) for i in range(3)]
    maxs=[max(vertices[i::3]) for i in range(3)]
    for offset in range(0,len(vertices),3):
        for axis in range(3):
            vertices[offset+axis] -= mins[axis]
    binary=struct.pack('<'+'f'*len(vertices),*vertices)
    sizes=[maxs[i]-mins[i] for i in range(3)]
    doc={'asset':{'version':'2.0','generator':'OSM draped vector routes'},'scene':0,
         'scenes':[{'nodes':[0]}],'nodes':[{'mesh':0}],
         'meshes':[{'primitives':[{'attributes':{'POSITION':0},'material':0}]}],
         'materials':[{'doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':color,'metallicFactor':0,'roughnessFactor':1},'extensions':{'KHR_materials_unlit':{}}}],
         'extensionsUsed':['KHR_materials_unlit'],'extensionsRequired':['KHR_materials_unlit'],
         'buffers':[{'byteLength':len(binary)}],
         'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':len(binary),'target':34962}],
         'accessors':[{'bufferView':0,'componentType':5126,'count':len(vertices)//3,'type':'VEC3','min':[0,0,0],'max':sizes}]}
    text=json.dumps(doc,separators=(',',':')).encode()
    text+=b' '*((-len(text))%4)
    binary+=b'\0'*((-len(binary))%4)
    (OUT/(name+'.glb')).write_bytes(struct.pack('<III',0x46546c67,2,28+len(text)+len(binary))+struct.pack('<II',len(text),0x4e4f534a)+text+struct.pack('<II',len(binary),0x004e4942)+binary)
    return {'file':name+'.glb','position':[mins[0],mins[2],mins[1]],
            'size':[sizes[0],sizes[2],sizes[1]],'vertices':len(vertices)//3,'display_half_width_m':half_width}

result={'RoadDetail':write_model('roads-detail',False,6,[.78,.81,.79,1]),
        'TrailDetail':write_model('trails-detail',True,3,[.75,.56,.32,1]),
        'notice':'Display ribbons over initial DEM; hide or rebuild after terrain edits beneath routes. Widths are illustrative.'}
(OUT/'route-detail.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
