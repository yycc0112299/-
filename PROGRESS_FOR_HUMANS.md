# 專題進度（重點版）

更新日期：2026-09-30

## 最新進度

本機最新整合版位於 `modelsim_draft/person_tracking`：電腦使用 OpenCV Zoo YOLOX 偵測人物，搭配專題自寫短期追蹤；ModelSim 負責完整 640×480 人物框內的色彩特徵處理。另有雙 USB 鏡頭流程，分別追蹤兩邊人物，再用自寫的外觀規則產生跨鏡頭候選。

## 驗證狀況

- 單鏡頭已保存兩輪 USB 實拍紀錄，共 240 張；偵測/追蹤及 ModelSim 特徵核對通過。
- 雙鏡頭程式已用保存影格 replay 整合測試；目前沒有兩台實體 USB 鏡頭的驗證紀錄。
- 雙鏡頭配對只是衣著外觀候選，不是身份辨識；整體流程也不是即時 FPGA AI 推論。

## GitHub 版本差異

共享 GitHub 目前仍是較早的 8×8 合成色彩原型和 FPGA SAD 展示，尚未同步本機最新的 ModelSim + YOLOX + 追蹤整合程式。本次已更新此進度說明，沒有搬移整合程式碼或重新執行驗證。

詳細交接與數據見 [PROGRESS_FOR_CODEX.md](PROGRESS_FOR_CODEX.md)。
