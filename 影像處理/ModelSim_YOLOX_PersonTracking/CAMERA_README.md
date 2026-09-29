# USB 攝影機：完整 640×480 逐幀比對

新增人物偵測與追蹤版本：執行 `run_person_tracking.ps1`，請看 [人物操作說明](person_tracking/README.md) 與 [實拍驗證報告](person_tracking/verification_report.html)。本文的 `capture_camera.ps1` 仍為整幅畫面比對，用於保留原先基準測試。

攝影機保存 640×480 PNG，ModelSim 也使用完整 640×480 RGB，每幀共 307,200 個像素，不縮圖、不抽樣。比較來源仍為同一台攝影機的相鄰影格。

在此資料夾的 PowerShell 執行：

```powershell
.\capture_camera.ps1 -Frames 90
```

先擷取並保存每張照片與 RGB 資料，再執行 ModelSim。程式會核對攝影機實際回傳尺寸；若不是 640×480 就報錯，避免悄悄縮放。可用 `-Camera 1` 選另一個裝置；`-Gui` 可在模擬成功後開啟波形。

## ModelSim 處理方式

- `color_feature_stream.v` 每個有效時脈接收一個 RGB 像素，按照由左至右、由上至下順序輸入。
- 每幀上半部 640×240，下半部 640×240，各統計 153,600 個像素的八色分布。
- 累計完整 307,200 個像素後，輸出上下半部主色、百分比與 feature_valid。
- `tb_camera_file.v` 保留上一幀特徵，和下一幀比對，產生 CSV。
- Python 使用全部原始像素獨立計算預期結果，再逐對核對 ModelSim 輸出。

這裡「全解析度」指全像素參與顏色特徵統計；判斷方式仍為上下半部主色與占比，沒有改成逐像素差分或影像身分辨識。

## 輸出檔案

每次結果位於 `camera_runs/日期_時間`：

- `frames`：完整原始 PNG。
- `pixels.rgb`：無標頭二進位 RGB888，一像素 3 bytes，一幀 921,600 bytes，逐幀連接。90 幀約 82.9 MB。
- `manifest.json`：輸入尺寸、像素數、時間与是否為舊照片重播。
- `comparison.csv`：相鄰影格序號、特徵、color_similar。
- `verification.json`：完整解析度及逐對核對結果。
- `report.html`：逐幀照片和比對表。
- `transcript`、`vsim.wlf`：模擬紀錄與特徵波形。為控制檔案大小，不記錄每個像素的完整波形。

2026-09-23 的舊測試結果使用 8×8，保留作歷史紀錄，不代表 640×480 的驗證結果。

## 範圍

目前比較全畫面的上下兩半，尚未加入人物偵測、人物框、遮罩與追蹤。因此 color_similar=1 只表示顏色特徵相近，不能確認是同一個人。攝影機拍攝、磁碟寫入與模擬是分階段執行，尚未保證即時 FPS 或硬體端無丟幀。照片只保存在本機。
