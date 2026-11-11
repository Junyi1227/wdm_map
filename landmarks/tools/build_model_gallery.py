import pathlib,json,html
from PIL import Image,ImageDraw,ImageFont
R=pathlib.Path(__file__).resolve().parents[1];h=html.escape
cards=[];tiles=[]
folders=['09-camel-rock','10-round-hill-pavilion','08-prayer-hill']
if (R/'02-hall-316/model/model.json').exists():folders.append('02-hall-316')
if (R/'04-god-waterfall/model/model.json').exists():folders.append('04-god-waterfall')
def source_links(folder,ids):
 refs=json.loads((R/folder/'references.json').read_text());mapping={p['id']:p['file'] for p in refs['photos']};links=[]
 for id in ids:
  if id in mapping:links.append('<a href="'+mapping[id]+'">'+h(id)+'</a>')
 return '　'.join(links)

for folder in folders:
 d=json.loads((R/folder/'model/model.json').read_text());base=folder+'/model/'
 imgs=''.join('<figure><a href="%s%s.png"><img src="%s%s.png" alt="%s"></a><figcaption>%s</figcaption></figure>'%(base,k,base,k,n,n) for k,n in [('front','主視角'),('right','右側'),('back','背面（推定）'),('left','左側')])
 links=' · '.join('<a href="'+base+f+'">'+h(f)+'</a>' for f in ['landmark.glb','landmark.blend','model.json']+d.get('modular_exports',[]))
 cards.append('<section id="%s"><h2>%s</h2><p>%s 三角面 · 公尺單位 · 原生可編輯網格</p><p>%s</p><aside>%s</aside><p>%s</p><div class="grid">%s</div><p>%s</p><details><summary>核對照片</summary>%s</details></section>'%(folder,h(d['name']),format(d['triangles'],','),h(d['method']),h(d['estimate']),h(d['unknown']),imgs,links,source_links(folder,d['sources'])))
 im=Image.open(R/folder/'model/front.png').convert('RGB');im.thumbnail((560,476));tile=Image.new('RGB',(600,560),'#f1f2e6');tile.paste(im,((600-im.width)//2,50));tiles.append(tile)
style='''body{margin:0;background:#f3f2e9;color:#294239;font:16px/1.7 -apple-system,"PingFang TC",sans-serif}header{background:#24493f;color:white;padding:42px max(24px,calc((100vw - 1280px)/2))}header a{color:#ddf1c6}h1{font-size:35px;margin:8px 0}main{max-width:1280px;margin:auto;padding:24px}section{margin:30px 0 55px}h2{font-size:27px}a{color:#36775b}aside{padding:14px 20px;background:#e3e8d7;border-left:3px solid #96ab7c}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}figure{margin:0;background:white;border-radius:14px;overflow:hidden}img{width:100%;display:block}figcaption{padding:10px 18px;color:#657364}details{font-size:14px}@media(max-width:650px){.grid{grid-template-columns:1fr}}'''
(R/'models.html').write_text('<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>月明洞｜地標模型初稿</title><style>'+style+'</style><header><a href="index.html">← 照片圖冊</a><h1>地標模型與四面預覽</h1><p>照片輔助建模 · 身分已確認 · 外形與風格待確認 · 八角亭、316會館與湖畔石景已置入核心區，其他模型獨立檢視</p></header><main><aside><b>可轉動的模型：</b>用 GDevelop 開啟 <a href="preview/project.json">landmarks/preview/project.json</a>，按預覽。1 駱駝石、2 八角亭、3 禱告山、4 316會館；左鍵旋轉、右鍵平移、滾輪縮放，Home重設。以下是四面靜態預覽。</aside><p>沒有使用 Meshy／Tripo，沒有扣點或付費。背面、遮擋處與尺寸是明示的推定，不是實測重建。Blender 檔中的 LANDMARK 集合是模型，PREVIEW 集合與燈光、相機僅供預覽。</p>'+''.join(cards)+'</main></html>')
fontpath='/System/Library/Fonts/STHeiti Medium.ttc'
try:font=ImageFont.truetype(fontpath,30)
except:font=ImageFont.load_default()
sheet=Image.new('RGB',(600*len(folders),560),'#f1f2e6')
for i,(tile,name) in enumerate(zip(tiles,['駱駝石','圓山八角亭','禱告山','316會館'])):
 ImageDraw.Draw(tile).text((26,14),name,fill='#24493f',font=font);sheet.paste(tile,(i*600,0))
sheet.save(R/'models-overview.jpg',quality=90)
print('Model gallery and overview built')
