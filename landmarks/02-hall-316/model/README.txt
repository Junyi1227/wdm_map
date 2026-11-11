316會館／聖子愛之家：可愛簡化模型初稿

以照片輔助在本機Blender建模，沒有使用Meshy、Tripo或付費生成服務。沒有將照片投影成貼圖。

landmark.glb：完整模型，可匯入GDevelop、Blender及支援glTF的工具。
landmark.blend：原生可編輯檔。LANDMARK editable model集合下有五個組件子集合；相機、燈光、PREVIEW地板只供預覽。
base_stairs.glb：基座、前階梯與欄杆。
columns.glb：16根外柱，正面8根、兩側各4根。
main_body.glb：退在柱列後方的玻璃主樓；柱廊有真正空隙。
canopy.glb：綠色大屋簷與簷底。
roof_terrace.glb：上部白色退縮樓體、露台與棚架。
front/right/back/left.png：四個方向預覽；背面是簡化推定。
perspective.png：較低視角的正面斜角預覽。
model.json：來源照片ID、估計尺寸、面數及限制。
validation.json、gdevelop-validation.json：模型與GDevelop實際載入／鏡頭操作檢查。

全部GLB保留共用原點。整體模型與五個拆件二選一使用，不能同時重疊放置。
公尺單位：工作比例約寬36.2m、含前階梯深25.82m、高22.45m，非實測。
13928三角面，16根獨立外柱，約1.15m前柱廊淨距，PBR純色材質無外部貼圖依賴。
玻璃以不透明藍綠材質呈現，方便遊戲穩定顯示，沒有製作室內或可行走碰撞體。
完整背面、內部格局、上層精確退縮及局部基座曲線仍待照片補充。

GDevelop以Z向上使用此GLB時，物件模型初始X旋轉90度，原點與中心點都選ModelOrigin。
獨立測試專案：landmarks/preview/project.json，按4選316會館；左鍵旋轉、右鍵平移、滾輪縮放、Home重設。
已放入核心地圖月明湖東側，正面朝湖；位置依既有OSM輪廓，尺寸為估計。

手動修改以Blender檔為準，另存版本。build_hall316_model.py是初稿生成工具，重跑會覆寫模型與預覽，不要在手動修改後直接執行。
