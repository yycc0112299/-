# 影像處理

此資料夾用於存放影像處理相關的程式、文件與測試資料。

## 目前內容

- `MCDPT_FPGA/`：既有 EGo1 / FPGA 影像處理展示架構。
- `MCDPT_Verilog_Two_Image_ReID/`：依照 MCDPT GitHub 專案概念簡化的兩張圖人物再辨識 Verilog testbench 原型。

## 亮度版 Verilog Testbench

新版目前只做到 Verilog 模組與 testbench 模擬，重點是用最小結構示範「影像轉特徵、特徵算距離、門檻判斷」：

1. 兩張 8x8 RGB 測試圖片輸入。
2. 每個 pixel 先用亮度公式轉成灰階亮度。
3. 各自抽出簡化亮度 feature vector。
4. 計算兩個 feature vector 的距離。
5. 距離小於門檻時輸出 `same_object = 1`。

主要入口檔案：

- `MCDPT_Verilog_Two_Image_ReID/brightness_feature_extractor.v`
- `MCDPT_Verilog_Two_Image_ReID/brightness_matcher.v`
- `MCDPT_Verilog_Two_Image_ReID/tb_brightness_matcher.v`

目前尚未宣稱完成 FPGA 上板、VGA 顯示或多攝影機系統。
