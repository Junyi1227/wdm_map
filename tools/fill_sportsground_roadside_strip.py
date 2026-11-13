"""Fill the strip between the existing walkway and field, preserving field material."""
import ast,copy,hashlib,json,math,pathlib,struct,sys
R=pathlib.Path(__file__).resolve().parents[1];P=R/'wolmyeongdong/project.json';OUT=P.parent/'assets/core'
p=json.loads(P.read_text());before=copy.deepcopy(p);core=next(s for s in p['layouts'] if s['name']=='月明洞核心區');meta=json.loads((OUT/'geography.json').read_text());sites={s['object']:s for s in meta['sites']};sports=sites['SportsGround']['polygon_xy'];lawn=sites['Lawn']['polygon_xy']
assert len(sports)==70 and len(lawn)==69,'Already edited; inspect before rerunning.'
def glb(path):
 b=path.read_bytes();size=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+size]),b[28+size:]
def texture(doc,binary):
 v=doc['bufferViews'][doc['images'][0]['bufferView']];return binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
old_doc,old_bin=glb(OUT/'sportsground.glb');old_texture=texture(old_doc,old_bin)
assert old_texture==(OUT.parent/'trail-detail.png').read_bytes()
outer=json.loads((OUT.parent/'geography.json').read_text());w,s,e,n=outer['bbox_wsen'];mx=outer['width_m']/(e-w);my=outer['height_m']/(n-s)
def road(id):return [[(x-w)*mx,(n-y)*my] for x,y in next(f for f in json.loads((R/'source-data/roads.geojson').read_text())['features'] if f['properties']['osm_id']==id)['geometry']['coordinates'][0]]
walk=road(120371425)[8:];top=road(120371406)[:5]
new_edge=walk+top[1:];new_sports=sports[:17]+new_edge[1:]+sports[26:]
# Clip the lawn at the same road, including its intersection with the old lawn edge.
a,b=walk[9],walk[10];c,d=lawn[6],lawn[7]
def cross(u,v):return u[0]*v[1]-u[1]*v[0]
u=[b[i]-a[i] for i in range(2)];v=[d[i]-c[i] for i in range(2)];t=cross([c[i]-a[i] for i in range(2)],v)/cross(u,v);assert 0<t<1
intersection=[a[i]+t*u[i] for i in range(2)]
shared=list(reversed(top))+list(reversed(walk[10:-1]))+[intersection];new_lawn=shared+lawn[7:]
sys.path.insert(0,str(R/'landmarks/tools'));from lake_rock_layout import ground
names={'write_glb','cross','inside_triangle','polygon_triangles','refined'};tree=ast.parse((R/'tools/build_core.py').read_text());env={'OUT':OUT,'json':json,'struct':struct,'math':math,'ground':ground};exec(compile(ast.Module(body=[f for f in tree.body if isinstance(f,ast.FunctionDef) and f.name in names],type_ignores=[]),'mesh helpers','exec'),env)
# Preserve original field triangles. Only append the missing roadside band.
acc=old_doc['accessors'][0];view=old_doc['bufferViews'][acc['bufferView']];values=struct.unpack_from('<'+'f'*(acc['count']*3),old_bin,view.get('byteOffset',0));pos=meta['models']['SportsGround']['position'];offset=[pos[0],pos[2],pos[1]];original_vertices=[[values[i+j]+offset[j] for j in range(3)] for i in range(0,len(values),3)]
band=list(reversed(sports[16:26]))+new_edge[1:-1];extra=[]
for tri in env['polygon_triangles'](band):env['refined'](tri,extra)
report={'request':'草皮／道路／草皮／運動場 → 草皮／道路／運動場','boundary_basis':'既有步道120371425及120371406；僅填滿道路與運動場間區帶，不移動道路。','original_field_triangles_retained':len(original_vertices)//3,'added_triangles':len(extra)//3,'changes':[]}
for name,poly in [('SportsGround',new_sports),('Lawn',new_lawn)]:
 doc,binary=glb(OUT/(name.lower()+'.glb'));color=doc['materials'][0]['pbrMetallicRoughness']['baseColorFactor']
 if name=='SportsGround':verts=original_vertices+extra
 else:
  verts=[]
  for tri in env['polygon_triangles'](poly):env['refined'](tri,verts)
 data=env['write_glb'](name.lower(),verts,color);new_doc,new_bin=glb(OUT/(name.lower()+'.glb'))
 assert new_doc['materials']==doc['materials'] and texture(new_doc,new_bin)==texture(doc,binary),'Material changed'
 meta['models'][name]=data
 obj=next(o for o in core['objects'] if o['name']==name);obj['content'].update(dict(zip(['width','height','depth'],data['size'])))
 inst=next(o for o in core['instances'] if o['name']==name);inst.update(dict(zip(['x','y','z'],data['position'])));inst.update(dict(zip(['width','height','depth'],data['size'])))
 site=sites[name];report['changes'].append({'object':name,'original_polygon_xy':site['polygon_xy'],'effective_polygon_xy':poly});site.update(polygon_xy=poly,world_bbox=[min(v[0] for v in poly),min(v[1] for v in poly),max(v[0] for v in poly),max(v[1] for v in poly)])
for layout,prior in zip(p['layouts'],before['layouts']):
 for key in ['objects','instances']:assert [o for o in layout[key] if o['name'] not in ['SportsGround','Lawn']]==[o for o in prior[key] if o['name'] not in ['SportsGround','Lawn']]
report['field_material_and_embedded_texture_identical']=True;report['field_texture_sha256']=hashlib.sha256(old_texture).hexdigest()
P.write_text(json.dumps(p,ensure_ascii=False,indent=2));(OUT/'geography.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));(R/'source-data/sportsground-roadside-strip.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='changes'},ensure_ascii=False,indent=2))
