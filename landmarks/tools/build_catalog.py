"""Build an offline catalogue. No network, login, framework, or server needed."""
import json,pathlib,html,shutil
R=pathlib.Path(__file__).resolve().parents[1];D=json.loads((R/'manifest.json').read_text())
h=html.escape
confirmed=json.loads((R/'confirmed.json').read_text()) if (R/'confirmed.json').exists() else {'landmark_ids':[]}
for g in D:
 if g['id'] in confirmed['landmark_ids']:
  g.setdefault('identity_confirmed_by_user','2026-11-10')
  if g['id']=='10-round-hill-pavilion':g['name']='圓山八角亭／둥그레산 팔각정'
  model=R/g['id']/'model/model.json'
  if model.exists():g['model']=json.loads(model.read_text());g['status']='已確認身分；簡化初稿待風格確認'
  else:g.setdefault('status','已確認身分；照片整理')
  (R/g['id']/'references.json').write_text(json.dumps(g,ensure_ascii=False,indent=2))
(R/'manifest.json').write_text(json.dumps(D,ensure_ascii=False,indent=2))
modelcount=sum('model' in g for g in D)

cards=[];nav=[]
for g in D:
 nav.append('<a href="#%s">%s</a>'%(g['id'],h(g['name'])))
 photos=[]
 for p in g['photos']:
  if 'download_error' in p:continue
  notes=p.get('visual_review',p.get('evidence_note',p['source_caption']))
  photos.append('''<figure><a href="{f}" target="_blank"><img loading="lazy" src="{f}" alt="{a}"></a><figcaption><b>{id}</b><p>{note}</p><small>拍攝日期：未知<br>頁面／活動日期：{date}<br>原始尺寸：{w} × {hh}</small><details><summary>來源與原圖說</summary><p>{alt}</p><a target="_blank" href="{src}">來源／說明</a> · <a target="_blank" href="{url}">線上原圖</a><p class="rights">{rights}</p></details></figcaption></figure>'''.format(f=h(p['file']),a=h(notes),id=h(p['id']),note=h(notes),date=h(str(p.get('publication_date') or '未標示')),w=p['width'],hh=p['height'],alt=h(p['source_caption']),src=h(p['source_page'] or p['file']),url=h(p['image_url'] or p['file']),rights=h(p['rights'])))
 extra=''
 if g['id']=='09-camel-rock':extra='<aside>先看 route-12 的延伸岩體、lake-18 的表面特徵。兩張都有遮擋或裁切，缺少適合直接生成完整單體的照片。<a href="09-camel-rock/upload-pack/README.md">上傳準備說明</a></aside>'
 if g['id']=='02-hall-316':extra='<aside>使用者已於2026-11-11確認316會館、聖子愛之家、316紀念館為同一棟建築。<a href="02-hall-316/index.html">查看18張專屬圖冊與6張AI上傳照片包</a>。</aside>'
 if g['id']=='10-round-hill-pavilion':extra='<aside>候選名稱：둥그레산 팔각정。2011 年階梯完工照片，使用者已於2026-11-10確認地標身分。現況、位置與實測尺寸仍未確認。</aside>'
 if 'model' in g:extra+='<aside>已完成照片輔助的簡化初稿，待確認風格。<a href="models.html#'+g['id']+'">看四面預覽與模型檔</a></aside>'
 cards.append('<section id="%s"><div class="section-title"><span>%s</span><h2>%s</h2><em>%d 張參考</em></div>%s<div class="missing"><b>待補／待核對</b><ul>%s</ul></div><div class="grid">%s</div></section>'%(g['id'],g['id'][:2],h(g['name']),len(photos),extra,''.join('<li>'+h(x)+'</li>' for x in g['missing_angles']),''.join(photos)))
style='''*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f4f2e9;color:#253e38;font-family:-apple-system,BlinkMacSystemFont,"PingFang TC",sans-serif;line-height:1.6}header{padding:52px max(24px,calc((100vw - 1280px)/2));background:#24493f;color:#fff}header small{letter-spacing:3px;color:#b8d9b5}h1{font-size:40px;margin:12px 0}header p{max-width:850px;color:#e2ebe2}a{color:#397363}header a{color:#dcf6bb}.stats{display:flex;gap:28px;flex-wrap:wrap;margin-top:25px}.stats b{font-size:27px;display:block}.stats span{font-size:13px;color:#c9dbd1}main{max-width:1328px;margin:auto;padding:25px 24px}nav{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 32px}nav a{text-decoration:none;padding:7px 12px;border:1px solid #c9d7c6;border-radius:18px;background:#fff;font-size:13px}section{scroll-margin-top:20px;margin-bottom:60px}.section-title{display:flex;align-items:center;gap:14px;flex-wrap:wrap}.section-title span{background:#dce6ca;border-radius:14px;padding:9px 14px;font-weight:bold}h2{font-size:25px;margin:0}.section-title em{font-size:13px;font-style:normal;color:#718078}aside,.missing{border-left:3px solid #b2be8b;background:#e8ecdf;padding:14px 18px;margin:16px 0}.missing{background:transparent;border-left-color:#c9d0bd}.missing ul{margin:5px 0;padding-left:22px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px}figure{margin:0;background:#fff;border-radius:16px;overflow:hidden;border:1px solid #e0e3d8}figure img{width:100%;height:240px;object-fit:contain;background:#e8e9e2;display:block}figcaption{padding:18px}figcaption p{margin:8px 0;font-size:14px}small,.rights{font-size:12px;color:#778078}details{border-top:1px solid #e7e9e1;margin-top:12px;padding-top:10px;font-size:13px}summary{cursor:pointer}footer{padding:24px;border-top:1px solid #d8dfd0;color:#728077;font-size:13px}@media(max-width:600px){h1{font-size:29px}header{padding:30px 22px}.grid{grid-template-columns:1fr}}'''
page='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>月明洞｜地標參考圖冊</title><style>{style}</style><header><small>WOLMYEONGDONG · REFERENCE LIBRARY</small><h1>先看真實樣貌，再準備模型</h1><p>十組地標的公開照片與缺圖清單。以可愛簡化、外形可辨識為方向；已開始製作使用者確認的五組地標，模型與照片分開標示；八角亭、316會館與湖畔石景已配置到核心區；其他模型待後續確認。</p><div class="stats"><div><b>10</b><span>地標資料組</span></div><div><b>{count}</b><span>參考圖片</span></div><div><b>0</b><span>目前身分待核對</span></div><div><b>{modelcount}</b><span>簡化模型初稿</span></div></div></header><main><p><a href="models.html">查看五組地標模型初稿與操作說明 →</a></p><p>點圖片可開啟完整尺寸；圖說依實際畫面補註。發布日與拍攝日分開記錄，未知角度不以 AI 補成現場證據。照片著作權與使用限制見每張來源。</p><nav>{nav}</nav>{cards}</main><footer>整理日期：2026-11-11。離線可瀏覽，沒有將照片上傳 AI 服務。機器可讀資料：<a href="manifest.json">manifest.json</a> · <a href="README.md">流程與服務說明</a></footer></html>'''.format(style=style,count=sum(len(g['photos']) for g in D),nav=''.join(nav),cards=''.join(cards),modelcount=modelcount)
(R/'index.html').write_text(page)
# Byte-for-byte source copies: no invented background or missing geometry.
pack=R/'09-camel-rock/upload-pack';pack.mkdir(exist_ok=True)
for src,dst in [('route-12.jpg','01-context-original.jpg'),('lake-18.jpg','02-detail-original.jpg')]:shutil.copy2(R/'09-camel-rock/photos'/src,pack/dst)
(R/'review-queue.json').write_text(json.dumps({'phase':'model-style-review','ai_attempts':0,'reason':'使用者無法登入Meshy；以照片輔助的Blender網格製作初稿。','core_map_landmarks':['10-round-hill-pavilion','02-hall-316','04-god-waterfall'],'identity_confirmed':confirmed['landmark_ids'],'pending_identity':[],'models_require_style_review':[g['id'] for g in D if 'model' in g]},ensure_ascii=False,indent=2))
print('Built offline catalogue:',sum(len(g['photos']) for g in D),'images;',modelcount,'model drafts')
