import sys,pathlib,json,urllib.parse,concurrent.futures
sys.path.insert(0,str(pathlib.Path(__file__).parent));from collect import get
R=pathlib.Path(__file__).resolve().parents[2];D=json.loads((R/'.cache/landmark-pages/hall316-inventory.json').read_text());O=R/'landmarks/02-hall-316/photos'
SELECT={'tw-guide':[21,22,23,24],'side2013':[0],'front2013':[0,1],'rear2013':[0,1,2,3],'construction':[0,1]}
def one(arg):
 k,i=arg;d=D[k]['images'][i];u=urllib.parse.urljoin(D[k]['url'],d.get('data-src',d.get('src','')))
 if u.startswith('http:'):u='https:'+u[5:]
 ext=pathlib.Path(urllib.parse.urlsplit(u).path).suffix
 if ext not in ['.jpg','.png','.jpeg','.webp']:ext='.jpg'
 name=k+'-%02d'%i+ext
 try:
  p=O/name
  if not p.exists():p.write_bytes(get(u))
  return {'id':k+'-%02d'%i,'file':'02-hall-316/photos/'+name,'image_url':u,'source_page':D[k]['url'],'source_caption':d.get('alt','')}
 except Exception as e:return {'id':k+'-%02d'%i,'error':str(e),'image_url':u,'source_page':D[k]['url']}
a=list(concurrent.futures.ThreadPoolExecutor(7).map(one,[(k,i) for k,inds in SELECT.items() for i in inds]));(R/'.cache/landmark-pages/hall316-candidates.json').write_text(json.dumps(a,ensure_ascii=False,indent=2));print(json.dumps(a,ensure_ascii=False))
