# 專題共享內容索引

盤點日期：2026-09-30

此倉庫用來讓共同開發者及另一個 Codex 查閱專題程式、技術脈絡、交付簡報與進度。最新版功能以 `影像處理/ModelSim_YOLOX_PersonTracking/` 為準。

## 目前共享的內容

- `影像處理/ModelSim_YOLOX_PersonTracking/`：YOLOX 人物偵測、自寫短期追蹤、ModelSim 640×480 ROI 色彩特徵、雙 USB 鏡頭外觀候選配對及 localhost 即時網站。
- `影像處理/MCDPT_Verilog_Two_Image_ReID/`：早期兩張 8×8 合成影像特徵/比對 RTL 原型，非最新整合版。
- `tools/`：本機專題中整理 PDF 頁面、摘要、逐行說明及程式碼截圖的輔助工具。`build_line_explanations.py` 依賴未共享的舊 Vivado 範例 RTL，只作歷史工具參考；其他腳本依傳入的本機來源檔使用。
- `references/MCDPT/`：MCDPT 開源專案的參考程式子集；僅供閱讀，執行主流程不依賴此目錄。授權與引用資訊見其中 README。
- `deliverables/presentations/`：四份舊原型簡報成品，方便協作者了解早期設計與報告成果；不是目前功能規格。
- `deliverables/synthetic-test-patterns/`：四張 8×8 合成色塊/人形圖案，作為早期 testbench 測試素材；不是相機拍到的真人影像。
- `PROGRESS_FOR_CODEX.md`：詳細技術交接、狀態、驗證邊界及資料範圍紀錄。
- `PROGRESS_FOR_HUMANS.md`：人類閱讀的重點版進度。

## 本機盤點後排除

- `verilog_demo/` 與舊 `影像處理/MCDPT_FPGA/` Vivado 原型：使用者明確表示不要共享 Vivado 程式碼。前者留在本機；後者已從目前 Git 檔案樹移除，但較早 Git 提交仍保有歷史內容。
- `論文的簡報/*.pdf`：第三方論文全文，不複製到共享倉庫；可透過論文題名/原始出版來源取得。
- `modelsim_draft` 下模型權重、個人/公開測試影像、相機拍攝資料、完整模擬輸出、執行環境二進位與快取：可重建的大型/生成/含影像資料；保留原始碼、驗證摘要與下載方法。`person_tracking/verification_report.html` 因會載入本機相機影像資料夾而未共享；摘要 JSON 已隨程式包提供。
- `output/rca_report/`：截圖包含本機檔案路徑，因此不共享。
- `.codex-finalizer/`、`build/`、`.Xil/`、各種 `.jou`/`.log`/`.sdb`/`.wlf` 執行產物：候選稿、預覽、工具快取或模擬暫存。
- `automation/join-weekly-google-meet.ps1`、`.line-read-state.json`、`transcript` 及根目錄 Vivado 執行記錄：與專題交付無關或屬於個人/應用程式狀態。

盤點涵蓋當日 Codex「專題」工作資料夾中可見的檔案與目錄。未把個人偏好、Codex 設定或本機帳號資料寫入共享內容。
