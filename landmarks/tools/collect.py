"""Collect public reference pages and image metadata. Originals remain unmodified."""
import json, pathlib, urllib.request, urllib.parse, concurrent.futures
from html.parser import HTMLParser
ROOT=pathlib.Path(__file__).resolve().parents[2]; CACHE=ROOT/'.cache/landmark-pages'; CACHE.mkdir(parents=True,exist_ok=True)
PAGES={
 'camel':'https://www.wolmyeongdong.kr/works/rock-sculptures/the-camel-rock',
 'pine':'https://www.wolmyeongdong.kr/works/trees/the-prayer-sign-pine',
 'hill':'https://www.wolmyeongdong.kr/intro/scenic-spots/the-prayer-hill',
 'first':'https://www.wolmyeongdong.kr/works/waterfall',
 'route':'https://www.wolmyeongdong.kr/experience/thrill-course',
 'lake':'https://god21.tw/post/wmd_lake/',
 'round2011':'https://www.god21.net/Square/News/Wmd/View/9248',
 'roundstairs':'https://www.god21.net/Square/News/Wmd/View/9140',
 'festival':'https://2026rockfestival.com/',
 'holy':'https://god21.tw/post/夏季靈修會線上月明洞導覽聖靈歷史篇/',
}
def get(url):
 u=urllib.parse.urlsplit(url);url=urllib.parse.urlunsplit((u.scheme,u.netloc,urllib.parse.quote(u.path,safe='/%'),u.query,''))
 return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=40).read()
class Parser(HTMLParser):
 def __init__(self): super().__init__();self.images=[];self.links=[];self.context='';self.heading=False
 def handle_starttag(self,t,a):
  d=dict(a)
  if t in ['h1','h2','h3','h4']:self.heading=True
  if t=='img': self.images.append(dict(d,context=self.context[-250:]))
  if t=='a' and d.get('href'):self.links.append(d['href'])
 def handle_endtag(self,t):
  if t in ['h1','h2','h3','h4']:self.heading=False
 def handle_data(self,s):
  if s.strip():self.context=(self.context+' '+s.strip())[-500:]
def page(item):
 k,url=item
 try:
  f=CACHE/(k+'.html')
  if not f.exists():f.write_bytes(get(url))
  p=Parser();p.feed(f.read_text(errors='replace'))
  return k,dict(url=url,images=p.images,links=p.links)
 except Exception as e:return k,dict(url=url,error=str(e))
if __name__=='__main__':
 data=dict(concurrent.futures.ThreadPoolExecutor(6).map(page,PAGES.items()));(CACHE/'inventory.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
 for k,v in data.items():print(k,len(v.get('images',[])),v.get('error',''))
