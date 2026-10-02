# 專題狀態與交接記錄（供 Codex）

最後核對：2026-10-02

## 2026-10-02 變更：雙鏡頭人物照片保存及配對核對

- `live_site/dual_server.py`：每次 `/api/start` 建立 `person_tracking/live_captures/<時間戳>/`；處理執行緒對每個鏡頭的每個 `status=confirmed` Track ID 首次出現時裁切人物框，存為一張 JPEG，並更新 `manifest.json`。原始連續影格仍只在記憶體中。`/api/live` 新增 `session`、`saved_people`、`matched_pairs`；`/api/photo/A|B/<track_id>` 只讀取目前工作階段已登記的照片，不接受任意檔案路徑。Host/Origin 防護及 loopback 限制保留。
- `live_site/dual_index.html`：顯示本次已保存照片；對 `confirmed_candidate` 且有 P 標籤、兩側照片均存在的配對，保留 A/B 並排照片、ID 與分數供人工檢查。新工作階段清空頁面舊卡片，但不刪硬碟照片。照片 DOM 節點不隨每次輪詢重建，避免反覆下載 JPEG。
- `.gitignore` 排除 `person_tracking/live_captures/`；相機照片與 manifest 不上傳 GitHub。限制：只存每個已確認 Track ID 的首張裁切照，並非連續錄影；遮擋/重建 ID 可使同一人有多張。P 是衣著外觀候選而非身分確認，人工仍須核對。ModelSim 不在即時網站迴圈中。
- 驗證：`live_site/test_dual_server.py` 以合成影格確認 A/B JPEG 各只存一張、manifest 及 P 配對含兩張照片 URL；單元測試 PASS。重啟本機服務後用實體鏡頭 2/1 檢查 `/api/live` 為 live、雙側人物照片有保存、`/api/photo/A/1` 回傳 JPEG 200、瀏覽器照片載入無破圖。當次多人場景只見 ambiguous 候選，尚無真實 P 配對可供現場人工正誤核對；並排照片的資料流程由合成測試確認，實機配對展示仍待兩鏡頭出現滿足門檻的同一人。

## 2026-10-02 變更：跨鏡頭外觀分數修正

- 使用者提供同一人出現在兩台鏡頭、A 鏡頭只見部分身體的截圖，舊版網頁分數約 0.367。舊特徵使用 192 格 HSV 直方圖，且取上下兩區較低的交集分數，對曝光及視角裁切敏感。
- `person_tracking/dual_camera.py` 改用 15 維平滑色彩統計：低彩度區依明暗柔性分配，彩色區依相鄰色相格分配；`cross_camera.py` 的總分改為上區 75%、下區 25% 的交集加權和。保留 0.72 門檻、互為最佳、次佳差 0.08 與三次連續確認。
- 對提供的截圖框位置離線重算，同一人約 0.84；圖中藍衣及白衣其他人物約 0.46、0.60。單張截圖有框線與壓縮，僅為針對該例的檢查，未建立一般化準確率。單元測試含明暗改變、只見上半身、黑白差異、上下衣交換及配對規則。
- 同步移除 `sequential_handoff.py` 對舊 192 維特徵的硬編碼，特徵庫依偵測結果的形狀建立；其 JSON 輸出欄位改為 `upper_lower_color_histograms`。既有外部讀取舊欄位的程式須對應更新。
- 重啟本機雙鏡頭服務後，以鏡頭 2/1 驗證 `/api/live` 為 live，兩側都有人物偵測；當次候選分數約 0.62–0.85，多人外觀相近的候選被標為 ambiguous，沒有被強制賦予 P 身分標籤。背景 AI 約 1.8 FPS。這是現場功能檢查，未逐一標記每個人的真實身分。

## 2026-10-02 變更：雙鏡頭即時 localhost 儀表板與實機驗證

- 新增 `影像處理/ModelSim_YOLOX_PersonTracking/live_site/dual_server.py`、`dual_index.html` 與 `start_dual.ps1`。Server 僅綁定 `127.0.0.1:8766`，以雙 DirectShow capture、兩個獨立 `Tracker` 和既有 `CrossCameraMatcher` 在記憶體中處理畫面；`/api/live` 回傳兩張 JPEG、各側人物和候選配對。閒置 10 秒後釋放兩台鏡頭。
- 實機確認鏡頭 0（Integrated Camera）與鏡頭 1（Logitech C270）可同時擷取 30 張 640×480 影格。兩側各自送入 `run_rtl`，均回傳 `PERSON_RTL_PASS: 30 person/empty regions`，ModelSim 編譯／模擬為零 error、零 warning。該批沒有 confirmed P 候選；這是外觀門檻未連續滿足的結果，非擷取或 RTL 失敗。
- 網頁即時模式不呼叫 ModelSim，避免在每一幀阻塞瀏覽器畫面；ModelSim 驗證仍由 `run_dual_camera.ps1 -Rtl` 的離線擷取流程負責。
- 儀表板初版把 AI 完成後的註記影格直接當作串流來源，雙鏡頭 CPU 推論約 1.7 FPS 時造成頁面卡頓。現改為 capture thread 每 0.1 秒最多 JPEG 編碼一次並即時回傳最新 A/B 影格，process thread 只更新人物／候選 metadata；`dual_index.html` 以 DOM overlay 繪製框線。實測網頁畫面約 9 FPS、背景 AI 1.6 FPS、AI 延遲約 0.7 秒。框線可比底圖落後一個推論循環，屬刻意的延遲／視覺流暢度取捨。

## 重要：目前最新版本在哪裡

使用者確認的最新工作方向，以及本機檔案/執行記錄所支持的最新整合版，源自 `C:\Users\USER\Desktop\codex\專題\modelsim_draft\`；已同步至本倉庫 `影像處理/ModelSim_YOLOX_PersonTracking/`。後續應以該路徑為共享程式碼基線，較早的 8×8 合成 testbench 不得覆蓋它。

2026-09-30 已把單鏡頭、雙鏡頭、RTL 與即時網站的必要原始碼同步進共享路徑。YOLOX 35 MB 權重、公開測試圖片、相機實拍圖、生成報告畫廊、ModelSim WLF/transcript 和本機 OpenCV binaries 均排除；以 `person_tracking/setup_assets.ps1` 下載模型及公開測試圖片，模型 SHA-256 會核對。`modelsim_draft` 本身不是 Git checkout；原始執行紀錄仍只存在本機，本次只同步程式/文件並整理可重建安裝方式，沒有上傳相機影像。

## 接手與同步規則

1. 每次工作先檢查共享倉庫 `git fetch origin`、目前本機/遠端分支與狀態，再檢查 `modelsim_draft` 最新檔案和結果時間；先判斷哪裡有較新的程式/紀錄。
2. 進行程式修改前，先明確選定最新源碼基線並檢視差異；不確定時保留兩邊，不做整批覆蓋。
3. 程式碼改動要同步至共享 GitHub `main`，同一變更更新本文件及 `PROGRESS_FOR_HUMANS.md`，提交並推送。
4. 模型權重和生成的個人相機/人物影像不要加入 Git；使用 `.gitignore` 與 `setup_assets.ps1` 的 hash 驗證下載模型。
5. 區分原始碼檢閱、已有 ModelSim/測試紀錄、USB 實拍，以及雙實體鏡頭驗證；不可互相代替。

## 最新整合版的組成（本機 `modelsim_draft`）

### 單鏡頭人物偵測、追蹤與 ModelSim RTL

使用說明：`modelsim_draft/person_tracking/README.md`；共享驗證摘要：`person_tracking/verification_report.json`。HTML 報告仰賴本機相機影格資料，僅留在來源機器。

- `person_tracking/pipeline.py`：使用 OpenCV Zoo 的 YOLOX ONNX 模型在 CPU 偵測人物；專題自寫 `Tracker` 依位置與 HSV 外觀做短期關聯、確認/維持/超時管理，輸出暫時性的 track ID。這不是 YOLOX 自帶的跨鏡頭 Re-ID。
- `person_tracking/person_roi_stream.v`：接收 640×480 完整 RGB888 影格（307,200 pixels/frame）及人物框座標，逐像素累積框內上/下兩區 8 色統計。這是 ModelSim RTL 特徵處理，外部偵測框由 CPU YOLOX 提供。
- `person_tracking/person_feature_compare.v`：比較同一 track ID 前次與本次的上下區域主色/比例特徵；最多 35 個百分點差異。
- `person_tracking/tb_person_roi.v`：將完整 RGB 與框座標交給 RTL。驗證報告記載每幀處理完 307,200 pixels；RTL testbench 暫存各 ID 歷史特徵供比較，範圍 ID 1–4095。
- `person_tracking/run_*` 與 `modelsim_draft/run_person_tracking.ps1`：拍攝/影像序列轉換、ModelSim 批次執行與輸出結果。

### 雙 USB 鏡頭候選配對

共享程式路徑：`影像處理/ModelSim_YOLOX_PersonTracking/`。操作文件 `person_tracking/DUAL_CAMERA.md`；入口 `run_dual_camera.ps1`；主要邏輯 `person_tracking/dual_camera.py`、`person_tracking/cross_camera.py`。

- `dual_camera.py` 使用兩個不同 USB 裝置索引，各自擷取 640×480 影格、呼叫相同 YOLOX detector、維護兩個互相獨立的本地 tracker；可用 `-Rtl` 對 A/B 各自執行 ModelSim ROI 特徵驗證。
- `cross_camera.py` 是自寫 Python 外觀候選配對：人物框中央 60% 寬度、上下區 HSV 直方圖；兩區相似度至少 0.72、雙方互為最佳候選且與次佳差至少 0.08，連續三次確認才分配 P 候選標籤。
- A:track_id 與 B:track_id 是鏡頭內局部 ID；P 標籤只代表同時觀測時衣著外觀相似候選，不是身份判定。
- 不是 YOLOX/CNN Re-ID，不含離開 A 後再於 B 出現的歷史資料庫；相機 `grab/retrieve` 只縮小主機讀取間隔，沒有硬體同步保證。整批先擷取再處理，沒有即時雙鏡頭 FPS 聲明。

### 單鏡頭即時網站

- `live_site/server.py` 直接匯入 `person_tracking/pipeline.py` 的 `Detector` 與 `Tracker`。它是既有偵測/追蹤器的 localhost 顯示介面，不另寫第二份推論器，也不在即時迴圈呼叫 ModelSim。
- `GET /api/health` 回報服務名稱/版本；`GET /api/live` 回傳狀態、人物框/ID、影格、FPS 與延遲；`POST /api/start`、`POST /api/stop` 控制相機。Host/Origin 僅允許 localhost/127.0.0.1；約 10 秒無頁面 heartbeat 後釋放相機。
- `live_site/README.md`、`start.ps1`、`index.html` 是說明、啟動器與 UI。歷史 `verification.json` 記錄 health、origin guard、停止、閒置釋放及 live frame integration check 通過；本次沒有重新連 USB 相機或啟動服務。

### 共享包的執行環境

- `requirements.txt` 宣告 NumPy/OpenCV Python 套件；`assets/yolox.py` 是 OpenCV Zoo 模型前處理/推論包裝；`setup_assets.ps1` 取得 YOLOX ONNX 及公開測試圖片並校驗模型 SHA-256。
- 檔案最初在使用者 Codex runtime 環境完成；`run_person_tracking.ps1`、`run_dual_camera.ps1`、`live_site/start.ps1` 現可用 `PROJECT_PYTHON` 或 PATH 的 `python`，並保留 Codex runtime 後備位置。ModelSim executable 可設 `MODELSIM_VSIM`，亦可從 PATH 解析，否則保留原安裝路徑後備。
- 本次只檢閱和同步程式碼，未安裝 dependencies、下載模型或執行腳本；以上安裝/可攜式 fallback 在本次未重新驗證。

## 已有驗證紀錄及其邊界

以下是本機保存的 2026-09-25 記錄，不是本次重新執行：

- ModelSim RTL `PERSON_RTL_PASS`：5 個人物/空景 ROI 手算案例，transcript 為零 compile error/warning。
- USB 單鏡頭實拍兩輪，共 240 幀，均為原生 640×480；報告記載 YOLOX 每輪 120/120 偵測，track ID 1 連續，ModelSim 每輪 120/120 特徵逐筆核對通過，完整 RGB 每幀 307,200 像素。
- 網路照片序列：兩張人物照片、三個亮度層級、每組七個位置；主要人工標記 105 次全匹配、無 ID 切換。三組黑/白/水果無人負例沒有誤報。追蹤單元邏輯 6 項 PASS。
- 已知漏抓：bus 圖中左側大幅裁切的人物，在 21 張變換影格只偵測到 4 張；這些未計入 105 次主要標記，因此不可宣稱任意畫面零漏抓。
- 雙鏡頭整合只看到兩個 `dual_runs` replay 紀錄，各 8 幀，來源是同一 USB 單鏡頭兩輪的已保存影格。兩組 A/B ModelSim RTL 都各核對 8 個 ROI PASS；其中一組有 1 幀出現確認的 P 候選。`dual_camera_capture_completed=false`，沒有接兩台實體攝影機的驗證結果。

## 共享倉庫內其他原型（不是最新整合版）

- `影像處理/MCDPT_Verilog_Two_Image_ReID/` 是 8×8 合成 RGB 色彩分類/閾值原型，最新倉庫提交歷史曾切換至 `person_color_feature.v`、`person_matcher.v` 與 `tb_two_camera_color.v`。它沒有 CPU 偵測器、短期 tracker、完整解析度串流或本機雙 USB 流程。
- MCDPT 為概念參考；舊 8×8 原型不等於 CNN/OpenVINO 深度 Re-ID。

## 專案來源與共享範圍盤點（2026-09-30）

- 最新可執行整合程式仍以 `影像處理/ModelSim_YOLOX_PersonTracking/` 為準；舊 8×8 Verilog 原型保留作歷史脈絡，不得誤稱為最新流程。
- `tools/` 收錄本機專題中的 PDF 頁面抽取、摘要/逐行說明與程式碼截圖輔助工具；`build_line_explanations.py` 預設引用未共享的舊 Vivado RTL，因此僅供歷史參考。其他工具需搭配使用者提供的來源檔或 PDF；目前沒有把論文 PDF 一起放入倉庫。
- `references/MCDPT/` 收錄本機專題引用的 MCDPT 參考實作子集，僅供閱讀，並非本專題執行相依；其上游 README 含 MIT 授權與引用資訊。
- `deliverables/presentations/` 收錄四份本機簡報成品。簡報 OOXML metadata 僅顯示 `Walnut Exporter`，沒有個人帳號名稱；這些是舊原型簡報，不代表最新 ModelSim 實作。
- `deliverables/synthetic-test-patterns/` 收錄四張早期 testbench 的 8×8 合成圖樣；不是相機影像或真實人物照片。
- 舊 `影像處理/MCDPT_FPGA/` EGo1/Artix-7 Vivado 原型已從目前共享檔案樹移除，因使用者明確限定不共享該 Vivado 程式碼；本機原始目錄保留。這次採一般刪除提交，未改寫 Git 歷史，因此較早提交仍包含該原型。
- 明確未納入：`verilog_demo/` Vivado 專案與截圖、`automation/join-weekly-google-meet.ps1`、Codex/應用程式狀態檔、Vivado/XSim 執行日誌、`.Xil`/`build`/套件快取、論文 PDF、個人相機影像、模型權重與生成模擬資料。這些分別是先前明確排除的 Vivado 內容、私人/無關資料、第三方文件或可由原始碼重建的暫存輸出。
- `output/rca_report/` 的畫面截圖未加入；它含本機路徑文字。`.codex-finalizer/` 內簡報候選稿與驗證中介檔和交付簡報重複，未加入。
- `modelsim_draft/person_tracking/verification_report.html` 會連結本機相機影像資料夾，單獨搬入後會形成失效/隱私風險連結，因此只分享其驗證 JSON 摘要，不分享該 HTML 和影像資料夾。

### 2026-09-30 共享內容整理

- 新增 `PROJECT_CONTENTS.md` 作為完整範圍索引、`tools/` 專題工具、`references/MCDPT/` 授權參考程式，以及簡報和合成 test pattern 等交付素材。
- 移除目前分支上的 `影像處理/MCDPT_FPGA/`，避免目前共享檔案樹包含使用者排除的 Vivado 原型；本機原始檔未刪除，Git 舊歷史仍可見。
- 更新本文件、人類摘要及 `影像處理/README.md`，並保留 ModelSim/YOLOX 整合版為唯一最新實作基線。

## 2026-09-30 變更紀錄：同步最新整合版本

- 核對共享遠端分支、本機 `modelsim_draft` README、RTL、單鏡頭驗證 JSON/HTML、ModelSim transcript、雙鏡頭程式/兩組 replay summary，以及即時網站狀態。
- 同步單鏡頭 YOLOX + 自寫短期追蹤 + 完整 640×480 ModelSim ROI RTL、雙 USB 外觀候選配對、本機即時網站及早期 RTL 基準原始碼。
- 增加可攜式 Python/ModelSim 執行路徑選擇、requirements 與模型/公開測試圖片下載腳本。該程式碼包尚未在本次重新執行模擬、相機或網站驗證。
- 排除大型模型權重、公開/私有圖片、相機輸出、生成報告畫廊、WLF 與本機 OpenCV 執行二進位；細節見專案 `.gitignore`。

## 2026-10-02 變更紀錄：單鏡頭 A→B 時序特徵交接

- 新增 `person_tracking/sequential_handoff.py` 與根目錄啟動器 `run_sequential_handoff.ps1`。預設使用同一台 640×480 USB 攝影機，0–10 秒標為 A，10–11 秒切換空檔，第 11 秒起標為 B，B 段再執行 10 秒；時間均可用參數調整。
- A 段用既有 YOLOX 偵測與自寫 tracker。對每個已確認 A track，計算中央 60% 人物框的上下區 HSV 直方圖並累積平均；切換時將特徵庫寫到本機 `person_tracking/runs/handoff_<timestamp>/camera_a_feature_gallery.json`，並重置 B 段局部 Tracker 以模擬新鏡頭 ID。
- B 段仍用同一 YOLOX 與全新 Tracker；新觀測與凍結 A 特徵庫透過既有 `CrossCameraMatcher` 比對。兩區相似度門檻 0.72、互為最佳候選、與次佳差至少 0.08，連續 3 次才顯示 `P<n> SAME-CANDIDATE`。逐影格匹配及摘要寫入本機 `handoff_matches.json`、`summary.json`；不保存影像，輸出路徑在 `.gitignore` 忽略的 `person_tracking/runs/`。
- 預覽視窗顯示 A/B 標籤、局部 track ID 和候選結果；`-NoDisplay` 可純文字執行，按 `q` 可提早結束。預設流程需同一人持續出現在畫面中；若 A 段沒有足夠已確認的 track，B 不會產生候選。
- 此設計測試保存特徵、重置 tracker、時間交接後重新關聯的資料流程；由於同一鏡頭視角/裝置不變，不能證明雙實體鏡頭視角、光照、色彩差異下可正確配對，更不能宣稱人物身分辨識已完成。
- 程式新增後已用本機 USB camera 0 跑完一次 21.125 秒現場流程：A 43 幀、切換 27 幀、B 45 幀；A/B 偵測數皆 0、A 特徵庫 0 個，沒有候選結果。因此此次只證明相機擷取迴圈及時間切段結束，無法判定特徵交接是否成功，也不能說辨認失敗。執行時畫面中未確認有可偵測人物。結果 JSON 在本機 `modelsim_draft/person_tracking/runs/handoff_20261002_100707/`，沒有保存/上傳影像。
- 第一次由 PowerShell 啟動時選到 WindowsApps Python alias，啟動失敗；`run_sequential_handoff.ps1` 已調整為優先選 Codex bundled Python，再退回 PATH，後續現場重跑應使用此啟動器。
- 需要同一人完整出現在 A 與 B 畫面中重跑，才可得到 `candidate_found` 或「B 有人物但未達配對」的有效結果。既有 2026-09-25 雙 USB replay 數據是歷史紀錄，不是此新模式的驗證。
