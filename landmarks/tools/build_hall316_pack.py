# -*- coding: utf-8 -*-
"""Build the confirmed hall's offline evidence album and original-photo upload pack."""
import pathlib,json,hashlib,shutil,zipfile,html
from PIL import Image,ImageDraw,ImageFont
R=pathlib.Path(__file__).resolve().parents[1];O=R/'02-hall-316';C=R.parent/'.cache/landmark-pages';D=json.loads((C/'hall316-inventory.json').read_text());h=html.escape
old=json.loads((O/'references.json').read_text());festival=next(p for p in old['photos'] if p['id']=='festival-31');festival.update(identity='使用者確認為同一建築的露台',visual_review='來源明示3.16館屋頂露台；用於細長上層棚架、露台及欄杆參考，不當成整棟外觀。',role='rooftop-detail')
photos=[festival]
def add(id,file,page,url,caption,role,date=None,note=''):
 im=Image.open(O/'photos'/file)
 p={'id':id,
 'file':'02-hall-316/photos/'+file,
 'source_page':page,
 'image_url':url,
 'source_caption':caption,
 'visual_review':note or caption,
 'role':role,
 'publication_date':date,
 'photo_date':None,
 'retrieved':'2026-11-11',
 'identity':'使用者確認別名與標的，並與所附照片外觀比對',
 'rights':'原權利人保有著作權，未發現明確開放授權；第三方AI上傳及公開使用請確認來源條款或使用自有照片。',
 'width':im.width,
 'height':im.height,
 'sha256':hashlib.sha256((O/'photos'/file).read_bytes()).hexdigest()};photos.append(p);return p
notes={
 'spring':('較平視的正面全景：長正立面、完整大柱列、綠色簷帶、上方白色退縮樓體。湖與植栽只作環境參考。',
 'main-view'),
 '':('正面斜角A：可看柱廊深度、玻璃立面及側端轉折；低視角會產生透視縮短。',
 'angle-view'),
 'sky':('正面斜角B：與A相反方向的柱廊轉角。可核對短側面、簷板厚度與柱列。不是完整背面。',
 'angle-view'),
 'pillar':('柱頭、柱腳、圓柱分段與屋簷底部近照；適合細節核對，不適合單張生成整棟。',
 'column-detail'),
 'lake':('跨湖正面斜角：下層基座與建築相對湖岸的高差；湖水與倒影不屬建築。',
 'context'),
 'octagonal-pavilion':('建築與湖中亭同框；亭子是另一個物件，不能讓AI合併成會館附件。',
 'context'),
 'blossom':('春季跨湖全景，前景花朵遮擋建築；不作主要輸入。',
 'context'),
 'night':('夜景輪廓與立面照明；藍色燈光不是白日材質顏色。',
 'night-only'),
 'reflection':('紫色夜景及水面倒影；不要把倒影生成為第二棟建築。',
 'night-only'),
 'night-light':('柱列夜間近景：柱頭、玻璃分格與簷底可核對；紫紅光不是石柱固有顏色。',
 'night-only')}
seen=set()
for src in D['official']['images']:
 u=src.get('src',
 '');prefix='/img/intro/scenic-spots/the-holy-sons-house-of-love/the-holy-sons-house-of-love'
 if not u.startswith(prefix) or u in seen:continue
 seen.add(u);file='official-'+pathlib.Path(u).name;suffix=pathlib.Path(u).stem.replace('the-holy-sons-house-of-love',
 '').lstrip('-')
 if suffix not in notes:continue
 note,role=notes[suffix];add('official-'+(suffix or 'corner-a'),file,D['official']['url'],
 'https://www.wolmyeongdong.kr'+u,
 '官方建築介紹的外觀參考圖（圖意轉述）',role,note=note)
candidates=json.loads((C/'hall316-candidates.json').read_text());byid={p['id']:p for p in candidates if 'file' in p}
for id,note,role,date in [
 ('tw-guide-21',
 '跨湖斜角與湖中亭。照片可比對綠色簷帶，建築身分由文章同名說明佐證。',
 'context',
 '2021-08-23'),
 ('tw-guide-22',
 '遠景全區圖；屋頂高低關係可作輔助，主體在畫面中偏小。',
 'context',
 '2021-08-23'),
 ('tw-guide-23',
 '夜景與倒影，僅作燈光、環境參考。',
 'night-only',
 '2021-08-23'),
 ('front2013-00',
 '2013年歷史近照：前方綠化與弧形基座／簷下空間；並非完整正立面。',
 'historical-detail',
 '2013-08-17'),
 ('rear2013-00',
 '2013年背側施工：可見白色側牆與高柱，但坡地、工程及樹木遮擋；非現況背面。',
 'historical-side',
 '2013-09-03'),
 ('rear2013-03',
 '2013年背側白牆與小窗，施工中局部；不能推定所有背面細節。',
 'historical-side',
 '2013-09-03')]:
 p=byid[id];add(id,pathlib.Path(p['file']).name,p['source_page'],p['image_url'],
 '歷史報導／中文導覽建築參考（圖意轉述）',role,date,note)
add('user-winter',
 'user-confirmed-winter.jpg',None,None,
 '使用者提供並確認的冬季照片，畫面帶有「月明洞隨筆手札」字樣。',
 'upper-volume-user',note='高視角斜向全景：上方白色退縮樓體、長條屋頂棚架與露台清楚；有掃描／網紋、積雪及浮水印。只參考幾何，不複製這些影像效果。')
g={'id':'02-hall-316',
 'name':'316會館／聖子愛之家／316紀念館',
 'aliases':['316空提紀念館',
 '聖子愛之家',
 '316會館',
 '316紀念館',
 '성자 사랑의 집',
 '성자사랑의집',
 '3.16관',
 '316기념관',
 '316휴거기념관'],
 'status':'身分已由使用者確認；照片與AI建模輸入包已整理，尚未建模',
 'identity_confirmed_by_user':'2026-11-11',
 'identity_evidence':[{'type':'user-confirmation',
 'date':'2026-11-11',
 'note':'使用者明示三個中文名稱指同一棟建築，並提供冬季照片。'},{'type':'published-name-equivalence',
 'url':D['tw-guide']['url'],
 'note':'中文導覽明列316空提紀念館又名聖子愛之家。'}],
 'missing_angles':['完整且較新的背立面，包含與山坡連接處',
 '垂直俯拍屋頂：各層退縮、露台邊界及棚架配置',
 '兩側完整短立面，樹木遮擋少，避免只拍到前轉角',
 '入口、下層出入口、弧形基座與坡道的完整連接',
 '可靠總長、總深、總高；官方柱徑約1m可作次級比例參考，非本案實測'],
 'photos':photos,
 'parts':['三層主體及玻璃立面',
 '16根大型外柱與柱頭柱腳',
 '綠色大屋簷與外廊',
 '上部白色退縮量體',
 '屋頂露台與長條棚架',
 '下方基座、階梯／坡道；分開處理'],
 'model':None}
g.pop('model')
if (O/'model/model.json').exists():
 g['model']=json.loads((O/'model/model.json').read_text());g['status']='本機Blender簡化初稿完成，待外形確認'
(O/'references.json').write_text(json.dumps(g,ensure_ascii=False,indent=2));m=json.loads((R/'manifest.json').read_text());m=[g if p['id']==g['id'] else p for p in m];(R/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
confirmed=json.loads((R/'confirmed.json').read_text());confirmed['landmark_ids']=list(dict.fromkeys(confirmed['landmark_ids']+[g['id']]));confirmed.setdefault('additional_confirmations',[]);item={'date':'2026-11-11',
 'id':g['id'],
 'aliases':g['aliases'],
 'note':'使用者提供冬季圖並確認同名建築。'}
confirmed['additional_confirmations']=[p for p in confirmed['additional_confirmations'] if p.get('id')!=g['id']]+[item];(R/'confirmed.json').write_text(json.dumps(confirmed,ensure_ascii=False,indent=2))
# Exact source copies for the user to submit, not synthetic multiview images.
pack=O/'upload-pack';pack.mkdir(exist_ok=True)
choices=[('official-spring',
 '01-front-main.jpg',
 '首選；較平視正面全景'),('official-corner-a',
 '02-front-corner-A.jpg',
 '第二視角；有透視縮短'),('official-sky',
 '03-front-corner-B.jpg',
 '另一側前角；非背面'),('official-pillar',
 '04-column-detail.jpg',
 '柱與簷底細節；不要填背面欄'),('user-winter',
 '05-upper-volume-winter-user.jpg',
 '上部量體參考；忽略雪、網紋與浮水印'),('festival-31',
 '06-rooftop-terrace.jpg',
 '露台棚架參考；不作整體主圖')]
records=[]
for id,dest,role in choices:
 p=next(p for p in photos if p['id']==id);shutil.copy2(R/p['file'],pack/dest);records.append({'upload_file':dest,
 'reference_id':id,
 'recommended_use':role,
 'source_page':p['source_page'],
 'source_image_url':p['image_url'],
 'photo_date':p['photo_date'],
 'source_sha256':p['sha256']})
(pack/'sources.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
# Contact sheet for choosing references, never passed off as a real multiview capture.
font=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',20);sheet=Image.new('RGB',(1440,690),
 '#edf0e4')
for i,(_,file,label) in enumerate(choices):
 im=Image.open(pack/file).convert('RGB');im.thumbnail((460,285));x=i%3*480;y=i//3*345;sheet.paste(im,(x+(480-im.width)//2,y+38));draw=ImageDraw.Draw(sheet);draw.text((x+12,y+8),file,fill='#24493f',font=font);draw.text((x+12,y+319),label[:22],fill='#24493f',font=font)
sheet.save(O/'recommended-views.jpg',quality=90)
# Gallery stays offline and retains date/role/source distinctions.
parts=[]
for p in photos:
 source='<a href="'+h(p['source_page'])+'" target="_blank">來源頁</a>' if p['source_page'] else '使用者提供；原拍攝者與拍攝日期未知'
 parts.append('<figure><a href="photos/'+pathlib.Path(p['file']).name+'"><img loading="lazy" src="photos/'+pathlib.Path(p['file']).name+'" alt="'+h(p['visual_review'])+'"></a><figcaption><b>'+h(p['id'])+'</b> <span>'+h(p['role'])+'</span><p>'+h(p['visual_review'])+'</p><small>'+str(p['width'])+' × '+str(p['height'])+' · 拍攝日期未知 · 頁面日期 '+h(p.get('publication_date') or '未標示')+'</small><p>'+source+'</p></figcaption></figure>')
style='body{margin:0;background:#f3f2e8;color:#294239;font:16px/1.7 -apple-system,"PingFang TC",sans-serif}header{background:#24493f;color:white;padding:40px max(24px,calc((100vw - 1280px)/2))}header a{color:#dff1bb}main{max-width:1280px;margin:auto;padding:24px}h1{font-size:34px;margin:8px 0}h2{margin-top:35px}a{color:#327653}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px}figure{margin:0;background:white;border-radius:14px;overflow:hidden}figure img{width:100%;height:265px;object-fit:contain;background:#e6e9df}figcaption{padding:15px}figcaption p{font-size:14px}small,span{color:#788371;font-size:12px}aside{border-left:3px solid #9caf7d;background:#e5eada;padding:16px 20px}.overview{width:100%;border-radius:12px}.buttons a{display:inline-block;padding:10px 16px;margin:4px 8px 4px 0;border:1px solid #b8caa7;border-radius:8px;background:white}'
page='<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>316會館｜AI建模照片與資料</title><style>'+style+'</style><header><a href="../index.html#02-hall-316">← 地標總圖冊</a><h1>316會館 · 聖子愛之家 · 316紀念館</h1><p>同一建築，身分已確認。先選對照片，再交給3D建模AI。</p></header><main><div class="buttons"><a href="316-hall-ai-reference-pack.zip">下載6張精選照片包 ZIP</a><a href="upload-pack/START-HERE.txt">上傳順序與建模提示</a><a href="README.md">建築特徵與來源說明</a></div><h2>建議先用這6張</h2><img class="overview" src="recommended-views.jpg" alt="六張照片的選圖聯絡表"><aside><b>單張生成：</b>先試01；若背景讓AI混入湖岸或樹木，再換02。<br><b>自由多圖參考：</b>先用01＋02＋03，上部量體可加05。04與06作人工細節核對。<br><b>前／後／左／右固定欄位：</b>目前沒有完整背面，勿把正面斜角硬填成背面，也不要把六張聯絡表當成一張實拍輸入。</aside><h2>外形必留</h2><p>長方形三層主體、前方8根與兩側各4根大型石柱（來源列16根）、退在柱廊後的玻璃立面、綠色大簷帶、上方白色退縮量體、屋頂露台與長條棚架。柱間與下方開放處保留空隙；不要生成三角山牆或傳統八角亭屋頂。</p><h2>尚缺的資料</h2><ul>'+''.join('<li>'+h(x)+'</li>' for x in g['missing_angles'])+'</ul><h2>全部18張參考</h2><p>含日景、細節、環境、夜景與2013年施工局部。施工與夜景不建議混入同一次幾何重建。拍攝日期未知時不以發布日代替。</p><div class="grid">'+''.join(parts)+'</div><p>照片原檔未修改；未上傳任何AI、未生成模型、未改遊戲。來源照片保有原著作權，公開使用與第三方上傳請確認權限或換成自有照片。</p></main></html>'
if (O/'model/model.json').exists():page=page.replace('未上傳任何AI、未生成模型、未改遊戲。','未上傳第三方AI；已另行建立本機模型初稿，未改核心遊戲。').replace('<h2>建議先用這6張</h2>','<aside>已完成本機建模初稿：<a href="../models.html#02-hall-316">查看模型與四面預覽</a> · <a href="model/landmark.glb">GLB</a> · <a href="model/landmark.blend">Blender檔</a>。尺寸與背面仍為估計；已放入核心地圖月明湖東側，位置與尺寸仍待精確核對。</aside><h2>建議先用這6張</h2>')
(O/'index.html').write_text(page)
report={'date':'2026-11-11',
 'building_identity':'user confirmed; independently linked by Chinese organization guide',
 'reference_photos':len(photos),
 'selected_upload_photos':len(records),
 'blocked_downloads':[x for x in candidates if 'error' in x],
 'duplicates_excluded':['official-view02_01.jpg identical to official-spring'],
 'excluded_from_album':['front2013-01 near-duplicate landscaping',
 'rear2013-01 and rear2013-02 mainly construction/rocks',
 'tw-guide-24 distant context'],
 'photo_edits':False,
 'ai_uploads':0,
 'game_modified':False};(O/'research-log.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('Hall references:',len(photos),
 'selected:',len(records))
