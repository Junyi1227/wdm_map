"""Fetch public reference pages and download candidate photographs, not AI output."""
import pathlib,sys,json,urllib.parse,concurrent.futures
sys.path.insert(0,str(pathlib.Path(__file__).parent));from collect import get,Parser
R=pathlib.Path(__file__).resolve().parents[2];C=R/'.cache/landmark-pages';O=R/'landmarks/02-hall-316/photos';O.mkdir(exist_ok=True)
PAGES={
 'official':'https://www.wolmyeongdong.kr/intro/scenic-spots/the-holy-sons-house-of-love',
 'tw-guide':'https://god21.tw/post/夏季靈修會線上月明洞導覽空提喜悅篇/',
 'side2013':'https://jmsprovi.net/entry/PHOTO-월명동-성자-사랑의-집-옆모습',
 'front2013':'https://www.god21.net/Square/News/Wmd/View/21956?page=9',
 'rear2013':'https://www.god21.net/Square/News/Wmd/View/22276?page=9',
 'construction':'https://mannamdaehwa.tistory.com/278'}
def page(item):
 k,url=item
 try:
  f=C/('hall316-'+k+'.html')
  if not f.exists():f.write_bytes(get(url))
  p=Parser();p.feed(f.read_text(errors='replace'));return k,{'url':url,'images':p.images,'links':p.links}
 except Exception as e:return k,{'url':url,'error':str(e)}
D=dict(concurrent.futures.ThreadPoolExecutor(6).map(page,PAGES.items()));(C/'hall316-inventory.json').write_text(json.dumps(D,ensure_ascii=False,indent=2))
for k,v in D.items():
 print(k,len(v.get('images',[])),v.get('error',''))
 if k=='official':
  seen=set()
  for img in v['images']:
   src=img.get('src','')
   if '/the-holy-sons-house-of-love/' in src and src not in seen:
    seen.add(src);u=urllib.parse.urljoin(v['url'],src);name='official-'+pathlib.Path(src).name
    try:
     f=O/name
     if not f.exists():f.write_bytes(get(u))
    except Exception as e:print(name,str(e))
