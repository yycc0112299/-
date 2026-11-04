# PYNQ / EGo1 板級接線邊界

`roi_feature_board_top.v` 是目前可共用的 FPGA top-level 核心：它把既有的
`person_roi_stream.v` 接成一個同步 RGB 像素串流，完成一個 640×480 frame 後輸出
上下區域主色特徵、像素數與 `result_led`。

目前刻意不把 PYNQ-Z2 或 EGo1 的腳位、輸入時脈與相機介面寫死。兩塊板的
constraint 與影像輸入方式不同；接上指定板子後，再加入對應的 XDC、clock/reset
adapter，以及相機或 PS/AXI 到下列訊號的轉接：

```text
clk, reset, frame_start, pixel_valid, pixel_rgb[23:0], person_detected
x0/y0/x1/y1[9:0]
```

輸出 `feature_valid` 只在完整 frame 結束時脈衝一次。`person_valid` 表示人物框的
上下區都有有效像素；`result_led` 是兩者的合併指示。YOLOX 偵測與追蹤仍在 CPU
端，這個模組不宣稱已在 FPGA 上完成 AI 推論或相機擷取。

## ModelSim / Vivado

把本檔和上層 `person_tracking/person_roi_stream.v` 一起加入專案即可先做 RTL
compile。既有 `person_tracking/open_rtl_regression.ps1 -Batch` 仍是功能回歸入口；
真正接板時必須另外以目標板的 Vivado board part、XDC 與 clock wizard 重新合成。

## 跨鏡頭候選確認核心

`../person_tracking/cross_camera_pair_matcher.v` 可接在兩側 `person_roi_stream` 的結果之後。
它不自行挑選多個人，而是由 CPU／上層邏輯對每個 frame 提供一組已選定的
`feature_a`、`feature_b` 與每個 frame-pair 的 `observation_valid`／`pair_present`。兩側 feature 都有效、上/下主色相同且
兩個比例差各不超過 35 時，`candidate_valid` 有效；連續三個符合的已觀測 frame 才
會輸出一拍 `confirmed`。沒有候選或不符合即清除計數。這保留了現有 Python 流程的
「連續三次才確認」保護，但尚未硬體化 HSV 15-bin 分數、0.72 門檻、互為最佳與
多人物歧義判斷。

在這台電腦以 Vivado 2024.2 XSim 執行
`tb_cross_camera_pair_matcher.v`：`CROSS_CAMERA_PAIR_MATCHER_PASS checks=10`。
這是 RTL 模擬，不是 PYNQ/EGo1 合成、時序分析、相機串流或上板驗證。

`dual_camera_roi_match_top.v` 把兩路同 clock 的 RGB888 pixel stream、CPU/YOLOX 提供的
A/B bbox、兩個 640×480 ROI feature core 與候選確認器串接。每個完整 frame-pair 的
feature 會先緩衝、下一個 clock 才送進 matcher，因此影格間 idle clock 不會重設三次
連續計數。USB 相機若不同 clock 或非硬體同步，仍需 frame buffer / clock-domain adapter；
YOLOX 網路、多人物排程、bbox 傳輸介面和板級相機輸入尚未硬體化。
