"""Check core georeferencing, polygon coverage, metre scale and local resources."""
from pathlib import Path
import hashlib
import json
import math
import struct
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'wolmyeongdong/project.json'
project=json.loads(P.read_text())
core=next(s for s in project['layouts'] if s['name']=='月明洞核心區')
meta=json.loads((P.parent/'assets/core/geography.json').read_text())
outer=json.loads((P.parent/'assets/geography.json').read_text())
assert project['firstLayout']==core['name']
assert len(project['layouts'])==2
terrain=next(o for o in core['objects'] if o['name']=='WolmyeongTerrain')
inst=next(i for i in core['instances'] if i['name']=='WolmyeongTerrain')
assert terrain['type']=='Terrain3D::Terrain3D' and terrain['content']['Resolution']=='1024'
assert terrain['content']['HeightmapImage']=='core-heightmap-rg16.png'
assert sum(i['name']=='WolmyeongTerrain' for i in core['instances'])==1
assert abs(inst['width']-meta['width_m'])<1e-6 and abs(inst['height']-meta['height_m'])<1e-6
assert [inst['x'],inst['y'],inst.get('z',0)]==meta['terrain_position']
assert len(json.loads(terrain['content']['Edits']))==meta['paint_edits']
for resource in project['resources']['resources']:
    assert not Path(resource['file']).is_absolute() and '://' not in resource['file']
    assert (P.parent/resource['file']).is_file()

def load_model(name):
    data=meta['models'][name];blob=(P.parent/data['file']).read_bytes()
    magic,version,length=struct.unpack_from('<III',blob);assert magic==0x46546c67 and version==2 and length==len(blob)
    size=struct.unpack_from('<I',blob,12)[0];doc=json.loads(blob[20:20+size]);offset=28+size
    acc=doc['accessors'][0];view=doc['bufferViews'][acc['bufferView']]
    coords=struct.unpack_from('<'+'f'*(acc['count']*3),blob,offset+view.get('byteOffset',0))
    return doc,coords

areas=[]
for site in meta['sites']:
    name=site['object'];data=meta['models'][name];doc,v=load_model(name)
    points=site['polygon_xy']
    source_area=abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1])))/2
    mesh_area=0
    for i in range(0,len(v),9):
        ax,ay=v[i],v[i+2];bx,by=v[i+3],v[i+5];cx,cy=v[i+6],v[i+8]
        mesh_area+=abs((bx-ax)*(cy-ay)-(by-ay)*(cx-ax))/2
    assert abs(mesh_area-source_area)/source_area<.0001,(name,mesh_area,source_area)
    instance=next(i for i in core['instances'] if i['name']==name)
    for key,expected in zip(('x','y','z'),data['position']):assert abs(instance[key]-expected)<1e-6
    for key,expected in zip(('width','height','depth'),data['size']):assert abs(instance[key]-expected)<1e-6
    assert abs(instance['x']-site['world_bbox'][0])<.001
    assert abs(instance['y']-site['world_bbox'][1])<.001
    assert abs(instance['x']+instance['width']-site['world_bbox'][2])<.001
    assert abs(instance['y']+instance['height']-site['world_bbox'][3])<.001
    if name!='MoonLake':assert 'TEXCOORD_0' in doc['meshes'][0]['primitives'][0]['attributes']
    areas.append({'name':name,'source_area_m2':source_area,'render_mesh_area_m2':mesh_area})

width_checks=[]
for name in ['RoadDetail','TrailDetail']:
    walking=name=='TrailDetail'
    widths=sorted(set(w['display_width_m'] for w in meta['road_widths'] if (w['highway'] in ('footway','path','steps'))==walking))
    expected=[w/math.ceil(w) for w in widths]
    doc,coords=load_model(name)
    samples=[math.hypot(coords[i]-coords[i+6],coords[i+2]-coords[i+8]) for i in range(0,len(coords),9)]
    matched=[any(abs(sample-e)<.0002 for sample in samples) for e in expected]
    assert all(matched),(name,matched)
    width_checks.append({'name':name,'stripe_widths_m':expected,'matched':matched})
assert all(w['display_width_m'] in (1.2,2.8,3.5) and not w['measured'] for w in meta['road_widths'])

image=Image.open(P.parent/'assets/core/heightmap-rg16.png')
old_image=Image.open(P.parent/'assets/heightmap-rg16.png')
def height(image,c,r):
    red,green,blue=image.getpixel((c,r));assert blue==0
    return (red*256+green)/65535*600
controls=[]
for c,r in [(0,0),(512,0),(0,512),(512,512),(256,256)]:
    x=inst['x']+c/512*meta['width_m'];y=inst['y']+r/512*meta['height_m']
    u=x/outer['width_m']*512;v=y/outer['height_m']*512;i,j=int(u),int(v);a,b=u-i,v-j
    expected=height(old_image,i,j)*(1-a)*(1-b)+height(old_image,i+1,j)*a*(1-b)+height(old_image,i,j+1)*(1-a)*b+height(old_image,i+1,j+1)*a*b
    actual=height(image,c,r);assert abs(actual-expected)<=600/65535/2+1e-6
    controls.append({'x':x,'y':y,'z':actual,'source_error_m':abs(actual-expected)})
def events(items):
    for event in items:
        assert event['type']!='BuiltinCommonInstructions::JsCode'
        assert not any(a['type']['value'].startswith('Terrain3D::') for a in event.get('actions',[]))
        events(event.get('events',[]))
events(core['events'])
report={'passed':True,'default_scene':core['name'],'extent_m':[meta['width_m'],meta['height_m']],
        'native_terrain_instances':1,'contour_areas':areas,'route_width_checks':width_checks,'dem_controls':controls,
        'scene_uses_native_events':True,'relative_resources':len(project['resources']['resources']),
        'checkpoint_commit':'e202f26','project_sha256':hashlib.sha256(P.read_bytes()).hexdigest()}
(ROOT/'validation/core-assets-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
