# 對話與進度同步紀錄

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
- Git／同步：本次驗證紀錄將提交並推送至 `main`；結果會在完成後補記。
