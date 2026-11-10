# 駱駝石：待核對的上傳素材

**目前未生成模型。** 兩張照片為公開參考原檔的逐位元副本，未修圖或補出背面。輸入照片的第三方AI使用權未確認，暫不要直接上傳；可換成你有權使用、角度相同且更完整的實拍照。

- `01-context-original.jpg`：來源為官方體驗路線頁 `route-12`，1200×899。可看沿草坡延伸的岩體，有人群與樹木遮擋。
- `02-detail-original.jpg`：來源為中文導覽 `lake-18`，600×391。表面及細長延伸處清楚，但整體出框、解析度有限，不能直接當完整單體的唯一輸入。
- 逐張原網址及來源頁見 `../references.json`；`../photos/` 保留完整來源庫。

## 需要補的照片

先一張：光線均勻、岩體完整入鏡、遮擋少，四周留白，盡量避免超廣角。再補左右側、背面、基底及一個可確認的比例尺（例如已量測物件）。不必一次拍完所有地標，先只補駱駝石即可。

## 可複製的造型要求

> Cute simplified low-poly natural rock formation based on the reference photo. Preserve the elongated irregular gray bedrock ridge, sloping top silhouette, and broad grounded base. This is Wolmyeongdong's Camel Rock, a natural rock embedded in a hillside. Do not turn it into a camel animal, statue, four legs, eyes, a saddle, or decorative objects. Keep only the rock; exclude people, trees, signs, lawn and sky. Simplify stone colors to a warm neutral gray with restrained lighter facets. Unknown hidden sides are provisional, not a surveyed reconstruction.

提示文字不能修正缺失幾何，也不能保證服務遵從。先看輪廓，再考慮貼圖。

## 帳號可用之後

1. 確認照片使用權與主要視角；進入 [Meshy 圖片轉3D](https://www.meshy.ai/zh-Hant/workspace?sidebar=model&model-tab=image-to-3d&from=home)。
2. 明確選 **Meshy 6 Lite**，確認免費可下載、當次點數及公開／授權設定。若免費方案不允許所需操作，先停下，不升級。
3. 僅用有權使用的完整單體照生成。其他參考角度作人工核對；不要假設免費方案提供多視角生成。
4. 最多先試兩次，記錄結果。不能接受的項目：變成駱駝動物、基底漂浮、主岩體缺段、四周草地整片黏住、背面重大破面。
5. 可用才下載GLB，進Blender清理與減面；未知尺寸明確註記估計。另存.blend與四面預覽。
6. 在獨立GDevelop測試專案確認載入、材質及重開，之後請你確認風格；本輪不修改既有遊戲。
