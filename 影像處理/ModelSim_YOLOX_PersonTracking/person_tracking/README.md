# 人物偵測、短期追蹤與 ModelSim 人物特徵

雙 USB 鏡頭草稿已新增，請看 [DUAL_CAMERA.md](DUAL_CAMERA.md)。原本單鏡頭流程保持可用。

資料流程：USB 攝影機原生 640×480 → YOLOX 人物框 → 短期追蹤 ID → 人物框座標及完整 RGB 影格 → ModelSim → 每個 ID 的上下區域主色與比例、前次同 ID 的顏色比對。

## 執行

在上一層 `modelsim_draft` 的 PowerShell：

```powershell
.\run_person_tracking.ps1 -Mode camera -Frames 90
.\run_person_tracking.ps1 -Mode web
```

## 兩板 Wi-Fi 偵測資料交換（Linux）

`peer_protocol.py` 是兩塊 PYNQ-ZU 之間的第一個、可獨立驗證的
TCP 資料協定。它只傳送人物框、confidence、local track ID、frame ID、
capture timestamp 與影像尺寸，不把高頻寬原始影像假裝成必要資料。
schema 固定為 `pynq-person-detections-v1`；目前只接受 `person`，並在
接收端驗證座標、尺寸、類別與封包大小，才寫入最新 JSON。

板 B（接收端）：

```sh
python3 peer_protocol.py receive --bind 0.0.0.0 --port 8790 --output peer_latest.json
```

板 A（傳送端，`frame.json` 必須符合上述 schema）：

```sh
python3 peer_protocol.py send --host <board-b-wifi-ip> --port 8790 --input frame.json
```

這個模組目前經本機 loopback TCP 與 schema unit tests 驗證；尚未在兩塊
實體 PYNQ-ZU 的 Wi-Fi 上驗證，也尚未直接接上 YOLOX/YOLOv8/DPU detector。

第一行從 USB 攝影機新拍 90 張；第二行使用下載的公開人物照片做平移序列和空白負例。每次結果都放入 `person_tracking/runs` 的新資料夾，`report.html` 可直接看人物框和 ID。

另有 `validate_camera.py` 會先連續擷取兩輪各 120 張，再處理；`validate_web.py` 會使用兩張人物照片、三種亮度和每組七個位置，搭配手標人物框核對 IoU 與 ID 切換，並測試水果照片等負例；`test_tracking.py` 測試追蹤交會、遮擋、離開，以及手算 ROI 硬體案例。

只有一台 USB 攝影機時，可從專案根目錄執行 `run_sequential_handoff.ps1 -Camera 0 -ASeconds 10 -TransitionSeconds 1 -BSeconds 10`，以前 10 秒模擬鏡頭 A，第 11 秒起模擬鏡頭 B。程式會保存 A 段已確認追蹤目標的上下區 HSV 外觀特徵、重置 B 段局部 tracker，再檢查同一人是否能重新關聯。需同一人持續留在畫面中；這是單鏡頭時間切段模擬，不等於雙實體鏡頭驗證。

## 檔案分工

- `pipeline.py`：人物偵測、位置／HSV 外觀追蹤、原圖與標註存檔、RTL 驗證。
- `person_roi_stream.v`：每拍一個原始 RGB 像素，掃完整 307,200 個像素，僅人物框內參與直方圖。以人物框高度的中點分上下區域；奇數高度多一列歸下區域。
- `person_feature_compare.v`：比較同 ID 前次與本次主色、比例差（最多 35 個百分點）。
- `cross_camera_pair_matcher.v`：接收外部已選定的一組 A/B 人物 24-bit 特徵；兩側特徵有效、上下主色相同且兩個比例差都不超過 35 個百分點時視為本影格候選，連續三個已觀測候選才輸出 `confirmed`。缺少配對或任一不相似影格會歸零連續計數。它是可綜合的單一候選確認核心；不含 YOLOX、人物框產生、多人物互為最佳或次佳差距仲裁，這些仍需由 CPU/上層排程器處理。
- `tb_cross_camera_pair_matcher.v`：上列核心的獨立 RTL regression，涵蓋第三次命中確認、已確認飽和、色碼／比例不符、缺失影格、黑色服裝特徵及 reset。
- `tb_person_roi.v`：讀完整 RGB 與人物框，驗證資料長度、有效訊號與像素數；每個 ID 的历史特徵目前由 testbench 保存，支援 ID 1–4095。

模型來源：[OpenCV Zoo YOLOX](https://github.com/opencv/opencv_zoo/tree/main/models/object_detection_yolox)，Apache 2.0，完整授權見 `assets/LICENSE_YOLOX`。模型 SHA-256：`c5c2d13e59ae883e6af3b45daea64af4833a4951c92d116ec270d9ddbe998063`。公開照片來源存於 `assets/sources.json`；水果負例來自 [OpenCV samples](https://github.com/opencv/opencv/blob/master/samples/data/fruits.jpg)。照片僅用於本機測試，沒有上傳。

## 介面與結果

## PYNQ CPU YOLOv8 fallback

The requested detector target is YOLOv8. `assets/yolov8.py` accepts the raw
Ultralytics detection output in either `(1,84,8400)` or `(1,8400,84)` form,
keeps only COCO class 0 (`person`), de-letterboxes it and emits the existing
`box`/`confidence` contract. It first uses ONNX Runtime and falls back to
OpenCV DNN only when ONNX Runtime is unavailable. The PYNQ image's OpenCV
4.5.4 cannot parse this current YOLOv8 ONNX graph, so ONNX Runtime is required
for this CPU fallback.

On a development PC run `python assets/prepare_yolov8_onnx.py` after installing
the recorded Ultralytics exporter environment. It emits ignored
`assets/yolov8n.onnx`, with IR metadata limited to version 9 for the verified
PYNQ ONNX Runtime 1.16.3. On the current PYNQ, `numpy==1.21.6` and
`onnxruntime==1.16.3` are installed in the `xilinx` user site. A live C270
320x240 frame completed CPU inference in 1.017 seconds; the test scene
contained no person, so it did not validate a positive detection. This is not
DPU/VART inference and does not replace the required B512 `.xmodel` flow.

## Two-board detection packets

`pynq_yolov8_peer.py` captures exactly one C270 per board, calls the default
YOLOv8/tracker pipeline, and sends compact person metadata through
`peer_protocol.py`; it never transfers raw frames. On board A, run a receiver
on board B first, then run:

```sh
python3 person_tracking/pynq_yolov8_peer.py \
  --board-id pynq-a --peer-host <board-b-wifi-ip> --camera 0
```

For a finite bring-up run use `--frames 1`. The board-side loopback test has
verified one C270 frame through YOLOv8, tracker, TCP framing and strict schema
validation. It is not evidence of Wi-Fi, a second board, or a positive person
detection in a live camera frame.

攝影機輸入不縮小：640×480 只在偵測模型底部補至 640×640，不縮圖。公開照片為了固定測試座標，先等比例放入 640×480 畫布；這是測試照片的前處理，和攝影機原生解析度不同。

`detections.json` 保存每幀人物框、信心值、追蹤 ID 及 tentative/confirmed 狀態。兩次觀測後為 confirmed。漏抓時保留短期追蹤狀態最多 8 幀，但不把預測位置假裝成實際偵測結果；超時後新出現的人使用新 ID。

`features.csv` 保存 ModelSim 結果：frame、track_id、valid、feature、top_pixels、bottom_pixels、previous_available、color_similar。沒有人物的影格仍送入 RTL，必須輸出 invalid 與零特徵。人物框的像素數、特徵與比較結果都由獨立 Python 計算逐筆核對。

`feature` 的六位十六進位依序為：上區域色碼、下區域色碼、上區域百分比兩位、下區域百分比兩位。色碼 0 黑、1 白／淺灰、2 紅、3 綠、4 藍、5 黃、6 棕／橘、7 其他。

## 實作界線

這是電腦端 AI 偵測／追蹤與 ModelSim 特徵處理的整合。YOLOX 沒有被轉成 Verilog；完整 FPGA 相機介面、AI 推論與追蹤歷史記憶體尚未實作。流程先拍完再處理，沒有宣稱即時 FPS。

人物框不等於精確人體分割，框內仍可能有背景；人物只有上半身入鏡時，框的上下兩半也不等於解剖上的上半身／下半身。追蹤 ID 是單次序列內的暫時編號，不是人臉辨識或跨攝影機身分。穿著相似、嚴重遮擋、快速移動或長時間離開都可能造成追蹤錯配。公開 bus 照片最左邊大幅裁切的人物仍有漏抓，驗證報告另列，不能把主要人物測試通過說成任意畫面都零漏抓。

可用 `python evaluate_cross_camera.py` 重跑三個固定的 matcher 回歸案例（同色連續確認、不同色拒絕、競爭者判為 ambiguous）。它會輸出 `cross_camera_evaluation.json`；這是合成門檻回歸，不是真人雙鏡頭準確率。
