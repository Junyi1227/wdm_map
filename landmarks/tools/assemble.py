import sys,json,pathlib,urllib.parse,concurrent.futures,hashlib
from PIL import Image,ImageOps,ImageDraw
sys.path.insert(0,str(pathlib.Path(__file__).parent));from collect import get
ROOT=pathlib.Path(__file__).resolve().parents[1];D=json.load(open(ROOT.parent/'.cache/landmark-pages/inventory.json'))
GROUPS=[
 ('01-yasimjak','野心作／야심작',[('route',[11])],['連續正面全景','各段石壁側背面','階梯及通道尺寸']),
 ('02-hall-316','316會館（外觀待核對）',[('festival',[31])],['正面建築全景與名稱同框','左右立面、屋頂','入口及階梯；現有圖僅露台活動，不能推定外形']),
 ('03-lake-pavilion','月明湖＋湖中亭',[('lake',[8,9,10])],['亭子正面、側背面及屋頂俯視','橋與島接點','柱間及入口細節']),
 ('04-god-waterfall','神的瀑布',[('lake',[5,6,7])],['全岩壁側面與頂部','落水口及下方水池尺度']),
 ('05-holy-spirit-waterfall','聖靈瀑布',[('holy',[6])],['側背面、落水口近照','水池邊界與岩壁連接']),
 ('06-first-waterfall','第一瀑布／제1폭포',[('first',[2,3,4,6])],['落水口俯視','岩壁背側與水池輪廓']),
 ('07-prayer-pine','禱告奇蹟松／기도표적소나무',[('pine',list(range(8,15)))],['根部四面、樹幹分叉近照','拍攝方向與目前枝形核對']),
 ('08-prayer-hill','禱告山／기도동산',[('hill',[6,7,8,9]),('holy',[14,15])],['平台俯視、山坡側面','道路與階梯起終點及高低差']),
 ('09-camel-rock','駱駝石／낙타바위',[('route',[12]),('lake',[17,18]),('camel',[8])],['左、右及背面完整輪廓','基底接地處、比例尺','官方背景為空拍區域圖，僅作位置環境參考']),
 ('10-round-hill-pavilion','圓山八角亭（둥그레산 候選）',[('round2011',list(range(7)))],['先確認是否就是你指的亭子','現況正側背面、屋頂、柱間與階梯；2011照片不代表現在'])]
DATES={'lake':'2026-05-06','holy':'2021-08-30','round2011':'2011-06-09','roundstairs':'2011-05-31','festival':'2026（活動年，頁面發布日未確認）'}
def one(arg):
 slug,k,i=arg;d=D[k]['images'][i];u=urllib.parse.urljoin(D[k]['url'],d.get('data-src',d.get('src','')))
 if u.startswith('http:'):u='https:'+u[5:]
 ext=pathlib.Path(urllib.parse.urlsplit(u).path).suffix.lower();ext=ext if ext in ['.png','.jpg','.jpeg','.webp'] else '.jpg'
 f=ROOT/slug/'photos'/(k+'-%02d'%i+ext);f.parent.mkdir(parents=True,exist_ok=True)
 record={'id':k+'-%02d'%i,'source_page':D[k]['url'],'image_url':u,'source_caption':d.get('alt',''),'nearby_text':d.get('context','')[-250:],'publication_date':DATES.get(k),'photo_date':None,'retrieved':'2026-11-10','rights':'未發現明確開放授權；著作權屬原權利人。限參考整理，公開散布、AI上傳與衍生使用前需確認權限。','identity':'候選待核對' if slug in ['02-hall-316','10-round-hill-pavilion'] else '依來源章節及圖說分類','file':str(f.relative_to(ROOT))}
 if k=='camel':record['evidence_note']='官方頁面背景為空拍環境圖；星光是頁面另外疊加的元素，本檔沒有星光。不是單體特寫。'
 if k=='festival':record['evidence_note']='圖說明示3.16館屋頂露台；僅證明活動場地，不能核對建築外觀。'
 try:
  if not f.exists():f.write_bytes(get(u))
  im=Image.open(f);record.update(width=im.width,height=im.height,sha256=hashlib.sha256(f.read_bytes()).hexdigest())
 except Exception as e:record['download_error']=str(e)
 return slug,record
args=[(s,k,i) for s,n,p,m in GROUPS for k,inds in p for i in inds]
results=list(concurrent.futures.ThreadPoolExecutor(8).map(one,args));manifest=[]
for s,n,p,m in GROUPS:
 photos=[r for slug,r in results if slug==s];entry={'id':s,'name':n,'status':'照片整理；尚未核對／建模','missing_angles':m,'photos':photos,'parts':{'01-yasimjak':['分段石壁','特色巨石','階梯／通道'],'03-lake-pavilion':['湖岸','島','橋','亭'],'08-prayer-hill':['局部地形','平台','階梯']}.get(s,['主體；細分待照片核對'])};manifest.append(entry)
 (ROOT/s/'references.json').write_text(json.dumps(entry,ensure_ascii=False,indent=2))
 (ROOT/s/'README.md').write_text('# '+n+'\n\n目前為參考資料，未確定位置或實測尺寸。\n\n待補：\n\n'+''.join('- '+a+'\n' for a in m)+'\n逐張來源見 references.json。照片年代未知時保留空值；發布日期不當成拍攝日期。\n')
(ROOT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
# Visual review supersedes broad source captions.
notes={
 'lake-08':'亭下動物雕刻石柱細節，並非亭子全景。',
 'lake-09':'湖中亭與歷史活動人群；非現況無遮擋全景。',
 'lake-10':'核心區空拍，含湖岸、島、亭與橋。',
 'lake-07':'湖、橋、亭與野心作的周邊關係；非瀑布特寫。',
 'pine-08':'主幹／主枝近景；來源雖稱全樹，實際有裁切。',
 'pine-09':'主幹分枝視角；來源雖稱遠景，實際偏近景。',
 'pine-10':'山坡平台遠景，樹體細節不足。',
 'pine-12':'樹幹主枝近景，不只是樹皮細節。',
 'holy-15':'山區遠眺，僅作周邊環境，不能據此重建禱告山平台。',
 'lake-17':'草坡道路環境，駱駝石受樹木遮擋，不能用於單張生成。',
 'lake-18':'岩體斜向近景，岩體下端出框；不可假定為完整外形。',
 'route-12':'駱駝石與草坡全景，有人群／樹木遮擋；可參考延伸輪廓。',
}
for entry in manifest:
 for r in entry['photos']:
  if r['id'] in notes:r['visual_review']=notes[r['id']]
 (ROOT/entry['id']/'references.json').write_text(json.dumps(entry,ensure_ascii=False,indent=2))
(ROOT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
# A contact sheet is a browsing aid; originals remain intact.
thumbs=[]
for s,r in results:
 if 'download_error' in r:continue
 im=Image.open(ROOT/r['file']).convert('RGB');tile=Image.new('RGB',(320,240),'#f0eee6');im.thumbnail((312,205));tile.paste(im,((320-im.width)//2,0));ImageDraw.Draw(tile).text((6,210),s[:2]+' '+r['id'],fill='black');thumbs.append(tile)
w=1280;sheet=Image.new('RGB',(w,240*((len(thumbs)+3)//4)),'white')
for i,t in enumerate(thumbs):sheet.paste(t,((i%4)*320,(i//4)*240))
sheet.save(ROOT/'contact-sheet.jpg',quality=85)
print(json.dumps({'groups':len(manifest),'photos':len(results),'failed':[(s,r['id'],r.get('download_error')) for s,r in results if 'download_error'in r]},ensure_ascii=False))
