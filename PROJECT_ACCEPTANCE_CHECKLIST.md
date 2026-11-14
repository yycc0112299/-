# 專題驗收與進度核對表

> 最後更新：2026-11-14。此表是目前專題的單一進度來源；`PASS` 必須有實際證據，
> `READY` 代表程式/產物已備妥但尚未實機驗證，`BLOCKED` 代表需要硬體或使用者提供的條件。

| 階段 | 項目 | 狀態 | 目前證據／下一個驗收條件 |
|---|---|---|---|
| 硬體架構 | USB 鏡頭介面責任劃分 | PASS（設計） | USB UVC 走 Zynq PS MIO/USB，非 PL/MIPI 腳位；介面地圖已納入 `fpga/PYNQ_ZU_DPU_USB_CAMERA_INTERFACE.md`。 |
| Vivado | PYNQ-ZU DPU B512 Block Design | PASS（建置／JTAG） | PS、AXI、DDR HP ports、clock/reset、IRQ 已建置；JTAG 實測 bitstream startup 成功。 |
| Vitis | 2022.1 XSA → XPFM handoff | PASS | 同一份 DPU XSA 已產生 Vitis 2022.1 platform；Linux DPU 推論不需額外 bare-metal inference ELF。 |
| PetaLinux | 2022.1 DPU Linux、VART/XIR、模型與 UVC | READY | final WIC 含 DPU runtime、模型、追蹤程式、Python modules、fusion runtime 與 board acceptance gate；rootfs pre-flash gate PASS。 |
| 下一版 PetaLinux | 兩板 fusion runtime source staging | PASS（映像內容） | final 6,385-task rebuild PASS；WIC 已匯出並以 SHA-256 核對，尚未寫入 SD。 |
| SD | 修正版映像寫入 SD | BLOCKED | 需把 SD 卡插回這台電腦；寫入工具已鎖定 fusion WIC 與 SHA-256。 |
| 單板 Linux | SD 開機與 UART 登入 | PASS（舊映像） | 已從 SD 開到 `pynqzudpu20221` UART login；修正版仍待寫卡。 |
| 單板 Linux | final rootfs AArch64 Python imports | PASS（QEMU） | QEMU 實跑 final rootfs：NumPy、OpenCV、VART、XIR 與部署程式 imports PASS；不含 `/dev/dpu`／相機證明。 |
| 單板 DPU | NumPy/OpenCV/VART/XIR/GraphRunner 實際 import | BLOCKED | 修正版 SD 開機後跑 `verify_dpu_runtime.py`；舊映像因缺 Python `json` 未通過。 |
| 單板鏡頭 | UVC/V4L2 讀取一支 USB 鏡頭 | BLOCKED | 修正版 SD 開機且接上鏡頭後確認 `/dev/video*`、讀取影格。 |
| 單板 YOLOv8 | GraphRunner → DPU → YOLOv8 人物偵測＋Tracker | BLOCKED | 修正版 SD 開機後執行 `pynq_yolov8_dpu_inference.py --frames 3`。 |
| 兩板程式 | TCP metadata protocol／Wi-Fi preflight／重試 | PASS（主機測試） | 封包、預檢與重試測試通過；未宣稱實體 Wi-Fi 已完成。 |
| 兩板程式 | DPU-only deployment bundle | PASS（主機測試） | bundle 內含 DPU sender、GraphRunner、Wi-Fi/TCP，且不含 CPU ONNX。 |
| 跨鏡頭程式 | 外觀特徵封包與保守候選關聯 | PASS（主機／封裝測試） | 2×15 特徵、confirmed gate、TCP 接收、候選服務、rootfs staging／DPU bundle tests 都通過；待新 WIC／實機。 |
| 兩板模擬 | 兩個獨立 fusion process 的雙向 TCP 候選關聯 | PASS（loopback） | `simulate_two_pynq_cross_camera.py` 會啟動兩個 listener、雙向送出多次 confirmed metadata，兩端皆產生 `confirmed_candidate`；非 Wi-Fi、相機、DPU 或身份辨識證明。 |
| 兩板實機 | 各一支鏡頭、Wi-Fi 雙向資料交換 | BLOCKED | 需要第二塊板、各自鏡頭、授權 Wi-Fi 與實際 IP。 |
| 兩板實機 | 跨鏡頭人物候選追蹤 | BLOCKED | 前一列完成後，用跨鏡頭候選服務驗收；不會把衣物外觀候選稱為身份辨識。 |

## 下次有 SD 卡時的固定驗收順序

1. 寫入修正版 WIC，確認 writer 的 SHA-256 gate 通過。
2. SD mode 開機，UART 登入並跑 DPU/Python runtime gate。
3. 接一支 USB 鏡頭，驗證 UVC/V4L2。
4. 跑單板 GraphRunner/DPU YOLOv8 三影格與 tracker gate。
5. 單板通過後，再進入第二塊板與 Wi-Fi 雙向 metadata 驗證。
