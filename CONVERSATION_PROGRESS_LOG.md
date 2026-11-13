# 對話與進度同步紀錄

## 2026-11-13 — Verified the local Vitis AI 2.5 DPU compilation boundary for YOLOv8

- 需求／決策：PetaLinux 2022.1 download form remains external-account gated, so continue an independent YOLOv8/DPU preflight rather than wait.
- 實際完成：read-only Docker inspection of pre-existing `xilinx/vitis-ai:2.5.0` confirms `vitis-ai-pytorch`, PyTorch 1.10.1, `pytorch_nndct 2.5.0`, and `vai_c_xir`. Its actual help requires `-x XMODEL`; `vai_q_onnx` is absent. This establishes that tracked `yolov8n.onnx` is a CPU fallback input, not a compile-ready DPU model.
- 驗證範圍／未完成：未下載 weights、未量化／編譯 `.xmodel`、未檢查 real compiled tensors、未做 VART/board inference。現有 VART adapter remains deliberately decoder-gated.
- Git／同步：本次文件變更將與同一筆 Git commit 推送至 `origin/main`；Docker image 與外部 DPU build assets 不入 Git。

## 2026-11-13 — Audited board Wi‑Fi readiness without changing network configuration

- 需求／決策：在 Vivado 安裝仍進行時，先以唯讀 SSH 檢查目標端將來兩板 Wi‑Fi 互傳的基本條件。
- 實際完成：`wlan0` 存在但不 associated、MAC 皆為 zero；`nmcli`、`rfkill` 不存在，沒有已知 Wi‑Fi profile。現有可用連線為 USB gadget `usb0`。
- 驗證界線／未完成：未設定 SSID/password、未啟用或掃描 WLAN、未連 AP、未執行兩板 peer protocol；不能宣稱 Wi‑Fi readiness。
- Git／同步：本次文件變更待提交並推送到 `origin/main`。

## 2026-11-12 — Rechecked both USB cameras after USB-video overlay programming

- 需求／決策：確認剛下載的 PL overlay 不破壞 PS USB camera access；採 sequential single-frame capture，避免 USB2 shared-hub bandwidth 的 simultaneous capture 風險。
- 實際完成：overlay loaded 後，OpenCV/V4L2 對 `/dev/video0` 與 `/dev/video2` 皆得到 `POST_OVERLAY_CAMERA_OK` `(480, 640, 3)`。
- 驗證界線／未完成：不代表資料經 FPGA/DMA、雙相機同時、DPU、YOLOv8 或 Wi‑Fi peer 成功。
- Git／同步：本次文件變更待提交並推送到 `origin/main`。

## 2026-11-12 — Verified USB-video overlay control-plane registers on PYNQ hardware

- 需求／決策：在 PL programming 已確認後，以 root-enabled PYNQ verifier 實測 inert control-plane registers，並保證不啟動 DMA。
- 實際完成：使用者提供板端 output `PYNQ_ZU_USB_VIDEO_OVERLAY_PASS frame_id=0x5a17c0de initial_control=0x00000000`。這證明 GPIO 和 mailbox frame-ID write/read 成功、initial DMA control 為 zero；verifier finally 清零 tested registers。
- 驗證界線／未完成：沒有 DMA CONTROL/UVC stream/DPU/YOLOv8/Wi‑Fi peer 或雙板成功聲稱。bit/HWH 與 SSH key 為外部板端/host state，不進 Git。
- Git／同步：本次文件變更待提交並推送到 `origin/main`。

## 2026-11-12 — Programmed the USB-video overlay from PYNQ Linux and isolated root-only MMIO follow-up

- 需求／決策：修復 XRT device access 後，使用既有安全 overlay verifier 下載 USB-video bitstream；以 kernel/XRT 事實區分 PL programming 與控制面驗證。
- 實際完成：`xilinx` 加入 `render` group 後 XRT 報告 Pynq-ZU ready device。使用者在 interactive sudo session 執行 verifier；kernel 顯示 `writing pynq_zu_usb_video.bin`，ZOCL xclbin read `ret: 0`，故 PL programming PASS。
- 驗證界線／未完成：一般使用者 PYNQ MMIO 被 `/dev/mem` root requirement 擋下；noninteractive `sudo -n` 無 credential cache。尚未有 root frame-ID write/read/clear、DMA、camera-on-overlay、DPU/YOLOv8 或 Wi‑Fi peer 成功聲稱。
- Git／同步：本次文件變更待提交並推送到 `origin/main`；staged overlay binary/SSH private key 不入 Git。

## 2026-11-12 — Diagnosed PYNQ overlay/XRT access failure after safe USB-video overlay staging

- 需求／決策：利用已確認可用的板端 SSH key，在不啟動 DMA 的前提下嘗試 USB-video overlay control-plane verifier，並定位任何 runtime blocker。
- 實際完成：upload matching `.bit/.hwh` + verifier 至 `/home/xilinx/codex_usb_overlay`。PYNQ verifier 安全停止於 `No Devices Found`。後續 read-only diagnosis 顯示 XRT/ZOCL/FPGA manager/base.bin 均存在，但 `xilinx` 不屬於 `render` group，不能存取 660 `root:render` 的 `/dev/dri/renderD128`；`xbutil` 因此見到 0 devices。
- 驗證界線／未完成：沒有 DMA control、camera stream、overlay success、DPU、YOLOv8 或 Wi‑Fi 實測。以 noninteractive SSH 嘗試 `sudo usermod -aG render xilinx` 被 password prompt 正確擋下，未修改群組；需使用者在已有 SSH session 完成 sudo 後重新登入。
- Git／同步：本次文件變更待提交並推送到 `origin/main`；SSH private key 和 staged binary overlay 都屬外部機器/板端狀態，不入 Git。

## 2026-11-12 — Verified direct SSH access and sequential capture from both USB cameras on PYNQ

- 需求／決策：使用者完成 SSH key 授權後，直接在板端確認兩支實體相機是否可擷取；採 sequential one-frame capture，避免把 USB2 hub 同時帶寬問題誤判為相機失敗。
- 實際完成：key auth PASS（`AUTH_OK xilinx / pynq`）。`lsusb` 顯示兩支 Logitech C270（`046d:0825`）；OpenCV/V4L2 逐一讀取 `/dev/video0`、`/dev/video2` 均 PASS，frame shapes 為 `(480, 640, 3)`。
- 驗證界線／未完成：沒有同時開兩支、沒有寫檔、DMA、overlay、DPU、YOLOv8 或 Wi‑Fi peer 實測。`wlan0` 仍 DOWN；無 `/dev/dpu*`，`v4l2-ctl` 未安裝。SSH private key 是主機外部憑證，未加入 Git。
- Git／同步：本次文件變更待提交並推送到 `origin/main`。

## 2026-11-12 — Verified SSH login, Linux/PYNQ runtime, and V4L2 node enumeration on the board

- 需求／決策：板子重開且 SSH 可達後，先以實際已登入終端確認目標端 Linux/PYNQ 與相機 device node；不寫入板子。
- 實際完成：使用者提供 `xilinx@pynq` 終端證據：`whoami=xilinx`、Linux `6.6.10-xilinx-v2024.1` aarch64、`PYNQ_OK 3.1.1`、`/dev/video0` 至 `/dev/video3` 均存在。
- 驗證界線／未完成：尚未讀取 V4L2 format/frames，不能把 node presence 當成一或兩支相機出圖、同時串流、DMA/DPU/YOLOv8/Wi‑Fi success。沒有對板子寫入。
- Git／同步：本次文件變更待提交並推送到 `origin/main`。

## 2026-11-12 — Completed host-side person-tracking and deployment contract tests while toolchain installation runs

- 需求／決策：安裝 Vivado/Vitis 2022.1 期間先完成不需工具鏈或板端線材的工作。
- 實際完成：`person_tracking/tests` 24/24 PASS；`live_site/tests` 2/2 PASS，涵蓋 YOLOv8/VART、peer protocol、Wi‑Fi preflight、USB overlay 與雙板 bundle contracts。
- 驗證界線：僅 host-side tests，不是 DPU、xmodel、UVC、DMA、相機或雙板 Wi‑Fi 實測；2022.1 安裝仍進行。無二進位檔上傳。
- Git／同步：本次文件變更待提交並推送到 `origin/main`。

## 2026-11-12 — Diagnosed the post-JTAG-reset recovery state through the actual FTDI UART

- 需求／決策：在 SSH 未回來時以 UART 判斷板子是否有正常回到 SD/Linux，不向板子寫入命令；區分目前 cable 的 UART 與已消失的其他 serial device。
- 實際完成：host user-site 安裝 external `pyserial 3.5`。現存 Xilinx TUL FTDI 介面為 A/B + COM5；COM4（VID_03FD）已不再 present。以 115200 只讀 COM5 12 秒得到 0 bytes；同時 `192.168.3.1:22` TCP/ping FAIL。沒有 transmit serial data 或變更 board config。
- 驗證範圍／未完成：這表示 JTAG cable 枚舉存在但 board 尚未輸出 SD boot/Linux networking；需 physical power-cycle 才能恢復並做 SSH/overlay/camera checks。不能據此判定 UVC/DMA/DPU/YOLO/Wi-Fi success or failure。pyserial 是 host 外部 dependency，不入 Git。
- Git／同步：已提交為 `942c78a`（`Record UART recovery diagnostics`）並成功推送至 `origin/main`；本行同步結果由下一筆文件提交補上。

## 2026-11-12 — Verified JTAG hardware discovery and programmed the USB-video PL, while stopping safely at A53 debug timeout

- 需求／決策：使用者同時接上線後，將 USB-video Block Design 由 Vivado 直接下載到實體 PL，並嘗試讓 Vitis ELF 接管 A53；所有結果需區分 PL program 和 Vitis execution，不能因為其中一步 PASS 宣稱完整成功。
- 實際完成：新增 read-only Hardware Manager scan Tcl/test。Vivado 實測枚舉 `xczu5_0`/ARM DAP，並成功 temporary program external USB-video bitstream，`End of startup status: HIGH`、program property 指向預期 bitstream；未寫 SD/flash。新增 test-first JTAG Vitis launch Tcl（external artifacts、volatile actions、result mrd、可 explicit skip modes）。XSDB 的 generic target compatibility check 阻擋 `fpga`，故沒有使用 skip-device-compatibility。利用 Vivado 已載入 PL、SD-initialized PS 的 skip mode 嘗試 A53 #0 時，`stop` 收到 `Cannot halt processor core, timeout`，立即停止；PMU/FSBL/app 均未下載執行。
- 驗證範圍／未完成：PL program PASS 只證明 bitstream 可在 FPGA config，沒有驗證 Vitis DMA/control、UVC、two cameras、DPU/YOLO/Wi-Fi。JTAG reset 後 SSH temporarily unavailable，需要 physical power-cycle return to SD/Linux before any further board action。外部 artifacts/temporary Tcl/log 不入 Git。
- Git／同步：已提交為 `6eebbb3`（`Add PYNQ USB video JTAG diagnostics`）並成功推送至 `origin/main`；本行同步結果由下一筆文件提交補上。

## 2026-11-12 — Checked simultaneous UART, SSH, and JTAG transport state without programming hardware

- 需求／決策：使用者已同時插接兩條板端連線，需以實際 enumeration 區分 UART/SSH/JTAG 是否各自可用，而非以插頭存在推斷；只允許 read-only inspection。
- 實際完成：Windows 確認 UART 為 COM4，並列出 FTDI USB serial-converter A/B；對 `192.168.3.1:22` TCP check PASS。用 Embedded Vitis 2024.2 XSDB/hw_server 執行 `connect; targets -target-properties; disconnect`，結果沒有 FPGA target 列出。沒有 program/reset/write board，temporary hw_server 沒有保留。
- 驗證範圍／未完成：這證實 UART 與 SSH transport 可同時存在；僅能證明 JTAG USB enumeration，不證明 JTAG chain/FPGA access。須在 XSDB 顯示 `xczu5_0` 後才可 JTAG download；SSH authentication 仍未成功，故未執行 overlay/UVC/DMA board tests。
- Git／同步：已提交為 `17bb1ac`（`Record board transport verification`）並成功推送至 `origin/main`；本行同步結果由下一筆文件提交補上。

## 2026-11-12 — Added a dedicated deployable PYNQ check for the USB-video overlay

- 需求／決策：讓已封裝的 USB-camera Block Design 有可由 SD/Linux deployment bundle 執行的實機 control-plane check，且不得將它與舊 `pynq_zu_yolox` bring-up overlay 混用或意外啟動 DMA/UVC。
- 實際完成：新增 USB verifier，要求 matching `pynq_zu_usb_video.bit/.hwh`，下載 overlay 後只測 GPIO `0xA0010000` 和 mailbox frame-ID `0xA0020004` 的非破壞 readback，finally 清零，從不寫 CONTROL。fake-overlay/MMIO tests 2/2 PASS。bundle 新增 verifier 和 `--usb-video-overlay-dir`，把 artifacts 分置 `overlay_usb_video/`；deploy helper 新增 opt-in USB overlay argument/check。bundle/runtime tests 共 4/4 PASS、PowerShell parse PASS；external tar 實測含 verifier、bit、HWH。
- 驗證範圍／未完成：尚無有效 authenticated board login，故沒有 SCP、PYNQ `Overlay()`、MMIO、UVC/DMA 或 board writes。external tar/bit/HWH 不入 Git；host tests 不能取代 on-board hardware evidence。
- Git／同步：已提交為 `5254d41`（`Verify deployed USB video overlay`）並成功推送至 `origin/main`；本行同步結果由下一筆文件提交補上。

## 2026-11-12 — Staged the exact USB-video Vivado implementation as a PYNQ Linux overlay

- 需求／決策：在板端 SSH 尚未可驗證時，先完成不需插線的 Linux-overlay handoff；只接受 USB-video Block Design 實作產物，不混用舊 bring-up overlay，且不得寫板子／SD。
- 實際完成：新增 `prepare_pynq_zu_usb_video_overlay.ps1` 與 test-first static contract test（缺 script 時 FAIL，實作後 1/1 PASS）。script 僅複製 implementation 的 `pynq_zu_usb_video_wrapper.bit` 與 matching BD HWH，輸出同 stem 的 `.bit/.hwh`、檢查非空並列出 SHA-256，沒有 SSH/SCP/bootgen。實跑 external build，產出 7,797,821-byte bit 和 333,915-byte HWH，SHA-256 分別為 `e92ee2cc3f7493ea141e7e363a80893b393225e744562c33093b1011e34cd6c2`、`ac5497244a55b17810c6bc318dd050fec159c3e84005afe3eb91ce31b375c6b5`。
- 驗證範圍／未完成：artifact 只留在 external `%TEMP%`，不進 Git、未上傳或載入 PYNQ。它證明 Linux bring-up 可取得正確的 matching hardware pair，不代表 UVC、DMA-BUF, two-camera、DPU/YOLOv8/Wi-Fi 或任何 board runtime 已成功。
- Git／同步：已提交為 `912a918`（`Stage USB video PYNQ overlay`）並成功推送至 `origin/main`；本行同步結果由下一筆文件提交補上。

## 2026-11-12 — Rebuilt the USB-video Vitis ELF using the complete Embedded installation

- 需求／決策：直接反查並修復 USB-video Vitis 重建遭 Lopper path failure 阻塞的 host toolchain；保留既有 external workspace，不對硬體做寫入。
- 實際完成：比對既有成功 BSP metadata 後，確認正確安裝為 `C:\Xilinx_Embedded_2024_2\Vitis\2024.2`，其 embedded software repository 與 Lopper 1.2.0 都可用；另一套 `C:\Xilinx\Vitis\2024.2` 的 Lopper install log 則記錄 requirements path 缺失。用完整安裝及新的 external workspace 重跑 tracked build script，實際產出 352,344-byte A53 ELF。對同一 external XSA 與新 generated `xparameters.h` 執行 handoff verifier PASS：DMA `0xA0000000`、frame GPIO `0xA0010000`、mailbox `0xA0020000`；verifier tests 3/3 PASS。
- 驗證範圍／未完成：只驗證 host platform/application build 與 control-plane address contract；external workspace/ELF/log 均不入 Git。未 JTAG program、未寫 SD/PL，也不代表 UVC capture、Linux DMA ownership、two-camera、DPU/YOLOv8 或 Wi-Fi 已在板端運作。
- Git／同步：已提交為 `d68e05c`（`Rebuild USB video Vitis platform`）並成功推送至 `origin/main`；本行同步結果由下一筆文件提交補上。

## 2026-11-12 — Reopened and verified the USB-camera Block Design in Vivado

- 需求／決策：以 Vivado 本身而非僅 XML/XSA parser 重新確認可重跑 USB-camera Block Design 與 Vitis control address interface；不改動既有 implementation 或 hardware。
- 實際完成：新增 read-only `verify_pynq_zu_usb_video_bd.tcl` 和 test-first static contract test（缺 script 時 FAIL，實作後 1/1 PASS）。Vivado 2024.2 batch 實際 open external completed project，載入 local packaged IP repo，成功讀取 `pynq_zu_usb_video` BD。`validate_bd_design` status valid；實測 `axi_dma_0=0xA0000000`、`frame_id_gpio_0=0xA0010000`、`yolox_video_rtl_0=0xA0020000`，marker PASS、exit=0。
- 驗證範圍／未完成：未 synthesis/implementation/export、未 JTAG program／改 SD，也未開啟 UVC/DPU/Wi-Fi。Vivado session log 留在 `%TEMP%` 不入 Git；這是 BD control-plane verification，不是 camera/DPU runtime proof。
- Git／同步：已提交為 `af7b8bf`（`Verify USB video Block Design in Vivado`）並成功推送至 `origin/main`；本行同步結果由下一筆文件提交補上。

## 2026-11-12 — Confirmed PYNQ SSH transport without assuming board access

- 需求／決策：重新取得 board-side runtime evidence，但只作唯讀登入；不因為 TCP 22 開放就假設可執行板端檢查。
- 實際完成：`192.168.3.1:22` TCP PASS。為免 interactive SSH prompt 阻塞，host user-site 安裝 `paramiko` 5.1.0，以使用者先前提供的 default credentials 對 `xilinx` user 嘗試一次 password authentication。結果為 `AuthenticationException: Authentication failed`。
- 驗證範圍／未完成：沒有 remote command 送達或執行，故沒有重新驗證 video nodes/DPU/VART/Wi-Fi；沒有 SD/PL/account/network writes，也沒有嘗試其他密碼。後續需要可用 key 或使用者在本機輸入 current password。
- Git／同步：已提交為 `1c30acc`（`Record PYNQ SSH authentication state`）並成功推送至 `origin/main`；本行同步結果由下一筆文件提交補上。

## 2026-11-12 — Recorded verifiable identity for the native DPU B512 artifacts

- 需求／決策：讓後續 2022.1 Linux／model deployment 能以 exact DPU artifact identity 取代易混淆的資料夾名稱或版本猜測。
- 實際完成：新增 read-only artifact verifier，讀 component XML、arch JSON、bitstream、XSA，輸出 IP version、fingerprint 與 SHA-256。test-first：synthetic test 先因 module absent FAIL，實作後 1/1 PASS。對 external B512 build 實跑 PASS：IP 4.0、fingerprint `0x101000016010400`，bitstream SHA `1e173c9a707d050defca9a4d7235e8f2e51e680fd40040d976256b24ee46e29e`，XSA SHA `8b0f59c19d239de34dbe5366eb61f826a299c9caae78a671738407addeb9cc57`。
- 驗證範圍／未完成：identity record 不證明 image/device tree/driver/VART/xmodel/model output 或 board inference；未寫 PL/SD/board。external binary paths 和 artifacts 不進 Git。
- Git／同步：已提交為 `3147429`（`Verify DPU deployment artifact identity`）並成功推送至 `origin/main`；本行同步結果由下一筆文件提交補上。

## 2026-11-12 — Packaged the full two-board Wi-Fi and future VART runtime sources

- 需求／決策：確保實際部署到每塊 PYNQ 的 runtime tarball 包含目前兩板 Wi-Fi gate 與 VART YOLOv8 adapter，而非 repository 有程式但 target bundle 缺檔。
- 實際完成：新增 `runtime_sources()` 並令 bundle 使用它；加入 Wi-Fi preflight 和 `yolov8_vart.py`。test-first：新的 bundle contract test 先因缺 function FAIL；實作後 1/1 PASS，person_tracking suite 22/22 PASS。實際 tarball 初次輸出到 `C:\` root 失敗，ACL evidence 顯示 root 沒有一般檔案寫入權；改用 user `%TEMP%` 後成功產出 archive，`tar -tzf` 確認兩檔皆存在。
- 驗證範圍／未完成：artifact 是 local `%TEMP%` 檔，未加入 Git、未 SCP/解壓至 board；不證明 VART runtime、DPU model、Wi-Fi association 或兩板 exchange。未改 SD/PL/network。
- Git／同步：已提交為 `be77f37`（`Bundle WiFi and VART PYNQ runtime sources`）並成功推送至 `origin/main`；本行同步結果由下一筆文件提交補上。

## 2026-11-12 — Documented the full-duplex one-camera-per-board launch contract

- 需求／決策：把兩板目標從舊的單向 sender example 明確化為全雙工 metadata exchange；每塊板各一個相機、各自收發，且不得硬編碼跨電腦的 IP/camera path。
- 實際完成：更新 `person_tracking/README.md`，要求 A/B 均先啟動 receiver、兩邊皆以 real peer address 通過 read-only Wi-Fi gate，再以相反 peer IP／本機 camera index 啟動 sender；加入 `--frames 1` bring-up guidance。同步修正 VART 文件為現有 opt-in `yolov8_vart` Detector backend 的實際 contract。
- 驗證範圍／未完成：文件與既有 loopback/retry coverage 不等於 Wi-Fi 實測；目前仍無第二板、authorized Wi-Fi topology 或 full-duplex run。本次未改 SSID/network/board/SD/PL。
- Git／同步：已提交為 `0d0ad99`（`Document two-board full-duplex deployment`）並成功推送至 `origin/main`；本行同步結果由下一筆文件提交補上。

## 2026-11-12 — Verified the actual Vivado XSA to Vitis control-address handoff

- 需求／決策：直接驗證本專案「Vivado Block Design 硬體檔→Vitis 控制檔」的 control-plane address contract，而非只依賴固定 C test address。
- 實際完成：XSA verifier 新增 optional `--xparameters`，讀 Vitis generated `xparameters.h` 並與 HWH contract 比對 DMA=`0xA0000000`、frame GPIO=`0xA0010000`、mailbox=`0xA0020000`。test-first：新增 function import test 先失敗；實作後 verifier tests 3/3 PASS。用 external completed Vivado XSA 和 Vitis platform header 實跑，輸出 `PYNQ_ZU_USB_VIDEO_XSA_PASS`，全部 address match。
- 驗證範圍／未完成：這驗證已完成 2024.2 USB-video hardware build 的 handoff/compile address interface；不代表 camera UVC stream、Linux DMA ownership、IRQ, DPU、YOLOv8 或 two-board Wi-Fi 已在板端運作。未 program PL/改 SD；外部 XSA/workspace 不入 Git。
- Git／同步：已提交為 `20e546a`（`Verify Vivado to Vitis address handoff`）並成功推送至 `origin/main`；本行同步結果由下一筆文件提交補上。

## 2026-11-12 — Connected the opt-in DPU backend to the existing detector facade

- 需求／決策：使編譯後的 YOLOv8 DPU model 能沿用既有 `Detector` → tracker → peer packet dataflow，同時維持 CPU YOLOv8 為可用預設、避免未驗證 xmodel output 被自動解碼。
- 實際完成：`PERSON_DETECTOR=yolov8_vart` 現要求 explicit `PYNQ_VART_XMODEL`，驗證 `.xmodel` 後用 `VartYoloV8.from_xmodel()`；只有 explicit `PYNQ_VART_STANDARD_OUTPUT=1` 才使用前輪 conditional standard decoder，否則 decoder 保持未註冊並安全拒絕 detection。test-first：新增 missing-xmodel contract 先因 backend unsupported 失敗，實作後 backend tests 3/3、完整 person_tracking 22/22 PASS。
- 驗證範圍／未完成：未有 xmodel、VART target runtime 或 board DPU；DPU backend 未實際執行。仍需 matching 2022.1 image/driver/runtime、compile xmodel、檢查 tensor shape，才可設定 standard-output flag 或寫 custom decoder。
- Git／同步：已提交為 `a6a609f`（`Add opt-in YOLOv8 VART detector backend`）並成功推送至 `origin/main`；本行同步結果由下一筆文件提交補上。

## 2026-11-12 — Added a conditional standard YOLOv8 VART decoder bridge

- 需求／決策：在尚未能建 target image 時，補上未來 DPU YOLOv8 tensor 到既有 tracker／Wi-Fi person schema 的安全接點；不得假設所有 compiled DPU graph 都輸出 ONNX raw head。
- 實際完成：`standard_yolov8_decoder()` 只對驗證過的單一 raw Ultralytics layout `(1,84,N)`／`(1,N,84)` 生效，重用既有 de-letterbox/person/NMS contract。test-first：新增 import/test 先因函式缺失失敗；實作後 VART adapter 5/5、完整 person_tracking 21/21 PASS。單頭 synthetic person tensor 還原成 `[160,160,480,320]`，ambiguous multi-head outputs 明確拒絕。
- 驗證範圍／未完成：沒有 xmodel，沒有真的 VART runner／DPU inference 或 board frame；未註冊任何猜測 decoder。真正 compiled output 若為 multi-head/feature maps 必須另寫並實測 model-specific decoder。
- Git／同步：已提交為 `5a26881`（`Add guarded YOLOv8 VART decoder bridge`）並成功推送至 `origin/main`；本行同步結果由下一筆文件提交補上。

## 2026-11-12 — Connected WSL to the verified Vitis AI 2.5 compiler and hardened the version gate

- 需求／決策：讓實際 PetaLinux/WSL host 能使用已下載的 Vitis AI 2.5 compiler image，並避免只因 Docker CLI 或使用者輸入版本字串存在就把不相容 host 誤判為 ready。
- 實際完成：external WSL user-local `/home/petalinux/.local/bin/docker` symbolic link 指向既有 Docker Desktop CLI；WSL 實測能 inspect `xilinx/vitis-ai:2.5.0`，digest=`sha256:eaa85efb06924995ebdb973546e7f69169b003b8cc525764bd9524ad554dddbe`。並用 WSL `docker run --rm` 啟動 image、activate `vitis-ai-pytorch`，container 內 `vai_c_xir` 成功輸出 compilation banner。preflight 現會檢查 exact fixed Docker image，並新增 `--petalinux-root` 從 `settings.sh` 讀 `PETALINUX_VER`、確認 `scripts/petalinux-create`。test-first：新增 import 的 test 先失敗，再實作；preflight tests 6/6 PASS。
- 驗證範圍／未完成：WSL 實跑確認 current root 確實為 2024.1，Docker/image/arch JSON 與 PetaLinux executable 都可見，但 gate 正確 FAIL：DPU 4.0/AI 2.5 需要 2022.1。未取得/安裝 2022.1 Vivado/PetaLinux、未建 image/xmodel、未寫 SD/PL 或碰板子。
- Git／同步：已提交為 `6b9e2fa`（`Record WSL Vitis AI compiler execution`）並成功推送至 `origin/main`；本行同步結果由下一筆文件提交補上。

## 2026-11-12 — Cross-linked VART 2.5 against the correct 2022.1 SDK

- 需求／決策：在實際 DPUCZDX8G 4.0 的 2.5/2022.1 contract 下，先用最小 AArch64 link smoke 驗證 SDK sysroot 與 VART/XIR runtime 能共用，而不把 runtime 錯裝到現有 PYNQ 2024.1 SD image。
- 實際完成：official 2022.1 SDK 已 external 安裝於 WSL `/home/petalinux/sdk_2022_1`；Vitis AI 2.5 runtime archive 只 overlay 到該 sysroot。新增 tracked `vart_link_smoke.cpp`、`build_vart_link_smoke.sh` 和 source-contract test。test-first：缺檔時 test 如預期失敗；實作後 test PASS。source matching environment 後實際輸出 ARM aarch64 PIE ELF，`readelf -d` 確認 NEEDED `libvart-runner.so.2`、`libxir.so.2`、`libunilog.so.2`。
- 驗證範圍／未完成：這是 cross-link ABI smoke，程式的 null subgraph 使它不可執行；沒有 PetaLinux 2022.1 image、DPU driver/VART board runtime、xmodel、YOLOv8 compile 或板端 inference。SDK/runtime/ELF 均為外部資產不入 Git，未改 SD/PL/UART/network。
- Git／同步：已提交為 `9379e8c`（`Add VART 2.5 link smoke validation`）並成功推送至 `origin/main`；本行同步結果由下一筆文件提交補上。

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
- Git：已提交為 `e588a7f`（`Retry two-board metadata delivery`）並成功推送至 `origin/main`；本行的同步結果將由下一筆文件提交記錄。

## 2026-11-11 — Vitis Linux single-C270 packed-lane hardware check

- 需求／決策：同板兩 C270 同時串流已被 USB hub bandwidth 證據阻擋；為之後每板一鏡頭架構提供可由 Vitis/Linux 實際驗證的單 lane source，而非複製影像假裝雙鏡頭。
- 實際完成：`uvc_v4l2_packer.c` 新增 `--single-a`／`--single-b`，未使用的 32-bit RGB lane 維持黑色，並修正 packed-frame partial-write handling。Vitis 2024.2 AArch64 compile 以 `-Werror` 先檢出 declaration-order error；修正後產生 ELF。
- 實機驗證：暫存 ELF 到 `192.168.3.1:/tmp`，`--single-a /dev/video0` 協商 320×240 YUYV、10 FPS，輸出 2,457,600 bytes、307,200 words；A nonzero=307,160，B nonzero=0。測後 `/tmp/uvc_v4l2_packer`、`/tmp/vitis_single_a.bin` 已清除。
- 驗證界線／未完成：尚無 contiguous DMA/AXI DMA/PL/DPU、第二板或 Wi-Fi 結果；未改 SD 卡或系統設定。現有兩 C270 shared-hub STREAMON failure 仍有效。
- Git：已提交為 `f64bf98`（`Add Vitis single-camera packed lane mode`）並成功推送至 `origin/main`；本行的同步結果將由下一筆文件提交記錄。

## 2026-11-11 — Vitis Linux B-lane hardware confirmation

- 需求／決策：確認未來第二板的 `--single-b` 不會將 C270 RGB 填到 A lane；僅使用既有 board、`/tmp` 和相同 Vitis-built ELF。
- 實機驗證：`--single-b /dev/video0` 協商 320×240 YUYV、10 FPS，輸出 307,200 words；A nonzero=0、B nonzero=307,176。此結果與 `--single-a` 的反向 lane 結果一起確認 lane selection。
- 驗證界線／未完成：仍是同一實體板／相機，不是第二板、Wi-Fi、AXI DMA、PL 或 DPU；暫存 ELF/output 已清除且未變更 SD/system settings。
- Git：已提交為 `0f08f57`（`Record Vitis B-lane hardware verification`）並成功推送至 `origin/main`；本行的同步結果將由下一筆文件提交記錄。

## 2026-11-11 — Read-only two-board Wi-Fi preflight

- 需求／決策：在尚未取得第二板／授權 SSID 前，建立不會改網路設定的 gate，避免把有 `wlan0` 介面誤說成已可交換 metadata。
- 實際完成：新增 `pynq_wifi_peer_preflight.py` 和 4 個 offline contract tests。gate 要求 interface up、IPv4；給 `--peer-host` 時還要求 peer TCP 可達。支援任意 interface name 並只做一次 TCP connect。
- 實機驗證：暫傳至現有 PYNQ `/tmp` 以 `wlan0` 執行，JSON 證實 interface exists 但 down、沒有 IPv4，預期 exit=1／FAIL；暫存檔已移除。
- 驗證界線／未完成：沒有 SSID scan/join、沒有 network write、沒有第二板或 Wi-Fi packet。未來需在共同 Wi-Fi/AP 上啟動 peer receiver 後，以 `--peer-host` 通過。
- Git：已提交為 `02c8183`（`Add two-board WiFi readiness gate`）並成功推送至 `origin/main`；本行的同步結果將由下一筆文件提交記錄。

## 2026-11-11 — Sequential two-C270 Vitis Linux packing check

- 需求／決策：同時 STREAMON 已受 shared-hub `ENOSPC` 阻擋，但仍需以 Vitis/Linux 實機確認兩支已接 C270 均可送進既有雙 lane packed format；明確採 sequential，禁止誤稱同步雙鏡頭。
- 實際完成：`uvc_v4l2_packer.c` 新增 `--sequential`，先擷取/關閉 A 再擷取/關閉 B，copy 兩個 YUYV source 後才 pack。Vitis 2024.2 AArch64 compile PASS。
- 實機驗證：`--sequential /dev/video0 /dev/video2` 兩者各協商 320×240 YUYV、10 FPS；輸出 307,200 words，A nonzero=307,168、B nonzero=307,112。`/tmp` ELF/output 已清除。
- 驗證界線／未完成：沒有共同 timestamp／simultaneous streams，沒有 DMA/PL/DPU/person inference 或第二板/Wi-Fi。既有 simultaneous USB bandwidth failure 仍有效。
- Git：已提交為 `bd525f5`（`Support sequential dual C270 packing`）並成功推送至 `origin/main`；本行的同步結果將由下一筆文件提交記錄。

## 2026-11-11 — Linux CMA / DMA-BUF read-only audit

- 需求／決策：判定 Vitis/Linux packer 下一步是否已有 contiguous allocation source，且不以 standalone physical-address model 或 `/dev/mem` 冒充 Linux DMA ownership。
- 實際驗證：live PYNQ 有 `/dev/dma_heap/linux,cma`、`/dev/dma_heap/system`，CmaTotal=524288 KiB、CmaFree=517188 KiB。
- 驗證界線／未完成：沒有 allocate/submit DMA buffer、沒有 DMA-BUF importer/driver、沒有 DMA/PL/DPU transfer；未改 kernel/module/bitstream。需要 matching kernel client/driver attach/map/sync DMA-BUF 才能接 AXI DMA。
- Git：已提交為 `cc4d3d3`（`Document Linux CMA DMA handoff boundary`）並成功推送至 `origin/main`；本行的同步結果將由下一筆文件提交記錄。

## 2026-11-11 — DPU v4.0 branch / Vitis AI 3.5 version clarification

- 需求／決策：核對官方 release wording，避免把 DPU source branch `v4.0` 誤填為 Vitis AI runtime/compiler `4.0`，而下載錯 toolchain。
- 實際完成：官方 Vitis-AI v4.0 release notes 證實該 branch DPU IP 搭配 Vitis AI 3.5 與 2024.1 tools；preflight docstring 和 Linux README 已明確區分。3/3 tests PASS，exact arch JSON 實跑仍 FAIL 於 compiler/PetaLinux/2024.2 mismatch。
- 驗證界線／未完成：未下載或安裝工具；AMD Chrome profile 目前 signed out，故無法在本機取得 PetaLinux 2024.1。C: 剩餘約 165.70 GiB，超過 AMD UG1144 所列 100 GB host free-space minimum，但還需 Linux host。
- Git：已提交為 `a5f9262`（`Clarify DPU Vitis AI version contract`）並成功推送至 `origin/main`；本行的同步結果將由下一筆文件提交記錄。

## 2026-11-11 — Non-download host validation and WSL prerequisite check

- 需求／決策：使用者要求在等待 AMD 下載表單資訊時，繼續不需要該表單的其他目標；不得填寫、送出或變更 AMD export/download 資料。
- 實際完成：以 Python 內建 `unittest` 重跑 19 個 `person_tracking` tests 與 3 個 DPU build-host preflight tests，皆 PASS；因系統未裝 `pytest`，未額外安裝測試套件。以 exact B512 `arch.json` 實跑 preflight，仍正確 FAIL 於 Docker/`vai_c_xir`、PetaLinux 缺失及 2024.2 vs required 2024.1 contract。Vitis direct AArch64 GNU compiler 亦成功重建 UVC packer（外部 75,272-byte ELF）。
- 環境檢查：嘗試 WSL install 前檢查發現目前 `wsl.exe` 是舊版系統層級介面；Windows Optional Feature 查詢要求 elevated permission。因此沒有安裝 WSL distribution/Docker/PetaLinux、沒有要求或繞過管理員權限、也沒有重開機。
- 驗證界線／未完成：沒有改 tracked code、AMD 帳號/表單、板子、相機、SD 或 network；cross-compile 不等於 Linux DPU driver/VART/YOLOv8 DPU inference。仍待有效的 PetaLinux 2024.1 取得、受支援 Linux host、matching 2024.1 hardware/image、DPU runtime 與實機驗證。
- Git：已提交為 `251fa59`（`Record host validation and WSL prerequisite`）並成功推送至 `origin/main`；本行的同步結果由下一筆文件提交補上。

## 2026-11-11 — Reject empty xmodel files in DPU runtime gate

- 需求／決策：在等候需要使用者在場的 Windows administrator / AMD download 工作前，繼續完成不需外部權限的 DPU runtime acceptance tooling，避免 artifact placeholder 被誤認為可部署模型。
- 實際完成：採 test-first 方式新增 offline DPU runtime tests；先得到預期 import failure，證明舊程式沒有 model validation helper。新增 `valid_xmodel()` 後，明確指定的 `.xmodel` 必須是非空一般檔案；空檔、錯誤副檔名或 stat error 一律拒絕。新增的 fake device tree test 只接受 `xlnx,dpuczdx8g-4.0` compatible node。
- 驗證界線／未完成：全部離線 tests 為 24/24 PASS（person_tracking 19、DPU Linux 5）。沒有登入板子、下載/安裝軟體、改 Windows/AMD 表單或執行 VART；nonempty model 檔也不等於已匹配 B512 architecture 或 inference PASS。
- Git：已提交為 `71bf3ca`（`Reject empty DPU xmodel artifacts`）並成功推送至 `origin/main`；本行的同步結果由下一筆文件提交補上。

## 2026-11-11 — Rebuilt USB-camera Vivado Block Design and Vitis controller

- 需求／決策：使用者要求以 Vivado Block Design 做硬體檔、Vitis 做控制檔，且目前先以一塊 PYNQ-ZU/兩個 USB C270 為硬體資料路徑；USB C270 必須保持 PS USB MIO/UVC，不可虛構 PL camera pins。
- 實際完成：於新的外部短路徑重新跑 complete tracked flow：PYNQ-ZU project、custom IP Catalog package、Block Design、`validate_bd_design`、synthesis、implementation、bitstream、fixed XSA export。XSA 為 1,573,588 bytes 且含 bitstream/HWH/PS init/system metadata。route report 16,007/16,007 fully routed、0 errors；WNS `+0.752 ns`、WHS `+0.020 ns`，all user timing constraints met。使用同一新 XSA 實跑 Vitis Embedded 2024.2，輸出 352,272-byte AArch64 ELF；platform macro addresses 為 DMA `0xA0000000`、GPIO `0xA0010000`、RTL mailbox `0xA0020000`。
- 驗證：FPGA static contracts 5/5 PASS，Vitis direct AArch64 compiler 以 warnings-as-errors 成功編譯 `video_control.c`。host C unit executable 未能執行，因本機沒有 host C compiler；不以此掩蓋，且 Vitis ELF build 本身已完成。
- 驗證界線／未完成：未將這次 bitstream/ELF 寫入板子或 SD，未開相機、未配置 DMA-BUF/CMA、未解決同 hub 雙 C270 bandwidth、未跑 DPU/VART/YOLOv8/Linux or Wi-Fi。所有 large artifacts 保持在 `C:\pynq_zu_usb_video_rebuild_20261111`／`C:\pynq_vitis_usb_video_rebuild_20261111`，不進 Git。
- Git：已提交為 `8ceb710`（`Record USB video hardware and Vitis rebuild`）並成功推送至 `origin/main`；本行的同步結果由下一筆文件提交補上。

## 2026-11-11 — Executed Vitis controller host unit test

- 需求／決策：補齊 USB-video Vitis control source 的 executable unit test，不安裝額外工具、不改系統。
- 實際完成：重新盤點既有 Xilinx install 後找到 Vitis bundled MinGW GCC，臨時加入 process PATH，以 `-std=c11 -Wall -Wextra -Werror` 編譯並執行 `video_control.c` + `test_video_control.c`，輸出 `VIDEO_CONTROL_TEST_PASS`。測試覆蓋 frame ID、bbox payload 與最後 CONTROL commit 的 register write ordering，以及遺失必要地址時的拒絕；暫存 executable 已移除。
- 驗證界線／未完成：此為 host pure-C contract，不觸碰硬體，未執行 A53 ELF、UVC、DMA、DPU 或 Wi-Fi。前一筆 Vivado/XSA/Vitis build evidence 與 Linux deployment blockers 維持不變。
- Git：已提交為 `c6af6b1`（`Verify Vitis controller host contract`）並成功推送至 `origin/main`；本行的同步結果由下一筆文件提交補上。

## 2026-11-11 — Added USB-video XSA structural handoff gate

- 需求／決策：讓可重建的 Vivado USB-video XSA 在交給 Vitis 前有 machine-readable gate，避免只以檔案存在誤稱 Vivado→Vitis control mapping 正確。
- 實際完成：新增 `verify_pynq_zu_usb_video_handoff.py` 和兩個 offline tests。gate 讀取 archive/HWH，要求 bitstream、HWH、system definition、PS init source，並核對 AXI DMA=`0xA0000000`、frame GPIO=`0xA0010000`、video RTL mailbox=`0xA0020000`。test-first run 先得到 missing-module failure；第一次真實 artifact run 又發現 HWH `0X` prefix normalization 和 missing-bitstream diagnostics 的缺口，已修正。
- 驗證：FPGA tests 7/7 PASS；對剛重新建出的 1,573,588-byte XSA 回傳 `PYNQ_ZU_USB_VIDEO_XSA_PASS`，addresses 與 Vitis `xparameters.h` 對齊。
- 驗證界線／未完成：gate 是 host read-only structural verification；未載入 bitstream、未跑 A53 ELF/UVC/DMA/PL/DPU/Wi-Fi，產物未上傳 Git。
- Git：已提交為 `48ea575`（`Verify USB video Vivado handoff`）並成功推送至 `origin/main`；本行的同步結果由下一筆文件提交補上。

## 2026-11-11 — Read-only live PYNQ UART runtime recheck

- 需求／決策：在不需要使用者操作、SSH password 或燒錄板子的前提下，確認目前已連線 UART 的 PYNQ-ZU Linux/DPU/camera/Wi-Fi 真實狀態。
- 實際完成：Windows 偵測 COM4 為 USB CDC serial；使用 115200 baud、DTR/RTS disabled 讀到 Linux prompt。只送出 read-only shell queries，證實 kernel `6.6.10-xilinx-v2024.1-gb6067dbebcc8` AArch64，`/dev/video0..3` 存在；`/dev/dpu*`、DPU compatible DT node、`xdputil` 均不存在，Python VART/XIR 皆 false。`wlan0` 存在但 DOWN/zero MAC/no IPv4。
- 驗證界線／未完成：沒有寫 console data、上傳、PL program/reset、SD/network/camera state change。此結果不能替代 matching DPU Linux image/VART/xmodel、C270 simultaneous streaming、second board 或 Wi-Fi peer test。
- Git：已提交為 `16a15dd`（`Record live PYNQ UART runtime check`）並成功推送至 `origin/main`；本行的同步結果由下一筆文件提交補上。

## 2026-11-11 — Read-only live C270 USB topology verification

- 需求／決策：釐清四個 `/dev/video*` 是實體相機數量還是每支 UVC camera 的多節點，並以真實 USB topology 驗證同 hub bandwidth 限制；不開啟 stream 或改硬體設定。
- 實際完成：UART read-only query 顯示 `video0..3` 都是 C270 HD WEBCAM；`lsusb` 顯示兩支 `046d:0825` C270（bus 001 device 006/007）共用 `0424:2744` USB2 hub。另有 board 的 `0424:5744` USB3 hub；C270 的兩個 V4L2 node pattern 表示實物為兩支相機，非四支。
- 實際 Wi-Fi evidence：`/sys/class/net/wlan0/address` 為 all-zero MAC，與既有 DOWN/no IPv4 一致。沒有第二板/SSID，故未連線或修改網路。
- 驗證界線／未完成：不重跑 simultaneous capture；先前 real `ENOSPC` remains applicable。未寫 SD/PL、未開 UVC/DPU/VART/YOLO/Wi-Fi peer；兩板各一鏡頭仍是後續 deployment route。
- Git：已提交為 `cd8857a`（`Record C270 USB topology verification`）並成功推送至 `origin/main`；本行的同步結果由下一筆文件提交補上。

## 2026-11-11 — Read-only PYNQ Wi-Fi driver diagnosis

- 需求／決策：判定 all-zero/down `wlan0` 是缺 hardware/driver 還是未完成 Linux/network setup；只讀取現況，不 scan/join/write Wi-Fi。
- 實際完成：UART 讀取 sysfs/dmesg；`wlan0` 是 SDIO `mmc1:0001:1` 的 `wilc_sdio` driver，dmesg 明示 `Driver Initializing success`。但 `cfg80211` 無法載入 `regulatory.db`（error -2），並有未連線 RSSI read failure。
- 驗證界線／未完成：未啟用 interface、未設定 regulatory data/SSID/peer，沒有第二板。這證實 driver/hardware initialization，不能證實 wireless association、IP addressing、TCP peer 或雙板工作。
- Git：已提交為 `8c366ad`（`Record PYNQ WiFi driver diagnosis`）並成功推送至 `origin/main`；本行的同步結果由下一筆文件提交補上。

## 2026-11-11 — Corrected regulatory database conclusion by package audit

- 需求／決策：驗證 boot dmesg `regulatory.db` error -2 是否代表 rootfs 真缺少 wireless regulatory database，避免未經證據重裝/修改 image。
- 實際完成：UART read-only check 證實 `/lib/firmware/regulatory.db`（4,160 bytes）與 `.p7s` 都存在；`wireless-regdb` package status 是 `install ok installed`，installed/candidate 均為 `2021.08.28-0ubuntu1`。
- 更正：先前記錄的 kernel load error 仍是事實，但不能推論為 package/file missing；目前較合理的未驗證原因是 early boot/load timing 或 association 前的 driver state。未來應在授權 SSID 下啟用/association diagnostics 後才決定 image repair。
- 驗證界線／未完成：沒有 network writes、reload/installation、interface up 或 scan；仍無第二板/SSID/peer test。
- Git：已提交為 `f237e2e`（`Correct PYNQ regulatory database diagnosis`）並成功推送至 `origin/main`；本行的同步結果由下一筆文件提交補上。

## 2026-11-12 — Verified PetaLinux installer download

- 需求／決策：確認使用者表示已完成的 PetaLinux download 是否實際存在、完成且可供下一步 Linux-host installation 使用；只讀取檔案，不執行 installer。
- 實際完成：在 Downloads 找到 `petalinux-v2024.1-05202009-installer.run`，大小 3,296,562,820 bytes，SHA-256 `9EFB6191DC9A90AFEB374EAFD8733CBC8C27C2E5D54E2D388FA0302294B5BB93`。
- 驗證界線／未完成：這是 installer acquisition，不是 PetaLinux/WSL/Vitis AI 安裝或 DPU Linux image build；未執行檔案、未改 Windows/board。大檔保持 Downloads、因外部 installer 且不適合 Git，未上傳 repository。
- Git：已提交為 `808bb54`（`Record PetaLinux installer verification`）並成功推送至 `origin/main`；本行的同步結果由下一筆文件提交補上。

## 2026-11-12 — Enabled Windows WSL prerequisites pending reboot

- 需求／決策：使用者已在電腦前，開始 PetaLinux 所需 Linux host 的系統前置設定；避免自動關閉正在運行的 Vivado/Vitis。
- 實際完成：以 elevated Windows command 啟用 `Microsoft-Windows-Subsystem-Linux` 與 `VirtualMachinePlatform`，exit code=0、使用 `-NoRestart`。讀取 reboot markers 結果為 CBS `RebootPending=True`、`PendingFileRenameOperations=True`；`wsl --list --verbose` 尚無 Linux distribution，符合重開前預期。
- 驗證界線／未完成：未重開 Windows，未安裝 Ubuntu/PetaLinux/Docker/Vitis AI，未執行 3.07-GiB PetaLinux installer，未變更 board/SD/FPGA。需使用者先儲存 GUI work 並確認 reboot，重開後再建立受支援 Ubuntu 22.04。
- Git：已提交為 `622f52b`（`Record WSL prerequisite enablement`）並成功推送至 `origin/main`；本行的同步結果由下一筆文件提交補上。

## 2026-11-12 — Installed WSL2 Ubuntu and PetaLinux 2024.1 build host

- 需求／決策：建立能產生 matching PetaLinux/DPU Linux image 的實際 Linux host，避免把單純 Windows/Vivado 交接誤稱為可部署的 DPU runtime。
- 實際完成：修復後仍偵測到 Windows inbox WSL payload 缺失（`0x8007019e`），遂以 winget 安裝 hash-verified official `Microsoft.WSL` 3.0.5，重開機後確認 WSL2 kernel `6.18.58.1-1`。已註冊 Ubuntu 22.04、建立 non-root `petalinux` user、安裝 PetaLinux host dependencies與 `zlib1g-dev`，並以已驗證 SHA-256 的 AMD 2024.1 installer 安裝 aarch64 PetaLinux 至 `/home/petalinux/xilinx/petalinux/2024.1`。final installer log 宣告 SDK ready；Bash source 後 `petalinux-create`、`petalinux-config`、`petalinux-build` 可用。
- 安裝清理：installer 的 `--dir` 在此 flow 未生效。首次誤產生於 repo 的未追蹤 outputs 已移至 `C:\\pynq_wsl_setup\\quarantine_peta_wrong_target_20261112`，partial WSL install 已移至 `/home/petalinux/quarantine_partial_install_20261112`；兩者均非 Git 資產，repo worktree 確認乾淨。
- 驗證界線／未完成：PetaLinux setup 不等於已建立 rootfs、DPU driver/VART/XIR、matching 2024.1 XSA、Docker/Vitis AI compiler、xmodel、SD boot、camera/DMA 或 Wi-Fi peer。installer 只有 non-blocking TFTP warning。未觸碰板子、SD、PL 或相機；現有 2024.2 USB-video artifact 仍不構成 DPU 2024.1 deployment verification。
- Git：已提交為 `a182ced`（`Record PetaLinux WSL host installation`）並成功推送至 `origin/main`；PetaLinux/WSL installers、SDK、quarantine artifacts 均不納入 repository。

## 2026-11-12 — Revalidated DPU build gate from installed WSL PetaLinux host

- 需求／決策：確認 PetaLinux installation 真正解除哪一項 DPU Linux-image blocker，避免把 SDK install 誤稱為完整 DPU deployment。
- 實際完成：在 WSL `bash` source `/home/petalinux/xilinx/petalinux/2024.1/settings.sh` 後，使用 exact generated `arch.json` 執行 tracked preflight。結果確認 `petalinux-create=true`、arch JSON exists、PetaLinux=2024.1；gate 仍 FAIL，但明確只剩 Docker/`vai_c_xir` Vitis AI 3.5 compiler route 與 Vivado hardware=2024.2（需 2024.1）。
- 驗證界線／未完成：沒有建立或燒錄 image、沒有安裝 VART/XIR/driver/xmodel、沒有把 2024.2 XSA 當成相容、沒有接觸板子/SD/相機/Wi-Fi。Docker installer 等待 Windows UAC completion，不以下載或 installer process 視為 Docker available。
- Git：已提交為 `4f301a7`（`Record installed PetaLinux DPU preflight`）並成功推送至 `origin/main`。

## 2026-11-12 — Created matching-family PetaLinux project skeleton

- 需求／決策：在 PetaLinux host 可用後建立 ZynqMP project foundation，但不得把已知 2024.2 XSA 匯入 2024.1 DPU contract，避免產生看似可用但不相容的 deployment image。
- 實際完成：以 sourced PetaLinux 2024.1 Bash environment 成功執行 `petalinux-create project --template zynqMP --name pynq_zu_dpu_2024_1`，新 project 位於外部 WSL path `/home/petalinux/work/pynq_zu_dpu_2024_1`。
- 驗證界線／未完成：尚未 config hardware description、build rootfs、加 DPU/VART/driver、compile xmodel 或寫 SD；無硬體/board/network side effect。此 generated project 不進 Git，仍待 matching Vivado 2024.1 XSA。
- Git：已提交為 `d8ef2b7`（`Record PetaLinux ZynqMP project skeleton`）並成功推送至 `origin/main`。

## 2026-11-12 — Corrected Vitis AI 3.5 toolchain contract

- 需求／決策：重新核對官方版本矩陣，防止以錯誤的 2024.1 host 產生 DPU Linux image。
- 實際完成：官方 Vitis AI 3.5 release、embedded quick-start 與 recipes 均證實相容版本是 Vivado/Vitis/PetaLinux 2023.1。採 test-first 修正 tracked preflight 由 2024.1 改為 2023.1；preflight tests 3/3、person_tracking tests 19/19 PASS。
- 驗證界線／未完成：已安裝 PetaLinux 2024.1、現有 Vivado 2024.2、external 2024.1 project skeleton 都不可當作 Vitis AI 3.5 deployable contract；仍待 matching 2023.1 toolchain/XSA/image/DPU runtime。Docker 已完成 engine verification，但尚未 pull Vitis AI container。
- Git：已提交為 `a078ede`（`Correct Vitis AI 3.5 toolchain contract`）並成功推送至 `origin/main`。
## 2026-11-12 — Corrected DPU IP/toolchain mapping

- 需求／決策：使用者要求自行找出正確工具鏈；以實際已建 DPU B512 產物與 AMD 官方 matrix 為準，不用相近版本猜測。
- 實際完成：讀取 `C:\\pynq_zu_dpu_native_build\\native_dpu_ip\\dpu_ip\\DPUCZDX8G_v4_0_0\\component.xml`，確認 IP=`4.0`。將 build-host preflight 改成明確矩陣：4.0→Vitis AI 2.5→2022.1；4.1→Vitis AI 3.5→2023.1，並新增 `--dpu-ip-version`。test-first 證據：先因舊函式不接受新參數而得到 4 個預期 TypeError，實作後 4/4 PASS。
- 驗證範圍／未完成：尚未取得 2022.1 或 DPU 4.1 source／2023.1，未重新 build hardware、Linux image 或模型。現有 4.0 bitstream、2024.2 Vivado、2024.1 PetaLinux、3.5 compiler Docker 不可宣稱互相可部署。仍未碰板子、SD、相機或 Wi-Fi。
- Git／同步：已提交為 `33add7e`（`Correct DPU IP toolchain contract`）並成功推送至 `origin/main`；外部 IP、bitstream、模型及帳密不進 Git。本行同步結果由下一筆文件提交補上。

## 2026-11-12 — Acquired and verified official DPU 4.0 source bundle

- 需求／決策：在不依賴 AMD account login 的情況下自行取得可驗證的官方 DPU source，釐清目前 bitstream 的真實出處與下一個工具鏈下載目標。
- 實際完成：從 AMD official `download.amd.com/opendownload/xlnx/DPUCZDX8G.tar.gz` 取得 61,086,986-byte bundle（SHA-256 `2888c035f73c907e29de1ae524e2caf4474b05a59ba30aeac3ebe2c818557603`），保存在外部 `C:\pynq_toolchain_sources\DPUCZDX8G_official`。其中 component IP=4.0、changelog=Vitis AI 2.5/Vivado 2022.1；其 component.xml 與既有 native B512 build 的 SHA-256 都是 `70e6c6c4923b872d907d9b007c0308393eda30bbc0a30e515843b630f329fb3d`，確認 byte-identical。另 clone Vitis-AI v3.5 tag `7a0d5a695027b0dc1494c7299918959608c3fab2` 供 version matrix 離線查核。
- 驗證範圍／未完成：source acquisition／hash verification 不是 2022.1 安裝、hardware rebuild、PetaLinux image、VART、xmodel 或 board inference。public 4.0 bundle 沒有可驗證的 DPU 4.1 source；仍不得混用 3.5 container 或 2024.x 工具鏈。
- Git／同步：已提交為 `cde24b6`（`Record official DPU source verification`）並成功推送至 `origin/main`；下載 archive、clone、bitstream、模型及任何帳密均不進 Git。本行同步結果由下一筆文件提交補上。

## 2026-11-12 — Verified Vitis AI 2.5 compiler for the actual DPU 4.0

- 需求／決策：取得並驗證與現有 DPUCZDX8G 4.0／2022.1 contract 同版的模型編譯器，而非繼續以 3.5 compiler 混編。
- 實際完成：下載 official Docker Hub image `xilinx/vitis-ai:2.5.0`，digest `sha256:eaa85efb06924995ebdb973546e7f69169b003b8cc525764bd9524ad554dddbe`。container activate `vitis-ai-pytorch` 後實測 command path `/opt/vitis_ai/conda/envs/vitis-ai-pytorch/bin/vai_c_xir`；conda packages `vaic`、`xcompiler`、`xir`、`vart`、`pytorch_nndct_cpu` 均為 2.5.0。
- 驗證範圍／未完成：只驗證 compiler runtime，沒有 quantize/compile YOLOv8、沒有建立 Linux image、安裝 VART、寫 SD 或碰板子。YOLOv8 並非此 2.5 image 已驗證的現成 output/decode contract；必須等 exact 4.0 target image 與 model integration test 才可聲稱 DPU inference。
- Git／同步：已提交為 `20ec629`（`Record Vitis AI 2.5 compiler verification`）並成功推送至 `origin/main`；27-GB Docker image、source archive、model/bitstream 與帳密均不進 Git。本行同步結果由下一筆文件提交補上。

## 2026-11-12 — Acquired and verified Vitis AI 2.5 target SDK/runtime assets

- 需求／決策：補齊 DPU 4.0/2022.1 正確 target runtime 與交叉編譯資產，但不把它誤裝到現有 2024.1 PYNQ SD image。
- 實際完成：從 Vitis-AI v2.5 官方 source 連結下載 `sdk-2022.1.0.0.sh`（942,561,547 bytes、SHA-256 `e2becdb06564f7f26ac1c61e81201d1ada78e9d7f6bb2aacc0969a0d63ba84e4`）與 `vitis_ai_2022.1-r2.5.0.tar.gz`（7,247,361 bytes、SHA-256 `cc04a31abc147b9936fa2cc15ec3a8348a3dc27ab5a52dbc2239326e31567511`）。在 WSL ext4 解壓 bundle，驗證 `libvart-runner.so -> libvart-runner.so.2`、versioned VART/XIR libraries、`xdputil`，並計得 13 個 versioned VART libraries。
- 驗證範圍／未完成：Windows NTFS staging 不能建立 Linux symlink，故不作 runtime 安裝證據；ext4 解壓才是 bundle completeness check。沒有執行 SDK installer、未建 2022.1 image、未複製 runtime 到板子、未改 SD/PL/UART/network；DPU inference 未完成。
- Git／同步：已提交為 `b1684b1`（`Record DPU 2022.1 runtime assets`）並成功推送至 `origin/main`；SDK/runtime archives、external source clone、Docker images、models、bitstreams 和帳密均不進 Git。本行同步結果由下一筆文件提交補上。

## 2026-11-12 — Verified fixed Vitis AI 3.5 compiler container

- 實際完成：Docker Desktop 4.99.0 已以 `hello-world` pull/run 驗證；固定 tag `xilinx/vitis-ai-pytorch-cpu:ubuntu2004-3.5.0.306` 已拉取。container activate `vitis-ai-pytorch` 後確認 `vai_c_xir`、`vaic`、`xcompiler`、`xir` 均為 3.5.0。
- 驗證界線／未完成：這提供 compiler route，但尚無 matching 2023.1 Vivado/PetaLinux/XSA、target rootfs/VART image 或 compiled xmodel，未碰板子/SD。
## 2026-11-12 — Acquired matching Vivado/Vitis 2022.1 Windows installer

- 需求／決策：取得與現有 DPUCZDX8G 4.0／Vitis AI 2.5 相配的 2022.1 Windows 工具鏈，避免再以現有 2024.2 或最新 2026.1 混建。
- 實際完成：AMD export-address validation 後，實際讀取 `C:\Users\dsic\Downloads\Xilinx_Unified_2022.1_0420_0327_Win64.exe`，大小為 215,919,904 bytes，對應官方列出的 205.92-MB Windows Unified Web Installer。
- 驗證界線／未完成：未啟動或安裝 EXE、未選元件、未改現有 2024.2、未取得/安裝 PetaLinux 2022.1、未重建 DPU/XSA/image/xmodel，且未觸及 SD、板子、相機或 Wi-Fi。installer 是外部 binary，不上傳 Git。
- Git／同步：已提交為 `6d731ea`（`Record Vivado 2022.1 installer acquisition`）並成功推送至 `origin/main`。本同步註記將由下一筆文件提交記錄。

## 2026-11-12 — Rechecked PYNQ transport after user power-cycle

- 需求／決策：使用者表示已重新開機板子；先以唯讀方式確認 SSH/network 是否恢復，不猜測 UART 或登入密碼。
- 實際完成：`192.168.3.1` ping PASS、TCP/22 OPEN；Windows 重新枚舉 USB serial COM4。COM4 以 115200 讀取 4 秒為 0 bytes。
- 驗證界線／未完成：SSH credentials 尚未驗證，UART prompt 未取得；未上傳程式、未載入 overlay、未執行 Vitis ELF、未測 UVC/DMA/DPU/YOLOv8/Wi-Fi。唯一 2022.1 installer 視窗保留但尚未完成安裝。
- Git／同步：已提交為 `4808af3`（`Record PYNQ reboot transport recovery`）並成功推送至 `origin/main`。本同步註記將由下一筆文件提交記錄。

## 2026-11-13 — Verified usable Vivado 2022.1 core after installer final-processing failure

- 需求／決策：使用者指出 Vivado installer 尚停在 76%，因此先區分「下載/安裝器完成」與「主工具是否可執行」，避免在未完成 GUI 安裝時做不實宣稱。
- 實際完成：觀察到 installer 的 `Execution of Pre/Post Installation Tasks Failed` dialog；唯讀執行 Vivado 2022.1 version check 與 Vitis 2022.1 XSCT help，兩者 exit code=0，並確認 Zynq UltraScale+ device data 已落在安裝樹。
- 驗證範圍／未完成：僅證明核心 tools 可啟動，未證明 post-install tasks、完整 device/IP coverage 或 2022.1 DPU/USB-video build 成功；未改板子、SD、USB 相機、Wi-Fi 或 tracked program source。下一步以隔離 build directory 做 real project/IP validation。
- Git／同步：本紀錄與兩份進度文件將隨本次文件提交推送；installer tree 與 logs 為本機工具狀態，不納入 Git。

## 2026-11-13 — Rebuilt and validated the USB-video Block Design in Vivado 2022.1

- 需求／決策：以正確 DPU 4.0/2022.1 toolchain 重做硬體檔，並保持 USB UVC camera 在 PS/Linux、DDR/AXI DMA 到 PL 的真實硬體邊界。
- 實際完成：在 external `C:\pynq_zu_usb_2022_20261113` 建立 project、封裝 custom IP、建立 BD。第一次實跑發現 2022.1 的 ZynqMP PS IP 是 `3.4`、且 auto address order 與 Vitis contract 不同；修正 tracked Tcl 以 selected compatible PS VLNV 及強制 DMA/GPIO/mailbox = `0xA0000000/0xA0010000/0xA0020000`。2022.1 `validate_bd_design` 與 read-only address verifier 都 PASS；Python contract tests 3/3 PASS。
- 驗證範圍／未完成：仍未 synthesize/implement/bitgen/export 2022.1 XSA、建立 2022.1 Vitis application、program board、capture UVC、run DPU/VART/YOLOv8 或 Wi-Fi peer。external build output 不進 Git；PS IP version and address repair source does。
- Git／同步：本項 source、tests 和三份進度紀錄將隨本次提交推送至 `main`。

## 2026-11-13 — Built the 2022.1 USB-video bitstream and Vitis XSA

- 需求／決策：以已驗證的 2022.1 Block Design 建立可交給 matching Vitis 2022.1 的硬體 handoff，不把 BD-only success 當成 FPGA deliverable。
- 實際完成：external build 的 top synthesis、implementation、bitgen 和 fixed include-bit XSA export 全部成功。bitstream=7,797,821 bytes，XSA=1,612,457 bytes；archive verification PASS，control addresses 為 DMA/frame GPIO/mailbox=`A0000000/A0010000/A0020000`。
- 驗證範圍／未完成：routing 15,930/15,930、routing errors=0；final WNS/WHS=`+0.034/+0.011 ns` and timing constraints met。Routed DRC 有 3 warnings、0 errors（DMA BRAM NO_CHANGE advisory、SmartConnect internal no-load advisory）。此結果沒有下載到 board、沒有 Linux UVC/CMA/DMA、DPU/VART/YOLOv8 或 Wi-Fi peer 驗證；generated artifacts/logs 是 external state，不進 Git。
- Git／同步：本結果的三份進度文件將隨本次提交推送；hardware source compatibility repair 已在前一提交 `7c65322` 推送。

## 2026-11-13 — Compiled the 2022.1 A53 USB-video control ELF

- 需求／決策：以 Vivado 2022.1 已輸出的 exact XSA 產生 matching Vitis A53 control build，避免把 Vitis 2024.2 Python client 用於 2022.1 handoff。
- 實際完成：新增 tracked `vitis/pynq_zu_usb_video/build_vitis_2022.tcl` 與 README version guard；external 2022.1 XSCT platform 產生 `standalone_domain` BSP。handoff verifier 對 XSA 與 generated `xparameters.h` PASS，DMA/frame GPIO/mailbox 分別為 `A0000000/A0010000/A0020000`。用 Vitis 2022.1 `aarch64-none-elf-gcc`、該 BSP 的 `libxil.a` 和 generated linker script 實際輸出 203,736-byte ELF64/AArch64 control ELF。
- 驗證範圍／未完成：第二次以新增 `finish_vitis_2022_app.tcl` 重新 import project 時，已實際寫入 tracked C/H sources，但 XSCT/Eclipse 在 build request 前報 `xsct server communication channel has closed unexpectedly`/`Connection reset`；僅關閉這次 isolate workspace 的 processes，未改 installer、board、SD、USB/UART 或網路。因此 tracked Tcl 尚未在此主機端 full completion verified。manual ELF compilation 與 address contract 不代表 JTAG/Linux execution、PL programming、UVC dual capture、DPU/VART/YOLOv8 或 Wi-Fi peer。
- Git／同步：本次 source/README/三份 progress documents 將提交並推送到 `main`；external XSA/workspace/BSP/ELF/logs 不入 Git。

## 2026-11-13 — Rebuilt the native DPUCZDX8G 4.0 B512 Block Design in Vivado 2022.1

- 需求／決策：將 exact DPU 4.0/Vitis AI 2.5/2022.1 route 從先前 2024.2 build 移至 matching Vivado 2022.1，並維持 USB UVC 在 PS/Linux 而不是虛構 PL camera pins。
- 實際完成：新增 DPU BD contract tests，先證明 2022.1 scripts 缺少 PS 3.4 fallback 與 PYNQ-ZU board repo setup，再實作它們。tests 3/3 PASS。external `C:\pynq_zu_dpu_2022_20261113` real Vivado run 讀入 official DPUCZDX8G 4.0 source，選擇 `zynq_ultra_ps_e:3.4`，完成 BD validate/save；read-only reopen 讀到 DPU native pins，control segment=`0x0400000000` (16 MiB)，data0/data1/instruction 接 HP0/HP1/HP2。
- 驗證範圍／未完成：這不是 DPU synthesis/bitstream/XSA，更不是 PetaLinux 2022.1 image、device tree/driver/VART、xmodel/YOLOv8、board camera/DMA 或 Wi-Fi peer。沒有改 board/SD/UART/network。official source and generated build are external/non-Git.
- Git／同步：本次 scripts/tests/三份 progress documents 將提交並推送到 `main`。

## 2026-11-13 — Completed DPU 4.0 B512 implementation and XSA handoff in Vivado 2022.1

- 需求／決策：將已驗證的 native DPU 4.0 B512 Block Design 完成至可交接給 matching Linux/Vitis flow 的 implementation、bitstream 與 XSA，且不把 generated binaries 寫入 repository。
- 實際完成：external `C:\pynq_zu_dpu_2022_20261113` 的 synthesis、implementation、bitgen 和 fixed include-bit XSA export 都成功。bitstream 為 7,797,815 bytes，XSA 為 2,628,256 bytes；archive check 確認包含 bitstream、HWH、`sysdef.xml`、`xsa.json`。final routed timing 的 setup/hold/pulse-width 均為 0 failing endpoints（worst slack 分別 +5.017/+0.011/+3.500 ns），final bitgen DRC=0 errors/0 critical warnings；98 項是 DPU/DSP pipelining advisories。
- 驗證界線／未完成：這只證明 2022.1 FPGA hardware handoff。尚未建立 matching 2022.1 PetaLinux image、device tree/DPU driver/VART/XIR、xmodel 或板上 bitstream/SD/UVC/DMA/YOLOv8/Wi-Fi 實測。official source、generated bit/XSA/reports/logs 留在 external paths、不入 Git。
- Git：本筆與兩份進度文件將隨文件提交推送至 `main`。

## 2026-11-13 — Prepared the exact 2022.1 PetaLinux DPU 4.0 integration path

- 需求／決策：在尚未取得 PetaLinux 2022.1 installer 前，先把 official DPU 4.0 PetaLinux reference 轉為可重跑、拒絕錯版工具鏈的 external-project staging flow；不能用現有 PetaLinux 2024.1 假裝完成 Linux image。
- 實際完成：新增 `prepare_dpu_4_0_petalinux_project.py` 和 tests。工具驗證 official 4.0 kernel patch、`CONFIG_XILINX_DPU=y` 及 VART/XIR/unilog/target-factory/vitis-ai-library recipes，將它們合併進 external project 並保留既有 rootfs entries。對 actual official DPUCZDX8G reference 的 temporary external project stage PASS；tests 3/3 PASS。實跑先揭露 official patch filename 本身是 `compatibale`，且 bbappend 也引用這個拼字；工具現在從 bbappend 解析 patch filename，避免 staging 後 recipe reference 斷裂。
- 版本更正：Vivado/Vitis 實際已安裝於 `C:\Xilinx\Vivado\2022.1`，DPU B512 XSA 也是這套 2022.1 產生；舊 README 的 2024.2 host 描述已更正。仍只有 PetaLinux 2024.1 安裝，helper/README 明確拒絕其用於 DPU 4.0/2.5 route。
- 驗證界線／未完成：尚無 PetaLinux 2022.1 installer/project/image、未 import XSA、未編譯 device tree/rootfs、未寫 SD、未載入 DPU driver/VART、未 compiled xmodel、未做板端 inference、UVC DMA 或兩板 Wi-Fi。official source、temporary staged project、bitstream/XSA 和帳密不入 Git。
- Git：本項 source/tests/docs 將隨本次提交推送至 `main`。

## 2026-11-13 — Quantized and compiled YOLOv8n for the generated B512 DPU

- 需求／決策：使用 YOLOv8（不偷換成 YOLOX）建立 real Vitis AI 2.5 → native DPUCZDX8G 4.0 B512 artifact，並如實保留 compiled graph execution boundary。
- 實際完成：新增 C2f static-slice quantization helper and tests；Vitis AI 2.5 calibration/test produced `DetectionModel_int.xmodel` (12,943,875 bytes) with three raw heads. `vai_c_xir` compiled it against exact generated B512 `arch.json`, outputting external `yolov8n_b512.xmodel` (5,513,997 bytes) and MD5 `5921d60a43728ed9f40be0e433bdf0e9`.
- 驗證範圍／未完成：compiler reports 121 device subgraphs and 60 DPU subgraphs because SiLU is retained as a float op. Therefore this proves quantization/compiler compatibility but not one-runner VART inference, person boxes, DPU-only performance, board execution, PetaLinux image, camera capture, or Wi-Fi peer. External models/logs/weights are not in Git.
- Git／同步：依使用者要求，這個 progress chunk 暫留本機工作樹，尚未 commit/push；將在後續較大整合段落一起同步。

## 2026-11-13 — Verified the B512-compatible YOLOv8 activation route

- 實際完成：新增 and tested LeakyReLU activation option. Vitis AI 2.5 calibration/test plus `vai_c_xir` compiled the activation probe to B512, reducing compiler partitioning from 121/60 device/DPU subgraphs to 29/9.
- 驗證界線：probe reused SiLU-trained weights after activation replacement, so it proves toolchain/hardware compatibility only, not detection accuracy. Hardswish was tested and rejected because the Vitis AI 2.5 quantizer's own module has two reproducible graph bugs. No commit/push yet per user instruction.

## 2026-11-13 — Chose the upstream YOLOv8n model as the deployment baseline

- 決策：依使用者要求，project uses the pretrained upstream Ultralytics YOLOv8n model directly; no custom LeakyReLU retraining is part of the deliverable. The existing original-SiLU compiled B512 xmodel plus Vitis AI GraphRunner is the selected DPU deployment route. LeakyReLU remains documented only as an untrained hardware-partitioning experiment.
- 驗證界線：the compiled model still awaits matching PetaLinux 2022.1 / GraphRunner target runtime; no model accuracy or on-board inference claim is made.

## 2026-11-13 — Added tested raw YOLOv8 DFL output decoding

- 實際完成：`raw_yolov8_dfl_decoder` accepts the exact three raw heads seen during Vitis AI quantization, derives DFL boxes and returns the existing tracker-compatible person detection schema. A hand-checkable DFL bin fixture verifies the box, class and confidence; full project suite passes 29 tests.
- 驗證界線：this is decoder correctness only. It requires a future Vitis AI 2.5 GraphRunner runtime on a matching PetaLinux image to feed real heterogeneous graph outputs; no target/board inference claimed. Changes remain local/unpushed per user instruction.

## 2026-11-13 — Enabled the Python GraphRunner dependency in staged PetaLinux recipes

- 實際完成：the DPU 4.0 staging helper now writes the Vitis AI Library bbappend needed to enable its Python binding; behavioral Linux staging tests are 13/13 PASS.
- 驗證界線：this only prepares an external PetaLinux 2022.1 project. PetaLinux 2022.1 is still unavailable locally, so no rootfs/image/package installation or target GraphRunner import has been verified. Changes remain local/unpushed per user instruction.

## 2026-11-13 — Strengthened the target DPU runtime gate and rechecked the board

- 實際完成：runtime gate now requires Python `vitis_ai_library.GraphRunner`, and Linux tests are 14/14 PASS. Read-only SSH inspection of the current PYNQ board found four UVC video nodes but no DPU node or VART/XIR/GraphRunner Python modules.
- 驗證界線：this is negative runtime evidence for the present PYNQ 2024.1 SD image, not a PetaLinux 2022.1 target deployment. Changes remain local/unpushed pending the next larger batch.

## 2026-11-13 — Implemented the upstream YOLOv8 GraphRunner-to-DPU bridge

- 需求／決策：使用者澄清 DPU 應是接上既有 YOLOv8 的橋樑，而不是把 YOLOv8 重做為 Verilog 或換成自行訓練模型。維持 official pretrained Ultralytics YOLOv8n 與已產生的 B512 xmodel 為唯一部署基線。
- 實際完成：新增 `GraphRunnerYoloV8`，以 Vitis AI Python GraphRunner 的 complete XIR graph/TensorBuffer API 執行 upstream SiLU YOLOv8 的 CPU+DPU partitions；實作 input/output synchronization、INT8 camera pre-process、fixed-point output conversion，並在 selected `yolov8_vart` backend 綁定 raw DFL decoder。更新 README 以區分 whole-graph GraphRunner 和 legacy single-DPU VART runner。新增 fake TensorBuffer test；bridge/unit suite 10/10 PASS。
- 驗證範圍和未完成：僅 host-side contract tests；目前 PYNQ 2024.1 SD 沒有 DPU/VART/XIR/GraphRunner，未執行 target GraphRunner、真實人像辨識、兩鏡頭或 Wi-Fi。仍需 matching Linux image/SD 後做完整 camera→DPU→YOLOv8 verification。
- Git／同步：本項 source、tests 和三份進度文件待本次完整 regression 後一併提交與推送至 `main`；外部 `.pt`/`.xmodel`/build logs 不納入 Git。

## 2026-11-13 — Connected GraphRunner YOLOv8 detections to the existing tracker

- 需求／決策：讓 DPU bridge 的既有 YOLOv8 output 能直接供 project tracker、RTL feature 與 peer protocol 使用，而非另創模型或格式。
- 實際完成：修正 `Detector.detect()` 將 `yolov8_vart` dictionary output 與 CPU `yolov8` 共用既有 box filtering/HSV histogram contract；新增 injected GraphRunner-row regression。relevant adapter/backend tests 11/11 PASS。
- 驗證範圍／未完成：host-only format contract; no target DPU/VART/GraphRunner, camera, second board or Wi-Fi test.
- Git／同步：本次修正與三份進度文件待完整 regression 後提交並推送至 `main`；無外部模型或私密資料加入 Git。

## 2026-11-13 — Verified the current one-board/two-C270 topology cannot stream concurrently

- 需求／決策：在等候 matching DPU Linux image 時，實機驗證原需求的單板雙 USB camera path，而不是由各自可開啟的結果推定可同時使用。
- 實際完成：SSH on the live PYNQ-ZU verified `video0` and `video2` individually deliver MJPEG frames. Concurrent two-thread tests failed at both 320×240/15 FPS (one side 60 frames, the other 0) and 160×120/10 FPS (40/0); which side succeeded changed between tests. Added `pynq_usb_camera_preflight.py --simultaneous`, whose actual 20-frame board run correctly failed 20/0 and whose temporary board copy was removed. Added two fake-device regression tests for pass/fail contracts.
- 驗證範圍／未完成：proves this tested shared USB topology is unsuitable for live two-camera capture, not that all possible hardware wiring fails. No PL/DPU/SD/Wi-Fi settings were changed; use one camera per board or an independent USB controller and re-run the gate.
- Git／同步：source/tests/docs are pending full regression then push; no images, board secrets or external build artifacts are added.

## 2026-11-13 — Initialized and verified PYNQ-ZU Wi-Fi radio capability

- 需求／決策：為兩板一鏡頭的 Linux peer path 驗證實際 Wi-Fi hardware/driver state，不任意加入未知網路。
- 實際完成：initial `wlan0` was DOWN/all-zero MAC with no NetworkManager or saved profiles. Authorized `ip link set wlan0 up` initialized WILC SDIO to UP/LOWER_UP with a valid MAC and IPv6 link-local address. One `iw dev wlan0 scan` succeeded and returned 11 BSS records; SSID/BSSID data was intentionally not retained. No SSID association, DHCP request, credential write, source change, SD change or second-board connection was performed.
- 驗證範圍／未完成：this proves Wi-Fi radio scan capability only. Two-board exchange still requires an authorized chosen SSID/passphrase, a second board, IPv4 association on both sides and the existing TCP peer preflight.
- Git／同步：three progress records are being committed/pushed; no credentials, SSIDs, MAC addresses or private network data enter Git.

## 2026-11-13 — Checked JTAG readiness without programming the board

- 需求／決策：在相容 Linux image 尚未取得時，先驗證已建立的 Vivado 2022.1 hardware artifacts and Vitis control ELF 能否安全進入 JTAG bring-up；target enumeration must pass before any download.
- 實際完成：confirmed external bitstreams/XSA and manual A53 ELF exist; started 2022.1 `hw_server`, connected XSCT localhost, and queried targets. Windows sees healthy FTDI dual-channel USB cable and COM5 UART, but XSCT reports no JTAG target. No bitstream/ELF download, reset, boot change, cable-driver mutation, SD write or board configuration change was performed.
- 驗證範圍／未完成：host-side FTDI enumeration is not scan-chain proof. Repeat after physical JTAG chain/power/boot-selection check; only a listed target authorizes programming/hardware validation.
- Git／同步：three progress documents are being committed/pushed; external artifacts and any board identifiers are excluded.

## 2026-11-13 — Identified the PYNQ-ZU JTAG boot-selection prerequisite

- 需求／決策：resolve empty JTAG target using board-specific primary documentation before mutating USB drivers or programming hardware.
- 實際完成：official PYNQ-ZU Reference User Manual v1.2 confirms JTAG/SD DIP selects boot mode; JTAG is left and MicroSD is right. Current project work deliberately uses SD boot for SSH/PYNQ Linux, making boot selection the first physical prerequisite for a JTAG-target recheck.
- 驗證範圍／未完成：documentation evidence only; no physical switch/power cycle was performed. JTAG target visibility after switching remains unverified, and SD mode remains required for current Linux workflow.
- Git／同步：three progress records are being committed/pushed; no private board, account or network data is recorded.

## 2026-11-13 — Installed and verified the matching PetaLinux 2022.1 host tools

- 需求／決策：為已完成的 Vivado/Vitis 2022.1 DPU 4.0 B512 handoff 補上相同 release 的 PetaLinux host tool，避免將 2022.1 hardware 交給既有的 2024.1 toolchain。
- 實際完成：從 AMD Download Center 取得 timestamped 2022.1 installer，於 WSL Ubuntu 的非 root development account 安裝 aarch64 sources 到獨立 2022.1 directory；補上 installer 明確要求的 `zlib1g:i386` prerequisite。`settings.sh` and `petalinux-create --help` verified successfully; existing 2024.1 installation remains separate.
- 驗證範圍／未完成：host-install only. No PetaLinux project/XSA import, DPU recipe staging, image build, SD write, target boot, DPU driver/VART/GraphRunner, camera or YOLO inference has been claimed. AMD installer, hashes, logs and WSL tool files are intentionally not tracked.
- Git／同步：本筆與三份 progress documents will be committed and pushed to `main`; no account, address, credential, network identifier, installer or generated image is included.

## 2026-11-13 — Verified JTAG scan chain and programmed the DPU B512 bitstream

- 需求／決策：使用者將 PYNQ-ZU 切至 JTAG boot，繼續 Vivado/Vitis hardware bring-up；programming is permitted only after a real target scan.
- 實際完成：Vivado 2022.1 Hardware Manager found the FTDI target, `xczu5_0`, and `arm_dap_1`. It programmed the existing DPU B512 bitstream and reported `End of startup status: HIGH`. The bitstream contains no supported debug core, so no debug waveform was expected or claimed.
- 驗證範圍／未完成：this proves volatile FPGA configuration download only. It did not write SD/QSPI nor prove PS software, DPU device node/driver, VART/XIR/GraphRunner, YOLOv8, UVC cameras, tracking or Wi-Fi. The USB-video ELF is intentionally not run because it does not match this DPU address map.
- Git／同步：this hardware verification and progress docs will be committed/pushed; external bitstream, XSA, tool logs and hardware identifiers are excluded.

## 2026-11-13 — Built the Vitis 2022.1 platform and corrected the PetaLinux DPU-runtime image composition

- 需求／決策：在使用者不在電腦前時持續可自動執行的工作；保留需要使用者實體確認的 SD 寫入、SD boot 與後續 Wi-Fi/第二板測試為待辦。
- 實際完成：實跑 Vitis 2022.1 XSCT，從同一份 DPU B512 XSA 產生 external XPFM platform。External PetaLinux project 的 first minimal build completed 4,345 tasks，device tree 也確認含 exact DPU 4.0 node。發現 first image 不會因 `user-rootfsconfig` 的 package declaration 自動帶入 VART/XIR；新增 tested staging logic，以 image bbappend 的 `IMAGE_INSTALL:append` 強制帶入 VART、XIR、unilog、target-factory、vitis-ai-library，並將過去錯誤的 `=y` declaration 正規化。rootfs silentconfig 與 staging tests 3/3 PASS。
- 驗證範圍和未完成：新的 runtime image rebuild 已在 external WSL background job 啟動，尚未完成時不宣稱 VART/GraphRunner package 或 board import 成功。尚未寫入 SD、切 SD boot、boot target、run `/dev/dpu`、camera→YOLOv8，亦未設定 Wi-Fi credentials 或測第二板。
- Git／同步：程式、tests 和三份進度文件將在 runtime rebuild 結束並完成 regression 後一併提交並推送 `main`。`petalinux_installation_log` 是本機暫存安裝記錄，刻意不納入 Git；外部 XSA/XPFM/image/bitstream/logs 也不追蹤。

## 2026-11-13 — Built and verified the DPU runtime SD image

- 需求／決策：完成不需使用者實體操作的 DPU Linux artifact，SD 卡寫入與 SD boot 仍保留為人工確認步驟。
- 實際完成：PetaLinux 2022.1 runtime build completed 6,355 tasks with all succeeded. Rootfs inspection confirms VART, XIR, `xdputil` and Vitis AI Library. Device tree contains DPU 4.0 and the actual kernel build config contains built-in `CONFIG_XILINX_DPU=y`. `BOOT.BIN` and `petalinux-sdimage.wic` were generated externally; the 6.1 GiB WIC image was read-only checked for a FAT32 boot partition, ext4 rootfs partition, and the required boot files (`BOOT.BIN`, `image.ub`, `boot.scr`).
- 補充驗證：rootfs contains ARM64 Python 3.9 `vitis_ai_library.so`, `vart.so`, and `xir.so`; the GraphRunner binding binary contains `GraphRunner` and `create_graph_runner` symbols. This is still image-content evidence, not a board-side import.
- 驗證範圍／未完成：this proves artifact composition, not physical SD writing, target boot, `/dev/dpu`, VART/XIR/GraphRunner target imports, camera-to-YOLOv8 inference or two-board Wi-Fi. The existing PYNQ 2024.1 card remains unchanged. External WIC/rootfs/build logs are intentionally not committed.
- Git／同步：本次三份 progress documents will be committed and pushed to `main`; only the local `petalinux_installation_log` remains untracked because it is a temporary installation log.

## 2026-11-13 — Added the Python camera runtime to the DPU SD image

- 需求／決策：the tracked GraphRunner camera pipeline imports NumPy and OpenCV, so a DPU-only VART runtime is insufficient for the actual project.
- 實際完成：test-first update to the staging helper appends `python3-numpy` and `python3-opencv` to the generated image bbappend. The newly written contract failed on the prior output, then passed after the minimal implementation; Linux suite passed 14/14. The external 2022.1 project was restaged from the exact official DPU 4.0 source and rebuilt successfully (6,355 tasks, all succeeded). Rootfs inspection confirms ARM64 NumPy and Python OpenCV, then BOOT.BIN/WIC were regenerated and WIC boot files were read-only verified.
- 驗證範圍／未完成：image package contents only. No physical SD write, SD boot, target Python imports, `/dev/dpu`, UVC capture or YOLOv8 inference occurred. Generated WIC/rootfs remain external.
- Git／同步：helper, test, Linux README and the three progress documents will be committed and pushed to `main`; local `petalinux_installation_log` remains intentionally untracked.

## 2026-11-13 — Staged USB/UVC camera support for the DPU Linux kernel

- 需求／決策：the new image must support the requested USB C270 camera path, not only DPU runtime and Python packages.
- 實際完成：rootfs/kernel audit revealed no UVC/V4L2 config in the prior image. A test-first staging change adds built-in PS USB host/DWC3, media/V4L2 and UVC configuration. The test correctly failed before implementation, then Linux suite passed 14/14. The external generated kernel config confirms all required core symbols are enabled; a full kernel/image rebuild has started.
- 驗證範圍／未完成：rebuild remains live at this record; no new WIC, physical SD write, target boot or camera frame capture is claimed. The result will be separately verified after the live build terminates.
- Git／同步：helper/test/README/progress changes will be committed and pushed to `main`; external build logs and artifacts remain untracked.

## 2026-11-13 — Corrected the DWC3 mode after the USB-camera kernel build failed

- 需求／決策：make the USB UVC configuration buildable instead of retaining an image setting that fails at kernel link.
- 實際完成：the first UVC rebuild failed at Linux `do_compile`: host-only DWC3 configuration omitted `gadget_hibernation.o`, while Xilinx DWC3 `core.o` references `dwc3_gadget_exit_hibernation`. Kernel source/Kconfig inspection verified `USB_GADGET=y` and `EXTCON=y` are already available. Test-first replacement of `CONFIG_USB_DWC3_HOST=y` with `CONFIG_USB_DWC3_DUAL_ROLE=y` failed under old staging output, then full Linux tests passed 14/14 after implementation. The corrected external PetaLinux build has started.
- 驗證範圍／未完成：the corrected build is live; no successful UVC image, SD write, target boot or camera frame capture is claimed yet. Failed build logs and later artifacts remain external.
- Git／同步：source/test/README and progress documentation will be committed and pushed to `main`; no generated images or logs are tracked.

## 2026-11-13 — Rebuilt and verified the final UVC-capable DPU SD image

- 需求／決策：完成可自動執行的 PetaLinux work, while retaining physical SD selection/writing and boot as explicit manual gates.
- 實際完成：corrected dual-role DWC3 build completed 6,355/6,355 tasks successfully. Actual kernel config confirms built-in Xilinx DWC3 dual-role, V4L2 and UVC symbols. `petalinux-package --boot` and `--wic` produced external `BOOT.BIN` and a 6.1 GiB WIC; read-only partition inspection verified FAT32 boot plus ext4 rootfs and the boot files. Final package manifest includes VART, XIR, Vitis AI Library, NumPy and Python OpenCV.
- 驗證範圍／未完成：image composition only; no physical SD write, SD boot, target DPU device, GraphRunner import, UVC frame, YOLOv8 inference, two-camera concurrency or Wi-Fi peer is claimed. External artifacts/logs remain outside Git; `petalinux_installation_log` remains intentionally untracked.
- Git／同步：the staging helper/test/README and all three progress records are to be committed and pushed to `origin/main` in this change.

## 2026-11-13 — Put the compiled original YOLOv8 model into the DPU SD image

- 需求／決策：the target image must contain the exact B512 `.xmodel` used by GraphRunner, rather than relying on an untracked Windows path or switching to a CPU ONNX model.
- 實際完成：test-first staging now accepts a validated `--xmodel`, packages it at `/opt/models/yolov8n_b512.xmodel`, and records its hash externally. The actual 5,513,997-byte model was staged and its extracted rootfs SHA-256 matches the compiler output. PetaLinux build completed 6,370/6,370 tasks, then BOOT/WIC were regenerated. Added explicit DPU deployment mode, DPU-aware preflight, and one-camera UVC→GraphRunner camera gate. Linux tests 16/16, tracking/DPU bridge tests 34/34, and bundle tests 5/5 passed; PowerShell and Bash parsing passed.
- 驗證範圍／未完成：no physical SD write, target boot, device node, GraphRunner import, UVC frame, positive person detection, same-board two-camera capture or Wi-Fi peer is claimed. The external model/image/logs are excluded from Git; `petalinux_installation_log` remains intentionally untracked.
- Git／同步：all code, tests, README and progress files for this deliverable are to be committed and pushed to `origin/main` together.

## 2026-11-13 — Exported the verified DPU/YOLOv8/UVC WIC for controlled SD writing

- 需求／決策：make the final image accessible to Windows without guessing or overwriting a physical SD target.
- 實際完成：copied the verified 6,442,455,040-byte WIC to `C:\pynq_zu_dpu_2022_20261113\sd_image_20261113\pynq_zu_dpu_yolov8_usb_2022_1.wic`; copy-side SHA-256 exactly matches the source image (`a4acc61f63febb28ab343f38c53b84ef7167e941888015c54d7a27ec0c7b914e`). Read-only disk inventory found only fixed 2 TB and 512 GB disks.
- 驗證範圍／未完成：no removable SD is present; no disk selection, formatting, write, SD boot, board runtime or camera/DPU inference occurred. The file is an external generated artifact and is not committed to Git.
- Git／同步：progress records for this export are to be committed and pushed to `origin/main`; `petalinux_installation_log` remains intentionally untracked.

## 2026-11-13 — Prepared first-stage single-camera DPU person tracking

- 需求／決策：the first hardware milestone is now one PYNQ-ZU and one UVC camera; two boards with one camera each and Wi-Fi exchange remain the later topology.
- 實際完成：the target GraphRunner camera gate now passes each YOLOv8 detection list through the existing Tracker and reports unique track IDs. Test-first fake-camera regression covers frame execution, association and capture failure; the full person-tracking suite passed 34/34.
- 驗證範圍／未完成：no WIC write or target boot has occurred, so this remains target-code/host-test evidence, not DPU inference, person tracking or camera hardware proof. The external WIC and model remain untracked.
- Git／同步：program, test, README and all progress records are to be committed and pushed to `origin/main` together.

## 2026-11-13 — Built a self-contained single-camera DPU tracker SD image

- 需求／決策：after SD boot, first-stage DPU tracking must not depend on copying project sources over SSH.
- 實際完成：added a validated rootfs package containing the minimal GraphRunner/tracker Python files and rebuilt PetaLinux successfully (6,385/6,385 tasks). Rootfs archive confirms runtime source files plus the exact B512 xmodel. Repackaged and exported the new WIC as `pynq_zu_dpu_single_camera_tracker_2022_1.wic`, SHA-256 `013f29c2f3feb8c0cf26b2f7f3987557905899d44b2157713cb0c9ae8e5791d6`. A first attempt exposed a missing license metadata QA error; fixed it with `CLOSED` rather than mislabelling project source licensing.
- 驗證範圍／未完成：all proof is build/rootfs content only. No SD write, target boot, DPU/GraphRunner import, camera frame, person detection or tracker result occurred. Earlier WIC exports are deliberately superseded for the current first-stage goal.
- Git／同步：helper/test/README and progress records are to be committed and pushed to `origin/main`; external image/model/logs and `petalinux_installation_log` remain untracked.

