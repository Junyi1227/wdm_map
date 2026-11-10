"""Check georeferencing, encoding, resources and scene invariants without changing the project."""
from pathlib import Path
import hashlib
import json
import math
import struct
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'wolmyeongdong'
meta=json.loads((P/'assets/geography.json').read_text())
project=json.loads((P/'project.json').read_text())
scene=project['layouts'][0]
terrain=next(o for o in scene['objects'] if o['name']=='WolmyeongTerrain')
instance=next(i for i in scene['instances'] if i['name']=='WolmyeongTerrain')
outer=json.loads((ROOT/'source-data/elevation-dense.json').read_text())
core=json.loads((ROOT/'source-data/elevation-core.json').read_text())
image=Image.open(P/'assets/heightmap-rg16.png')
assert image.size==(513,513) and image.mode=='RGB'
def decode(x,y):
    r,g,b=image.getpixel((x,y));assert b==0
    return (r*256+g)/65535*600+150
controls=[('northwest',0,0,outer['results'][44*45]['elevation']),
          ('northeast',512,0,outer['results'][44*45+44]['elevation']),
          ('southwest',0,512,outer['results'][0]['elevation']),
          ('southeast',512,512,outer['results'][44]['elevation']),
          ('retained core sample',256,256,core['results'][21*41+6]['elevation'])]
checks=[]
for name,x,y,expected in controls:
    decoded=decode(x,y)
    assert abs(decoded-expected)<=600/65535/2+1e-6,(name,decoded,expected)
    checks.append({'name':name,'x':x/512*meta['width_m'],'y':y/512*meta['height_m'],
                   'expected_z':decoded-150,'source_elevation_m':expected,'encoding_error_m':abs(decoded-expected)})
assert terrain['type']=='Terrain3D::Terrain3D'
assert terrain['content']['Resolution']=='1024'
assert terrain['content']['HeightmapImage']=='heightmap-rg16.png'
assert terrain['content'].get('SculptData','')=='' # Temporary brush test was intentionally reverted.
assert sum(i['name']=='WolmyeongTerrain' for i in scene['instances'])==1
assert abs(instance['width']-meta['width_m'])<1e-6 and abs(instance['height']-meta['height_m'])<1e-6
assert instance['depth']==600
assert not (ROOT/'yue-ming-terrain').exists()
for resource in project['resources']['resources']:
    assert not Path(resource['file']).is_absolute() and '://' not in resource['file']
    assert (P/resource['file']).is_file()
edits=json.loads(terrain['content']['Edits'])
assert len(edits)==1683 and all(e['tool']=='paint' and e['layer'] in [3,4] for e in edits)
assert all(-1e-6<=e[k]<=1+1e-6 for e in edits for k in ['x','y','toX','toY'])
def events(items):
    for item in items:
        assert item['type']!='BuiltinCommonInstructions::JsCode','Scene must use native events'
        for action in item.get('actions',[]):
            assert not action['type']['value'].startswith('Terrain3D::'),'No scene event may regenerate/sculpt terrain'
        events(item.get('events',[]))
events(scene['events'])
assert not any(o['name'].startswith(('Hall','Tree','Player','Pavilion')) for o in scene['objects'])
blob=(P/'assets/moon-lake.glb').read_bytes();magic,version,length=struct.unpack_from('<III',blob)
assert magic==0x46546c67 and version==2 and length==len(blob)
jslen,jstype=struct.unpack_from('<II',blob,12);gltf=json.loads(blob[20:20+jslen])
assert len(gltf['meshes'])==1 and gltf['accessors'][0]['count']>0
report={'passed':True,'control_points':checks,'heightmap_size':[513,513],'native_resolution':1024,
        'native_terrain_instances':1,'paint_edits':len(edits),'relative_resources':len(project['resources']['resources']),
        'old_output_deleted':True,'scene_uses_native_events':True,'temporary_brush_test_reverted':True,
        'project_sha256':hashlib.sha256((P/'project.json').read_bytes()).hexdigest()}
(ROOT/'validation/assets-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
