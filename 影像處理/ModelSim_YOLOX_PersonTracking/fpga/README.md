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

`tb_dual_camera_roi_match_top.v` 會實際送入四個完整 640×480 的同步 RGB frame，模擬
YOLOX 已提供完整人物 bbox。三個相似 A/B ROI 於第三個 frame-pair 確認，第四個
不同色 ROI 清除 streak；本機 Vivado 2024.2 XSim 結果為
`DUAL_CAMERA_ROI_MATCH_TOP_PASS checks=16`。

## YOLOX 到 FPGA 的 AXI4-Lite 邊界（2026-11-04）

`dual_camera_yolox_axilite_top.v` 是目前 PYNQ-ZU Vivado project 的整合 top：

```text
PYNQ PS / Python YOLOX → AXI4-Lite bbox mailbox → frame command adapter
                         → dual_camera_roi_match_top → feature / confirmed
```

- `yolox_bbox_axilite.v` 是 64-byte AXI4-Lite slave。先寫 `0x04` frame ID、`0x08/0x0c`
  A 的 `(x0,x1)/(y0,y1)`、`0x10/0x14` B 的座標，最後寫 `0x00 = 0x3` 提交一組存在的
  bbox。CONTROL bit 0=pending、bit 1=pair present、bit 2=overrun。
- `yolox_frame_command_adapter.v` 僅在相同 `stream_frame_id` 的 `frame_start` 鎖住 bbox；
  錯影格輸出 `frame_command_missing` 並不讓舊 bbox 用於新 frame。
- `person_tracking/pynq_yolox_mmio.py` 將既有 `rtl-yolox-bbox-v1` JSON 寫入 PYNQ `MMIO`。
  PYNQ overlay 完成後以 `open_pynq_mmio(<Address Editor 的 base address>)` 建立 MMIO；
  base address 不能硬編碼，必須取自最終 Vivado Block Design。

本機 Vivado 2024.2 的 `tb_yolox_command_path.v` 模擬通過
`YOLOX_COMMAND_PATH_PASS checks=5`，整個 `dual_camera_yolox_axilite_top.v` 也已編譯。
Python fake-MMIO 合約測試確認 packet 會先寫五筆 payload，最後才寫 control。這不是 PYNQ-ZU
上板結果：尚未完成 PS Block Design、MIPI/USB frame buffer、clock-domain crossing、XDC、
bitstream 或硬體 MMIO；YOLOX 仍是 CPU/PS 推論，不是 Verilog 神經網路。

## PYNQ-ZU PS Block Design 與綜合（2026-11-04）

依序以 Vivado batch 執行下列三個腳本：

1. `create_pynq_zu_rtl_project.tcl`
2. `create_pynq_zu_yolox_bd.tcl`
3. `synthesize_pynq_zu_yolox.tcl`

第二步建立 `Zynq UltraScale+ PS → SmartConnect → yolox_rtl_0`，以 100 MHz PL clock
與同步 reset 連接 AXI4-Lite，並保留 video pixel/feature 訊號為 BD 外部 ports。Address
Editor 自動配置 mailbox 為 `0xA000_0000`、4 KiB。第三步生成 BD wrapper 並綜合；本機
Vivado 2024.2 的結果為 `synth_design completed successfully`、0 error、0 critical warning，
checkpoint 位於所選 build directory 的 `pynq_zu_rtl.runs/synth_1/`。

Windows 上原始碼資料夾含中文且路徑很長，Vivado 會在產生 Zynq IP 時失敗。因此三個腳本
預設把**生成物**放到 `%TEMP%/pynq_zu_rtl`；可設定環境變數 `PYNQ_ZU_BUILD_DIR` 指向另一個
短的 ASCII 絕對路徑。這不改動或提交原始碼。雖已綜合，外部 pixel ports 尚未指定攝影機
來源/腳位/XDC，故實作、bitstream、overlay 和板端測試仍不是已完成項目。

## 通用雙鏡頭 AXI-Stream 入口（2026-11-04）

`axis_dual_rgb_stream_adapter.v` 接一條 64-bit AXI4-Stream：每個 word 的 A RGB888 位於
`[23:0]`、B RGB888 位於 `[55:32]`。它每 307,200 word 自動形成一個 640×480 frame，並以
`TLAST` 檢查邊界；錯誤會鎖存於 `frame_boundary_error`。因此兩張影像在同一 DMA 轉送內
保持逐像素同步，避免獨立兩個 DMA 發生 cycle gap 而違反既有 dual ROI core 的同步輸入要求。

`dual_camera_yolox_axis_top.v` 將這個 adapter 包在 AXI-Lite YOLOX mailbox top 外；可以由
PS USB/CSI capture 後的 DMA、HDMI frame buffer 或其他能輸出相同 AXI stream 格式的來源連接。
`pynq_yolox_mmio.py` 的 `pack_dual_rgb888_frames()` 會把兩個**已轉成 RGB** 的 NumPy `uint8`
H×W×3 frame 打成 `uint64` word；`copy_dual_frame_to_dma_buffer()` 可填入 PYNQ allocated DMA
buffer 並在支援時 flush。實際 DMA IP、camera driver 與 physical pin path 尚未選定/上板。

本機 XSim `tb_axis_dual_rgb_stream_adapter.v` 為
`AXIS_DUAL_RGB_STREAM_ADAPTER_PASS checks=7`；Python packing 合約測試的單一 word 為
`0x00aabbcc00112233`。這些是介面/打包驗證，並非 USB、CSI、PYNQ DMA 或板端相機驗證。
