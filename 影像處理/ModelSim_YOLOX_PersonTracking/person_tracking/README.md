# 人物偵測、短期追蹤與 ModelSim 人物特徵

雙 USB 鏡頭草稿已新增，請看 [DUAL_CAMERA.md](DUAL_CAMERA.md)。原本單鏡頭流程保持可用。

資料流程：USB 攝影機原生 640×480 → YOLOX 人物框 → 短期追蹤 ID → 人物框座標及完整 RGB 影格 → ModelSim → 每個 ID 的上下區域主色與比例、前次同 ID 的顏色比對。

## 執行

在上一層 `modelsim_draft` 的 PowerShell：

```powershell
.\run_person_tracking.ps1 -Mode camera -Frames 90
.\run_person_tracking.ps1 -Mode web
```

第一行從 USB 攝影機新拍 90 張；第二行使用下載的公開人物照片做平移序列和空白負例。每次結果都放入 `person_tracking/runs` 的新資料夾，`report.html` 可直接看人物框和 ID。

另有 `validate_camera.py` 會先連續擷取兩輪各 120 張，再處理；`validate_web.py` 會使用兩張人物照片、三種亮度和每組七個位置，搭配手標人物框核對 IoU 與 ID 切換，並測試水果照片等負例；`test_tracking.py` 測試追蹤交會、遮擋、離開，以及手算 ROI 硬體案例。

只有一台 USB 攝影機時，可從專案根目錄執行 `run_sequential_handoff.ps1 -Camera 0 -ASeconds 10 -TransitionSeconds 1 -BSeconds 10`，以前 10 秒模擬鏡頭 A，第 11 秒起模擬鏡頭 B。程式會保存 A 段已確認追蹤目標的上下區 HSV 外觀特徵、重置 B 段局部 tracker，再檢查同一人是否能重新關聯。需同一人持續留在畫面中；這是單鏡頭時間切段模擬，不等於雙實體鏡頭驗證。

## 檔案分工

- `pipeline.py`：人物偵測、位置／HSV 外觀追蹤、原圖與標註存檔、RTL 驗證。
- `person_roi_stream.v`：每拍一個原始 RGB 像素，掃完整 307,200 個像素，僅人物框內參與直方圖。以人物框高度的中點分上下區域；奇數高度多一列歸下區域。
- `person_feature_compare.v`：比較同 ID 前次與本次主色、比例差（最多 35 個百分點）。
- `tb_person_roi.v`：讀完整 RGB 與人物框，驗證資料長度、有效訊號與像素數；每個 ID 的历史特徵目前由 testbench 保存，支援 ID 1–4095。

模型來源：[OpenCV Zoo YOLOX](https://github.com/opencv/opencv_zoo/tree/main/models/object_detection_yolox)，Apache 2.0，完整授權見 `assets/LICENSE_YOLOX`。模型 SHA-256：`c5c2d13e59ae883e6af3b45daea64af4833a4951c92d116ec270d9ddbe998063`。公開照片來源存於 `assets/sources.json`；水果負例來自 [OpenCV samples](https://github.com/opencv/opencv/blob/master/samples/data/fruits.jpg)。照片僅用於本機測試，沒有上傳。

## 介面與結果

攝影機輸入不縮小：640×480 只在偵測模型底部補至 640×640，不縮圖。公開照片為了固定測試座標，先等比例放入 640×480 畫布；這是測試照片的前處理，和攝影機原生解析度不同。

`detections.json` 保存每幀人物框、信心值、追蹤 ID 及 tentative/confirmed 狀態。兩次觀測後為 confirmed。漏抓時保留短期追蹤狀態最多 8 幀，但不把預測位置假裝成實際偵測結果；超時後新出現的人使用新 ID。

`features.csv` 保存 ModelSim 結果：frame、track_id、valid、feature、top_pixels、bottom_pixels、previous_available、color_similar。沒有人物的影格仍送入 RTL，必須輸出 invalid 與零特徵。人物框的像素數、特徵與比較結果都由獨立 Python 計算逐筆核對。

`feature` 的六位十六進位依序為：上區域色碼、下區域色碼、上區域百分比兩位、下區域百分比兩位。色碼 0 黑、1 白／淺灰、2 紅、3 綠、4 藍、5 黃、6 棕／橘、7 其他。

## 實作界線

這是電腦端 AI 偵測／追蹤與 ModelSim 特徵處理的整合。YOLOX 沒有被轉成 Verilog；完整 FPGA 相機介面、AI 推論與追蹤歷史記憶體尚未實作。流程先拍完再處理，沒有宣稱即時 FPS。

人物框不等於精確人體分割，框內仍可能有背景；人物只有上半身入鏡時，框的上下兩半也不等於解剖上的上半身／下半身。追蹤 ID 是單次序列內的暫時編號，不是人臉辨識或跨攝影機身分。穿著相似、嚴重遮擋、快速移動或長時間離開都可能造成追蹤錯配。公開 bus 照片最左邊大幅裁切的人物仍有漏抓，驗證報告另列，不能把主要人物測試通過說成任意畫面都零漏抓。
