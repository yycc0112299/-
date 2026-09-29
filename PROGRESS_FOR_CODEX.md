# 專題狀態與交接記錄（供 Codex）

最後整理：2026-09-29

## 接手前先看

1. 閱讀本文件及 `AGENTS.md`。
2. 確認 `git status --short --branch`、目前分支與 `origin`；修改前先理解既有 RTL 和 testbench。
3. 本倉庫是專題共享倉庫，任何程式碼變更完成後，必須更新本文件與 `PROGRESS_FOR_HUMANS.md`，並推送 GitHub `main`。
4. 明確標示「由原始碼檢閱可確認」與「模擬/上板已執行驗證」兩種證據，不可把前者寫成後者。

## 倉庫結構與專題範圍

目前共享倉庫內影像處理相關內容位於 `影像處理/`：

- `影像處理/MCDPT_FPGA/`：EGo1 / Artix-7 的低資源 FPGA 追蹤展示設計，使用合成測試影格、特徵擷取與 SAD 搜尋追蹤。詳細設定見該目錄 `README.md`。
- `影像處理/MCDPT_Verilog_Two_Image_ReID/`：兩攝影機人物色彩特徵比對的 Verilog 原型。此路徑在整理日的最新提交 `2fb30f7` 已切換至色彩特徵 testbench；先前亮度版檔案已從目前版本移除，查看舊版需使用 Git 歷史。

這兩個資料夾是不同層級/版本的展示，不應假設它們已整合成單一系統。MCDPT 是概念參考；本倉庫不代表完成 CNN/OpenVINO 深度 Re-ID，也不代表多攝影機部署產品。

## 兩攝影機色彩特徵原型：目前程式行為

主要檔案：

- `影像處理/MCDPT_Verilog_Two_Image_ReID/person_color_feature.v`
- `影像處理/MCDPT_Verilog_Two_Image_ReID/person_matcher.v`
- `影像處理/MCDPT_Verilog_Two_Image_ReID/tb_two_camera_color.v`
- `影像處理/MCDPT_Verilog_Two_Image_ReID/run_xsim.tcl`

### 資料流程

1. Testbench 以兩個扁平化向量 `cam_a`、`cam_b` 提供兩張 8×8、每像素 RGB888 的合成影像；像素索引使用 `img[p*24 +: 24]`。
2. `person_color_feature` 對每個像素依 `r=img[k*24+16+:8]`、`g=img[k*24+8+:8]`、`b=img[k*24+:8]` 取 RGB，經 `color8` 量化成 0..7 色彩碼。0 是低亮度背景（最大通道 <35）；其餘規則依序分類近灰白、高紅、高綠、高藍、黃、橘棕條件，剩餘歸類為 7。
3. 模組逐像素計數上下半部各色數（`y < H/2` 為上半部）。色碼 0 不計入有效像素。`big_color` 選每半部計數最多的非背景色碼，產生 `top_c` / `bot_c`；`top_p` / `bot_p` 是該主色佔該半部有效色像素的整數百分比，分母為半部有效像素數，分母為 0 時輸出 0。
4. `has_person` 僅在上下半部各至少有一個有效色像素且總有效色像素數大於 10 時為 1。這是色彩像素數量啟發式，不是人體偵測器。`fmap={top_c,bot_c,top_p,bot_p}`，寬度為 24 位元。
5. `person_matcher` 將 24-bit 特徵拆成兩個 4-bit 顏色碼及兩個 8-bit比例值。僅在兩端都偵測到人、兩個顏色碼完全相同且兩個比例值的絕對差都小於 35 時輸出 `same=1`，其他情況輸出 0。門檻採嚴格小於 35。
4. Testbench 依序提供外觀近似的同一人跨攝影機樣本（要求判定相同），再提供綠/白衣著差異樣本（要求判定不同）。

### 解讀限制

- 這是由人工設計 8×8 RGB 圖案構成的合成資料測試，不是攝影機輸入或真實人物資料集。
- 人形區域與特徵是簡化色彩/區塊規則；相同特徵只表示符合這組閾值規則，不是可靠身份識別。
- RTL 的組合判定沒有跨影格 track 管理、身份資料庫、CNN/embedding、遮擋處理、攝影機同步或實際攝影機介面。
- `top_p` / `bot_p` 的確切計算語意請以 `person_color_feature.v` 原始碼為準；不要僅憑輸出名稱推論成真實人體比例或百分比準確度。
- 目前 `person_color_feature` 是 `always @(img)` 組合程序，以參數 `W/H/N/RGB` 描述影像尺寸，預設為 8×8/RGB888；修改參數時要同時確認向量位寬、索引及模擬器對函式/迴圈的支援。
- 整理時只檢閱了原始碼與 Git 歷史，沒有在本次工作執行 Vivado/XSim 或 FPGA 上板；因此不能在本文件聲稱最新版本模擬已由本次重新驗證。

## FPGA 追蹤展示：摘要與既有驗證聲明

`影像處理/MCDPT_FPGA/README.md` 描述此設計為 MCDPT 概念簡化版，而非完整深度 Re-ID。其文件所述架構包含 160×120、4-bit 合成 ROM 影格、4×4 區塊平均特徵、multi-cycle SAD 搜尋、VGA 4 倍放大至 640×480，以及以顏色方框呈現參考/搜尋/追蹤框。README 亦記載曾沿用 EGo1 Artix-7 板卡腳位資料，並提供 Vivado batch 模擬與建置命令。

上述是倉庫既有 README 的描述；接手時仍需查看 `src/`、`sim/`、`scripts/` 中實際內容及最新執行紀錄。此整理工作沒有重新執行 Vivado，也沒有重新確認板卡或 VGA 輸出。

## Git 歷史線索

截至 2026-09-29，本機 `main` 與 `origin/main` 同步，最新程式碼提交為 `2fb30f7 Switch to two camera color feature testbench`。該提交將亮度版抽取/比對與 testbench 替換為 `person_color_feature.v`、`person_matcher.v` 及 `tb_two_camera_color.v`。更早的亮度原型提交仍可由 Git 歷史查閱，不要在描述目前功能時混用舊版行為。

## 變更紀錄

### 2026-09-29：建立共享協作與狀態文件

- 新增 `AGENTS.md`，要求後續程式碼變更直接同步共享倉庫，且更新機器版與人類版進度文件。
- 新增本文件與 `PROGRESS_FOR_HUMANS.md`，記錄兩攝影機色彩原型的目前資料流程、比對門檻、限制，以及 FPGA 展示目錄的文件摘要。
- 本次沒有修改 RTL，也沒有執行模擬或上板驗證。
