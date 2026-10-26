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
