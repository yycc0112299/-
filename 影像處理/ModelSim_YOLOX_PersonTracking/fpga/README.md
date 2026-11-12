# PYNQ / EGo1 板級接線邊界

## PYNQ-ZU native DPU B512 Block Design（2026-11-11）

`create_pynq_zu_dpu_bd.tcl` 建立 PYNQ-ZU (`xczu5eg-sfvc784-1-e`) 的原生
`xilinx.com:ip:dpuczdx8g:4.0` B512 單核心 Block Design。這不是把 USB 相機
D+/D− 接到 PL：USB0/USB1 保持 PS MIO，由 Linux UVC/V4L2 把單鏡頭資料放到 DDR。

BD 接線為 A53 HPM0 → SmartConnect → DPU AXI-Lite 控制、DPU 128-bit DATA0/1
→ PS HP0/HP1、32-bit instruction → SmartConnect → PS HP2、DPU interrupt →
PS IRQ0；PL1 150 MHz 餵 DDR data domain，clock wizard 產生 300 MHz DPU 2x
clock。`synthesize_pynq_zu_dpu_b512.tcl` 與
`implement_pynq_zu_dpu_b512.tcl` 分別產出 synthesis 和 bitstream gate。
`export_pynq_zu_dpu_xsa.tcl` 僅在 `impl_1` 已完成 bitstream 時輸出含 `.bit` 的固定 XSA；
2026-11-11 實跑輸出 2,586,044-byte archive，確認包含 `.hwh`、`.bit`、PS init、
`sysdef.xml` 與 XSA metadata，供下一階段 Vitis/Linux 使用。

先設定 `DPUCZDX8G_HOME` 為官方 AMD DPUCZDX8G 解壓來源根目錄；可選設定短路徑
`PYNQ_ZU_DPU_BUILD_DIR`。2026-11-11 實跑 Vivado 2024.2：BD validate、synthesis、
implementation、routing、bitgen 都成功，0 errors/0 critical warnings；implementation
timing 為 WNS +0.966 ns、WHS +0.010 ns，所有使用者約束滿足。資源為 LUT 27.34%、
register 17.75%、BRAM 50.00%、DSP 10.74%。build 內 `.bit`/`.xsa`/report 是可由 Tcl
重建的外部產物，未納入 Git。

此 gate 不代表 PYNQ Linux 已能執行 DPU。仍需要與此 B512 設定一致的 device tree、
CMA/DPU driver、VART、`arch.json`、INT8 `.xmodel` 與板端 VART test；現有 SD image
沒有 `xdputil`、VART 或 `/dev/dpu`。

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

2026-11-05 起 mailbox 另提供 PL→PS 的 level IRQ：`IRQ_STATUS` 位於 `0x18`（write-one-to-clear）
而 `IRQ_ENABLE` 位於 `0x1c`。bit 0=雙路 feature frame 完成、bit 1=跨鏡頭 confirmed、bit 2=影格
開始時缺少相同 frame ID command、bit 3=覆寫尚未消耗 command。`irq` 已接到 PYNQ-ZU PS
`pl_ps_irq0`；只有已 enable 的 sticky source 會把 IRQ 拉高，PS 必須先讀 status、再寫相同 bit 清除。
`pynq_yolox_mmio.py` 提供 `set_irq_enable()`、`irq_status()` 和 `clear_irq()`。

本機 Vivado 2024.2 的 `tb_yolox_command_path.v` 模擬通過
`YOLOX_COMMAND_PATH_PASS checks=9`，整個 `dual_camera_yolox_axilite_top.v` 也已編譯。
可在任何已安裝 Vivado 的 Windows 電腦重跑：

```powershell
.\open_xsim_yolox_command_path.ps1 -Batch
```

腳本把三個所需 HDL 暫存到 ASCII 的 `%TEMP%` 路徑，避免含中文的 repository 路徑影響
XSim；可用 `VIVADO_XSIM_BIN` 指向其他 Vivado 的 `bin` 目錄。它只驗證 AXI-Lite mailbox、
frame-ID 接收與 IRQ 的合成 testbench，不接觸 PYNQ、JTAG 或任何相機。
Python fake-MMIO 合約測試確認 packet 會先寫五筆 payload，最後才寫 control。這不是 PYNQ-ZU
上板結果：尚未完成 PS Block Design、MIPI/USB frame buffer、clock-domain crossing、XDC、
bitstream 或硬體 MMIO；YOLOX 仍是 CPU/PS 推論，不是 Verilog 神經網路。

## PYNQ-ZU PS Block Design 與綜合（2026-11-04）

依序以 Vivado batch 執行下列四個腳本：

1. `create_pynq_zu_rtl_project.tcl`
2. `create_pynq_zu_yolox_bd.tcl`
3. `synthesize_pynq_zu_yolox.tcl`
4. `implement_pynq_zu_yolox.tcl`

第二步建立 `Zynq UltraScale+ PS → SmartConnect → yolox_rtl_0`，以 20 MHz PL clock
與同步 reset 連接 AXI4-Lite。預設 bring-up 設計把尚未選定實體來源的 RGB/video 輸入拉為 idle，
且不把結果輸出到未約束的 PL pins，因此可安全產生基礎 bitstream；Address
Editor 自動配置 mailbox 為 `0xA000_0000`、4 KiB。第三步生成 BD wrapper 並綜合；本機
Vivado 2024.2 的結果為 `synth_design completed successfully`、0 error、0 critical warning，
checkpoint 位於所選 build directory 的 `pynq_zu_rtl.runs/synth_1/`。

Windows 上原始碼資料夾含中文且路徑很長，Vivado 會在產生 Zynq IP 時失敗。因此這些腳本
預設把**生成物**放到 `%TEMP%/pynq_zu_rtl`；可設定環境變數 `PYNQ_ZU_BUILD_DIR` 指向另一個
短的 ASCII 絕對路徑。建立專案時也會把八個 HDL 輸入複製到該 build 目錄的 `rtl_src/`，避免
Windows 子綜合程序無法解析中文來源路徑；這不改動或提交原始碼。20 MHz bring-up 設計已完成
implementation/bitgen，且於 2026-11-05 透過 JTAG 成功下載到 PYNQ-ZU `xczu5_0`
（Hardware Manager 顯示 `Programmed`）。這只驗證 JTAG/PS/PL clock/AXI-Lite bring-up；外部
pixel ports 仍未指定攝影機來源/腳位/XDC，故 Overlay/MMIO、相機串流和雙鏡頭板端功能仍不是已完成項目。

`implement_pynq_zu_yolox.tcl` 保留 Vivado 的 UCIO/NSTD DRC 為 error；只有所有 external
ports 都有刻意的板級 XDC 後才容許產生 bitstream，不會為了產檔而降低 DRC。

若已選定並完成 CSI、HDMI 或 DMA 的板級設計與 XDC，才設定
`PYNQ_ZU_EXPORT_VIDEO_PORTS=1` 重新建立 BD，使 video/result signals 成為 external ports。
未設定時產出的 bring-up bitstream 可驗證 PYNQ-ZU PS、PL clock、AXI-Lite mailbox 及 JTAG
下載，但沒有相機影像輸入，不能當作雙鏡頭功能完成。

### PYNQ Linux overlay 部署與板端 AXI-Lite 驗證

JTAG 的 PL 下載是易失性的；要在 PYNQ Linux（SD boot）載入同一設計，先在開發電腦執行
`prepare_pynq_zu_overlay.ps1`。它會從已完成的 build 複製出同 stem 的
`pynq_zu_yolox.bit` / `pynq_zu_yolox.hwh`，這是 PYNQ Overlay 所需的命名規則。它不會自行
上傳或改寫 SD 卡。把兩個檔案及 `person_tracking/verify_pynq_zu_bringup.py` 複製到 PYNQ 上的
同一資料夾後，在板子上執行：

```text
python3 verify_pynq_zu_bringup.py
```

檢查會下載 overlay、從 `0xA000_0000` 讀取控制暫存器，對 frame-ID 寫入/讀回固定測試值，再
清回 0。只有輸出 `PYNQ_ZU_BRINGUP_PASS` 才能證明 PYNQ Linux 的 Overlay 與 AXI-Lite 實機通。
它不提交 pending command，因此 idle-video bring-up 不會留下未消耗的 mailbox 指令。

如要把 Overlay 和 PYNQ 雙 USB 網站合成單一傳送檔，可先執行
`prepare_pynq_zu_overlay.ps1 -BuildDir C:\\pynq_irq_build -OutputDir C:\\pynq_irq_build\\overlay`，再執行
`live_site/prepare_pynq_dual_bundle.py --overlay-dir C:\\pynq_irq_build\\overlay`。tarball 的 `overlay/`
含同 stem `.bit/.hwh`；仍必須由 PYNQ Linux 的 `Overlay()` 載入，USB 影像目前不會直接進 RTL。

## 通用雙鏡頭 AXI-Stream 入口（2026-11-04）

`axis_dual_rgb_stream_adapter.v` 接一條 64-bit AXI4-Stream：每個 word 的 A RGB888 位於
`[23:0]`、B RGB888 位於 `[55:32]`。它每 307,200 word 自動形成一個 640×480 frame，並以
`TLAST` 檢查邊界；錯誤會鎖存於 `frame_boundary_error`。因此兩張影像在同一 DMA 轉送內
保持逐像素同步，避免獨立兩個 DMA 發生 cycle gap 而違反既有 dual ROI core 的同步輸入要求。

`dual_camera_yolox_axis_top.v` 將這個 adapter 包在 AXI-Lite YOLOX mailbox top 外；可以由
PS USB/CSI capture 後的 DMA、HDMI frame buffer 或其他能輸出相同 AXI stream 格式的來源連接。
`pynq_yolox_mmio.py` 的 `pack_dual_rgb888_frames()` 會把兩個**已轉成 RGB** 的 NumPy `uint8`
H×W×3 frame 打成 `uint64` word；`copy_dual_frame_to_dma_buffer()` 可填入 PYNQ allocated DMA
buffer 並在支援時 flush。2026-11-06 已以 Vivado Block Design 的 AXI DMA 和
Vitis A53 在 PYNQ-ZU 上送出一張完整合成影格；真實 USB UVC driver、雙鏡頭穩定性與
physical USB topology 仍待驗證。

本機 XSim `tb_axis_dual_rgb_stream_adapter.v` 為
`AXIS_DUAL_RGB_STREAM_ADAPTER_PASS checks=7`；Python packing 合約測試的單一 word 為
`0x00aabbcc00112233`。這些是介面/打包驗證，並非 USB、CSI、PYNQ DMA 或板端相機驗證。

## USB C270 的 Vivado Block Design 與 Vitis 邊界（2026-11-06）

現有 Logitech C270 是 USB/UVC 相機。它的實體 D+/D− 不屬於 PL camera
pixel pins：PYNQ-ZU board preset 中 USB0 是 **MIO 52–63**、USB1 是
**MIO 64–75**，由 Zynq PS USB host 控制器和 Vitis/Linux USB driver 處理。
因此不要為 USB 相機新增 PL XDC 或把它接到 GPIO。

新增的可重跑流程為：

1. `create_pynq_zu_usb_video_project.tcl`
2. `create_pynq_zu_usb_video_bd.tcl`
3. `export_pynq_zu_usb_video_xsa.tcl`

For a non-destructive Vivado-native check of an already-built project, set
`PYNQ_ZU_BUILD_DIR` and run `verify_pynq_zu_usb_video_bd.tcl` in Vivado batch
mode. It reopens the BD, invokes `validate_bd_design`, and checks the PS
address segments for DMA (`0xA0000000`), frame GPIO (`0xA0010000`) and mailbox
(`0xA0020000`). It does not run implementation, export an XSA or program the
board.

BD IP Catalog 對應為 `zynq_ultra_ps_e`（PS USB/DDR）、`axi_dma`（MM2S）、
兩個 `smartconnect`、`axi_gpio`（frame ID）、`proc_sys_reset`，以及
`dual_camera_yolox_axis_top`。Vitis 從 USB/UVC driver 取得兩張影像、轉為既有的
64-bit A/B RGB word 後放到 DDR，AXI DMA 透過 PS `S_AXI_HP0_FPD` 讀取後送至
custom RTL 的 AXI4-Stream；Vitis 同時經 AXI-Lite 寫 frame ID、bbox mailbox，並讀
DMA/RTL IRQ。

`vitis/pynq_zu_usb_video/` 是 Vitis C controller skeleton；必須將成功產生的 XSA
建立為 Vitis platform，讓 `xparameters.h` 提供實際 AXI addresses。controller 的
payload 寫入順序受 `tests/test_video_control.c` 保護。本文所記錄的 BD 已
`validate_bd_design`，但 XSA、bitstream、Vitis BSP/UVC driver、DDR DMA 和上板影像
仍須分別成功驗證，不能據此宣稱 USB frame 已進入 FPGA。
