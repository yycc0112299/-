# 專題進度（重點版）

## 2026-11-06：改為 Vivado Block Design + Vitis 控制架構（進行中）

- 已新增 PYNQ-ZU 的 `pynq_zu_usb_video` Vivado Block Design 腳本：保留板上 USB0（MIO 52–63）與 USB1（MIO 64–75）給 Zynq PS，並加入 AXI DMA、DDR HP0、AXI-Lite bbox mailbox、frame-ID GPIO、64-bit 雙 RGB stream 與 IRQ。USB C270 的 D+/D− 是 PS USB 控制器接腳，不是可拉進 PL 的 GPIO。
- 本機 Vivado 2024.2 已實際完成 `validate_bd_design`；不代表相機影像、DMA、bitstream 或板端已完成。XSA 匯出已啟動，但 synthesis 子工作仍等待 Vivado queue，尚未產出 XSA。
- 已新增 Vitis C 控制核心與 host test，確認每個 frame 會依序寫 frame ID、bbox 資料，最後才 commit mailbox CONTROL。Vitis 實際 application 必須待 XSA 完成後以產生的 `xparameters.h` 編譯。
- 尚未完成：synthesis/implementation/XSA、Vitis BSP/application 實機編譯、USB UVC → DDR → DMA → PL 串流，以及雙 USB 鏡頭的實機頻寬問題。

## 2026-11-05：已完成換機前的 GitHub 交接整理

- 已盤點目前 `main` 與 GitHub `main` 相同，專題的程式、RTL、網站、啟動腳本、測試與交接文件都已在版本控制中；這次再補上明確的交接與忽略規則。
- 不會上傳 Vivado/XSim 日誌、模擬波形、暫存輸出、已簽名 PDF 預覽、硬體照片或本機網站日誌。它們不是執行專題所需原始碼，且可能含本機路徑或私人資料；未上傳不代表專題進度遺失。
- 換電腦後從 GitHub clone `main`，照詳細交接文件安裝 Python 套件與 YOLOX 模型，再先跑軟體／RTL 回歸。相機、PYNQ Linux、雙 USB 鏡頭與 FPGA 實機功能仍要在新環境各自重新驗證。

## 2026-11-05：已記錄板子展示計畫，尚未開始實作

- 未來展示會讓 PYNQ-ZU 接到區域網路，電腦瀏覽器開啟 `http://<板子-IP>:8766/`，查看兩個鏡頭畫面、人物框、追蹤編號，以及配對候選／確認結果。
- 預計先讓板上的 Python 網站讀 USB 鏡頭並顯示軟體結果，再接上 FPGA 的配對確認結果；UART 只看除錯文字，不用來傳即時影像。若要直接接螢幕，之後才另做 HDMI 畫面輸出。
- 目前這只是存到 GitHub 的工作計畫：尚未接板、尚未確認板子網路或相機、尚未產生/燒錄 bitstream，也尚未在板上實際看到畫面。

## 2026-11-04：YOLOX 已有可接 FPGA 的傳遞介面

- 保留 GitHub 先前已驗證的 Verilog：雙路人物框色彩特徵、跨鏡頭三次確認、640×480 模擬。
- 新增 PYNQ-ZU AXI4-Lite mailbox：Python YOLOX 可把每幀選定的 A/B bbox 和影格號寫入 FPGA；FPGA 只在相同影格開始時鎖住座標，避免錯影格或半寫入。
- 本機 Vivado mailbox 模擬 5 項檢查 PASS，整合 Verilog top 編譯成功；Python 寫入暫存器的合約測試也 PASS。
- 尚未上板：相機輸入、腳位/時脈、implementation/bitstream 與實機 MMIO 都未完成。YOLOX 仍在 CPU/PS，FPGA 只做接 bbox 後的 ROI 特徵及確認，不能說 YOLOX 已在 FPGA 推論。

## 2026-11-04：PYNQ-ZU 的 PS 與 Verilog 已可一起綜合

- 已建立 Zynq PS→AXI SmartConnect→自訂 YOLOX mailbox 的 Vivado Block Design；PYNQ Python 可使用的暫存器位址目前是 `0xA000_0000`。
- 補上同步 reset 後，Block Design 驗證通過；生成 wrapper 後，PYNQ-ZU 目標的 Vivado 綜合完成，結果為 0 error、0 critical warning。
- Windows 的專題資料夾路徑過長且含中文會造成 Zynq IP 生成失敗；腳本已改成預設把可丟棄的 Vivado 生成物放在短的 `%TEMP%/pynq_zu_rtl`，不影響 GitHub 原始碼。
- 尚未做相機輸入、腳位/XDC、implementation/bitstream、PYNQ overlay 或實機讀寫。因此這是「可綜合的硬體結構」，不是已經能在板子上看見雙鏡頭結果。

## 2026-11-04：雙鏡頭資料可由同一條 DMA 串流送進 FPGA

- 新增通用 64-bit AXI-Stream 入口：一個 DMA word 同時裝 A、B 兩個 RGB 像素，讓兩鏡頭像素保持同步；每 640×480 張影像自動形成一個 frame。
- Python 已能把兩張 RGB 影像打包到 PYNQ DMA buffer；Verilog 模擬 7 項檢查與 Python 打包測試都通過。
- 這可供未來的 USB/PS、CSI 或 HDMI 來源共用；還沒選定實體相機介面，也還沒接上 DMA/相機實機。

## 2026-11-04：PYNQ-ZU Vivado board file 已驗證

- 目標板確認為 TUL PYNQ-ZU（XCZU5EG-1SFVC784）。已從使用者下載的 Xilinx Board Store 解壓 board repository，並以 Vivado 2024.2 實測找到 `tul.com.tw:pynqzu:part0:1.1`。
- 新增可重跑的 `fpga/configure_pynq_zu_board.tcl`，它只設定目前 Vivado session 的 board repository，不修改 Vivado 安裝目錄。
- 大型第三方 `fpga/board_repos/` 已加入 Git ignore；尚未建立 bitstream、接通板端網路或驗證實體 PYNQ-ZU 開機。
- 新增 `fpga/create_pynq_zu_rtl_project.tcl`，以 PYNQ-ZU board part 建立 Vivado 2024.2 專案並加入目前的 ROI/候選 Verilog；本機已實跑成功建立專案。生成的 `fpga/build/` 不提交。尚未加入 PS block design、AXI、時脈/reset、XDC 或 bitstream。

## 2026-11-04：公開圖片 dataset 彙總評估

- 新增 `person_tracking/evaluate_detection_dataset.py`，讀取既有人工標註驗證報告並彙總 6 組 bus／zidane 亮度案例。
- 結果：105/105 個人工標註人物觀測配對成功，annotated recall=1.000、最低 IoU=0.855、ID switch=0，負例測試 PASS。
- 這是人物框／短期追蹤 dataset 評估，不是跨鏡頭真人身分配對準確率；後者仍需人工標記兩台鏡頭的同人／不同人資料。

## 2026-11-04：新增同人配對分數測試入口

- 新增跨鏡頭配對評估程式，可計算同一人判斷的 accuracy、precision、recall、F1、TP/TN/FP/FN，並檢查人物框座標最大誤差是否小於 20 px。
- 目前 4 筆範例回歸結果為 accuracy=1.000、F1=1.000、最大框誤差 8 px；這些是合成資料，只能證明程式可重跑，不能宣稱真人雙鏡頭準確率。
- 後續只要把 `person_tracking/matching_dataset.json` 換成實拍且人工標記「同人／不同人」的案例，再執行 `python evaluate_matching_dataset.py` 即可得到正式分數。

## 2026-11-04：EPFL 小型公開多鏡頭資料實測

- 使用 EPFL 公開資料的 939 個人工標註影格，實際跑專題 YOLOX；ground truth 1,302 框，預測 1,565 框。
- IoU>=0.5 配對 1,035，漏抓 267，誤抓 530；recall=0.7949、precision=0.6613、平均 IoU=0.7963、最低 IoU=0.5007，執行 133.84 秒。
- 另計算框座標誤差：平均 5.7932 px、最大 37 px；`<20 px` 門檻為 FAIL，不能宣稱全部人物框都在 20 px 內。
- 若依「物體位置」採用 matched box center 的 Euclidean distance，最大中心誤差為 19.5256 px、平均 2.9939 px，`center_error_pass=true`；報告同時保留嚴格四邊最大誤差 37 px，兩種指標不可混稱。
- 比較 Raw、EMA 0.25/0.5/0.75、median3 後，Raw YOLOX 最好；平滑法在非連續 EPFL 標註影格上使中心最大誤差升至 28.0401–43.5115 px，已排除。
- 新增相機框座標校正與底部邊界修正：用 80% calibration、20% held-out validation，`clamp=460` 的 validation 最大邊界誤差為 19 px，mean IoU=0.8164、recall=0.7993、precision=0.6847，正式低於 20 px。
- 結果為 `EPFL_DATASET_PARTIAL`，完整逐案例數字保存在 `person_tracking/epfl_dataset_evaluation.json`；這是外部資料實測，不是合成回歸。
## 2026-11-04：雙鏡頭候選確認 Verilog 核心

- 實際雙 USB 鏡頭 localhost 網站已啟動；白牆連續抽樣顯示兩側亮度接近，最新量測平均差約 1.1/255。這只驗證當時的影像一致性，不是人物配對準確率。
- 新增 Verilog `cross_camera_pair_matcher.v`：對上層已選定的一組 A/B 人物色彩特徵，連續三個相似且有效的觀測才確認候選；不相似或缺少配對時重置。新增測試平台後以這台電腦的 Vivado 2024.2 XSim 實跑 10 項檢查通過。
- 本核心目前使用既有的簡化 24-bit 主色／比例特徵；尚未搬移 Python 的 YOLOX、HSV 15-bin 相似度、0.72 分數、多人物最佳配對或上板相機介面。因此不能把這次模擬當成真人跨鏡頭準確率或 FPGA 實機完成。
- 新增 `dual_camera_roi_match_top.v`，將兩路同步 RGB 串流、CPU/YOLOX 提供的 A/B 人物框、兩個完整解析度 ROI 特徵核心及三次候選確認串接；已以 Vivado XSim 編譯通過。YOLOX 神經網路、不同時脈 USB 相機 frame buffer、bbox 傳輸及多人物仲裁仍未改成 Verilog。
- 新增完整 640×480 雙串流 testbench，實測三個連續相似人物框會在第三張確認，下一張不同色人物框會歸零；Vivado XSim 16 項檢查 PASS。這是合成像素與 bbox 的 RTL 模擬，不是實體 USB/FPGA 或 YOLOX 網路硬體驗證。
- `dual_camera.py` 現在會把 CPU/YOLOX 已選定的 A/B 配對輸出成每次執行的本機 `rtl_yolox_packets.json`：包含 frame、同步狀態、A/B track ID、bbox、確認狀態與相容的 24-bit RTL 色彩特徵。此檔是 Python 到 Verilog bbox 介面的資料契約，不包含影像，且尚未直接寫入 FPGA。

## 2026-11-03：無鏡頭等待中的公開 HTTPS 網站

- 在本機沒有 USB 鏡頭的狀態下，雙鏡頭網站仍可啟動並回報 `stopped`；這是等待未來插入鏡頭的正常狀態，不是架設失敗。
- 為 Cloudflare Quick Tunnel 增加明確的 `--allow-trycloudflare` 選項；只有啟用時才接受 `https://*.trycloudflare.com` 的頁面/API 請求，平時 localhost/LAN 的原有來源限制不變。
- 已用新產生的 Quick Tunnel HTTPS 連結驗證首頁、`/api/health` 和 `/api/live`；未啟動相機、未保存相機照片，也未提交 tunnel 網址或任何權杖。
- 新增一鍵遠端啟動器。它會保存 CameraA/CameraB 的等待設定，建立新的私有連結，但沒有鏡頭時仍不嘗試連線相機。

## 2026-10-31：這台電腦的可執行環境已複核

- Python、NumPy、OpenCV、YOLOX 模型和公開測試圖片都已可用，不需要再安裝；程式回歸共 24 項通過。
- Vivado 2024.2 已安裝，且有內建 xsim；但沒有找到 ModelSim，因此目前不能跑專案的 ModelSim 驗證入口。
- 現在可雙擊 `開啟VivadoXSim驗證.cmd` 使用已安裝的 Vivado XSim 跑相同 RTL 回歸；本機已跑完 7 張測試影格、89 項檢查並通過。這是 XSim 驗證，並不表示 ModelSim 已安裝。
- 目前 Windows 未偵測到可用相機，所以雙鏡頭網站尚未做實拍驗證。接上兩台相機後即可用 `啟動即時追蹤網站.cmd` 開啟 localhost 網站測試。

## 2026-10-30：第三台電腦的雙鏡頭網站啟動環境

- 第三台電腦已安裝正式 Python 3.12、NumPy 1.26.4、OpenCV 4.11.0，以及專題所需的 YOLOX ONNX 模型與公開測試素材；VS Code 已安裝 Python 擴充套件。
- 修正雙鏡頭啟動腳本：不再誤用 Windows Store 的空白 `python.exe` 啟動器，會優先尋找已安裝的 CPython；`啟動即時追蹤網站.cmd` 改為開啟雙鏡頭 localhost 儀表板（預設 `http://127.0.0.1:8766/`）。
- 此次只完成執行環境與啟動流程準備；尚未確認兩個實體 USB 攝影機、ModelSim 或 Vivado 的實機流程。

## 2026-10-15：可直接開啟的 ModelSim 自動驗證

- 新增 `影像處理/ModelSim_YOLOX_PersonTracking/開啟ModelSim驗證.cmd`，雙擊即開啟 ModelSim、執行測試並保留波形與結果。詳細操作見同目錄 `person_tracking/RTL_REGRESSION.md`。
- 本機 ModelSim SE-64 2020.4 實跑：7 張完整 640×480 合成影像、89 項檢查 PASS；編譯及模擬 0 errors / 0 warnings。涵蓋色彩特徵、人物框邊界、輸入暫停、連續影格及比較門檻。
- 本次沒有修改原本運算 RTL 或即時網站。這是上板前的功能驗證，尚未完成 PYNQ/EGo1 上板、YOLOX 硬體化或整套雙鏡頭判斷電路。

更新日期：2026-10-02

## 2026-11-03：保存鏡頭電腦公開啟動 Prompt

- 新增 `CAMERA_PC_PUBLIC_SETUP_PROMPT.md`，讓連 USB 鏡頭的電腦可以直接依 Prompt 啟動網站與 Cloudflare HTTPS 通道。
- Prompt 要求回傳 `private-link.txt`，並禁止公開 access token；完成仍須在非同一個 Wi-Fi 的手機實測。

## 2026-11-03：兩台電腦協作方式

- GitHub `main` 是程式同步來源；有鏡頭的電腦新增 `live_site/sync_camera_pc.ps1`，會先 `fetch`、`pull --ff-only` 再啟動雙鏡頭網站。
- 雙鏡頭服務新增可設定 LAN bind/allowed Host；鏡頭電腦可用 `-Bind 0.0.0.0 -AllowHost <鏡頭電腦IP>:8766`，另一台以瀏覽器開該網址看即時結果。
- GitHub 不承載即時影像；目前仍要求同一可信任 LAN 與鏡頭電腦防火牆允許 TCP 8766，未做公開網際網路部署。

## 2026-10-26：新增 PYNQ/EGo1 共用板級 RTL 邊界

- 新增 `影像處理/ModelSim_YOLOX_PersonTracking/fpga/roi_feature_board_top.v`，把現有 640×480 ROI 特徵 RTL 包成可接 PYNQ 或 EGo1 的同步串流核心。
- 新增 `fpga/README.md` 說明要接的 RGB/frame/bbox 訊號與後續 XDC/相機或 AXI adapter 工作。尚未宣稱已產生 bitstream、完成腳位約束或完成實體上板。

## 2026-10-26：新增可重跑的跨鏡頭 matcher 回歸評估

- 新增 `影像處理/ModelSim_YOLOX_PersonTracking/person_tracking/evaluate_cross_camera.py`，固定測試同色連續確認、不同色拒絕、相同外觀競爭者判為 ambiguous 三種情況，並輸出 `cross_camera_evaluation.json`。
- 本次合成回歸 3/3 PASS，另有既有 `test_cross_camera.py` 6/6 PASS。這是演算法門檻回歸，不是真人雙鏡頭準確率；PYNQ/EGo1 上板、標記影像準確率與雙實體鏡頭仍未完成。
- 完整 unittest discovery 目前因執行環境缺少 `cv2`，既有 camera/tracking 測試無法載入；未把缺少依賴誤報為測試通過。

## 最新進度

2026-10-02 完整同步盤點：現有程式、網站與先前進度已在 GitHub `main`；本次再補上尚未上傳的兩份精簡驗證紀錄（早期 8×8 ModelSim transcript、6 項追蹤測試 PASS 摘要），並更新內容索引與進度。採新增提交保留舊版，不強制覆蓋。人物照片、審核 manifest、模型權重及大量模擬／相機產物仍只留本機，沒有公開上傳；這些排除項目不等於專案進度遺失。

2026-10-02 人工審核按 ✓／✕ 後，配對照片和沒有其他待審核配對的對應人物縮圖約 5 秒後淡出、收起，讓畫面不再被舊照片佔滿；精簡審核數字及「查看／修改已審核照片」仍可重新展開。這只是網頁顯示，照片仍保存到按「停止雙鏡頭」時才清除。勾叉不訓練模型：✕ 僅排除本次同一組追蹤 ID，✓ 僅記錄人工判斷及凍結審核照片，準確率不會因此自動提高。6 項程式測試、網頁語法與五秒時間邊界測試通過；目前本機網站已提供新頁面，重新整理即可載入。此次尚未用真人雙鏡頭現場驗證淡出流程。

2026-10-02 停止雙鏡頭時，現在連本網站以前工作階段保存的人物照片也會清除。只刪本網站照片清單中登記的 A/B 人物 JPG；其他檔案和舊工作階段的說明／審核清單不動。即使網站已停止，再按一次停止也能清舊照片。

本機實際清理回報刪除 549 張；複查 8 個工作階段後人物 JPG 剩 0 張，8 份舊清單仍在，雙鏡頭已停止。

2026-10-02 改善側面照與人工核對：同一追蹤 ID 的照片會在較清楚、較完整或偵測到正面臉時更新，不再永遠使用第一張；即時配對會參考最近五次外觀特徵。人工審核區可自行選 A/B 兩張照片，按 ✓ 同一人或 ✕ 不是同一人，判斷只作用於本次連線；否決的那組 ID 不再自動配對。這不是人臉身分辨識，仍可能漏配或誤配。

若自動挑照角度仍不理想，可等人轉正、仍出現在畫面中時按「用目前畫面重拍並鎖定」；頁面重整不會清空本次審核或重啟鏡頭。

兩台實體鏡頭 2/1 的新版網頁已跑起來，照片與審核按鈕正常顯示；仍需由你親自對真實配對按 ✓／✕，目前沒有宣稱辨識準確率已經驗證。

2026-10-02 依使用者要求，「停止雙鏡頭」現在會停止鏡頭並清除**本次**由網站保存的人物 JPEG 和配對記錄；不刪以前工作階段或資料夾中的其他檔案。閒置自動停鏡頭不觸發清除。

實機以鏡頭 2/1 測試，停止後清除本次 17 張照片，先前照片資料夾保留；單元測試亦通過。

2026-10-02 雙鏡頭網頁新增本機人物照片留存：每個鏡頭的已確認追蹤 ID 首次出現時保存一張人物裁切照；產生 P 外觀配對候選後，頁面並排顯示兩張照片、A/B ID 和分數供人工核對。照片及 `manifest.json` 保存在本機 `person_tracking/live_captures/`，不會推到 GitHub。P 仍只是候選，可能誤配；追蹤 ID 重新建立時也可能為同一人再存一張。

合成測試已通過；實體鏡頭 2/1 已確認人物照片存檔並能在網頁正常顯示。現場多人畫面暫時只有模糊候選，沒有產生 P 配對，因此尚未以實際同一人的雙照片核對正誤。

最新整合版已上傳到 `影像處理/ModelSim_YOLOX_PersonTracking/`：OpenCV Zoo YOLOX 偵測人物，專題自寫短期追蹤維護追蹤編號，ModelSim 處理完整 640×480 人物框內的色彩特徵；另有雙 USB 鏡頭候選配對程式和本機即時追蹤網站。

新增單鏡頭 A→B 時序交接模擬：前 10 秒保存鏡頭 A 的人物外觀特徵，第 11 秒起重置追蹤器並以該特徵庫重新辨認 B 段人物。符合條件時標示 `SAME-CANDIDATE`。

2026-10-02 新增雙鏡頭 localhost 儀表板 `live_site/dual_server.py` 與 `dual_index.html`：可同時顯示 A/B USB 畫面、兩側本地 Track ID 及跨鏡頭外觀候選。實機以內建鏡頭與 Logitech C270 擷取各 30 張，兩側各完成 30 個 ROI 的 ModelSim 驗證 PASS；本次未產生已確認 P 候選。

儀表板後續改為「最新相機影格」與「背景 AI 標註」分離更新。實機頁面約 9 FPS，AI 約 1.6 FPS、延遲約 0.7 秒；影像不再等待 YOLOX 完成才更新。

同一人跨鏡頭截圖曾只有 0.367 相似分數。現將外觀特徵改為容忍曝光差異的平滑色彩統計，並提高上半身在總分中的比重；該張截圖離線重算約 0.84，圖中另外兩位不同衣著人物約 0.46、0.60。這些數字僅代表該張截圖，仍需更多已標記同／不同人影像檢驗誤配率。

## 驗證狀況

- 單鏡頭已保存兩輪 USB 實拍紀錄，共 240 張；偵測/追蹤及 ModelSim 特徵核對通過。
- 雙鏡頭程式已用兩台實體 USB 鏡頭各擷取 30 張；兩側 ModelSim ROI 驗證通過，但該批沒有確認的 P 候選。
- 單鏡頭 A→B 新程式已用 USB camera 0 跑完 21 秒；A、B 都沒有偵測到人物，因此沒有可判斷的配對結果。要確認功能，需讓同一人留在畫面中再跑一次。
- 雙鏡頭配對只是衣著外觀候選，不是身份辨識；整體流程也不是即時 FPGA AI 推論。

## GitHub 版本差異

先前已補上四份舊版專題簡報、早期測試用合成圖樣、文件整理工具與 MCDPT 授權參考程式，並從目前共享檔案樹移除舊的 Vivado FPGA 原型；本機檔案保留。更早的 Git 提交仍留有該原型。

論文 PDF、模型權重、個人相機影像、模擬暫存與私人/無關檔案沒有上傳。

詳細交接與數據見 [PROGRESS_FOR_CODEX.md](PROGRESS_FOR_CODEX.md)。

## 2026-11-05：以後每次進度都記錄並上傳

- 新增 `CONVERSATION_PROGRESS_LOG.md`：每次完成一個可交付進度，都會留下精簡摘要並與變更一起上傳 GitHub；不會上傳私人連結、帳密、個人影像或逐字聊天。
- 已確認目前本機 `main` 與 GitHub `main` 同步。最近的 PYNQ-ZU、IRQ 與雙 USB 部署工作都已有提交。
- 現有未追蹤檔是 Vivado/XSim 與本機網站的暫存日誌，不是漏傳的原始碼，會維持不公開。

## 2026-11-05：PYNQ-ZU bring-up 已燒入

- 已確認板子是 PYNQ-ZU，Vivado 透過 JTAG 看得到 `xczu5_0`。
- 已成功產生並透過 JTAG 下載 bring-up bitstream；Hardware Manager 顯示 `Programmed`。此設定斷電會消失，沒有改寫 SD 卡。
- 為了可產生安全 bitstream，暫時把尚未接好的影像輸入固定為 idle，且不把輸出接到未設定腳位；PS、20 MHz PL clock 與 AXI-Lite mailbox 都在設計內。
- 尚未完成真正的雙攝影機：仍要決定 CSI、HDMI 或 DMA/USB 的影像來源，加入對應硬體/IP/XDC，並在 PYNQ Linux 驗證 Overlay/MMIO 與影像資料流。

## 2026-11-05：換電腦也可直接部署到 PYNQ-ZU

- 新增一條可直接貼到新 Windows 電腦 PowerShell 的部署命令：從 GitHub clone 後，填入 PYNQ 的 IP，即可打包、SSH/SCP 傳送與解壓雙 USB 網站；不依賴目前電腦的 Vivado 暫存或既有 tarball。
- 可選擇立刻檢查兩支 USB 鏡頭各能讀取一張影格；若另有相符的 Overlay 檔，也可執行 AXI-Lite mailbox 的寫入／讀回檢查。
- 本機已實際驗證部署包可建立，內含網站、YOLOX ONNX、追蹤程式與板端驗證程式；尚未因板子仍未 SD 開機而進行 SSH、USB、Overlay 或瀏覽器實機驗證。

### 2026-11-05：新電腦模型自動補齊

- 盤點發現 YOLOX 模型依容量規則沒有上傳 GitHub；現在首次部署會自動下載官方 OpenCV Zoo 模型並核對 SHA-256，下載正確才會打包，因此新電腦不用手動找模型檔。
- 本機已核對現有模型雜湊及部署包內容；第一次部署電腦需可連網下載約 35 MB 模型。板子 SSH 與實機相機仍待 SD 開機後驗證。

### 2026-11-05：板端環境先檢查再碰鏡頭

- 部署命令新增系統檢查：先列出板端 Python、NumPy、OpenCV、模型與 PYNQ 套件狀態，再檢查兩支 USB 鏡頭，方便立即看出 SD 映像缺什麼。
- 本機已跑過此檢查與完整打包；本機沒有 PYNQ 套件屬預期。板子的實際套件和鏡頭仍待 SD 開機後檢查。

### 2026-11-05：離線軟體與 RTL 回歸重新驗證

- 雙鏡頭配對、特徵與追蹤的 Python 測試共 18/18 通過；網站人物照片／人工審核資料流程合成測試 6/6 通過。
- Vivado XSim RTL 回歸完成 7 個影格、89 個檢查，結果 PASS。這些是本機合成／模擬驗證，還不能取代 PYNQ、USB 相機或 Overlay 的實機測試。

### 2026-11-05：可重跑 FPGA 指令／中斷模擬

- 新增 Windows 一鍵 XSim 指令，可在沒有板子的電腦重跑 PYNQ mailbox、影格對齊與 IRQ 清除測試；本機結果為 9 個檢查全部通過。
- 同時更正文檔中先前誤寫的 5 個檢查數；實際 testbench 是 9 個。這仍是模擬，不代表板端中斷已實際觸發。

### 2026-11-05：全新 GitHub clone 部署包實測

- 已從 GitHub 的最新 `main` clone 到全新暫存資料夾，沒有手動放入模型；部署打包器自動下載 YOLOX 模型並成功建立含 11 個必要檔的板端 tarball。
- 因此「換電腦 clone 後直接貼部署命令」已在本機以乾淨 clone 實測通過。仍未接觸板子、SSH 或 USB 相機。

### 2026-11-05：準備 SD 開機後的驗證包

- 已產出 PYNQ Overlay 要用的 `.bit` 與 `.hwh` 配對檔，並加入板端 AXI-Lite 讀寫驗證程式；開發電腦的 Python 語法檢查通過。
- 現在 PYNQ 網頁 `192.168.3.1` 無法連線，因板子仍在 JTAG 階段且這台電腦目前是 `192.168.50.x` 網段。下一步必須切回 SD、重新開機，才可啟動 PYNQ Linux 並上傳/執行驗證。

### 2026-11-05：中斷與雙 USB 鏡頭網站

- 已補上 PS IRQ：feature 完成、跨鏡頭確認、命令遺失與 mailbox 覆寫都能觸發；程式可讀取並清除中斷。RTL 模擬通過，包含中斷拉高與清除。
- IRQ 版 bitstream 已完成時序/DRC/bitgen 檢查，並再次經 JTAG 成功燒入 PYNQ-ZU。
- 已製作 PYNQ Linux 用的雙 USB 鏡頭網站部署包；它包含現有 YOLOX、雙鏡頭網站、USB 鏡頭檢查程式與 overlay。
- 尚未在板上驗證：SD Linux、兩支已插入的 USB 鏡頭、YOLOX 推論與電腦瀏覽器畫面。USB 網站會先由 PYNQ 的 CPU 執行原本 Python 流程；目前影像尚未進 FPGA RTL。

### 2026-11-06：SD 卡已重新燒錄並驗證

- 已用 balenaEtcher 將官方 PYNQ-ZU v3.1.1 的 `pynq_zu_2025_09_25.img` 寫入確認過的 16 GB SD 卡；寫入後 Etcher 完整跑過驗證並顯示「燒錄成功」。
- 官方最新版的映像檔名就是 2025-09-25，且和電腦原有 v3.1.1 下載檔完全相同；因此不是因為下載到更舊／更新版本。
- Etcher 完成後已自動卸載 SD 卡。下一步是把卡插回板子、切到 SD、重新上電，確認紅色 PS ERR 是否消失；網站、相機與 FPGA overlay 尚未驗證。
- 本次燒錄與驗證紀錄已同步到共享 GitHub `main`。
## 2026-11-06：PYNQ Linux 與雙 USB 鏡頭實機部署

## 2026-11-06：Vivado USB/DMA 硬體重建（進行中）

## 2026-11-06：Vitis 控制程式已完成電腦端編譯

- 已安裝完整 Vitis Embedded，並把新的 PYNQ-ZU USB/DMA 硬體檔做成 A53 standalone 平台、FSBL 和控制程式 ELF；控制程式實際編譯成功。
- 發現 Windows 工作目錄太長會讓 Vitis 編譯失敗，專案現在提供短路徑的一鍵建置腳本，之後可重現產生 ELF。
- 尚未把這版硬體與 ELF 下載到板子；USB 雙鏡頭、DMA、FPGA 資料流和中斷都還沒有實機 PASS。
- 目前電腦看得到 JTAG 的 FTDI USB 裝置，但掃不到 PYNQ-ZU 晶片；重啟本機 Hardware Server 後仍一樣，所以尚不能下載硬體或控制程式到板子。

### 更新：Vitis 已實際控制 PYNQ-ZU

- 已確認 Vivado 能打開 PYNQ-ZU 的 JTAG target，並成功下載新的 USB/DMA FPGA bitstream。
- Vitis 已在板子的 A53 實際執行控制程式：寫入 frame ID 42 後，GPIO 與 FPGA mailbox 都讀回 42，代表 PS 到 FPGA 的控制線路真的通了。
- 現在尚缺 USB 相機實際取像、DDR/DMA 傳影格與 FPGA 影像運算；目前的 command 會等待尚未接上的影像資料流，這是預期狀態。

- USB 鏡頭會由 PYNQ-ZU 的 PS USB 接收，影格放到 DDR 後才經 DMA 送進 FPGA；不能把 USB 線直接接到 PL 影像腳位。
- 找到既有影像 RTL 在 100 MHz 跑不動，已改為 20 MHz；尚未產生可下載的新 bitstream。
- Vivado 目前被 module-reference 封裝快取錯誤卡住，尚未完成 Vitis 控制程式的實機建置。

- PYNQ-ZU 已可由 `192.168.3.1` 的 JupyterLab 操作；板端確認 Python 3.10.4、NumPy 2.1.5、OpenCV 4.5.4、PYNQ 3.1.1 與 YOLOX 模型皆可用。
- 專題雙鏡頭網站已實際部署至板子；系統與相機 preflight 曾通過，兩支鏡頭分別為 index 0 與 2，均成功讀取 640×480 影格。
- 修正網站對舊版 PYNQ OpenCV 的相容性、PYNQ 網址白名單與相機 index 被 API 重設的問題；網站健康檢查可從開發電腦取得成功回應。
- 啟動即時擷取後，核心回報 USB 頻寬不足並讓兩個 UVC 裝置斷線，目前 `/dev/video*` 不存在。因此尚未完成持續雙鏡頭串流或 YOLOX 人物偵測；需改善 USB 供電／改用不同 root hub 或降低相機頻寬後重新插拔，再重跑 preflight。

- 後續重新插拔後兩支 Logitech C270 再次出現並重跑 index 0/2 的 640×480 preflight PASS；網站以正確設定啟動後仍立刻回報雙鏡頭擷取中斷，未形成持續串流。這再次確認問題在 USB 傳輸資源，尚非軟體安裝或相機索引。
- 已額外嘗試雙路 MJPEG、320×240、10 FPS 的低頻寬模式，仍在同時擷取時中斷；目前不能在網站顯示雙路畫面，必須先改善 USB 實體拓撲／供電。

## 2026-11-06：Vivado USB/DMA 硬體檔完成

- 已把自訂影像 RTL 改成 IP Catalog 元件，避開 Vivado Windows module-reference 快取錯誤。
- 新的 PYNQ-ZU Block Design 已完整通過 Vivado 實作、DRC 和 bitstream，並成功輸出 Vitis 要用的 XSA；時序為正裕量。
- 這是硬體檔完成，不是雙鏡頭影像已跑通。下一步是用 XSA 建 Vitis 控制程式並以 JTAG 上板測試；USB 雙鏡頭同時串流的實體頻寬問題仍待解決。

## 2026-11-06：Vitis 工具環境阻礙已定位

- 已用新的 XSA 實際啟動 Vitis 建 platform，但本機 Vitis 2024.2 缺少完整 embedded flow（包含 `xsct`），且原本的 Lopper 安裝不完整。
- 補齊 Lopper 後，Vitis 已能繼續到 SDT 生成，但仍無法建立 platform；所以 Vitis 控制程式尚未編譯、更沒有上板。
- 下一步是修復／補安裝完整 Vitis Embedded Development 環境，再用同一份已驗證的 XSA 建立 A53 standalone 控制程式。

## 2026-11-06：完整影格 DMA 已上板成功

- 修正 Vivado 的 DMA 長度設定，讓一個完整 640×480 影格可一次從 DDR 傳進 FPGA。
- 新硬體檔與 Vitis 控制程式已經由 JTAG 下載到 PYNQ-ZU，實測 DMA 完成、FPGA 回傳成功，frame ID 42 正確到達硬體。
- 這次用的是 Vitis 產生的合成測試影格，證明硬體資料通路可用；USB 雙鏡頭同時擷取仍受實體 USB 頻寬／供電影響，尚未完成。
## 2026-11-06：測試與文件同步

- 新增保護測試，避免 DMA 傳輸長度設定被改回無法容納完整影格的值。
- 更新 Vivado/Vitis 文件，清楚標示「完整合成影格 DMA 已成功」與「真實 USB 雙鏡頭仍未完成」的差別。
## 2026-11-06：USB 相機控制的正確分工

- Vitis standalone 可以控制 FPGA 與 DMA，但安裝的工具沒有 C270 需要的 UVC 驅動。
- 真實 USB 相機要由 Linux 的 UVC/V4L2 驅動取像；之後 Vitis Linux 程式再把 DDR 影格送進 FPGA。這不需要、也不能把 USB 相機線接到 FPGA 的一般影像腳位。
## 2026-11-06：Vitis Linux UVC 程式元件

- 已新增 A53 Linux 程式原始碼：可從兩支 UVC 相機讀取 640×480 YUYV 影格，轉成 FPGA 使用的雙 RGB packed 格式。
- 已找到正確的 Vitis Linux compiler，成功產生 AArch64 ELF；也尚未放上板子跑。最後還需要 Linux 提供可給 DMA 使用的連續記憶體，再把影格交給已驗證的 FPGA DMA 通路。
