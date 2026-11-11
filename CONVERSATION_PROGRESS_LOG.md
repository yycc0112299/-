# 對話與進度同步紀錄

## 2026-11-06 — Vivado USB-camera Block Design 與 Vitis 控制起始實作

- 需求／決策：依使用者要求改為 Vivado 建硬體、Vitis 寫控制；現有鏡頭為兩支 USB Logitech C270，故 USB0/USB1 必須保留在 PYNQ-ZU PS 的 MIO，而非虛構 PL 相機腳位。
- 實際完成：新增可重跑的 PYNQ-ZU project/BD/XSA-export TCL、BD 合約 test，以及 Vitis C controller/host test。BD 已在 Vivado 2024.2 成功 `validate_bd_design`；設計包含 PS USB、AXI DMA、DDR HP0、AXI-Lite mailbox、frame ID GPIO、64-bit stream 和 PS IRQ。host test 驗證 mailbox 寫入順序與無效地址防護。
- 驗證界線：XSA export 的 synthesis child jobs 尚在 Vivado queue，尚未產生 XSA/bitstream；沒有 Vitis BSP 編譯、PYNQ 上板、UVC/DMA/PL 實機影像或雙鏡頭成功證據。`%TEMP%` Vivado build/log 是可重建暫存，不上傳。
- Git／同步：本輪待完成 diff/test 後建立本機提交並推送；最終提交與推送結果將由後續紀錄補上。

本檔保留每次已完成、可交付進度的精簡對話摘要，讓後續接手者能追溯決策與 GitHub 同步狀態。它不是逐字聊天備份；不記錄密碼、私人連結、個人影像、模型權重或機器特有的敏感資訊。

## 紀錄格式

每次完成一項進度時追加：日期、使用者需求／已作決策、實際變更、驗證界線、提交雜湊及推送結果、未完成事項。若這次沒有檔案修改或工作尚未完成，不新增「完成」項目。

## 2026-11-05 — 建立對話／進度同步機制與歷史稽核

- 需求：所有專案對話在每次完成一個進度後，要有可上傳到共同 GitHub 的紀錄，並檢查先前是否有已完成但未同步的工作。
- 實際變更：新增本檔，並在 `AGENTS.md` 納入強制的「完成進度 → 追加摘要 → 同次 commit + push」流程。內容採可交接的摘要，而非逐字聊天備份，以避免將私密資料和冗長上下文推上 GitHub。
- 歷史稽核：檢查時 `main` 與 `origin/main` 都是 `5fe1467`（`Add PYNQ-ZU IRQ and USB camera deployment`），最近 20 筆專題進度提交均可在遠端分支歷史看見。Git 歷史沒有先前的對話紀錄檔，因此無法從倉庫重建曾未被寫入檔案的逐字對話；沒有證據可判定哪一段既有聊天「沒有上傳」。
- 未上傳項目：工作樹存在未追蹤的 Vivado/XSim 模擬日誌、暫存輸出和本機網站日誌。它們屬可重建暫存或可能包含本機資訊，且已由 `.gitignore` 規則排除；本次不納入版本控制。
- 驗證／同步：本次將檢查 Markdown 差異、建立提交並推送；提交雜湊及實際推送結果在完成後補入下一則紀錄（本項本身的最終提交會由 Git 歷史可追溯）。

## 2026-11-05 — 同步結果

- 對話／進度同步機制已提交為 `5cd5812`（`Add conversation progress sync log`），並成功推送至 `origin/main`；遠端分支從 `5fe1467` 前進至 `5cd5812`。
- 此結果紀錄本身會以後續提交推送，確保 GitHub 中可直接查到這次的同步結果。

## 2026-11-05 — 換機前 GitHub 可攜性交接盤點

- 需求：使用者將改用其他電腦繼續專題，要求把目前這台電腦負責的專題內容同步到 GitHub，讓後續可由倉庫接續。
- 實際變更：先 fetch 並確認 `main` 與 `origin/main` 同為 `46e9371`；新增根目錄的 Vivado/XSim、本機輸出、暫存目錄和網站日誌 ignore 規則，並更新兩份進度文件與共享內容索引，列明可攜入口和換機順序。
- 未上傳項目與原因：根目錄 Vivado/XSim logs、波形、`.Xil/`、`xsim.dir/`，以及 `output/`／`tmp/` 的簽名文件預覽、硬體照片、暫時桌面啟動器與本機診斷，都是可重建暫存、私人素材或含本機資訊，並非可攜原始碼；本機網站三個 runtime log 同樣排除。
- 驗證界線：本次驗證 Git 遠端基線、受追蹤檔案清單與忽略規則，沒有重跑相機、PYNQ Linux、Overlay/MMIO 或 FPGA 實機。建立提交與實際推送結果會在下一則紀錄補入。

## 2026-11-05 — 換機交接同步結果

- 可攜性交接整理已提交為 `3955057`（`Document cross-computer project handoff`），並成功推送至 `origin/main`；遠端 `main` 已由 `46e9371` 前進到 `3955057`。
- 推送後以 `git ls-remote --heads origin main` 核對遠端 commit 與本機 HEAD 相同。本則同步結果會以緊接的紀錄提交推送，讓下一台電腦在 GitHub 可追溯完整結果。

## 2026-11-05 — PYNQ-ZU 換電腦可貼上式部署入口

- 需求／決策：板子尚不能切換到 SD 時，先完成不依賴目前電腦的部署流程；日後任何已 clone 此倉庫的 Windows 電腦可只填入 PYNQ IP 後執行。
- 實際變更：新增 `live_site/deploy_pynq_zu.ps1`，建立 bundle、SSH/SCP 傳送、非破壞性解壓，並提供可選 USB camera preflight 與 Overlay/MMIO mailbox check；bundle 同時納入既有 bring-up verifier。README 加入單行 PowerShell 操作方式。
- 驗證範圍：本機 Python syntax compile、實際 tarball 建立與內容列舉、PowerShell parse 及 Git whitespace 檢查通過。板子尚未 SD 開機，故沒有 SSH、UVC、PYNQ Overlay/MMIO 或網頁實機證據。
- 未上傳項目：測試產生的 tarball 位於被 Git ignore 的 `output/`，為可重建暫存；bitstream、HWH、Vivado 產物及任何帳密皆未納入 Git。
- Git／同步：已提交為 `36e94e1`（`Add portable PYNQ-ZU deployment command`）並成功推送到 `origin/main`。本同步結果將隨下一筆紀錄提交保留於 GitHub 歷史。

## 2026-11-05 — 修正新 clone 缺少 YOLOX 模型的部署風險

- 需求／決策：確保「任何已 clone 的新電腦可直接貼上部署命令」不是只在目前已有模型的電腦成立。
- 實際變更：bundle builder 缺少或雜湊不符 ONNX 時，會下載專案既有來源所指的 OpenCV Zoo 模型、核對固定 SHA-256，再納入部署包；README 與交接文件記錄首次須連網及模型不入 Git 的原因。
- 驗證範圍：已以現有模型核對 SHA-256，實際產生 tarball 並確認 ONNX 在包內，Python compile 及 Git whitespace 檢查通過；未模擬全新電腦下載，亦未進行板端 SSH 或硬體測試。
- Git／同步：已提交為 `16a7d45`（`Download YOLOX model for portable deployment`）並成功推送至 `origin/main`；本同步結果會隨後續交接紀錄保留於 GitHub 歷史。

## 2026-11-05 — 增加 PYNQ SD-boot 系統前置檢查

- 需求／決策：在日後實板部署時，先辨識 Python/模型/OpenCV 缺失，再嘗試開啟 USB 相機，讓問題可直接從終端輸出定位。
- 實際變更：新增並打包 `pynq_system_preflight.py`，部署入口增加 `-RunSystemPreflight`；README 的單行命令先跑系統檢查再跑兩鏡頭 V4L2 preflight。
- 驗證範圍：本機已實跑 Python/NumPy/OpenCV/model 成功、PYNQ package 缺失提示、tarball 內容、Python compile、PowerShell parse 與 whitespace check。沒有 PYNQ Linux、SSH、UVC 或 Overlay 實機測試。
- Git／同步：已提交為 `04c7d47`（`Add PYNQ deployment system preflight`）並成功推送至 `origin/main`；本同步結果會隨後續交接紀錄保留於 GitHub 歷史。

## 2026-11-05 — 不接板子的軟體與 RTL 回歸驗證

- 需求／決策：板子尚未可切換時，先完成所有可在開發電腦驗證的追蹤、網站與 RTL 回歸。
- 實際完成：person tracking unittest 18/18 PASS；dual dashboard 合成 unittest 6/6 PASS；Vivado 2024.2 XSim batch regression 輸出 `RTL_REGRESSION_PASS frames=7 checks=89`。
- 驗證界線：這些結果覆蓋本機 Python 資料流程與 Verilog 模擬；沒有相機、PYNQ Linux、SSH、Overlay/MMIO、IRQ 或瀏覽器 LAN 實機證據。XSim 暫存產物在 `%TEMP%`，不進 Git。
- Git／同步：已提交為 `168d7b6`（`Record offline software and RTL regression`）並成功推送至 `origin/main`；本同步結果會隨後續交接紀錄保留於 GitHub 歷史。

## 2026-11-05 — 可重跑 PYNQ mailbox／IRQ XSim 回歸

- 需求／決策：在不接板子的期間，讓後續電腦能直接重跑 AXI-Lite mailbox 與 frame command adapter 的 RTL 回歸，並以實際 testbench 輸出校正文檔。
- 實際變更：新增 `fpga/open_xsim_yolox_command_path.ps1` 及操作說明；修正三處舊文件的 `YOLOX_COMMAND_PATH_PASS checks=5` 為實測 `checks=9`。
- 驗證範圍：本機 Vivado 2024.2 完成 compile/elaborate/sim，輸出 `YOLOX_COMMAND_PATH_PASS checks=9`；PowerShell parse 與 Git whitespace 檢查通過。沒有 PYNQ、Overlay、PS Block Design 或實體 IRQ 測試。
- Git／同步：已提交為 `7130467`（`Add repeatable YOLOX command path regression`）並成功推送至 `origin/main`；本同步結果會隨後續交接紀錄保留於 GitHub 歷史。

## 2026-11-05 — 乾淨 GitHub clone 的可攜部署實測

- 需求／決策：確認新電腦 clone 後不會因 ignored YOLOX model 而無法直接打包部署。
- 實際完成：從 GitHub `main` 進行 depth-1 clone 到全新 `%TEMP%` 目錄，直接執行 bundle builder；它自動下載官方 YOLOX ONNX，並成功建立 tarball，內容列舉為 11 個必要檔。
- 驗證界線：此驗證涵蓋 GitHub clone、模型 bootstrap 與打包，不涵蓋另一台物理電腦、SSH/SCP、PYNQ Linux、USB 相機、Overlay/MMIO 或網站畫面。clone/tarball/model 都是 `%TEMP%` 暫存，不上傳。
- Git／同步：已提交為 `cf5cf56`（`Record clean clone deployment verification`）並成功推送至 `origin/main`；本同步結果會隨後續交接紀錄保留於 GitHub 歷史。

## 2026-11-06 — PYNQ-ZU SD 卡官方映像重新燒錄

- 需求／決策：因板上 `PS ERR` 紅色、SD 開機失敗，重新寫入官方 PYNQ-ZU v3.1.1 映像；先核對既有下載，避免將 2025-09 的檔名誤判為過時版本。
- 實際完成：官方 ZIP SHA-256 為 `7F61F9F7D9B74DB2DE64B8AC443CE472894C3FA70426906367A4386928F5A810`，與本機既有 ZIP 完全相同，內容為 `pynq_zu_2025_09_25.img`。已在 balenaEtcher 明確選取 15.9 GB `Generic- Multi-Card USB Device` 後進行新的寫入；本輪 Verify 曾觀察至 52%，最後 Etcher 顯示「燒錄成功」（23.2 MB/s）。
- 驗證範圍：此證據涵蓋 Etcher 的寫入與內建驗證；Etcher 完成後自動卸載媒體，Windows 顯示 `No Media`，未對卸載後的 Disk 2 做無效的分割區宣稱。尚未在板子上重新開機，故 PS ERR、Linux、USB 網路、Jupyter、SSH、相機、Overlay 及 FPGA 皆仍未驗證。
- 未上傳項目：官方 ZIP、9.84 GB `.img` 和重複下載副本均在 `C:\Users\dsic\Downloads\`，為大型可重建部署媒體，未上傳 Git；不含帳密或私人資料。
- Git／同步：初次推送因遠端已有新提交而被拒絕；已 `fetch`、成功 rebase 至 `origin/main` 後，以 `65c36f8`（`Record verified PYNQ-ZU SD imaging`）成功推送至 `origin/main`。此同步結果隨後續文件提交保留。
## 2026-11-06 — PYNQ Linux 環境與雙 USB dashboard 實機 bring-up

## 2026-11-06 — Vivado PS USB／DMA Block Design 時脈診斷

- 需求／決策：依 USB 實際拓撲以 PS UVC→DDR→AXI DMA→PL→Vitis 重建，而不將 USB D+/D- 偽裝成 PL 影像腳位。
- 實際完成：100 MHz implementation 的 post-placement WNS 約 -35 ns，關鍵位置在既有 YOLOX ROI feature accumulator；已將 PL0 與 RTL 匯流排 clock metadata 同步改為 20 MHz。合約測試 2/2 PASS，未產生或使用時序違反的 bitstream。
- 驗證界線／未完成：乾淨 project staging PASS；Vivado 2024.2 在 module-reference GUI customization 出現 `rodin:slave11`，因此新 BD validation、implementation、XSA、Vitis build 和硬體控制均未完成。暫存 build 僅在 `%TEMP%`，不進 Git。
- Git／同步：已提交為 `a360398`（`Record USB DMA timing constraint`）並成功推送至 `origin/main`；封裝／XSA 工作仍未完成。

- 需求：在已 SD 開機的 PYNQ-ZU 裝好可用 Linux 環境，讓接在板上的兩支 USB 鏡頭能接入專題網站。
- 實際完成：JupyterLab 可達；板端 Python、NumPy、OpenCV、PYNQ、YOLOX ONNX 均驗證可用。網站 bundle 已傳到板子，系統 preflight PASS；相機 index 0/2 都曾讀到 640×480 frame，專案 UVC preflight PASS。修正舊 OpenCV 無 `cv2.data` 的啟動崩潰、PYNQ Host allow-list 參數與 API 覆蓋相機 index 的問題；`/api/health` 已由開發電腦實測成功。
- 驗證界線與未完成：網站開始雙鏡頭擷取後，kernel 記錄 USB reset、`Not enough bandwidth for new device state/altsetting 7`、device 3/4 disconnect，且 `/dev/video*` 消失。未驗證持續影像串流、YOLOX 偵測、網頁畫面或 FPGA video data path；需先改善 USB 供電／分流或降低 UVC 傳輸需求。
- 未上傳項目：部署 tarball、模型和板上 `/root/pynq_dual_dashboard_v*` 都是可重建的本機／板端部署產物，不進 Git；不含帳密、私人影像或連結。
- Git／同步：已提交為 `0b8b768`（`Fix PYNQ dual camera dashboard bring-up`）並成功推送至 `origin/main`；本機與遠端 `main` 已同步。

## 2026-11-06 — 重新插拔後的雙 UVC 複測

- 實際完成：重新登入 JupyterLab、重新插拔後，兩支 Logitech C270 再次被 Linux 列成 `/dev/video0`–`/dev/video3`。專案 UVC preflight 以 camera A=0、B=2 再次 PASS，兩路皆讀到 640×480。
- 驗證結果：以已修正的 v5 dashboard 啟動，health endpoint 成功，POST `/api/start` 保留 `[0,2]`；約 7 秒後 `/api/live` 回報「雙鏡頭擷取中斷」、frame_id=0。未產生持續影像／YOLOX 結果。
- 判定／未完成：重插仍重現同時串流失敗，與先前 kernel 的 USB bandwidth/altsetting 錯誤一致。需要外接供電 hub、不同 root hub 或降低 UVC 格式/傳輸需求後才能繼續；這不是已完成的相機實機驗證。
- Git／同步：已提交為 `1995476`（`Record repeated PYNQ UVC bandwidth failure`）並成功推送至 `origin/main`。

## 2026-11-06 — 低頻寬雙鏡頭串流嘗試

- 需求：使 PYNQ 的雙鏡頭畫面可傳到電腦網站。
- 實際變更：Linux UVC 協商改為 MJPEG、預設 320×240、10 FPS，並可經 `PYNQ_UVC_FPS/WIDTH/HEIGHT` 覆寫；預檢查同步採用此低頻寬模式。
- 驗證：本機 6 項網站測試與 syntax compile PASS；透過 SSH 將 v7 部署到板子，網站 `/api/start` 保留 camera `[0,2]`。10 秒後 `/api/live` 仍為「雙鏡頭擷取中斷」、frame_id=0。
- 未完成：兩路畫面尚未能持續出現在電腦網站。需改變 USB root hub／外接供電或只保留一路後，再進行實機驗證。

## 2026-11-06 — Vivado PS USB／DDR／DMA Block Design XSA 匯出

- 需求／決策：依使用者指定的 Vivado 硬體檔加 Vitis 控制檔流程，保留 USB 鏡頭的真實 PS USB→DDR→AXI DMA→PL 架構，而非將 USB D+/D- 誤接為 PL 影像腳。
- 實際完成：新增可重跑的 `fpga/package_pynq_zu_video_ip.tcl`，把 staged `dual_camera_yolox_axis_top.v` 包為 `project.local:video:dual_camera_yolox_axis:1.0` IP Catalog core；BD script 改由此 IP 建立自訂 RTL，排除 Windows module-reference GUI cache 的 `rodin:slave11` 失敗。乾淨 Vivado 2024.2 build 的封裝、BD validation、synthesis、implementation、bitgen 與 `write_hw_platform -include_bit` 全部完成。
- 驗證範圍：bitstream 前 DRC 為 0 errors；routing 估算 WNS `+0.193 ns`、WHS `+0.012 ns`；含 bitstream 的 XSA 確實建立。暫存 build、bitstream、XSA 和 logs 位於 `%TEMP%`，為可重建產物，不上傳 Git。尚未建立/編譯 Vitis BSP/application，也尚未以此設計 JTAG 上板、啟動 DMA、接收 UVC frame 或驗證雙鏡頭資料流。
- Git／同步：本輪會連同三份進度文件做 whitespace/合約檢查、建立本機提交並推送 `origin/main`；實際 commit 與推送結果將由後續紀錄補上。

## 2026-11-06 — Vitis XSA platform 建置環境診斷

## 2026-11-06 — 完整 Vitis Embedded platform／A53 控制程式 host build

- 需求／決策：使用已完成的 PYNQ-ZU USB/DMA XSA 建立可重現的 A53 standalone 控制程式，並避免原先一般 Vitis 安裝缺少 Embedded 工具鏈的問題。
- 實際完成：安裝 Vitis Embedded Development 2024.2 至本機隔離路徑；`xsct` 與 Vitis Embedded client 均實測可啟動。使用短 Windows workspace 從 XSA 產生 platform、BSP、ZynqMP FSBL，platform export 回報 `SUCCESS`；再編譯現有控制程式為 `pynq_zu_usb_video_app.elf`（265,944 bytes）。實際 `xparameters.h` 證實 mailbox 基址宏為 `XPAR_YOLOX_VIDEO_RTL_0_BASEADDR`，已修正程式碼。新增可重建腳本 `build_vitis_embedded.py`。
- 驗證範圍：已完成 host-side Vitis platform/ELF build；沒有 JTAG 下載新 XSA/ELF、沒有 PYNQ-ZU USB UVC、DDR DMA、PL stream、mailbox 或 IRQ 實機驗證。安裝映像、Vitis 目錄與 temporary workspaces 屬本機工具／產物，不進 Git；第三台尚未安裝或驗證。
- Git／同步：本次會連同進度文件提交並推送 `origin/main`；實際提交與推送結果以下一筆終端回報為準。

### 同步結果

- 已提交為 `503718d`（`Build PYNQ-ZU Vitis embedded control app`）並成功推送至 `origin/main`；工作樹與遠端 `main` 同步。

## 2026-11-06 — JTAG 實機下載前的可見性掃描

- 需求／決策：在 Vitis host build 完成後，以 JTAG 對 PYNQ-ZU 下載並驗證控制端；先只進行 target 枚舉，避免未偵測到晶片時寫入。
- 實際驗證：Windows 正常列出 FTDI USB Serial Converter A/B 與 COM5，Hardware Server 正在 `localhost:3121`。XSCT 連線沒有列出 JTAG target；停止並重啟 Hardware Server 後重新掃描，仍沒有 target。
- 驗證界線／未完成：沒有下載 XSA、bitstream 或 ELF，未修改板子。需先由實體板端恢復供電、JTAG boot switch／線材／chain 的可見性，才可進行下載、mailbox read/write 與 DMA/USB 測試。

## 2026-11-06 — Vivado／Vitis JTAG AXI 控制實機驗證

- 需求／決策：把已完成的 USB/DMA Block Design 與 Vitis A53 control ELF 真正下載到 PYNQ-ZU，驗證 PS→PL AXI 控制，而非僅 host build。
- 實際完成：Vivado Hardware Manager 成功開啟 `Xilinx/1234-tulA`，枚舉 `xczu5_0`、`arm_dap_1`，並將 7,797,821-byte `pynq_zu_usb_video.bit` 下載到 `xczu5_0`。XSCT 改用 `connect -host localhost -port 3121` 後正確枚舉 PSU/APU/A53；實跑 system reset、PS/DDR init、PL config、A53 #0 ELF download/run。新版控制 ELF 提交 frame 42 bbox payload，讀回 GPIO、mailbox frame 與 status；乾淨重跑 result=`0`、GPIO=`42`、mailbox frame=`42`、status=`3`。
- 驗證範圍：這證明 Vivado bitstream 加 Vitis A53 對實機 AXI GPIO/mailbox 的寫讀控制。status `3` 是 pending/pair-present，因尚未有 UVC/DMA AXI stream 消耗這筆 command；未證明 UVC、DDR frame capture、DMA、PL feature/bbox、IRQ 或雙相機畫面。
- Git／同步：本次會提交 control smoke-test 原始碼與三份紀錄並推送 `origin/main`；實際提交結果由下一筆紀錄承接。

### 同步結果

- 已提交為 `5684f47`（`Verify PYNQ-ZU Vitis AXI control over JTAG`）並成功推送至 `origin/main`；工作樹與遠端 `main` 同步。

- 需求／決策：使用已完成的 PYNQ-ZU USB/DMA XSA 建立 Vitis A53 standalone platform，讓 Vitis 取代 Jupyter 擔任 AXI DMA、GPIO 與 mailbox 的控制端。
- 實際驗證：Vitis 2024.2 Python CLI 已實際啟動並讀取 XSA。初始 Lopper installation path 為 `null`；確認隨附 Lopper 包缺失 requirements link 後，以該安裝包的離線 wheels 建立本機 Lopper virtualenv，並驗證 `lopper -h`、YAML 與 libfdt imports。設定 `VITIS_LOPPER_INSTALL_LOC` 後，Vitis 已進一步嘗試從 XSA 產生 SDT。
- 驗證界線／阻礙：本機 Vitis 安裝未提供 `xsct`，也沒有 Vitis-side embedded software tree。即使 `ESW_REPO` 指向已存在的 Vivado `data/embeddedsw`，Vitis 仍在 SDT generation 失敗；未產生 platform、BSP、`xparameters.h`、ELF 或 JTAG application。Lopper virtualenv、Vitis temporary workspaces 和 logs 是此電腦本機工具產物，不上傳。
- Git／同步：本次把可重現的環境診斷及限制同步至文件；完成檢查後會建立提交並推送 `origin/main`，實際結果由下一筆紀錄承接。

## 2026-11-06 — Vivado/Vitis 完整影格 DMA 實板驗證

- 需求／決策：依 Vivado 硬體檔 + Vitis 控制檔路線，讓一個完整影格由 DDR 經 AXI DMA 送入 PYNQ-ZU PL；不將 USB UVC 的 D+/D- 誤當成 PL camera pins。
- 實際完成：修正 Block Design AXI DMA simple-mode transfer-length width 從 14 到 23；全新短路徑 Vivado build 的 bitstream/XSA 成功（bitgen 0 errors），新 Vitis Embedded BSP 讀到 `XPAR_AXI_DMA_0_SG_LENGTH_WIDTH=0x17`，並編譯 351,048-byte A53 ELF。Vitis 以 640×480 packed synthetic DDR frame 對 AXI DMA MM2S 發出一次完整傳輸。
- 實機驗證：透過 `localhost:3121` JTAG 完成 reset、PS init、PL bitstream 與 ELF download。執行後 JTAG 讀回 result `0`、GPIO `42`、mailbox frame `42`、mailbox status `2`、DMA status `0x1002`；DMA register 亦為 `0x1002`（idle/IOC completion）。
- 驗證界線／未完成：已證明 Vitis A53→DDR→AXI DMA→PL stream 及控制資料可實際完成一張 synthetic frame；尚未取得 PS USB UVC 真實 frame、未解決雙 C270 持續串流的實體 USB 資源問題，也未驗證真實 YOLOX 或 IRQ handler。
- Git／同步：待本次程式與三份紀錄的差異檢查、提交及 push 後補上 commit 結果。
## 2026-11-06 — full-frame DMA 契約回歸與交接文件修正

- 需求／決策：防止已驗證的完整影格 DMA 設定回退，且將文件從「DMA 未驗證」更新為事實。
- 實際完成：新增 static contract assertion，要求 BD script 保持 `CONFIG.c_sg_length_width {23}`；更新 FPGA/Vitis README，記錄 synthetic full-frame DMA 的實板結果和 UVC/雙鏡頭尚未完成的邊界。
- 驗證範圍：待執行 unittest 後補上；本輪未接觸真實 UVC 相機或變更實板配置。
- Git／同步：待本輪提交與 push 後補上結果。

### 編譯器修正

- 先前 `0xC0000135` 只影響錯誤使用的 Windows wrapper。改用 `gnu/aarch64/nt/aarch64-linux/bin/aarch64-linux-gnu-gcc.exe` 並把其 bin 放入 PATH 後，`uvc_v4l2_packer.c` 以 `-Wall -Wextra -Werror` 成功產生 74,624-byte AArch64 ELF64 PIE；`readelf -h` 已實際確認 Machine=`AArch64`。這仍不是板端 UVC/DMA runtime 驗證。
## 2026-11-06 — standalone UVC middleware 可行性確認

- 需求／決策：確認 Vitis standalone 是否能直接承擔 Logitech C270 UVC capture，避免在已完成 DMA 路徑上加入不存在的 driver。
- 實際完成：搜尋完整 Vitis Embedded 2024.2 `embeddedsw`；USB driver examples 僅見 storage/mouse/keyboard/microphone，沒有 UVC/USB Video Class host middleware。
- 結論／未完成：standalone A53 ELF 保留為已實證的 DMA/PL controller。真實 UVC 必須用 PYNQ Linux UVC/V4L2，下一步為 Vitis Linux A53 app 加 CMA contiguous DMA buffer；板端目前 USB 網路在 standalone reset 後未回來，尚無法做 UVC 實測。
- Git／同步：待本輪文件提交與 push 後補上結果。
## 2026-11-06 — Vitis Linux UVC/V4L2 frame-packing 元件

- 需求／決策：在不存在 bare-metal UVC middleware 的前提下，實作 Vitis Linux A53 route 的真實 UVC 輸入端，而不退回 Jupyter 或虛構 PL pins。
- 實際完成：新增 `linux/uvc_v4l2_packer.c`，兩路 V4L2 YUYV MMAP capture 會產生與 PL `S_AXIS_VIDEO` 相符的 640×480 packed dual-RGB uint64 frame。
- 驗證界線／未完成：嘗試隨附 AArch64 Linux cross compiler + sysroot 時，compiler 在產生 ELF 前以 `0xC0000135`（Windows loader dependency 缺失）結束，即使載入 `settings64.bat` 相同，因此尚未交叉編譯或在 PYNQ Linux 執行。輸出檔不是 DMA buffer；仍需板端 Linux boot、穩定兩路 UVC、以及 CMA/dma-heap/udmabuf/driver 的 contiguous physical memory allocation，才可接到 AXI DMA。
- Git／同步：待本輪提交與 push 後補上結果。
## 2026-11-06 — PYNQ-ZU SD boot/JTAG 操作邊界確認

- 需求／決策：釐清真實 UVC Linux 測試是否會排斥 Vivado/Vitis JTAG，避免將 boot switch 留在 standalone JTAG 而失去 UVC。
- 實際確認：官方 PYNQ-ZU Reference Manual v1.2 指出 `JTAG SD` boot switch 向左為 JTAG、向右為 MicroSD。切至 SD 並 power-cycle 可恢復 PYNQ Linux；SD boot 後仍可使用 JTAG 除錯。
- 驗證界線／未完成：這是官方操作規格確認，尚未因實體 switch/power-cycle 在目前回合再次取得 Linux、V4L2 或 UVC runtime 證據。
- Git／同步：待本輪文件提交與 push 後補上結果。
## 2026-11-06 — SD-boot 後 Vitis Linux UVC preflight

- 需求／決策：在下次可切回 SD/Linux 前，準備不依賴 Jupyter 的實板 UVC runtime gate。
- 實際完成：新增 `run_uvc_vitis_preflight.sh`；它驗證兩個 V4L2 device、執行 AArch64 packer、並要求輸出剛好為 640×480×8 = 2,457,600 bytes，PASS marker 為 `PYNQ_ZU_UVC_VITIS_PREFLIGHT_PASS`。
- 驗證範圍／未完成：Windows host 沒有可用 Git Bash/WSL，尚未執行 POSIX shell syntax check；更尚未因板子仍為 standalone/JTAG state 在 PYNQ Linux 執行，也不含 DMA/CMA handoff。
- Git／同步：待本輪提交與 push 後補上結果。
## 2026-11-06 — Vitis Linux UVC packer 可重跑建置

- 需求／決策：讓下次上板前可用一個受版本控制的命令重建 AArch64 UVC packer，避免再誤用失敗的 Windows wrapper。
- 實際完成：新增 `build_linux_uvc_packer.ps1`，使用 Vitis direct GNU compiler、暫時 PATH、`-Wall -Wextra -Werror`，輸出 deployable ELF 與 `PYNQ_ZU_UVC_PACKER_BUILD_PASS` marker。
- 驗證範圍／未完成：以 `%TEMP%/pynq_zu_uvc_build_check` 實跑成功，生成 74,624-byte packer；未進行板端 execution 或 DMA handoff。
- Git／同步：待本輪提交與 push 後補上結果。
## 2026-11-11 — Vitis Linux 真實 C270 UVC bring-up

- 需求／決策：在 SD-boot PYNQ Linux 上以 Vitis Linux C program（非 Jupyter）驗證兩支實體 C270 的 V4L2→packed frame 路徑。
- 實際完成：Composite USB/RNDIS、HTTP、SSH 都已實測通；以 `xilinx` 帳號登入後確認 Linux 6.6.10、兩支 `046d:0825` C270、`/dev/video0..3`。交叉編譯 packer 以 SCP 部署且板端辨識為 AArch64 ELF。
- 實際發現：第一輪兩路 640×480 YUYV capture 失敗，`dmesg` 明確是 second C270 的 `Not enough bandwidth ... altsetting 7`，不是檔案空間或 FPGA/DMA。packer 現改為以 `VIDIOC_S_PARM` 協商 10 FPS，再進行實測。
- 驗證界線／未完成：10-FPS build/retest 與 DMA/CMA handoff 尚未完成；本輪暫以 sudo 越過 `xilinx` 缺少 `video` group，未永久改帳號。

## 2026-11-11 — 實板雙 C270 bandwidth 結論、兩板架構與 DPU audit

- 需求／決策：先以一板兩鏡頭確認 Vitis Linux UVC 方案；後續改為兩板各一鏡頭、Linux/Wi-Fi 互通，並以 YOLOv8 為人物偵測目標、研究 DPU 接法。
- 實際完成：更新並 cross-build Vitis Linux packer，部署至 SD-boot PYNQ Linux。兩個 C270 capture nodes 實際協商為 320×240/10 FPS/YUYV，但第二路 `VIDIOC_STREAMON` 回傳 `ENOSPC`；`dmesg` 為 shared USB hub 的 `Not enough bandwidth ... altsetting 7`。加入可重跑 `--probe` 與 `--mjpeg-stream-test`；probe 顯示 C270 支援 YUYV/MJPG 與多個 sizes/FPS，而 320×240/10-FPS MJPEG 兩路 stream-only test 仍在第二路 `STREAMON` 失敗。這排除只靠降低解析度、FPS 或改 MJPEG 即可修復的說法。
- 實際完成：新增 `docs/pynq-zu-two-board-dpu-architecture.md`，規定第一個可交付目標為每板一鏡頭、Linux UVC/V4L2、每板 inference、Wi-Fi versioned detection message；raw video 傳輸留為後續選項。文件也將既有 YOLOX assets 與新 YOLOv8 target 分開，採 detector adapter 保持 tracker/fusion interface。
- DPU audit：板端實測無 `xdputil`、VART Python module 或 `/dev/dpu`。目前 PYNQ image 不具 DPU hardware/runtime；尚未有 YOLOv8 quantization、`.xmodel`、VART 或 DPU inference。需先為 `xczu5eg` 完成 DPUCZDX8G Vivado integration、matching Linux driver/VART/CMA image 和 DPU-specific `arch.json`。
- 驗證範圍／未完成：本次已實證實板 USB failure、AArch64 packer build/deploy/run 與 DPU runtime absence；未驗證單鏡頭持續串流、第二板、Wi-Fi、DPU image/bitstream、YOLOv8 inference 或 DMA/CMA handoff。
- Git／同步：已提交為 `8391da8`（`Diagnose PYNQ dual UVC and plan DPU architecture`）並成功推送至 `origin/main`；本機 `linux/build/` 只有可重建 AArch64 ELF，未上傳。

## 2026-11-11 — 兩板 Linux Wi-Fi person-detection protocol 基礎

- 需求／決策：為後續每板一鏡頭、Wi-Fi 互傳資料建立可由 YOLOX 或未來 YOLOv8/DPU 使用的共同介面，先傳 compact detections 而非 raw video。
- 實際完成：新增 `person_tracking/peer_protocol.py`，實作 versioned TCP newline-JSON schema `pynq-person-detections-v1`、strict packet/box/class validation、single-packet sender、持續 receiver 與 latest-result JSON 輸出；新增 four-case tests。
- 驗證範圍：`python person_tracking/tests/test_peer_protocol.py` 實測 4 tests PASS，含 localhost TCP framed transfer；`py_compile` PASS。這是開發電腦 loopback，不是兩塊 PYNQ 的 Wi-Fi 或真實 detector/DPU 推論驗證。
- Git／同步：待本輪差異檢查、提交與 push 後補上 commit 結果。
