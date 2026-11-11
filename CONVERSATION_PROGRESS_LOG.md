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
- Git／同步：已提交為 `a1ff8f4`（`Add two-board detection peer protocol`）並成功推送至 `origin/main`。

## 2026-11-11 — PYNQ-ZU native DPU B512 Vivado bitstream feasibility

- 需求／決策：依「Vivado 硬體檔 + Vitis/Linux 控制檔」重做 DPU 路線；USB C270 維持 PS USB/Linux UVC，不把 D+/D− 虛構成 PL camera pins。
- 實際完成：由官方 AMD DPUCZDX8G source 的原生 `xilinx.com:ip:dpuczdx8g:4.0` 建立 PYNQ-ZU `xczu5eg-sfvc784-1-e` B512 單核心 Block Design。DPU control、instruction、DATA0/1、clock/reset 和 IRQ 已以 tracked Tcl 接至 A53 HPM0、PS HP2、HP0/HP1、PL clocks 和 IRQ0；新增可重跑 create/inspect/synthesis/implementation Tcl。
- 實際驗證：Vivado 2024.2 `validate_bd_design`、top synthesis、implementation、routing、bitstream 均成功。最終 route status 為 68,180 fully-routed nets、0 routing errors；bitgen 0 errors/0 critical warnings；signoff WNS `+0.966 ns`、WHS `+0.010 ns`，所有 user timing constraints met。資源為 LUT 27.34%、register 17.75%、BRAM 50.00%、DSP 10.74%。外部 build 的 7,797,815-byte `.bit`、XSA/report 與 AMD source 都未上傳，因 Tcl 可重建且不是專案原始碼。
- 驗證界線／未完成：尚未下載此 bitstream 到板子，也沒有 matching Linux image/device tree/CMA/DPU driver/VART、B512 `arch.json`、YOLOv8 INT8 `.xmodel` 或 VART inference。現有 SD PYNQ image 先前已確認缺 `/dev/dpu`、`xdputil` 和 VART；因此不能聲稱 DPU 或 YOLOv8 已上板可用。
- Git／同步：已提交為 `dbaeb8f`（`Add PYNQ-ZU native DPU B512 Vivado flow`）並成功推送至 `origin/main`；下方同步紀錄提交會記錄此結果。

## 2026-11-11 — DPU XSA hardware handoff for Vitis

- 需求／決策：讓已完成的 Vivado DPU bitstream 可由後續 Vitis/Linux 流程取得，並拒絕從未完成 implementation 匯出硬體。
- 實際完成：新增 `fpga/export_pynq_zu_dpu_xsa.tcl`，它檢查 `impl_1` 為 `write_bitstream Complete!`，再從 routed run 執行 `write_hw_platform -fixed -include_bit`。
- 實際驗證：Vivado 2024.2 成功輸出 2,586,044-byte `pynq_zu_dpu_b512.xsa`；archive 實測含 `.hwh`、`.bit`、`psu_init.*`、`sysdef.xml`、`xsa.json/xml`。
- 驗證界線／未完成：XSA 是 Vitis handoff，尚未用於 Vitis platform、Linux image/device tree/CMA/DPU driver/VART 或板端 inference；外部 XSA/bitstream/report 未上傳，因 tracked Tcl 可重建。
- Git／同步：已提交為 `817a8cc`（`Export PYNQ-ZU DPU hardware handoff`）並成功推送至 `origin/main`；下方同步紀錄提交會記錄此結果。

## 2026-11-11 — Embedded Vitis DPU platform handoff

- 需求／決策：驗證 DPU XSA 能由完整 Vitis Embedded 產生 A53 software platform，不用舊 AXI-mailbox application 假裝控制 native DPU。
- 實際完成：新增 `vitis/pynq_zu_dpu/build_vitis_dpu_platform.py` 和 README；它以一個新的短 workspace 建立 `psu_cortexa53_0` / `standalone_domain` platform 與 FSBL，沒有建立不存在的 DPU bare-metal runtime。
- 實際驗證：`C:\Xilinx_Embedded_2024_2` 的 Vitis 2024.2 成功生成 SDT、BSP、FSBL、platform export 和 XPFM。生成 `xparameters.h` 實測為 DPU AXI-Lite `0x400000000`，與 Vivado 接線一致；FSBL 為 445,080 bytes。
- 驗證界線／未完成：這只驗證 Vivado→Vitis hardware handoff。沒有下載板子，沒有 matching Linux/device-tree/CMA/DPU driver/VART、INT8 `.xmodel` 或 DPU inference。workspace/XPFM/FSBL 是可重建本機產物，不上傳。
- Git／同步：已提交為 `6fd4f9b`（`Build Vitis platform for PYNQ-ZU DPU`）並成功推送至 `origin/main`；下方同步紀錄提交會記錄此結果。

## 2026-11-11 — PYNQ-ZU DPU Linux runtime acceptance gate

- 需求／決策：把已驗證的 Vivado bitstream/XSA/Vitis handoff 接向真正可由 Linux/VART 使用的 DPU，同時不把不存在的 PYNQ runtime 誤列為完成。
- 實際完成：新增 `vitis/pynq_zu_dpu/linux/verify_dpu_runtime.py` 和 README。verifier 是板端 read-only gate，檢查 `xlnx,dpuczdx8g-4.0` device tree、`/dev/dpu*`、CMA、VART/XIR、`xdputil query`、B512 `.xmodel` 與可選 UVC camera node，全部滿足才成功。官方 DPUCZDX8G 4.0 source 的 ZCU102 reference 已檢查：kernel patch 只加入 4.0 compatible；VART 2.5 recipe 要求 XIR/target-factory/XRT，不能作為 PYNQ 現有 image 的直接替換。
- 驗證範圍／未完成：host audit 找不到 `C:\Xilinx_Embedded_2024_2` 或 `C:\Xilinx` 下的 PetaLinux；尚未建置 matching Linux image、部署 bitstream、重刷 SD 或在板端執行 verifier。因而尚未有 DPU driver/VART/YOLOv8 inference 的實機聲稱。
- Git／同步：已提交為 `61abcdf`（`Add PYNQ-ZU DPU Linux runtime gate`）並成功推送至 `origin/main`。本機沒有上傳 Linux image、bitstream、模型或任何帳密；它們皆尚未產生或屬可重建／部署端產物。

## 2026-11-11 — SD PYNQ 實板雙 C270 capture 與 runtime recheck

- 需求／決策：在 SD Linux 實機重新驗證目前「先一板兩鏡頭」是否可行，並確認 DPU/Linux 現況，不以 device node 存在代替實際 frame capture。
- 實際完成：SSH 到 `192.168.3.1` 的 PynqLinux 3.0 / kernel `6.6.10-xilinx-v2024.1-gb6067dbebcc8`；兩支 C270 皆在 USB2744 480-Mbit/s hub 上，OpenCV/NumPy 存在。將 `xilinx` 加入既有 `video` 群組後，新 session 可開 V4L2 node。兩支各自 MJPEG 320×240、5 FPS 讀三張均成功；同時開啟則 `video0` 五張成功、`video2` 五張失敗。`dmesg` 實測對第二支記錄 `Not enough bandwidth for altsetting 7`。
- 驗證範圍／未完成：這證明個別 C270 可 capture 且一板雙 C270 在現有共用 hub 失敗，並非長時間串流測試。`wlan0` 存在但 DOWN/unconfigured，未做兩板 Wi-Fi。CMA 524288 KiB，但仍無 DPU DT node、`/dev/dpu*`、`xdputil`、VART/XIR；未部署 DPU bitstream、未重刷 SD、未跑 `.xmodel` 或 YOLOv8。
- Git／同步：已提交為 `6fd075b`（`Record PYNQ dual camera hardware result`）並成功推送至 `origin/main`。沒有上傳板端帳密、影像、bitstream 或模型。

## 2026-11-11 — PYNQ CPU YOLOv8 ONNX fallback

- 需求／決策：使用者確認目標模型是 YOLOv8；在 DPU/VART 尚未可用前，建立不改動 tracker/peer person schema 的 CPU fallback，並在實板驗證而非只在 host 假定 ONNX 相容。
- 實際完成：新增 YOLOv8 adapter、單元測試和可重建 exporter。官方 YOLOv8n 經 Ultralytics 8.3.0 匯出 static 640 ONNX。原 artifact 是 opset 18／IR 10；PYNQ OpenCV 4.5.4 的 Reshape parser 失敗，ONNX Runtime 1.16.3 也先拒絕 IR 10。以 ONNX checker 產生 IR 9 artifact 後，板端 ORT 成功回傳 `(1,84,8400)`，zero input 為 0.845 s；C270 `video0` 320×240 frame 經 adapter CPU inference 為 1.017 s，當次 0 person。
- 環境／範圍：第三台 PYNQ 的 `xilinx` user site 已安裝 NumPy 1.21.6、ONNX Runtime 1.16.3、flatbuffers/protobuf/coloredlogs 依賴；開發機安裝 Ultralytics 8.3.0、Torch 2.15.0、ONNX/onnxscript 以重建 model。模型、wheel 和 `/tmp` deployment files 不上傳 Git。尚未做含人物的正樣本驗證，這不是 DPU/VART 或 INT8 `.xmodel`。
- Git／同步：已提交為 `fbed6fe`（`Add PYNQ CPU YOLOv8 fallback`）並成功推送至 `origin/main`。模型、wheel、影像、帳密和 `/tmp` deployment files 均未上傳。

## 2026-11-11 — YOLOv8 接入既有 PYNQ pipeline/bundle

- 需求／決策：讓 YOLOv8 不只是一個 adapter，而是既有 person-tracking pipeline 與 PYNQ dashboard bundle 的預設 detector；YOLOX 僅作 `PERSON_DETECTOR=yolox` 的明確 legacy 回退。
- 實際完成：`pipeline.Detector` 預設選 YOLOv8，bundle 改含 `yolov8.py`/`yolov8n.onnx` 並將 preflight 擴充為 ONNX Runtime。修正 bundle 在 YOLOv8 mode 仍於 import time 載入未打包 `yolox.py` 的問題，改為只在選 legacy backend 時 lazy import。bundle tar 實測不含 YOLOX model。
- 實際驗證：4 個 adapter/backend unit tests PASS；打包後暫存至 PYNQ，system preflight PASS（NumPy 1.21.6、OpenCV 4.5.4、ONNX Runtime 1.16.3、13,057,836-byte model）。`pipeline.Detector()` 實測 backend=`yolov8`、讀取 C270 `video0` 320×240、CPU inference 1.255 s，當次 0 detections。
- 驗證範圍／未完成：暫存 `/tmp` bundle 非持久正式部署；無人物正樣本，未驗證 person box/tracker/dashboard/Wi-Fi peer。仍非 DPU/VART/INT8 `.xmodel`。
- Git／同步：已提交為 `fac5fee`（`Use YOLOv8 in PYNQ tracking pipeline`）並成功推送至 `origin/main`。模型、wheel、影像、帳密和 `/tmp` bundle 未上傳。

## 2026-11-11 — PYNQ YOLOv8 person positive inference

- 需求／決策：補足只有 0-person C270 frame 的驗證不足，以專案現有公開人物圖確認 PYNQ 上真正的 person detector/postprocess 結果。
- 實際驗證：同一暫存 bundle 的 `pipeline.Detector()` / `yolov8` backend 在 810×1080 public `bus.jpg` 回傳 4 person boxes，推論耗時 0.950 s，並輸出 `PYNQ_YOLOV8_POSITIVE_PASS`。
- 驗證範圍／未完成：公開圖經暫存傳送，未上傳或新增至 Git；不是 C270 現場人物、tracker confirmed state、dashboard、Wi-Fi peer 或 DPU/VART inference。
- Git／同步：已提交為 `bf9a830`（`Record PYNQ YOLOv8 positive inference`）並成功推送至 `origin/main`。公開圖只在板端 `/tmp` 驗證使用，未上傳。

## 2026-11-11 — PYNQ YOLOv8 one-camera peer producer

- 需求／決策：將「兩板各一鏡頭、Wi-Fi 傳資料」落實為每板 YOLOv8/Tracker 產生 validated person-detection metadata packet，不傳 raw USB video。
- 實際完成：新增 `pynq_yolov8_peer.py`、bundle inclusion 和 2 個 packet contract tests。它以 C270 V4L2 frame、project default detector/tracker、`peer_protocol.send_packet` 依序處理；可用 `--frames` 做有限 bring-up。
- 實際驗證：6 個 unit tests PASS；在 PYNQ 暫存 bundle 啟動 `peer_protocol receive --bind 127.0.0.1`，再由 `pynq_yolov8_peer.py --camera 0 --frames 1` 實跑。receiver 接收 `pynq-a:0`，packet 有正確 320×240 dimensions、schema 與空 detections。tar 對開發機時間戳印出 future-time warning，但解壓、執行與 packet 驗證皆成功。
- 驗證範圍／未完成：loopback 不是 Wi-Fi／第二板／跨網路斷線測試；未在 live camera 得到 person positive packet，非 DPU/VART。
- Git／同步：已提交為 `bf2a0fb`（`Add PYNQ YOLOv8 peer producer`）並成功推送至 `origin/main`。模型、wheel、影像、帳密與 `/tmp` bundle 均未上傳。

## 2026-11-11 — DPU Linux build-host recheck

- 需求／決策：確認現有主機是否能接續 Vivado/Vitis handoff 建置 PYNQ-ZU B512 的 matching Linux DPU runtime，而非將 absence 視為可略過的步驟。
- 實際驗證：Windows `wsl.exe` 存在但沒有任何 installed Linux distribution；未找到 Docker command。Xilinx 安裝樹沒有 PetaLinux executable/settings，僅有 installer EULA 與 lopper helper。
- 驗證範圍／未完成：本機確實不能建置 PetaLinux/VART/DPU driver image；未嘗試安裝 WSL、PetaLinux、重刷 SD 或下載 DPU bitstream。DPU Linux build 仍需要受支援 Linux host 的外部環境，不影響已驗證 CPU YOLOv8 path。
- Git／同步：已提交為 `e9413a3`（`Record DPU Linux build host blocker`）並成功推送至 `origin/main`。沒有安裝或上傳 PetaLinux、Linux image、bitstream、模型或帳密。

## 2026-11-11 — DPU build-host compatibility gate

- 需求／決策：使用者暫時不插 UART/JTAG，先推進不需板子的 DPU 部署工作；避免將 Vivado bitstream 成功誤當成 Linux/VART/YOLOv8 DPU 已可用。
- 實際完成：新增 `vitis/pynq_zu_dpu/linux/preflight_dpu_build_host.py` 與三個 unit tests，檢查 Vitis AI compiler route、PetaLinux、精確 `arch.json`、Vitis AI/Vivado/PetaLinux 版本契約。更新 DPU Linux README 與兩份進度文件。
- 驗證：新 unit tests `3/3 PASS`。在此 Windows host 實跑 gate，Docker、`vai_c_xir`、PetaLinux 與 exact `arch.json` 均不存在，輸出 `PYNQ_ZU_DPU_BUILD_HOST_FAIL`。AMD Vitis-AI v4.0 release notes 指出 DPUCZDX8G 4.0 + Vitis AI 3.5 已驗證於 2024.1；現有 Vivado/Vitis 2024.2 hardware handoff 因此不得宣稱 runtime compatibility。
- 未完成：必須取得受支援的 2024.1 PetaLinux/Vitis AI build host，重建 matching DPU hardware/XSA、Linux image、VART 與 YOLOv8 INT8 `.xmodel`，再上板驗證。未安裝系統軟體、未插板、未重刷 SD、未上傳模型/bitstream/私人資料。
- Git：已提交為 `dbfcad4`（`Add DPU build host compatibility gate`）並成功推送至 `origin/main`。未上傳 Linux image、bitstream、模型或私人資料；它們均尚未產生或屬部署端產物。

## 2026-11-11 — PYNQ-ZU Composite USB reconnect verification

- 需求／決策：使用者表示板子已重新接線，需先以系統偵測結果區分 Composite 網路與 UART/JTAG，避免對 Vivado 連線狀態誤判。
- 實際驗證：Windows 偵測到 PYNQ-USB、Remote NDIS（VID `03FD:010C`）且 `乙太網路 3` 為 Up；主機 `192.168.3.102` 對 `192.168.3.1:22` TCP 成功。非互動式 SSH 因沒有 key 回覆 `Permission denied (publickey,password)`，未登入或執行任何板端命令。
- 驗證界線／未完成：未偵測到 Xilinx/FTDI UART/JTAG 或新增 COM port，因此這是 Composite USB 恢復，不是 Vivado Hardware Manager JTAG 連線。未更動 boot switch、SD、bitstream、板端檔案或任何帳密。
- Git：已提交為 `f5ff5eb`（`Record PYNQ composite reconnect`）並成功推送至 `origin/main`。沒有上傳私人資料、模型、bitstream 或板端檔案。

## 2026-11-11 — Composite + UART/JTAG simultaneous connection verification

- 需求／決策：使用者已將兩個孔同時插上；須確認它們可並存，並讓 Vivado 對真正 JTAG target 做最終偵測。
- 實際驗證：Composite 仍提供 PYNQ-USB/RNDIS/`COM4`；Vivado Hardware Manager 成功連至 `localhost/xilinx_tcf/Xilinx/1234-tulA`，列出 `xczu5_0`（`xczu5`）與 `arm_dap_1`。兩條線可同時使用：Composite 給 Linux 網路，UART/JTAG 給 Vivado。
- 驗證界線／未完成：Hardware Manager 顯示 `xczu5_0` 已 Programmed 且其 Programming file 欄為 DPU wrapper，但本輪沒有可獨立證明新一次 Program 成功的 log。JTAG 開啟後 TCP 22 保持可達但 SSH banner 被板端 reset，未再對板子寫入、燒錄或重刷。需保留兩線並實體斷電重開、SD boot 後重新驗證 Linux/SSH，不能宣稱 DPU/VART inference。
- Git：已提交為 `eb42e95`（`Record simultaneous PYNQ JTAG connection`）並成功推送至 `origin/main`。沒有上傳私人資料、模型、bitstream 或板端檔案。

## 2026-11-11 — SD restart recovery and persistent YOLOv8 CPU deployment

- 需求／決策：SD restart 後，先確認 Linux 恢復，再將目前 GitHub 的 YOLOv8 bundle 部署到不覆寫舊 YOLOX dashboard 的新資料夾，優先完成單鏡頭可用路徑。
- 實際完成：SSH 成功登入；建立本機 13-member/11,104,503-byte bundle，部署至 `/home/xilinx/pynq_yolov8_20261111`。board system preflight PASS，確認 Python 3.10.4、NumPy 1.21.6、OpenCV 4.5.4、ONNX Runtime 1.16.3 與 13,057,836-byte YOLOv8 model。
- 實際驗證：C270 `video0` 在 MJPEG/320×240 成功輸入 YOLOv8，推論 0.964 s、當下 0 person；公開 `bus.jpg` 暫存正樣本測試回傳 4 persons、1.654 s。測試後 `PYNQ_TEMP_IMAGE_REMOVED` 與 persistent deploy file 都已實測。
- 驗證界線／未完成：僅一支 C270；未同時開兩相機、未測 Wi-Fi/第二板、tracker/dashboard、PL 或 DPU。現有 Linux 仍沒有 `/dev/dpu0`、`xdputil`、VART/XIR；CPU result 不得描述為 DPU。
- Git：已提交為 `3d74721`（`Record PYNQ YOLOv8 CPU deployment`）並成功推送至 `origin/main`。板端目錄、模型與公開圖未上傳 Git；公開圖已從 `/tmp` 移除。

## 2026-11-11 — Restarted-board sequential dual-C270 recheck

- 需求／決策：SD restart 後確認兩個已連接的 C270 各自仍能被 Linux/UVC 使用，同時維持先前「不可同時串流」的證據界線。
- 實際驗證：在新 YOLOv8 deployment 目錄執行 tracked camera preflight；`/dev/video0`～`/dev/video3` 存在，index 0 與 index 2 各自以 MJPEG/320×240 成功讀取一張 frame。
- 驗證界線／未完成：檢查會先關閉 A 才開 B，未同時開兩支相機，不能宣稱雙鏡頭同時串流已修復。未跑 YOLO/DPU/Wi-Fi/PL，沒有寫入板端資料或變更硬體設定。
- Git：已提交為 `a9c596f`（`Record restarted dual camera recheck`）並成功推送至 `origin/main`。沒有上傳相機影像、模型、bitstream 或板端檔案。

## 2026-11-11 — PYNQ-ZU Wi-Fi readiness diagnostic

- 需求／決策：為後續兩塊 PYNQ-ZU 各一支相機、以 Wi-Fi 交換人物 metadata 的架構，先確認第一塊板的無線硬體狀態；不連線、不掃描 SSID、不寫入網路設定。
- 實際驗證：`wlan0` managed interface/`phy#0` 存在，kernel dmesg 顯示 `wilc_sdio` 已初始化 `wlan0`。目前 `wlan0` DOWN、無 IP，NetworkManager/wpa_supplicant 皆 inactive。
- 驗證界線／未完成：沒有第二塊板，沒有 SSID/密碼/授權，故未設定 Wi-Fi、未收發 peer packet。`regulatory.db` 缺失與未連線的 RSSI 訊息僅記錄為 kernel 診斷，不當作 Wi-Fi 成功或失敗的替代證據。
- Git：已提交為 `64ff1db`（`Record PYNQ WiFi readiness`）並成功推送至 `origin/main`。沒有上傳 SSID、密碼、相機影像、模型、bitstream 或板端檔案。

## 2026-11-11 — Post-restart PL DPU bitstream state reconciliation

- 需求／決策：釐清 SD restart 後 Vivado DPU bitstream 是否仍載於 PL，避免把 Hardware Manager 的 stale file field 誤作硬體狀態或把硬體載入誤說成 runtime 完成。
- 實際驗證：Hardware Manager 顯示 `xczu5_0` status=`Programmed`，其 programming file 是 `pynq_zu_dpu_wrapper.bit`；同一 Vivado Tcl Console 記錄 `set_property PROGRAM.FILE` 與 `program_hw_devices [get_hw_devices xczu5_0]`。因此確定 DPU bitstream 目前載於 PL。
- 驗證界線／未完成：Linux SSH/UVC/CPU YOLOv8 正常，但 `/dev/dpu0`、`xdputil`、VART/XIR 皆仍不存在。未重新 programming、未寫 SD/flash、未製作 matching Linux image 或 `.xmodel`；不得稱 DPU inference 完成。
- Git：已提交為 `84fa551`（`Record active DPU bitstream state`）並成功推送至 `origin/main`。沒有上傳模型、bitstream、帳密、相機影像或板端檔案。

## 2026-11-11 — Exact native DPU architecture extraction

- 需求／決策：取得現有 PYNQ-ZU native B512 DPU 的精確 compiler architecture，而非用其他開發板的 `arch.json` 或猜 fingerprint。
- 實際完成：在完成的 Vivado generated IP 目錄找到 `arch.json`，fingerprint 為 `0x101000016010400`；新增 tracked `fpga/export_pynq_zu_dpu_arch_json.py` 與兩個 unit tests，安全輸出外部可重建的 deploy JSON。
- 驗證：2/2 unit tests PASS；對 `C:/pynq_zu_dpu_native_build` 實跑成功輸出 JSON，然後 build-host preflight 確認 `has_arch_json=true`。預期仍 FAIL，原因僅剩沒有 Docker/`vai_c_xir`、沒有 PetaLinux、以及 2024.2 hardware 不在 Vitis AI 3.5/DPUCZDX8G 4.0 已驗證的 2024.1 工具鏈。
- 驗證界線／未完成：未產生 `.xmodel`、未安裝任何工具、未重建 2024.1 hardware/image、未碰板子。generated arch JSON、bitstream、model 與帳密不進 Git。
- Git：已提交為 `444e66e`（`Export exact PYNQ-ZU DPU architecture`）並成功推送至 `origin/main`。generated arch JSON、bitstream、model 與帳密未上傳。

## 2026-11-11 — Downloaded-tool and Linux-host re-audit

- 需求／決策：確認使用者下載的約 6.6GB 工具檔是否可以解除 DPU Linux build blocker；只讀盤點，不做系統安裝或大型解壓。
- 實際驗證：該檔為 7,049,861,120-byte `Vitis_Embedded_Win_2024.2_1113_2356.tar`；Downloads 內沒有 PetaLinux/Vitis AI/2024.1 installer。WSL 尚未安裝 Linux distribution，Docker/Podman 也不存在。
- 驗證界線／未完成：Windows Vitis Embedded archive 不是 PetaLinux/Vitis AI runtime build host。未解壓 139GB Unified archive、未安裝 WSL/Docker/PetaLinux、未改板子。DPU runtime 仍需受支援的 2024.1 Linux/PetaLinux/Vitis AI 環境。
- Git：已提交為 `49b8755`（`Record DPU build host re-audit`）並成功推送至 `origin/main`；本行的同步結果將由下一筆文件提交記錄。

## 2026-11-11 — VART Python execution boundary

- 需求／決策：在尚未有可用 DPU Linux image／`.xmodel` 前，先把未來 DPU YOLOv8 的 Python 執行邊界接到既有 tracker／two-board metadata flow；不可假設 DPU compiled graph 的 output layout 等同 ONNX。
- 實際完成：新增 `person_tracking/assets/yolov8_vart.py` 與離線 contract test。程式以 VART/XIR `.xmodel` 的唯一 DPU subgraph 與 real tensor shape/fix point 做 RGB NHWC INT8 input、job execution、named dequantized output tensors。沒有已測 decoder 時，人物 `infer()` 會明確拒絕。
- 驗證界線／未完成：fake runner 加既有 YOLOv8 adapter/peer tests 共 7/7 PASS；未安裝 VART/XIR、未編譯 `.xmodel`、未修改 overlay/SD image 或板子，故沒有 DPU/VART/positive-person hardware claim。model-specific output decoder 仍必須以此 B512 的 compiled model 實測後才可接 `pipeline.Detector`。
- Git：已提交為 `1a60e45`（`Add VART YOLOv8 execution boundary`）並成功推送至 `origin/main`；本行的同步結果將由下一筆文件提交記錄。

## 2026-11-11 — Two-board metadata sender retry semantics

- 需求／決策：讓每板一鏡頭的 Wi-Fi metadata sender 可承受 peer receiver 短暫重啟；不傳 raw video，且不可把失敗誤報成送達。
- 實際完成：`pynq_yolov8_peer.py` 新增同一包 frame metadata 的 TCP retry helper、CLI retry budget/delay 與可見 retry logging。只對網路 `OSError` 重試，耗盡時 raise `ConnectionError`。
- 驗證界線／未完成：`test_yolov8_peer.py` fake sender 驗證兩次 transient failure 後第三次成功與耗盡失敗；尚未有第二 PYNQ、Wi-Fi SSID/IP 或實機封包。未變更任何網路或板子。
- Git：本次程式與進度紀錄待同一筆提交推送至 `origin/main`；提交後在此紀錄補上結果。
