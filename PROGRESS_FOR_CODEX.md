# 專題狀態與交接記錄（供 Codex）

## 2026-11-05：換機前 GitHub 交接盤點

- 使用者要求讓下一台電腦可直接以 GitHub 接續。本次先執行 `git fetch origin`，確認本機 `main` 和 `origin/main` 同為 `46e9371`，且工作樹沒有已修改但未提交的版本控制檔；倉庫中已有 124 個受追蹤檔案，包括目前 PYNQ-ZU RTL/腳本、Python/YOLOX 網站、測試、啟動器與交接文件。
- 新增根目錄 `.gitignore` 規則以排除這台電腦本次遺留的 Vivado/XSim `.jou`、`.log`、`.pb`、`.wdb`、`.Xil/`、`xsim.dir/`，以及 `output/`、`tmp/` 和本機網站啟動／伺服器日誌。這些皆是可重建暫存、簽名文件預覽、硬體照片或含本機路徑的診斷資料，並非未同步的專題來源；不可將它們未上傳誤報為進度遺失。
- `tmp/LaunchVisionSite.cs`／`.exe` 是臨時 C# 桌面啟動器，假定特定本機目錄和 `%LOCALAPPDATA%\\Programs\\Python\\Python312`，不作共享入口。跨電腦請使用已追蹤、會避開 Windows Store Python alias 的 `live_site/start_dual.ps1` 或 `啟動即時追蹤網站.cmd`；透過 `PROJECT_PYTHON` 指定不同 Python 路徑。RTL 回歸使用已追蹤的 `person_tracking/open_xsim_regression.ps1`／`開啟VivadoXSim驗證.cmd`。
- 本次僅完成 Git 交接整理，沒有重跑相機、PYNQ Linux、Overlay/MMIO、FPGA 或網站實機測試；已驗證狀態仍以本檔較早的明確日期記錄為準。下一台電腦最小接手順序：clone `main` → 依 `person_tracking/requirements.txt` 建 Python 環境 → 執行 `setup_assets.ps1` 下載／核對 YOLOX → 先跑合成／XSim 回歸 → 再依實機有無設定相機、PYNQ 與 Vivado。相機索引、模型位置與工具路徑保持可設定，勿硬編碼。

## 2026-11-05：PYNQ-ZU 上板後的畫面與配對結果展示方案（僅規劃）

- 使用者指定先把下列方案存入 GitHub，暫不實作；未來收到明確指示「讀／做」時再依此執行。目標展示為電腦瀏覽器同時顯示 A/B 即時鏡頭畫面、YOLOX 人物框與各自 Track ID、A/B 候選配對分數／連續命中數，以及 FPGA 回傳的 candidate/confirmed 狀態。
- 建議最終拓撲：兩支相機接 PYNQ-ZU（先以 PS USB/OpenCV 為優先驗證路徑；CSI/HDMI 需另選定板級介面），板子 Ethernet 與觀看用電腦接同一可信任 LAN；板上 PYNQ Linux 的 Python 服務提供網頁，電腦以 `http://<板子-IP>:8766/` 觀看。原始影像留在板子/區網，FPGA 僅經 AXI/MMIO 回傳小量配對結果；JTAG/UART（目前曾見 COM7）只用於開機和除錯文字，不能作為即時雙影像傳輸通道。
- 第一階段順序： (1) 確認 PYNQ image 開機、Ethernet IP 與電腦可連線；(2) 板上以 OpenCV 驗證一支、再兩支 USB camera 可取 640×480 影格；(3) 將既有 `live_site/dual_server.py` 與相依模型部署到板上，先由 PS Python 完整產生網頁畫面與軟體配對結果；(4) 建立 AXI DMA/HP memory、overlay 與板上 MMIO，將已配對 frame/bbox 送入現有 RTL，並把 `candidate_valid`、`confirmed`、命中數回填網頁；(5) 若展示需要實體螢幕，再另做 HDMI 疊圖輸出，這不屬現有 RTL 或網站功能。
- 既有 `live_site/dual_server.py`/`dual_index.html` 已能在 Windows 端呈現雙 USB 畫面、人物框、Track ID、候選配對和人工核對；LAN 模式設計為由另一台電腦開 `http://<鏡頭主機-IP>:8766/`。它尚未在 PYNQ Linux 執行，也尚未接讀 FPGA 狀態，不能描述為板端完成。
- 本次沒有變更 RTL、網站或 PYNQ 環境，沒有接板、沒有網路/相機/bitstream/DMA/MMIO 實測；本項只是後續上板與展示的可追溯規劃。硬體介面、IP 位址、相機索引及套件相容性須於目標第三台電腦／實際板子現場設定，不能硬編碼。

## 2026-11-04：YOLOX 到 PYNQ-ZU RTL 的 AXI4-Lite bbox 資料邊界

- 已核對並沿用既有 Verilog 提交：`6317be2` 跨鏡頭確認 matcher、`83cbdfe` 雙路 ROI 串接、`df14947` 完整 640×480 testbench；本次不重寫已驗證的 ROI/matcher 核心。
- 新增 `fpga/yolox_bbox_axilite.v`，提供同一 PL clock 的 AXI4-Lite command mailbox。PS 先寫 frame ID 和 A/B bbox，最後 CONTROL.bit0 commit；matching frame 接收後清除 pending，未消耗前再 commit 會置 `overrun` 且保留舊命令。
- 新增 `fpga/yolox_frame_command_adapter.v`，只在 video `frame_start` 與 command frame ID 相同時鎖住 bbox；`fpga/dual_camera_yolox_axilite_top.v` 將此 adapter、mailbox 與既有 dual ROI top 串接。`create_pynq_zu_rtl_project.tcl` 已新增 sources 並將該整合 top 設為 top。
- 新增 `person_tracking/pynq_yolox_mmio.py`，可驗證和送出 `dual_camera.py` 的 `rtl-yolox-bbox-v1` packet 到 PYNQ MMIO；硬體 base address 必須由最終 Block Design 的 Address Editor 提供，不寫死在共享程式碼。
- 此電腦驗證：Vivado 2024.2 `xvlog` 成功編譯完整整合 top；`tb_yolox_command_path.v` 的 commit、錯影格保留、正確影格 latch 與 consume 模擬通過，輸出 `YOLOX_COMMAND_PATH_PASS checks=9`。Python fake-MMIO 合約測試也通過，產生正確的 6 次 payload/control 寫入。
- 當時尚未驗證項目已由下一節更新；目前仍未驗證 PYNQ-ZU 的 PYNQ image/network、camera/MIPI 或 USB frame-buffer、XDC、implementation、bitstream、實機 MMIO。YOLOX 仍在 CPU/PS Python；RTL 只接收已選 pair 的 bbox，不能宣稱 YOLOX 神經網路已用 Verilog 實現。

## 2026-11-04：PYNQ-ZU Zynq PS Block Design 與綜合

- 新增 `fpga/create_pynq_zu_yolox_bd.tcl`：建立 board preset 的 `zynq_ultra_ps_e`、開啟 `M_AXI_HPM0_FPD`，接至 `axi_smc_0` 再接 `dual_camera_yolox_axilite_top` 的推導 `S_AXI` 介面。加入 `proc_sys_reset`、PS reset invert 和 100 MHz `pl_clk0`，避免第一次 BD validate 報告的非同步 reset critical warnings。影像輸入/輸出保持 BD external ports，因尚未選定 CSI/HDMI/USB frame buffer 的真實板級路徑。
- `assign_bd_address` 在此設計中實際配置 `/yolox_rtl_0/S_AXI/reg0` 到 PS address space 的 `0xA000_0000`、4 KiB；這是本腳本已驗證產生的地址，若日後變更 BD，PYNQ 端仍須以 Address Editor/HWH 為準。
- 新增 `fpga/synthesize_pynq_zu_yolox.tcl`，生成 BD HDL wrapper 並跑 `synth_1`。初次在 repo 中文長路徑下 IP generate 失敗（檔案找不到），已改三個 script 以環境變數 `PYNQ_ZU_BUILD_DIR` 可覆寫、預設 `%TEMP%/pynq_zu_rtl` 的短 ASCII 生成路徑；原 repo 下的舊 build 未刪除。
- 短路徑實跑：BD `validate_bd_design` 完成，僅有 SmartConnect 對 AXI4-Lite low-area/WRAP burst 的一般 warning；wrapper synth 產生 `pynq_zu_yolox_wrapper.dcp`，日誌為 `synth_design completed successfully`，0 errors、0 critical warnings。這證明 PS/AXI/RTL 結構可綜合，不證明 IO 約束、implementation、bitstream、PYNQ overlay、camera 影像或板端 MMIO。

## 2026-11-04：可接 DMA 的同步雙 RGB AXI-Stream 資料面

- 新增 `fpga/axis_dual_rgb_stream_adapter.v` 與 `dual_camera_yolox_axis_top.v`。前者把一條 64-bit AXI stream 的 A `[23:0]`、B `[55:32]` RGB888 word 轉成既有 dual ROI core 所需的同 clock/同拍 pixel stream；每 307,200 word 形成 640×480 frame，檢查 TLAST 是否落在終點並鎖存 boundary error。後者將 AXI stream adapter 與已驗證的 PS AXI-Lite bbox top 串接。
- 單一合併 DMA stream 是刻意設計：兩支獨立 DMA 若有 valid gap，既有同步 core 不能保證每個 A pixel 對應同一個 B pixel。此介面允許 PS/camera 軟體先將同時間 pair 成為一個 frame-pair buffer，再送入 PL。
- `pynq_yolox_mmio.py` 新增 `pack_dual_rgb888_frames()` 和 `copy_dual_frame_to_dma_buffer()`；只接受 matching `uint8` RGB H×W×3 frames，依硬體位元布局產生 `uint64` DMA words。fake NumPy test 的輸出為 `0x00aabbcc00112233`；Vivado XSim 的 adapter test 結果為 `AXIS_DUAL_RGB_STREAM_ADAPTER_PASS checks=7`，完整 axis top `xvlog` 成功。
- 未驗證：尚未選定/接上 PYNQ-ZU 的實體 camera interface（CSI、HDMI 或 PS USB），也尚未把 AXI DMA/high-performance memory port 加到 BD、產生 bitstream 或用 PYNQ DMA 實機傳影像。故這是已測試的資料格式/RTL 入口，不是相機上板結果。

## 2026-11-04：PYNQ-ZU board repository 與 Vivado 驗證

- 使用者提供板子照片確認為 TUL PYNQ-ZU，官方 board part 為 `tul.com.tw:pynqzu:part0:1.1`、device `XCZU5EG-1SFVC784`。本機偵測到其 Xilinx USB JTAG/UART（FTDI VID 0403/PID 6010）於 COM7，但當次打開後未收到 UART boot 輸出，未證明 PYNQ image 已開機或網路可達。
- 使用者下載的 `C:\Users\dsic\Downloads\XilinxBoardStore-master.zip` 已解壓到被忽略的 `fpga/board_repos/`。新增 `fpga/configure_pynq_zu_board.tcl`：以 script 相對路徑設定 `board.repoPaths`，檢查 `TUL/pynqzu/1.1/board.xml` 存在並執行 `get_board_parts *pynqzu*`。Vivado 2024.2 batch 實跑印出 `PYNQ_ZU_BOARD_PARTS=tul.com.tw:pynqzu:part0:1.1`；其他 Board Store 中此 Vivado 沒安裝的 device 警告與 PYNQ-ZU 無關。
- 下載的 `pynqzu_master.xdc` 是 Rev 3.B 的完整約束範本，目前不直接加入設計；必須待確定使用哪一個 PL I/O（HDMI/CSI/LED 等）再挑選對應 constraint。`.gitignore` 現排除 `fpga/board_repos/`，不提交約 224 MB 的第三方 Board Store。尚未產生 PYNQ-ZU bitstream、PS block design、AXI bridge、PYNQ overlay 或板端實機驗證。
- 新增 `fpga/create_pynq_zu_rtl_project.tcl`。它設定本機 board repo、`create_project` 使用 `xczu5eg-sfvc784-1-e`、套用 `tul.com.tw:pynqzu:part0:1.1`，並加入 `person_roi_stream.v`、`cross_camera_pair_matcher.v`、`dual_camera_roi_match_top.v`，top 為 `dual_camera_roi_match_top`。2026-11-04 以 Vivado 2024.2 batch 實跑建立成功；Vivado 警告專案中文/長路徑可能影響日後 IP/BD，未出現 RTL 加檔錯誤。`fpga/build/` 已加入 Git ignore。尚未 run synthesis 或建立含 PS/AXI 的 block design。

## 2026-11-04：公開圖片 dataset 評估彙總

- 新增 `person_tracking/evaluate_detection_dataset.py`，以 `verification_report.json` 為來源彙總 6 組公開圖片／亮度案例。
- 實際輸出 `DATASET_EVALUATION_PASS cases=6 observations=105 recall=1.000 minimum_iou=0.855`：105/105 人工標註觀測配對成功、0 miss、0 ID switch，負例 PASS。
- 這證明人物偵測框與短期追蹤的 dataset 評估已可交付；不延伸宣稱跨鏡頭真人身分準確率，因目前仍缺人工同人／不同人標註集。

## 2026-11-04：跨鏡頭同人配對正式評估入口

- 新增 `影像處理/ModelSim_YOLOX_PersonTracking/person_tracking/evaluate_matching_dataset.py`、`matching_dataset.json` 與 `MATCHING_EVALUATION.md`。評估人工標記的同人／不同人案例，輸出 TP、TN、FP、FN、accuracy、precision、recall、F1；有框座標時另檢查最大像素誤差是否小於 20 px。
- 目前附帶的 4 筆資料是合成 regression fixture，結果為 `TP=1/TN=3/FP=0/FN=0`、accuracy/precision/recall/F1 均 1.0、最大框座標誤差 8 px。這證明評估器與現有 matcher 可重跑，不是真人雙鏡頭準確率。
- 要取得正式實拍分數，需把 `matching_dataset.json` 換成兩台鏡頭錄影後人工確認的同人／不同人案例；測試集不可用來調門檻。

## 2026-11-04：EPFL 外部資料實測

- 新增 `person_tracking/evaluate_epfl_dataset.py`，使用專案 YOLOX/OpenCV 對 EPFL 6-camera 人物框資料逐張推論，依縮放後 ground truth 計算 IoU。
- 939 cases、1,302 ground-truth boxes、1,565 predictions；matches=1,035、misses=267、false positives=530，recall=0.7949、precision=0.6613、mean IoU=0.7963、minimum IoU=0.5007，耗時 133.84 秒。
- 座標誤差同步計算：mean=5.7932 px、maximum=37 px；`coordinate_error_threshold_px=20` 且 `coordinate_error_pass=false`，因此部分框超過 20 px。
- 另依物體中心位置計算 Euclidean distance：mean=2.9939 px、maximum=19.5256 px，`center_error_pass=true`。中心位置指標符合 `<20 px`，但四邊框誤差仍保留為 37 px，不能聲稱框的每一條邊都低於 20 px。
- 新增 `benchmark_box_stabilizers.py` 比較 Raw/EMA/median3；Raw 的 mean IoU=0.7963、中心最大誤差=19.5256 px 最佳，其他平滑法降低 recall 並超過 20 px，故未改主演算法。
- 新增 `fit_epfl_box_regressor.py` 與 `benchmark_box_refinements.py`。以 frame % 5 != 0 的人工標註配對學 per-camera 線性框校正，於 frame % 5 == 0 的 held-out validation 測試；`clamp=460` 得 max edge error=19 px、max center error=10.7355 px、mean IoU=0.8164，通過 `<20 px`。
- 結果 `EPFL_DATASET_PARTIAL`；完整逐案例明細在 `person_tracking/epfl_dataset_evaluation.json`，不可把先前 bus/zidane 回歸結果替代這次外部資料分數。
## 2026-11-04：雙鏡頭單一候選 Verilog 確認核心

- 本機目前以兩支 USB 鏡頭執行 `live_site/dual_server.py`，`/api/live` 曾回報 `live`、cameras `[0, 1]`、人物偵測與候選分數。白牆 10 個即時樣本的平均亮度 A/B 差為約 `+1.1/255`；另一輪以低飽和高亮區測得近似白色的 Lab 色差。這些是 2026-11-04 當時實機畫面量測，不等於人物同一性或準確率驗證，現場變化／自動曝光仍可能改變結果。
- 新增 `person_tracking/cross_camera_pair_matcher.v`，為可綜合的固定點單一 A/B pair 確認核心。輸入：時脈、reset、`pair_observed`、雙方有效位元、既有 `{top_color,bottom_color,top_percent,bottom_percent}` 24-bit 特徵；輸出：組合 `feature_similar`、每個相似觀測的 `candidate_valid`、第三個連續命中時的 `confirmed`，以及飽和於 3 的 `consecutive_hits`。主色兩段相等、各比例差 <=35 是相似條件；black 色碼 0 可透過獨立 valid 正確處理。缺少 pair 或不相似會清除計數。
- 新增 `person_tracking/tb_cross_camera_pair_matcher.v`，覆蓋第一次/第二次候選、第三次確認、確認後飽和、色碼不符、缺失觀測、black feature、36 個百分點比例差及 reset。用 `C:\Xilinx\Vivado\2024.2\bin\xvlog.bat`、`xelab.bat`、`xsim.bat` 實跑，輸出 `CROSS_CAMERA_PAIR_MATCHER_PASS checks=10`，無編譯或模擬錯誤。這是本機第三台的 XSim 模擬，非 ModelSim，也非合成、時序、PYNQ/EGo1 或相機實機驗證。
- 與 Python `cross_camera.py` 的關係：此 RTL 只確認一個已由上層選定的 pair，未等價實作 15-bin HSV overlap、0.72 門檻、歷史平滑、互為最佳、0.08 次佳差或多人物仲裁。YOLOX/Tracker/bbox 和 pair 選擇仍在 CPU；下一個 RTL 範圍應在固定 feature contract 後新增 A/B 多候選緩衝與仲裁，而不是聲稱已完全硬體化現有網站 matcher。
- 同日新增 `fpga/dual_camera_roi_match_top.v`：同一 clock domain 的雙 RGB888 pixel stream + CPU/YOLOX bbox integration top。兩個 `person_roi_stream` 在完整 640×480 frame 結尾輸出 feature 後，top 緩衝 feature，下一個 clock 送一拍 `observation_valid` 給 `cross_camera_pair_matcher`，避免讀到 nonblocking 舊值且不讓兩影格之間的 pixel gap 清空 hit 計數。以 Vivado 2024.2 `xvlog` 編譯 `person_roi_stream.v`、`cross_camera_pair_matcher.v`、此 top 成功；尚未建立真實 YOLOX bbox 的 pair testbench，也未完成不同時脈 USB / frame buffer、CPU-FPGA bbox protocol、多人物仲裁或 YOLOX network RTL。
- 新增 `fpga/tb_dual_camera_roi_match_top.v`，每個案例逐拍送完整 307,200 pixel 的 A/B RGB888 frame 與 bbox（用來模擬 YOLOX 已完成的偵測）。三張紅色相似 ROI 必須產生連續 1/2/3 並在第三張 `confirmed`，第四張紅/藍 mismatch 必須清為 0。以 Vivado 2024.2 XSim 實跑 `DUAL_CAMERA_ROI_MATCH_TOP_PASS checks=16`。這是 top 級合成影格與 bbox 模擬，仍不等於真實 YOLOX output、USB 兩時脈或 FPGA 實機。
- `person_tracking/dual_camera.py` 現在對每個已由 Python matcher 選出的非 unmatched A/B pair 寫入被忽略的 run artifact `rtl_yolox_packets.json`。格式 `rtl-yolox-bbox-v1` 含 640×480 resolution、frame、pair timing、兩側 track ID/bbox/confirmed、以 `pipeline.color_reference` 產生的 24-bit feature、軟體 score/status；不含 raw frame。這建立 YOLOX/Tracker 對 RTL `dual_camera_roi_match_top` bbox input 的可檢查封包契約，但未直接控制 FPGA、未證明 USB 同步，且不將 YOLOX 網路硬體化。已以 Python 3.12 `py_compile` 通過。

## 2026-10-31：第三台電腦執行環境複核

- 以 `%LOCALAPPDATA%\\Programs\\Python\\Python312\\python.exe` 實測：Python 3.12.10、NumPy 1.26.4、OpenCV 4.11.0 均可匯入；`person_tracking/setup_assets.ps1` 已確認 YOLOX ONNX 與三張公開測試圖存在，模型 SHA-256 為預期的 `c5c2d13e59ae883e6af3b45daea64af4833a4951c92d116ec270d9ddbe998063`。不需重複下載或安裝 Python 相依套件。
- 實際以此 Python 執行 `evaluate_cross_camera.py` 為 `CROSS_CAMERA_EVALUATION_PASS cases=3`；`unittest discover -s person_tracking -p test_*.py` 為 18/18 PASS；在 `live_site` 目錄執行 `python -m unittest test_dual_server.py -v` 為 6/6 PASS。這些是合成／程式回歸，不是 USB 相機或 FPGA 實測。
- 已確認 `C:\\Xilinx\\Vivado\\2024.2` 與內建 `xsim` 存在，但沒有偵測到 ModelSim 的 `vsim.exe`、安裝目錄或安裝媒體；因此現有 ModelSim 啟動器尚不能在本機執行，且不可把 Vivado 的 xsim 當成已驗證的 ModelSim 替代品。ModelSim 安裝仍需授權及安裝程式來源。
- Windows 裝置清單沒有回報狀態 OK 的 Camera，故未執行實體 USB／內建相機與 localhost 頁面影像流程。接上兩台相機且未被其他程式占用後，才可在 `http://127.0.0.1:8766/` 驗證雙鏡頭。
- 為讓已安裝的 Vivado 可立即使用，新增 `person_tracking/open_xsim_regression.ps1` 和上層雙擊入口 `開啟VivadoXSim驗證.cmd`。腳本複製 RTL 到 ASCII `%TEMP%/project_xsim_rtl_regression`，以 `xvlog`、`xelab`、`xsim` 編譯、elaborate、模擬；可用 `-Batch` 取得非互動 PASS/FAIL，或預設開 XSim GUI。實測 Vivado 2024.2 批次結果為 `RTL_REGRESSION_PASS frames=7 checks=89`。可設 `VIVADO_XSIM_BIN` 指向其他 Vivado 的 `bin` 目錄，沒有硬編碼使用者專屬路徑。

## 2026-10-30：第三台電腦環境與雙鏡頭啟動流程

- 目標端為第三台電腦；已安裝使用者層級 CPython 3.12.10：`%LOCALAPPDATA%\\Programs\\Python\\Python312\\python.exe`。以該直譯器安裝 `person_tracking/requirements.txt`，驗證版本為 NumPy 1.26.4 與 OpenCV 4.11.0；`person_tracking/setup_assets.ps1` 的 YOLOX ONNX 和公開圖片亦已準備。VS Code 已安裝 Microsoft Python、Pylance、Python Environments 與 debugpy 擴充套件；此前只解析到 WindowsApps 的 Store alias，並非可用解譯器。
- 更新 `live_site/start_dual.ps1`：優先由 `%LOCALAPPDATA%\\Programs\\Python` 找 CPython，排除 `WindowsApps\\python.exe` alias，才回退至 PATH 或 `PROJECT_PYTHON`。這避免桌面端啟動雙鏡頭網站時把 Store alias 當成 Python。
- 更新上層 `啟動即時追蹤網站.cmd` 為呼叫 `live_site/start_dual.ps1`，所以雙擊會執行 `dual_server.py --browser`，預設服務為 loopback `127.0.0.1:8766`。這會開 Chrome 或預設瀏覽器，但畫面是否開始取決於使用者在網站按下連接雙鏡頭、兩個 USB 鏡頭存在且未被其他程式占用。
- 未聲稱 USB 攝影機、ModelSim 或 Vivado 上板流程已驗證；目前已確認 `C:\\Xilinx\\Vivado\\2024.2` 存在，ModelSim 尚未在第三台確認。

## 2026-10-15：ModelSim 可重跑自動檢查與 GUI 入口

- 使用者要求下一個進度直接做在 Vivado 或 ModelSim，之後開啟可見。選擇驗證現有 ROI RTL，未假設 PYNQ 型號或鏡頭介面，也未改動原 RTL/網站。
- 修改前 `git fetch origin`，main 與 origin/main 為 `9c2070e`，工作樹乾淨；核對本機 modelsim_draft 與共享路徑兩份運算 RTL SHA256 相同。新增檔案以 modelsim_draft 為本機入口，同步共享最新整合路徑。
- `person_tracking/tb_rtl_regression.v`：自動比較手算答案，7 張完整 640×480 frame：全紅、偏移奇數高紅藍分區（插入 stalls）、右下邊界、無人物、零寬、一列高度、全黑。每張檢查完成時機、像素數、上下區面積、特徵/有效訊號；不 reset 的連續 frame 檢查累積器清除。比較器測 35/36 雙向門檻、主色不符與 invalid，末尾測 reset。失敗用 $fatal，另有 watchdog。
- `person_tracking/open_rtl_regression.ps1`：預設 ModelSim GUI 或 `-Batch` CLI，複製三份 Verilog 到 ASCII `%TEMP%/project_rtl_regression`，產生 regression.do，compile、模擬、記錄 WLF 並配置波形。GUI 保留視窗，Batch 要求 exit code 0 與 PASS 標記。可用 MODELSIM_VSIM 指定工具。`開啟ModelSim驗證.cmd` 為雙擊入口；`RTL_REGRESSION.md` 說明訊號與限制。
- 實際使用 ModelSim SE-64 2020.4 批次重跑通過，`RTL_REGRESSION_PASS frames=7 checks=89`，0 errors / 0 warnings；原始文字輸出保存 `person_tracking/rtl_regression_console.txt`。7 frame 不等於 7 個 checks，89 包含插入停拍的時機檢查。
- 限制：合成資料，未窮舉全部色彩分類門檻、未做亂數與中途 reset 測試，未做 synthesis/時序/上板；不能代表 YOLOX 或 Python 跨鏡頭 matcher 已搬到硬體。GUI 暫存副本需透過啟動器重開更新，原始碼在 repo。既有舊進度日期保留作歷史。

最後核對：2026-10-02

## 2026-11-03 變更：鏡頭來源端公開啟動交接文件

- 新增根目錄 `CAMERA_PC_PUBLIC_SETUP_PROMPT.md`，集中保存來源端檢查、CameraA 選擇、`start_remote.ps1` 啟動、private link 讀取和完成驗收條件。
- 這是來源端操作交接，不代表另一台電腦已實際啟動；目前仍缺目標電腦回傳的鏡頭、health、live 與跨網路手機證據。

## 2026-11-03 變更：雙電腦程式與網站協作

- `live_site/sync_camera_pc.ps1` 是鏡頭電腦的同步入口：驗證 Git checkout、`git fetch`、`git pull --ff-only`，失敗時停止，不覆蓋本機未提交變更，再呼叫 `start_dual.ps1`。
- `dual_server.py` 新增 `--bind` 與可重複的 `--allow-host`。預設仍為 loopback；明確指定 LAN bind/allowed Host 後，另一台電腦可用瀏覽器看 `/api/live` 與影像。
- `start_dual.ps1` 保留原本環境變數／CPython 尋找邏輯，並接受 `-ServerArgs` 傳遞服務參數。
- 未驗證目標電腦的實際 IP、Windows 防火牆、USB 鏡頭、Python/OpenCV/YOLOX 安裝或跨電腦 HTTP；這些需在鏡頭電腦現場執行。不要把 GitHub 當即時影像通道，也不要把 8766 公開到網際網路。

## 2026-10-26 變更：PYNQ/EGo1 共用板級 RTL wrapper

- 新增 `影像處理/ModelSim_YOLOX_PersonTracking/fpga/roi_feature_board_top.v`。它不重寫 ROI 計算，直接例化 `person_tracking/person_roi_stream.v`，保留 `pixel_valid`、`frame_start`、RGB888、人物 bbox 與 frame 完成訊號，並以 `result_led = feature_valid && person_valid` 提供最小板級結果指示。
- 這是 board-neutral synthesizable boundary，不是任一特定板子的可直接燒錄專案。PYNQ-Z2/EGo1 的 clock、XDC 腳位、相機輸入與 PS/AXI adapter 必須等實際板型與輸入方式確認後補上。

## 2026-10-26 變更：跨鏡頭 matcher 可重跑回歸評估

- 新增 `person_tracking/evaluate_cross_camera.py`。它使用明確的 2×15 合成外觀向量，重跑三個固定案例：同色連續三次後應為 `confirmed_candidate`、不同色應為 `unmatched`、相同外觀競爭者應為 `ambiguous`；使用 `assert`，並輸出同目錄的 `cross_camera_evaluation.json`。
- 實際結果：`CROSS_CAMERA_EVALUATION_PASS cases=3`；既有 `test_cross_camera.py` 為 6 tests OK。
- 這只驗證目前 Python matcher 的門檻、連續命中與歧義保護，不能替代真人標記資料的 precision/recall、雙實體 USB 實拍或身份辨識驗收。
- 完整 `unittest discover` 另有既有 `test_dual_features.py`、`test_tracking.py` 因目前 Python 3.10 環境未安裝 `cv2` 而無法載入；沒有安裝依賴或改變環境。

## 2026-10-02 變更：停止時清除舊工作階段照片

- 使用者補充「舊照片也刪掉」。`live_site/dual_server.py` 的 `stop_and_clear()` 現在在停止後遍歷**僅** `person_tracking/live_captures/` 下名稱符合 `YYYYMMDD_HHMMSS_ffffff` 的直接子資料夾；資料夾須不是 symlink、解析後仍在預期根目錄。每個工作階段只依其非 symlink `manifest.json`、且 `session` 名稱匹配，刪除 `people[].file` 列出、檔名符合 `[AB]_[0-9]{4,}.jpg` 的直接 JPEG。未登記 JPEG、其他檔案／資料夾、舊 manifest 保留；本次 manifest 仍按先前停止規則移除。沒有目前 session 也可按停止清舊照。API `deleted_photos` 和頁面訊息回報所有工作階段的刪除張數。
- `dual_index.html` 按鈕與說明改成「停止雙鏡頭並清除全部人物照片」。`test_dual_server.py` 改驗本次+舊工作階段登記照片刪除，未登記同命名 JPG、不同目錄 JPG、舊 manifest／其他檔案保留，重複停止安全。
- 實機操作：先核對 `live_captures` 8 個工作階段各有合法 manifest，549 張 A/B JPG 均列於 `people[].file`，無未登記同命名 JPG；停止原服務防止繼續拍攝，啟動新版後在無 active session 下呼叫 `/api/stop`，回報 `deleted_photos=549`。事後以同一目錄範圍複查，剩餘人物 JPG 為 0、8 份舊 manifest 保留，`/api/live` 為 stopped 且 `saved_people=[]`。未觸及 repo 其他未追蹤檔案。新增無 active session 的舊照清除單元測試。

## 2026-10-02 變更：多影格特徵、最佳人物照與人工審核

- 原本保存的首張人物 JPEG **不參與**跨鏡頭分數計算；分數取當次推論影格的衣著特徵。因此首張是側面照主要妨礙人工判讀，不直接造成配對失敗；實際低分/模糊候選仍可能來自視角、裁切、曝光與多人衣著相近。`live_site/dual_server.py` 新增 `AppearanceHistory`，每個鏡頭／Track ID 將最近五次特徵平均後與當前特徵各占一半，再交給既有 matcher；0.72 門檻、0.08 歧義差與三次連續 P 規則未變，尚未宣稱配對準確率改善。
- `snapshot_quality()` 比較人物框面積、清晰度、完整度、偵測信心；每個 ID 首次及其後每三次處理影格使用 OpenCV 隨附的 frontal-face Haar cascade 查正面臉，加權挑選較佳照。更新時覆寫同一檔名但 `photo_url` 增加 `?v=` 版本，避免瀏覽器顯示舊圖；每 ID 仍僅保留一張 JPEG。臉偵測可能漏檢/誤檢，不是姿態模型。已人工審核配對所涉的照片凍結，避免審核證據變動。
- `POST /api/manual_pair` 接收本次存在照片的整數 A/B ID，建立 M 標籤人工候選；`POST /api/review` 接收 P/M 標籤及 `same|different`，記錄審核與時間到本次 manifest。`/api/live` 的 `matched_pairs` 帶 `source`、`review` 與更新版照片 URL；網頁卡顯示雙照、✓/✕ 按鈕與判斷狀態。`cross_camera.py` 的 `excluded_pairs` 只在本次 session 阻止已被人工否決的 A/B ID 再自動配對；肯定判斷不訓練或改動模型。人工核對紀錄依前次要求在明確按「停止」時與本次照片一併清除。
- 實機正面臉 Haar 偵測在當次多人畫面未命中（截至觀察時 56 張照片、17 張有擇優替換、0 張帶 `face_detected`）；因此另加 `POST /api/retake`：只准對目前確認可見、最近一次推論不超過三秒、尚未審核的本次人物 ID，使用最近同一推論影格的人物 crop 手動覆蓋並鎖定 JPEG。相應照片與配對卡 URL 升版；可再手動重拍但自動挑選不覆蓋鎖定照。頁面每張照片下有「用目前畫面重拍並鎖定」，未在畫面中的 ID 或已審核者按鈕停用。
- 網頁載入改為只輪詢 `/api/live`，不再隱式 `POST /api/start`；重整頁面不換 session、不遺失人工審核。初次或手動停止後須使用者按「連接雙鏡頭」。
- 驗證：`live_site/test_dual_server.py` 五項合成單元測試 PASS，涵蓋最佳照替換、手動重拍鎖定、審核後凍結、手動 M 候選、否決組合排除、多影格特徵及停止清除；兩段網頁 JavaScript 語法檢查 PASS。新版服務以鏡頭 2/1 實機運行、頁面顯示雙鏡頭與人工 A/B 選單、P 卡 ✓/✕ 按鈕、每張照片的重拍按鈕，圖片無破圖；當次 AI 約 1.8 FPS、延遲約 0.6 秒，部分照片帶正面臉偵測標誌。沒有代替使用者對真實人物按 ✓/✕，也沒有任意挑角度對真實人物按重拍；這兩項實際人為操作仍由使用者核對。未有標註資料驗證漏配/誤配率。

## 2026-10-02 變更：手動停止時只清除本次人物照片

- `live_site/dual_server.py` 新增 `stop_and_clear()`：`POST /api/stop` 先停鏡頭並切換 epoch，鎖內只刪目前 `session_id` 工作階段中 `self.photos` 已登記的 JPEG 及該次 `manifest.json`，清空本次照片／P 候選狀態；資料夾僅在已空時移除。舊工作階段、未登記檔案、其他專題資料均不碰。10 秒無頁面輪詢的自動停鏡頭仍走 `control(False)`，不刪照片。API 成功回傳 `deleted_photos`，頁面訊息顯示數量。
- 網頁停止按鈕與說明文字更新為「停止雙鏡頭並清除本次照片」。單元測試加入本次照片／manifest 刪除、舊工作階段與未登記檔案保留、重複停止，以及非手動停鏡頭不刪除等檢查。此變更不追溯刪除先前已有的本機照片，需使用者另行指定範圍。
- 驗證：兩項 `live_site/test_dual_server.py` 單元測試 PASS。新版服務用實體鏡頭 2/1 啟動工作階段 `20261002_160018_047057`，停止 API 回報刪除 17 張本次 JPEG；之後 `/api/live` 為 `stopped`、`saved_people=[]`、`session=null`，本次資料夾已移除，先前 `20261002_155716_106196` 資料夾仍存在。網頁按鈕沿用同一 `/api/stop` 路徑；未另外做手動 UI 點擊驗證。

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

## 2026-10-02 變更紀錄：人工審核照片自動淡出

- `影像處理/ModelSim_YOLOX_PersonTracking/live_site/dual_index.html`：本頁操作以 POST 成功的本機時間開始計算，重整後改用伺服器回傳的 `reviewed_at`。按 ✓／✕ 後，配對照片保留約 5 秒、再淡出約 0.6 秒，然後從 DOM 及版面移除。已審核人物縮圖在沒有其他待審核配對使用該 Track ID 時也收起；未配對人物照與待審核照片仍顯示。頁面保留已審核同／不同人計數及「查看／修改已審核照片」切換，可重新展開改判；頁面重整不會讓舊審核照片永久重現。
- `dual_server.py` 的 `review_pair` 將審核時間記為毫秒精度 ISO 本機時間，支援較準確的五秒 UI 倒數；舊 manifest 秒級時間仍可解析。`test_dual_server.py` 增加時間格式檢查。
- 資料流未加入訓練：UI 審核寫入本次工作階段的 `matched_pairs`／`manifest.json`，正面判斷只凍結配對照片，負面判斷另在 `process()` 中轉為同一組 A/B Track ID 的 `excluded_pairs`，傳給 `CrossCameraMatcher.update()`；新工作階段沒有讀回舊標籤，`appearance_similarity()` 仍是固定 HSV 直方圖加權，YOLOX 權重未更動。五秒收起只是網頁視覺行為，本機 JPEG 仍留存至明確按停止時按 manifest 清除。
- 驗證：`live_site/test_dual_server.py` 6 項合成單元測試 PASS；兩段網頁 JavaScript 語法檢查 PASS；純函數 `reviewPhase()` 的 4999／5000／5599／5600 ms 邊界測試 PASS；目前執行中的 localhost:8766 已從磁碟回傳含新版淡出／重看按鈕的 HTML。未用真人雙鏡頭實拍驗證淡出視覺效果或配對準確率。執行中的 Python 服務未重啟（環境拒絕重啟命令），因此該程序仍以舊版秒級時間寫新審核；頁面操作已用 POST 完成時間作精確倒數，重整後亦可解析舊秒級時間，新啟動服務才會使用毫秒時間。

## 2026-10-02 變更紀錄：保留既有版本並同步目前進度

- 同步前 `HEAD` 與 `origin/main` 均為 `47773ef`，工作樹只有兩份未追蹤的精簡測試紀錄；既有程式、雙鏡頭網站、人工審核與五秒淡出已在遠端。本次採追加提交，不 force push、不刪除或覆蓋既有內容。
- 新納入 `影像處理/MCDPT_Verilog_Two_Image_ReID/modelsim_transcript_20261002.txt`：2026-10-02 00:28 的早期 8×8 RTL testbench 執行紀錄，`vlog` 顯示 0 errors／0 warnings，`vsim` 印出 3 個同人 frame `same = 1`、1 個不同人 `same = 0`，最後 `two camera color test ok`、0 errors／0 warnings。此檔為已存在的本機紀錄，本次只檢查文字並歸檔，沒有重新執行 ModelSim；不可當成最新 640×480 YOLOX／雙實體 USB 流程通過的證據。
- 新納入 `影像處理/ModelSim_YOLOX_PersonTracking/person_tracking/tests/tracking_results.json`：既有測試摘要記載 `tests_run=6`、`failures=0`、`errors=0`、`status=PASS`；本次尚未確認其個別測試案例或重新執行。被 `.gitignore` 排除的 `tests/rtl_*/` 逐次輸出中另有 `summary.json` 記載 5 個手算區域、307200 pixels/frame、PASS，但它和 WLF、完整 run 產物仍不入 Git；歷史驗證請區分摘要與原始輸出。
- `PROJECT_CONTENTS.md` 與 `PROGRESS_FOR_HUMANS.md` 更新共享範圍。`person_tracking/live_captures/` 的人物 JPEG／審核 manifest、下載的 YOLOX 權重、相機影格、大型 replay／run 與 WLF 等仍保留本機，不因本次「同步全部」而上傳；這遵循既有隱私與產物排除決策。若後續確實需要共享含人物的標註資料，應另行界定同意、匿名化及存取方式。
## 2026-11-03：無鏡頭的 Cloudflare Quick Tunnel 等待模式

- `live_site/dual_server.py` 新增明確 opt-in 的 `--allow-trycloudflare`。服務在保留既有 localhost/LAN Host + `http` Origin 檢查的前提下，額外允許 `https://*.trycloudflare.com`；這處理 Quick Tunnel 每次重啟有不同主機名，且反向代理可能把 Host 改寫為 local origin 的情況。初始 HTML 導航沒有 `Origin` 時，僅在 Host 本身是 `*.trycloudflare.com` 才放行。沒有此旗標，遠端 Origin 一律維持拒絕。新增 `--camera-a`／`--camera-b`，可在尚未開啟擷取前把等待中的預設相機組合回報給 `/api/live`，`camera-b=-1` 代表目前未配置第二台。
- 新增 `live_site/start_remote.ps1`：以目前專題目錄啟動服務、等待本機 health 成功、啟動未登入的 Cloudflare Quick Tunnel、將當次 URL 寫入被忽略的 `work/remote_site/private-link.txt`。它不會呼叫 `/api/start`，所以沒有鏡頭時仍維持 stopped 等待；每次啟動會停止本專題原有的 8766 listener，以確保新 tunnel 指向新服務。Cloudflare 執行檔與所有 URL/log 都只放使用者本機。
- `live_site/README.md` 明確說明服務可在沒有相機時保持 `stopped`，只有 `/api/start`／網頁連接動作才會碰相機；Quick Tunnel 連結、token、模型和相機相片屬本機私密資料，不入 Git。
- 2026-11-03 已在此電腦以 CameraA 0／CameraB -1 的等待設定啟動新 Quick Tunnel；未呼叫 `/api/start`，因此沒有相機實測或照片產生。透過新 HTTPS URL 的首頁回應 HTTP 200，`/api/health` 回傳應用程式/版本，`/api/live` 回報 `stopped`、`enabled=false` 和 cameras `[0, -1]`；當時 cloudflared 程序仍在執行。連結、log 與 `cloudflared.exe` 均只在使用者本機，不加入此倉庫。

## 2026-11-05：對話／進度同步紀錄

- 新增根目錄 `CONVERSATION_PROGRESS_LOG.md`，以精簡、可交接方式記錄每次已完成進度的需求、變更、驗證界線、Git 提交／推送結果和未完成事項；不保存逐字聊天、帳密、私人連結、個人影像或模型權重。
- `AGENTS.md` 已規定未來每次可交付進度均須追加該紀錄，並與相關檔案同次 commit + push 至 `main`。純討論、沒有檔案變更或未完成工作不製造完成紀錄。
- 本次稽核時 `main` 與 `origin/main` 同為 `5fe1467`；最近的 PYNQ-ZU/IRQ/USB 部署工作已有遠端提交。沒有發現既有對話紀錄檔，故不能由 Git 判斷或還原未曾落檔的舊聊天內容。未追蹤的 Vivado/XSim 與本機網站日誌維持排除，並非待上傳的專案原始碼。

## 2026-11-05 變更紀錄：PYNQ-ZU 可重建 bring-up bitstream 與 JTAG 實機下載

- PYNQ 目標已確認為 **PYNQ-ZU**（`XCZU5EG-SFVC784-1-E`），不是 PYNQ-Z1。Vivado Hardware Manager 實機枚舉為 `XUPJTAG` 下的 `xczu5_0`；板子供電恢復後可讀到裝置。依 PYNQ-ZU 官方手冊，直接由 Vivado JTAG 下載時 boot switch 使用 **JTAG（左側）**；SD 是從 SD card 開機 PYNQ Linux 的模式，兩者用途不同。
- 新增 `fpga/implement_pynq_zu_yolox.tcl`，會驗證 project/BD/wrapper，執行 `impl_1` 至 `write_bitstream`，並只在 `write_bitstream Complete!` 及 `.bit` 實際存在時回報成功。腳本沒有降低 UCIO/NSTD DRC 嚴重度。
- Windows 原始路徑含中文使 Vivado 子綜合程序無法解析來源；`create_pynq_zu_rtl_project.tcl` 現將八個必要 HDL 檔 stage 到可設定短 ASCII build directory 的 `rtl_src/` 後再加入 project。`synthesize_pynq_zu_yolox.tcl` 會先 reset 舊 `synth_1` run，避免重用 run 時的 reset 要求。
- 100 MHz 設計實作時 WNS 約 -32.945 ns，未下載至板。時脈降至 20 MHz 後，完整 external-video 版本 route WNS +0.013 ns，但因外部 video/result ports 沒有 XDC 而被 UCIO-1 正確阻止 bitgen；沒有繞過該 DRC。
- 預設 bring-up Block Design 使用 PS→SmartConnect→AXI4-Lite mailbox（`0xA000_0000`，4 KiB）、20 MHz PL clock。尚未指定板級來源的 video inputs 以常數 idle 驅動，result ports 不外拉至未約束的 PL pins。這版可驗證 PS/PL clock、AXI-Lite 與 JTAG，不是雙攝影機資料流。
- 本機 `C:\\pynq_zu_bringup` 的實作/bitgen 已完成（0 errors、0 critical warnings）；產物為 `C:\\pynq_zu_bringup\\pynq_zu_rtl.runs\\impl_1\\pynq_zu_yolox_wrapper.bit`。2026-11-05 已在 Vivado Hardware Manager 對實機 `xczu5_0` 成功下載；狀態顯示 `Programmed`，Tcl console 回報該 JTAG device is programmed。這是易失性的 JTAG PL 設定，不會寫入 SD 或開機 flash，斷電後消失。
- 尚未驗證：PYNQ Linux 下的 Overlay/HWH + MMIO 存取、AXI mailbox 實際讀寫，以及相機/DMA/CSI/HDMI 影像路徑。要啟用真實 video ports，必須先選定介面並提供對應 IP、clock/reset/CDC、XDC，再以 `PYNQ_ZU_EXPORT_VIDEO_PORTS=1` 重建；不可把此 bring-up 成功誤稱為雙鏡頭功能完成。

### 2026-11-05 後續：SD-boot overlay 部署準備

- 新增 `fpga/prepare_pynq_zu_overlay.ps1`，從完成的短 ASCII build directory 複製 `.bit` 與 handoff `.hwh`，並統一命名成 PYNQ Overlay 所需的同 stem `pynq_zu_yolox.bit` / `pynq_zu_yolox.hwh`。本機已以 `C:\\pynq_zu_bringup` 實跑，輸出目錄 `C:\\pynq_zu_bringup\\overlay` 包含 7,797,817-byte bitstream 與 182,680-byte HWH；兩者是可部署產物，沒有加入 Git。
- 新增 `person_tracking/verify_pynq_zu_bringup.py`：在 PYNQ Linux 下載 Overlay，對 mailbox `0xA000_0000` 的 frame-ID 做 write/readback，再清回 0。已在開發電腦通過 Python syntax compile；尚未在板上執行，因此不能當成 MMIO 實機 PASS。
- 板子目前仍因 JTAG 模式/目前電腦網段為 `192.168.50.x` 而無法存取既有 `http://192.168.3.1/lab`（瀏覽器為 `ERR_CONNECTION_RESET`，ICMP 亦沒有回覆）。下一個實機步驟需切回 **SD**、重新上電使 PYNQ Linux 開機，再把 overlay 檔案與驗證腳本上傳到板端；這與已完成的 JTAG PL 下載是兩個不同階段。

## 2026-11-05 變更紀錄：PS IRQ 與 PYNQ-ZU 雙 USB 鏡頭網站部署包

- 盤點後確認先前設計沒有任何 RTL IRQ 或 PS IRQ 接線，故「中斷問題」是未實作而非 JTAG 連線故障。`yolox_bbox_axilite.v` 新增 `IRQ_STATUS` (`0x18`, W1C) 和 `IRQ_ENABLE` (`0x1c`)；bit 0=雙路 feature 完成、bit 1=confirmed、bit 2=frame command missing、bit 3=mailbox overrun。只要 enable 的 sticky bit 尚未清除，`irq` 維持 level high。
- `dual_camera_yolox_axilite_top.v` 匯出 annotated `irq`，`create_pynq_zu_yolox_bd.tcl` 啟用 PS `IRQ0` 並接到 `pl_ps_irq0`。`dual_camera_yolox_axis_top.v` 同步匯出 irq；`pynq_yolox_mmio.py` 加入 set/read/clear IRQ helpers。XSim `tb_yolox_command_path.v` 以 result 和 overrun 事件驗證 enable、assert、W1C clear，輸出 `YOLOX_COMMAND_PATH_PASS checks=9`。
- 在乾淨 `C:\\pynq_irq_build` 做了完整 project/BD/synth/impl：synthesis 0 error/0 critical warning；implementation 的 DRC 0 error，bitgen 0 warning/0 critical warning，post-placement WNS +47.095 ns。產物 `C:\\pynq_irq_build\\pynq_zu_rtl.runs\\impl_1\\pynq_zu_yolox_wrapper.bit` 已在 Hardware Manager 對實機 `xczu5_0` 成功下載，Tcl console 回報 device programmed。
- `live_site/dual_server.py` 現會依平台使用 Windows DirectShow 或 Linux V4L2，新增 `pynq_usb_camera_preflight.py`、`start_pynq_dual.sh` 和 `prepare_pynq_dual_bundle.py`。後者可把既有雙鏡頭網站、YOLOX ONNX、追蹤程式與可選 Overlay 打成 PYNQ 可傳送 tarball。本機已成功產生 `C:\\pynq_irq_build\\pynq_zu_dual_deploy.tar.gz`（33,467,184 bytes），列出的 12 個檔包含 `overlay/pynq_zu_yolox.bit/.hwh`；不把模型/bitstream 產物提交到 Git。
- 未驗證且仍必須完成：PYNQ SD-boot Linux 的 Python/OpenCV/V4L2 相依、兩支實際 USB webcam `/dev/video*`、YOLOX 推論、LAN 網站畫面、Overlay/MMIO/IRQ 實機事件。現行 FPGA bring-up 沒有 USB capture-to-RTL 資料路徑；雙 USB 網站是由 PYNQ PS CPU 取 UVC 影像、執行既有 YOLOX/Tracker，這符合原 Python 網站資料流但不能稱 USB frame 已進 FPGA ROI core。

## 2026-11-05 變更紀錄：可攜的 PYNQ-ZU SD-boot 一鍵部署

- 新增 `live_site/deploy_pynq_zu.ps1`。它以參數取得 `-BoardHost`、可選 `-BoardUser`（預設 `xilinx`）、`-RemoteDir`、兩個 camera index、板端 Python 指令與可選 Overlay 目錄；沒有硬編碼任何電腦 IP、使用者資料夾、Vivado build 或密碼。它先要求本機 Python/Windows OpenSSH `ssh`/`scp`，再呼叫 bundle builder，SSH 探測板端、SCP 上傳、解壓並驗證 ONNX 已到位。目標目錄存在即失敗，刻意不覆寫或遞迴刪除板上資料。
- `prepare_pynq_dual_bundle.py` 現也納入 `person_tracking/verify_pynq_zu_bringup.py`，所以同一個 tarball 可供板端 Overlay/MMIO bring-up；Overlay 仍是選配，只有指定 `-OverlayDir` 才隨包傳送。`-RunCameraPreflight` 在解壓後以 V4L2 檢查兩支 UVC；`-RunBringupCheck` 會將同包的 bit/hwh 複製到驗證程式旁、下載 Overlay，並檢查 mailbox `FRAME_ID` write/readback。兩種開關都會在失敗時保留部署資料供診斷。
- `live_site/README.md` 已提供從 clone 根目錄直接貼上的 PowerShell 命令。資料流程是：Git tracked source+YOLOX ONNX → 暫時 tarball → SSH/SCP → `~/pynq_dual_dashboard` → 可選 preflight/MMIO → 板端 `start_pynq_dual.sh`。此入口不讀取 `C:\pynq_*`、`%TEMP%` 既有產物或目前使用者的設定；暫時 tarball 僅在執行電腦的暫存區生成。
- 本機驗證：三支 Python 腳本 `py_compile` 通過；實際建立 tarball 並以 `tar -tzf` 核對 11 個必要檔（網站、YOLOX ONNX、追蹤程式、preflight、bring-up verifier）皆在包內；PowerShell AST parse 與 `git diff --check` 通過。未驗證：不同電腦的 Python/OpenSSH 安裝、板端 SSH 認證、PYNQ Linux/OpenCV/V4L2、USB 鏡頭、Overlay/MMIO 及 LAN dashboard；不可據此宣稱上板成功。

### 2026-11-05 後續：新 clone 的 YOLOX 模型取得與完整性

- 可攜性稽核發現 `person_tracking/assets/yolox.onnx` 已被專案 `.gitignore` 排除，原本的新 clone 無法通過 bundle builder 的檔案檢查。`prepare_pynq_dual_bundle.py` 現在以標準函式庫 `urllib.request` 於模型不存在或 SHA-256 不符時，從 `sources.json` 記錄的 OpenCV Zoo public model URL 下載到被忽略的 assets 路徑；只有 SHA-256 `c5c2d13e59ae883e6af3b45daea64af4833a4951c92d116ec270d9ddbe998063` 符合才以原子 replace 寫入並進入 tarball。暫存 `.onnx.download` 在成功、雜湊錯誤或下載失敗時均清除。
- 本機驗證：`prepare_pynq_dual_bundle.py` syntax compile 通過；本機現有模型 hash 與固定值一致；實際 bundle 建立並確認 `person_tracking/assets/yolox.onnx` 在 tarball 中。新電腦第一次打包必須可連網取得約 35 MB 公開模型，未在無模型的新電腦實測下載；此限制已在 README 明示。模型本體仍不進 Git。

### 2026-11-05 後續：板端依賴診斷

- 新增 `live_site/pynq_system_preflight.py`，僅讀取板端狀態：輸出 Python/platform，強制檢查 `numpy`、`cv2`、非空 YOLOX ONNX；另嘗試載入 `pynq`，缺少時輸出 `PYNQ_OVERLAY_NOTE` 但不把它誤判成 USB dashboard 的必要依賴。成功標記為 `PYNQ_SYSTEM_PREFLIGHT_PASS`。bundle builder 已納入此檔；`deploy_pynq_zu.ps1 -RunSystemPreflight` 會在 optional UVC preflight 前以板端 Python 執行它。
- 本機驗證：syntax compile、實際 Python 執行（NumPy/OpenCV/model PASS、預期 PYNQ module note）、tar listing 與 PowerShell AST parse 全部通過。此為 Windows 模擬環境檢查，不是 PYNQ Linux/PYNQ package/USB 實機證據。

### 2026-11-05 後續：離線端到端回歸

- 在工作樹乾淨且不接 PYNQ 的條件下執行 `python -m unittest discover -s person_tracking -p test_*.py -v`，結果 18 tests OK；覆蓋本地 tracker 交叉／遮擋、跨鏡頭候選連續確認／互斥、衣著特徵與相機 index 防護。於 `live_site` 執行 `python -m unittest test_dual_server.py -v`，結果 6 tests OK；覆蓋人物快照、人工配對、審核凍結、拒絕 pair 排除、照片清除與特徵歷史。
- 另實跑 `person_tracking/open_xsim_regression.ps1 -Batch`（Vivado 2024.2），XSim 編譯、elaborate 及模擬成功，輸出 `RTL_REGRESSION_PASS frames=7 checks=89`。暫存 XSim 輸出位於 `%TEMP%`，未納入 Git。上述皆為 host 模擬／合成測試；沒有呼叫 USB 相機、SSH、PYNQ Linux、Overlay/MMIO 或硬體 IRQ。

### 2026-11-05 後續：可重跑的 mailbox／IRQ XSim 回歸

- 新增 `fpga/open_xsim_yolox_command_path.ps1`，將 `yolox_bbox_axilite.v`、`yolox_frame_command_adapter.v` 與 testbench stage 至 `%TEMP%/project_xsim_yolox_command_path`，用 `xvlog`、`xelab`、`xsim` 執行。可傳 `-Batch` 供 CI/終端 PASS/FAIL，省略則開 GUI；`VIVADO_XSIM_BIN` 可覆寫 Vivado bin。這使新電腦能重跑 AXI-Lite payload commit、overrun、frame-ID 對齊、bbox latch／consume、result/overrun IRQ/W1C clear 測試，不需接 PYNQ。
- 本機實跑 Vivado 2024.2 結果為 `YOLOX_COMMAND_PATH_PASS checks=9`。更正先前文件誤載的 `checks=5`；目前 testbench 的 9 個 assert 才是可重現的實際輸出。此測試不包含 PS Block Design、Overlay 或硬體 IRQ 電氣連線。

### 2026-11-05 後續：乾淨 GitHub clone 的可攜部署驗證

- 使用 `git clone --depth 1 https://github.com/yycc0112299/-.git` 至全新 `%TEMP%/pynq_portable_clone_<GUID>/repo`，在該 clone 直接執行 `live_site/prepare_pynq_dual_bundle.py --output <temp>/pynq_dual_dashboard.tar.gz`。clone 內原本沒有 `.onnx`（ignore 規則生效），輸出明確顯示從 OpenCV Zoo URL 下載 YOLOX，並成功建立 tarball；`tar -tzf` 列出 11 個必要項目。這直接驗證了新電腦所需的 Git tracked source → model bootstrap → bundle 資料流，而不依賴原開發工作樹的模型或 Vivado 產物。
- 驗證界線：此為同一台 Windows 的全新目錄／遠端 clone 模擬，證明 GitHub snapshot 和公開模型來源可用；尚未驗證另一台實體電腦、Windows OpenSSH、PYNQ SSH 認證、Linux package、UVC、Overlay 或 LAN dashboard。暫存 clone、下載模型與 tarball 位於 `%TEMP%`，非專案原始碼，不納入 Git。

### 2026-11-06：PYNQ-ZU 官方 SD 映像重新燒錄（Etcher 驗證完成）

- 官方 AMD download 的 `pynq_zu_v3.1.1.zip`（2,250,235,183 bytes）SHA-256 為 `7F61F9F7D9B74DB2DE64B8AC443CE472894C3FA70426906367A4386928F5A810`，與本機既有同名 ZIP 完全一致。ZIP 中的唯一映像為 `pynq_zu_2025_09_25.img`（9,840,650,240 bytes），所以既有「2025-09」映像實際上就是目前官方 v3.1.1，不是另外一個舊版本。
- 使用 balenaEtcher 重新選取該 `.img` 與人工核對的 `Generic- Multi-Card USB Device`（15.9 GB；先前 Windows disk inventory 為 Disk 2），而非沿用 Etcher 的舊成功畫面。新一輪流程完成寫入後進入 Verify；即時觀察到驗證 6%、22%、37%、52%，速度約 19.5–19.8 MB/s，最後 Etcher 對本輪的 `pynq_zu_2025_09_25.img` 顯示「燒錄成功」，完成速度 23.2 MB/s。這是工具的整體寫入與驗證 PASS 證據。
- Etcher 成功後自動卸載目標；Windows 隨後對 Disk 2 顯示 `No Media`／0 bytes，故未把先前舊卡的分割區列舉誤當作本輪後驗證。需重新插回板子後，才能驗證 PS-STATUS、DONE/LED、USB Composite 網卡、`192.168.3.1/lab`、SSH、Overlay/MMIO 及 UVC；本次不宣稱這些板端功能已通過。
- 官方 ZIP、解壓 `.img` 和重複下載副本位於 `C:\Users\dsic\Downloads\`，是大型可重新取得的本機部署媒體，未加入 Git；本次只同步程式交接紀錄。
- 這次紀錄已在整合共享 `main` 的新增提交後，以 `65c36f8` 成功推送至 `origin/main`；沒有覆寫其他電腦先行推送的校正／benchmark 變更。

