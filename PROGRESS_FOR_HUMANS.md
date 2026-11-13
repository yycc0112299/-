# 專題進度（重點版）

## 2026-11-13：YOLOv8 的 DPU 轉換路線已核對

- 本機已有正確的 Vitis AI 2.5 Docker 環境，裡面有 DPU 編譯器與 PyTorch quantizer。
- 編譯器需要先有量化後的 `.xmodel`；目前只有 CPU 用的 YOLOv8 ONNX 檔，不能直接編譯成 DPU 模型。
- 所以現在不能宣稱 YOLOv8 已在 DPU 上運作；下一步是以相容的 YOLOv8 PyTorch 模型量化、編譯，再依實際輸出接上人物框 decoder。

## 2026-11-13：板端 Wi‑Fi 目前尚不可作為兩板互傳通道

- `wlan0` 介面存在但未連線，顯示 `ESSID:off/any`、`Not-Associated`，MAC 為全 0。
- 板上沒有 `nmcli` 或 `rfkill`，沒有可讀取的已設定 Wi‑Fi 連線資訊。
- 因此目前可用的板端網路仍是 USB gadget `usb0`；雙板 Wi‑Fi 必須等待真正可用的 WLAN 硬體／驅動與網路設定後再實測。

## 2026-11-12：overlay 載入後兩支相機仍可逐支擷取

- 在 USB-video overlay control-plane 驗證通過後，再以 OpenCV 依序讀取 `/dev/video0`、`/dev/video2`，皆成功得到 `640×480×3`。
- 這證明本次 PL overlay 下載沒有干擾 PS USB 相機的 sequential capture；不代表畫面已經走 DMA 或 FPGA 影像資料路徑。

## 2026-11-12：USB-video overlay 的板端控制介面已實測通過

- 板端終端實測 `PYNQ_ZU_USB_VIDEO_OVERLAY_PASS frame_id=0x5a17c0de initial_control=0x00000000`。
- 這確認下載到 FPGA 的 USB-video Block Design 可由 PYNQ 存取 frame-ID GPIO 與 mailbox frame-ID 暫存器，且起始 DMA control 為 0。
- verifier 不會寫 DMA CONTROL、不會啟動 DMA 或相機串流；因此仍未完成影像經 DMA、DPU／YOLOv8 或雙板 Wi‑Fi 實測。

## 2026-11-12：USB-video 硬體檔已由 PYNQ Linux 成功下載至 FPGA

- 完成 `render` 群組設定後，XRT 已能辨識 Pynq-ZU device；使用 sudo 執行 overlay verifier 時，kernel 記錄 `writing pynq_zu_usb_video.bin to Xilinx ZynqMP FPGA Manager`，並有 XRT xclbin 成功讀取紀錄。
- 這證明 USB-video 的 PL hardware file 已由板端成功下載；仍未啟動 DMA、相機串流或人物辨識。
- 最後的 frame-ID MMIO 寫回讀仍待 root 工作階段執行；PYNQ 3.1 對這個 `/dev/mem` MMIO 操作要求 root，即使使用者已有 `render` 權限。

## 2026-11-12：板端 PYNQ overlay／XRT 診斷定位到 render 權限

- USB-video overlay 的 `.bit`、matching `.hwh` 與安全 verifier 已傳到板端；verifier 在下載前因 XRT 顯示 0 devices 而安全停止，沒有啟動 DMA 或相機。
- 板上 XRT 2.17、ZOCL 與 FPGA manager 都存在，開機記錄顯示 `base.bin` 已載入；但帳號 `xilinx` 不在 `render` 群組，無權存取 `root:render` 的 `/dev/dri/renderD128`，因此 PYNQ/XRT 無法開啟 device 0。
- 尚待在已登入 SSH 終端以 sudo 將 `xilinx` 加入 `render` 群組後重新登入，再重新驗證 overlay。這不是 DPU、YOLOv8 或 DMA 已成功。

## 2026-11-12：兩支 USB 相機已在 PYNQ 板上逐支實際擷取成功

- 板端 `lsusb` 實測兩支 Logitech Webcam C270（`046d:0825`）；第一支對應 `/dev/video0`/`video1`，第二支對應 `/dev/video2`/`video3`。
- 以板端 OpenCV 依序開啟 `/dev/video0`、`/dev/video2`，各讀取一張影像成功，兩者皆為 `640×480×3`。
- 此結果是逐支 sequential capture；尚未驗證兩支相機同時串流（先前 USB2 hub 帶寬可能不足）。`wlan0` 目前 DOWN；未見 `/dev/dpu*` 或完整 VART/XIR runtime，因此尚未完成 Wi‑Fi、DPU 或 YOLOv8 板端推論。

## 2026-11-12：PYNQ Linux、SSH 與 video device 枚舉已實測

- SSH 已以帳號 `xilinx` 成功登入板子；畫面實測 `whoami` 回傳 `xilinx`，Linux 為 `6.6.10-xilinx-v2024.1`、`aarch64`。
- `python3` 可匯入 PYNQ `3.1.1`；`/dev/video0` 到 `/dev/video3` 均存在。
- 這只證明 Linux/PYNQ 與 V4L2 device node 枚舉，尚未驗證任一相機能出圖、兩支相機可同時串流、DMA/DPU/YOLOv8 或雙板 Wi‑Fi。

## 2026-11-12：工具鏈安裝等待期間完成主機端 Python／部署測試

- 重跑人物追蹤、YOLOv8 adapter、VART gate、Wi‑Fi peer 協定與 USB overlay verifier：`24/24` 通過。
- 雙板部署 bundle 的來源檢查：`2/2` 通過。
- 這些是主機端測試，不代表 DPU、相機、DMA 或雙板 Wi‑Fi 已在實體板上運作；2022.1 安裝仍在進行。

## 2026-11-12：板子重新開機後網路已恢復

- 重新開機後 `192.168.3.1` ping 成功，TCP/22（SSH）已開啟；表示 SD/Linux 網路已回來。
- Windows 目前重新枚舉到 USB 序列埠 COM4；以 115200 baud 唯讀 4 秒收到 0 bytes，因此尚未把 UART 開機訊息當成已驗證。沒有向 UART 寫入資料，也沒有登入或修改板子。
- 安裝精靈仍只保留一個 2022.1 視窗；這次檢查未碰安裝器或板端設定。

## 2026-11-12：DPU 4.0 所需的 2022.1 Windows 安裝程式已取得

- 已在 `Downloads` 實際確認 AMD Unified Installer：`Xilinx_Unified_2022.1_0420_0327_Win64.exe`，大小為 215,919,904 bytes（AMD 頁面標示 205.92 MB）。這是目前 DPUCZDX8G 4.0／Vitis AI 2.5 所需的 2022.1 工具鏈取得步驟。
- 尚未執行安裝程式，也沒有移除現有 Vivado/Vitis 2024.2、建立 2022.1 專案、重建 DPU 硬體、改寫 SD 或碰板子；下載完成不等於 DPU／YOLOv8 已可上板。

## 2026-11-12：目前必須斷電重開板子

- 正確的 PYNQ UART 是 COM5；可開啟但沒有收到開機訊息，SSH 網路也仍不能連。
- JTAG USB 線仍被電腦辨識，因此問題是板子尚未回到 SD/Linux，而不是電腦失去線材。
- 請斷電再開後維持 SD boot；重開後我會先確認 UART、SSH 和兩支相機。

## 2026-11-12：USB 硬體已成功由 Vivado 暫時下載到 FPGA

- Vivado 現在確定可看到 FPGA，並已成功把 USB-video 的 bitstream 暫時下載到 PL；沒有寫 SD 或 flash。
- Vitis 的 A53 控制程式還未實跑：JTAG 無法暫停目前核心，工具逾時後已停止，不會假裝成功。
- 先前 JTAG reset 令 Linux 網路暫時消失。請將板子斷電再開，讓 SD/Linux 正常開機後再繼續。

## 2026-11-12：兩條線可同時插；JTAG 後續已由 Vivado 確認

- 已確認 UART 是 COM4，板子 SSH 網路埠當時也可連線，兩者可以同時使用。
- 初次 XSDB 顯示不完整；後續 Vivado 已實際看到 FPGA 並完成暫時 PL 下載，請以本檔較新的 USB 硬體項目為準。
- 目前因 JTAG reset 暫時失去 SSH；斷電重開回到 SD/Linux 後，仍需要可用登入資料才能上傳並跑實機檢查。

## 2026-11-12：USB 硬體檔已有專用的板端安全檢查

- 部署包現在會帶 USB-video 的硬體檔和檢查程式，不會混用舊版測試硬體。
- 板端檢查只載入 overlay、確認兩個 frame-ID 暫存器可寫回讀，並清回零；不會啟動 DMA、相機或人物辨識。
- 已在電腦端測試與實際封裝；仍待板子有效登入後才可做真正載入測試。

## 2026-11-12：USB 硬體檔已可安全準備給 Linux 板子使用

- 已從 USB-camera Block Design 的實際 Vivado 結果封裝出成對的 `.bit`／`.hwh` overlay 檔案，名稱及雜湊均已核對。
- 封裝步驟只在電腦上複製檔案，不會燒錄 SD、連線板子或偷偷變更開機。
- 仍待有效板端登入後，才能實際載入 overlay 並驗證 USB 相機與 DMA。

## 2026-11-12：Vitis 控制程式已用正確 Embedded 安裝重新編出

- 找到完整的 Embedded Vitis 2024.2 安裝，修正另一套 Vitis 因 Lopper 缺失而「表面 exit code 成功、實際平台建立失敗」的問題。
- 已重新產生 A53 的 USB-video 控制 ELF，並再次核對 DMA、frame ID、mailbox 三個位址都和 Vivado XSA 一致。
- 這是電腦端建置驗證；尚未燒錄或在板上執行相機、DPU 或 Wi-Fi。

## 2026-11-12：Vivado 已重新開啟並驗證 USB 相機 Block Design

- 已用 Vivado 2024.2 實際打開完成的 Block Design，硬體設計維持有效。
- DMA、frame ID 和 mailbox 三個 Vitis 控制位址皆由 Vivado 重新讀回正確值。
- 這仍未啟動相機、燒錄板子或跑 DPU。

## 2026-11-12：板子的 SSH 網路可達，但目前不能登入

- 電腦可連到板子 `192.168.3.1` 的 SSH 埠，表示網路線路正常。
- 目前預設登入資料被拒絕，所以沒有執行任何板端指令、沒有改動 SD 或設定。

## 2026-11-12：DPU 硬體檔已有可核對的身分紀錄

- 新工具會記錄目前 DPU 的 IP 版本、硬體設定 fingerprint，以及 bitstream／XSA 等檔案雜湊。
- 已實際核對目前 B512 DPU 是 4.0；這可避免之後拿錯硬體檔做 Linux 映像或模型。
- 這是檔案身分核對，不是 DPU 已在板子上推論。

## 2026-11-12：兩板部署包已補齊 Wi‑Fi 與 DPU 程式

- 部署 tarball 現會包含 Wi‑Fi 檢查工具與未來 DPU YOLOv8 adapter；已實際建立 archive 並確認檔案在內。
- 沒有上傳或寫入任何板子，尚不是兩板 Wi‑Fi／DPU 執行驗證。

## 2026-11-12：兩塊板的一鏡頭互傳流程已寫成可執行步驟

- 文件現在明確要求兩塊板都先開啟接收端、通過 Wi‑Fi 檢查後，再各自傳送自己相機的人物框給另一塊板。
- 不會把某一塊板的 IP、相機編號或 Wi‑Fi 資訊寫死；仍待第二塊板與真實 Wi‑Fi 實測。

## 2026-11-12：Vivado 與 Vitis 的控制介面已實際核對

- 已實際比對 Vivado 匯出的硬體檔與 Vitis 自動產生的控制位址：DMA、frame ID、影像處理 mailbox 三個位址全部一致。
- 這證明硬體 Block Design 與 Vitis 控制程式使用同一套控制介面；尚不是相機或 DPU 的上板執行測試。

## 2026-11-12：人物偵測程式已預留 DPU 模式

- 原本的偵測程式現在有可選 `yolov8_vart` 模式；日後提供 DPU `.xmodel` 即可走同一個 tracker／Wi‑Fi 流程。
- 預設仍是已驗證的 CPU YOLOv8。DPU 模式缺模型、輸出格式不符或 runtime 未部署時會停止，不會假裝偵測成功。

## 2026-11-12：YOLOv8 的 DPU 輸出可接回既有人物追蹤格式

- 已補上「標準 YOLOv8 單一輸出」的解碼器，能把人物框轉成既有 tracker／Wi‑Fi 程式所用格式，並完成離線測試。
- 真正 DPU 模型還沒產生，所以程式不會猜測它的輸出；等 `.xmodel` 完成後才會確認能否使用此解碼器。

## 2026-11-12：Linux 建置環境已能看見正確的 DPU 編譯器

- 已讓 WSL 的建置環境使用既有 Docker Desktop 裡正確的 Vitis AI 2.5 compiler image，不用重新下載。
- 已從 WSL 實際啟動該 compiler container，確認模型編譯指令能執行。
- 檢查工具現在會直接讀 PetaLinux 安裝內容，確認目前只有 2024.1；因此會正確擋下 DPU 4.0 所需 2022.1 被假裝已完成的情況。
- 還是不能建出正式映像：真正缺的是 Vivado/PetaLinux 2022.1，不是 Docker 或模型編譯器。

## 2026-11-12：正確版本的 DPU 函式庫已能交叉編譯連結

- 已安裝 DPU 4.0 所需的 2022.1 SDK，並放入對應的 Vitis AI 2.5 函式庫；實際編出 ARM 版測試程式，確認它會連到 VART、XIR 和 unilog。
- 這只證明電腦端的編譯工具與函式庫版本可搭配，沒有在板子上執行，沒有寫入 SD，也還不是 YOLOv8 DPU 偵測。

## 2026-11-12：DPU 工具鏈已按實際 IP 更正

- 讀到現有 DPU 硬體的實際 IP 為 **4.0**。它的官方搭配是 Vitis AI 2.5＋Vivado/Vitis/PetaLinux 2022.1；若要用 Vitis AI 3.5／YOLOv8 路線，必須先換成 DPU IP 4.1，再用 2023.1 重建。
- 因此現有的 Vivado 2024.2、PetaLinux 2024.1、DPU 4.0 bitstream 與 Vitis AI 3.5 Docker image 不能直接組成可部署系統。已新增檢查，會明確擋下這種混版。

## 2026-11-12：已找到並驗證官方 DPU 原始碼

- 已自行下載 AMD 官方 DPU 原始碼並核對：它和目前做出的 B512 DPU 硬體檔完全相同，確認是 DPU 4.0、2022.1／Vitis AI 2.5 路線。
- 原始碼保留在電腦的外部工具資料夾，不上傳 Git；這證實硬體來源，但還沒有 Linux 映像、模型或板端 DPU 測試。

## 2026-11-12：DPU 4.0 的模型編譯器已就緒

- 已下載並實測對應的 Vitis AI 2.5 Docker 編譯環境；DPU 模型編譯所需工具都能啟動。
- 還不能宣稱模型已跑在板上：仍缺 2022.1 的 Vivado/PetaLinux、Linux DPU 驅動與板端映像。

## 2026-11-12：已備妥正確的 2022.1 runtime 資產

- 已下載正確版本的 target SDK 與 Vitis AI 2.5 runtime，並在 Linux 環境確認 VART、XIR、xdputil 函式庫內容完整。
- 這些檔案尚未寫入 SD 卡或板子；要等 2022.1 Linux 映像完成後才可使用。

## 2026-11-11：找到 Linux 的連續影像記憶體，但 DMA 還不能直接使用

- 板子已具備可分配連續記憶體的 CMA；這是相機資料未來送往 FPGA 所需的條件之一。
- Linux 程式還不能直接取得可給 AXI DMA 使用的實體地址，仍需要正確的 kernel DMA driver 來交接資料。
- 本次只讀檢查，沒有修改 DMA、核心、bitstream 或系統。

## 2026-11-11：同一塊板的兩支 C270 都能被 Vitis/Linux 讀取

- 新增依序擷取模式：先讀第一支、關閉後再讀第二支，接著產生雙鏡頭硬體資料格式。
- 已實測兩支 C270 都成功讀到影像並放進 A/B 槽位。
- 這是依序的測試，不是兩支同時串流；共用 USB hub 的同時串流限制仍存在。

## 2026-11-11：已加入兩板 Wi-Fi 開始前的檢查

- 新工具會檢查 Wi‑Fi 是否已取得 IP，以及另一塊板的接收埠是否可連；不會存取或改動 Wi‑Fi 密碼／SSID。
- 現在這塊板的 Wi‑Fi 尚未設定，工具正確回報不能開始兩板傳送。

## 2026-11-11：Vitis Linux 已實際讀到一支 C270

- 新的 Vitis/Linux 程式可讓每塊板各讀一支 C270，並將影像填入硬體資料格式的 A 或 B 槽位；另一槽會保持黑色，不會偽造第二鏡頭。
- 已在 PYNQ-ZU 實測：320×240、10 FPS 的 C270 成功轉成 640×480 的 packed RGB 資料，A 槽與 B 槽兩種板端角色都已確認方向正確。
- 這還沒有將資料送入 DMA、FPGA/DPU，也不是同板雙鏡頭或兩板 Wi‑Fi 完成證明。

## 2026-11-11：兩塊板資料傳送可處理短暫斷線

- 每一張人物偵測資料預設會重試三次；另一塊板剛重開時，不會立刻遺失這一張資料。
- 連續失敗仍會清楚報錯，不會假裝 Wi-Fi 傳送完成。
- 已用模擬連線測試重試邏輯；尚未有第二塊板或實際 Wi-Fi 驗證。

## 2026-11-11：DPU 的 Python 執行介面已先做好

- 新增可在未來 DPU Linux 上載入 `.xmodel`、送入量化影像、取回反量化 tensor 的 Python 介面；它會和既有 tracker／Wi-Fi 資料格式銜接。
- 已用不需板子的假 DPU runner 測過影像顏色順序、量化、輸出還原與錯誤保護（7 個測試全部通過）。
- 尚未有真正 DPU 編譯模型，所以還不能從 DPU tensor 產生人物框；程式會明確停止，不會把猜測的結果當作偵測成功。

## 2026-11-11：已確認下載的 Vitis 檔不能建 DPU Linux

- 約 6.6GB 的下載檔是 Windows 版 Vitis Embedded 2024.2，不是 PetaLinux 或 Vitis AI Linux 建置環境。
- 這台電腦沒有已安裝的 WSL Linux、Docker、PetaLinux，也沒有 2024.1 工具鏈；因此仍不能從這台機器產生 DPU runtime。
- 沒有進行安裝、解壓大型工具或改動系統。

## 2026-11-11：DPU 正確的模型架構檔已找到

- 已從 Vivado 產生的 DPU IP 找到正確的架構檔，fingerprint 是 `0x101000016010400`。這是之後編譯 YOLOv8 DPU 模型時必須使用的精確設定，不是其他板子的範例檔。
- 已加入可重跑的擷取工具；目前仍缺 Vitis AI compiler、PetaLinux 與相配 Linux runtime，所以還不能產生或執行 DPU YOLOv8 模型。

## 2026-11-11：DPU 硬體檔目前已在 PL，但尚不能推論

- Vivado 確認 PYNQ‑ZU 的 PL 目前載入 DPU bitstream。
- SD Linux 仍可開機、相機和 CPU YOLOv8 仍可用；但 DPU driver、VART/XIR 與 DPU 模型都沒有，所以目前不能用 DPU 做 YOLOv8 推論。
- 沒有再次燒錄或改動 SD；下一步必須先做相配的 Linux DPU runtime。

## 2026-11-11：板載 Wi‑Fi 硬體已確認，但尚未連網

- 板子的 `wlan0` 與 Wi‑Fi 驅動已存在，可作為未來兩塊板傳送人物框資料的網路介面。
- 目前 Wi‑Fi 未啟用、沒有 IP，也沒有連上任何網路；尚未設定 SSID 或密碼。
- 要開始兩板互傳，需指定要連的受信任 Wi‑Fi 網路或兩板直連方式。

## 2026-11-11：重開後兩支 C270 都可個別取像

- `video0` 與 `video2` 都在 320×240 的依序檢查中成功讀到影格。
- 這不代表兩支可同時串流；先前確認的 USB hub 頻寬不足限制仍存在。

## 2026-11-11：重開後 YOLOv8 已重新部署並實測

- 板子重開後 Linux、SSH 與相機節點都已恢復；最新 YOLOv8 程式部署到新的資料夾，沒有覆蓋舊 YOLOX dashboard。
- 單一 C270 成功讀到 320×240 影格並完成 YOLOv8 CPU 推論，約 0.964 秒；當下畫面沒有偵測到人。
- 以臨時公開人物圖驗證，同一套板端 YOLOv8 成功找到 4 人，約 1.654 秒；測試圖已刪除。
- 這仍是 CPU/ONNX Runtime，不是 DPU；DPU driver、VART/XIR、雙鏡頭同時串流、Wi-Fi 第二板與 FPGA DPU 推論都尚未完成。

## 2026-11-11：兩條線可同時使用，JTAG 已找到

- Composite 與 UART/JTAG 可以同時插；目前 Composite 維持 Linux/網路，Vivado 已實際找到 PYNQ‑ZU 的 `xczu5` JTAG target。
- 現在 SSH port 雖仍可到達，但登入前會被板子重設連線。為了回到 SD Linux 的乾淨狀態，下一步要維持兩條線都插著，將板子關機後再開機。
- 尚未證明 DPU Linux、VART 或 YOLOv8 DPU 可運作，也沒有重刷 SD、安裝套件或部署模型。

## 2026-11-11：板子已重新以 Composite USB 連線

- 電腦目前看得到 PYNQ-USB 與板子的 USB 網路，並可連到 `192.168.3.1` 的 SSH port。
- 這不是 UART/JTAG：Vivado Hardware Manager 目前仍不會透過這條 Composite 線看到板子。若要燒錄/除錯，還要接 UART/JTAG 孔。
- 尚未登入板子或改動板子的 SD、開機設定和 bitstream。

## 2026-11-11：DPU Linux 建置環境已做離線檢查

- 新增 DPU 主機檢查程式，會在真正開始做 Linux 映像前確認 Vitis AI 編譯器、PetaLinux 與正確的 DPU 架構檔都存在，避免把不相容的模型或映像燒進板子。
- 查到目前 DPU 硬體用 Vivado 2024.2 做成；AMD 公開驗證的 DPU 4.0 + Vitis AI 3.5 組合是 2024.1。因此硬體雖可做出 bitstream，仍必須在 2024.1 重建並搭配同版 PetaLinux，才可進入正式 DPU/YOLOv8 部署。
- 目前這台電腦沒有 Docker、Vitis AI compiler、PetaLinux 或可用的 DPU `arch.json`，所以尚不能建 DPU Linux image；沒有進行任何系統安裝、重刷 SD 或板子操作。

## 2026-11-06：改為 Vivado Block Design + Vitis 控制架構（進行中）

- 已新增 PYNQ-ZU 的 `pynq_zu_usb_video` Vivado Block Design 腳本：保留板上 USB0（MIO 52–63）與 USB1（MIO 64–75）給 Zynq PS，並加入 AXI DMA、DDR HP0、AXI-Lite bbox mailbox、frame-ID GPIO、64-bit 雙 RGB stream 與 IRQ。USB C270 的 D+/D− 是 PS USB 控制器接腳，不是可拉進 PL 的 GPIO。
- 本機 Vivado 2024.2 已實際完成 `validate_bd_design`；不代表相機影像、DMA、bitstream 或板端已完成。XSA 匯出已啟動，但 synthesis 子工作仍等待 Vivado queue，尚未產出 XSA。
- 已新增 Vitis C 控制核心與 host test，確認每個 frame 會依序寫 frame ID、bbox 資料，最後才 commit mailbox CONTROL。Vitis 實際 application 必須待 XSA 完成後以產生的 `xparameters.h` 編譯。
- 尚未完成：synthesis/implementation/XSA、Vitis BSP/application 實機編譯、USB UVC → DDR → DMA → PL 串流，以及雙 USB 鏡頭的實機頻寬問題。

## 2026-11-05：已完成換機前的 GitHub 交接整理

- 已盤點目前 `main` 與 GitHub `main` 相同，專題的程式、RTL、網站、啟動腳本、測試與交接文件都已在版本控制中；這次再補上明確的交接與忽略規則。
- 不會上傳 Vivado/XSim 日誌、模擬波形、暫存輸出、已簽名 PDF 預覽、硬體照片或本機網站日誌。它們不是執行專題所需原始碼，且可能含本機路徑或私人資料；未上傳不代表專題進度遺失。
- 換電腦後從 GitHub clone `main`，照詳細交接文件安裝 Python 套件與 YOLOX 模型，再先跑軟體／RTL 回歸。相機、PYNQ Linux、雙 USB 鏡頭與 FPGA 實機功能仍要在新環境各自重新驗證。

## 2026-11-05：已記錄板子展示計畫，尚未開始實作

- 未來展示會讓 PYNQ-ZU 接到區域網路，電腦瀏覽器開啟 `http://<板子-IP>:8766/`，查看兩個鏡頭畫面、人物框、追蹤編號，以及配對候選／確認結果。
- 預計先讓板上的 Python 網站讀 USB 鏡頭並顯示軟體結果，再接上 FPGA 的配對確認結果；UART 只看除錯文字，不用來傳即時影像。若要直接接螢幕，之後才另做 HDMI 畫面輸出。
- 目前這只是存到 GitHub 的工作計畫：尚未接板、尚未確認板子網路或相機、尚未產生/燒錄 bitstream，也尚未在板上實際看到畫面。

## 2026-11-04：YOLOX 已有可接 FPGA 的傳遞介面

- 保留 GitHub 先前已驗證的 Verilog：雙路人物框色彩特徵、跨鏡頭三次確認、640×480 模擬。
- 新增 PYNQ-ZU AXI4-Lite mailbox：Python YOLOX 可把每幀選定的 A/B bbox 和影格號寫入 FPGA；FPGA 只在相同影格開始時鎖住座標，避免錯影格或半寫入。
- 本機 Vivado mailbox 模擬 5 項檢查 PASS，整合 Verilog top 編譯成功；Python 寫入暫存器的合約測試也 PASS。
- 尚未上板：相機輸入、腳位/時脈、implementation/bitstream 與實機 MMIO 都未完成。YOLOX 仍在 CPU/PS，FPGA 只做接 bbox 後的 ROI 特徵及確認，不能說 YOLOX 已在 FPGA 推論。

## 2026-11-04：PYNQ-ZU 的 PS 與 Verilog 已可一起綜合

- 已建立 Zynq PS→AXI SmartConnect→自訂 YOLOX mailbox 的 Vivado Block Design；PYNQ Python 可使用的暫存器位址目前是 `0xA000_0000`。
- 補上同步 reset 後，Block Design 驗證通過；生成 wrapper 後，PYNQ-ZU 目標的 Vivado 綜合完成，結果為 0 error、0 critical warning。
- Windows 的專題資料夾路徑過長且含中文會造成 Zynq IP 生成失敗；腳本已改成預設把可丟棄的 Vivado 生成物放在短的 `%TEMP%/pynq_zu_rtl`，不影響 GitHub 原始碼。
- 尚未做相機輸入、腳位/XDC、implementation/bitstream、PYNQ overlay 或實機讀寫。因此這是「可綜合的硬體結構」，不是已經能在板子上看見雙鏡頭結果。

## 2026-11-04：雙鏡頭資料可由同一條 DMA 串流送進 FPGA

- 新增通用 64-bit AXI-Stream 入口：一個 DMA word 同時裝 A、B 兩個 RGB 像素，讓兩鏡頭像素保持同步；每 640×480 張影像自動形成一個 frame。
- Python 已能把兩張 RGB 影像打包到 PYNQ DMA buffer；Verilog 模擬 7 項檢查與 Python 打包測試都通過。
- 這可供未來的 USB/PS、CSI 或 HDMI 來源共用；還沒選定實體相機介面，也還沒接上 DMA/相機實機。

## 2026-11-04：PYNQ-ZU Vivado board file 已驗證

- 目標板確認為 TUL PYNQ-ZU（XCZU5EG-1SFVC784）。已從使用者下載的 Xilinx Board Store 解壓 board repository，並以 Vivado 2024.2 實測找到 `tul.com.tw:pynqzu:part0:1.1`。
- 新增可重跑的 `fpga/configure_pynq_zu_board.tcl`，它只設定目前 Vivado session 的 board repository，不修改 Vivado 安裝目錄。
- 大型第三方 `fpga/board_repos/` 已加入 Git ignore；尚未建立 bitstream、接通板端網路或驗證實體 PYNQ-ZU 開機。
- 新增 `fpga/create_pynq_zu_rtl_project.tcl`，以 PYNQ-ZU board part 建立 Vivado 2024.2 專案並加入目前的 ROI/候選 Verilog；本機已實跑成功建立專案。生成的 `fpga/build/` 不提交。尚未加入 PS block design、AXI、時脈/reset、XDC 或 bitstream。

## 2026-11-04：公開圖片 dataset 彙總評估

- 新增 `person_tracking/evaluate_detection_dataset.py`，讀取既有人工標註驗證報告並彙總 6 組 bus／zidane 亮度案例。
- 結果：105/105 個人工標註人物觀測配對成功，annotated recall=1.000、最低 IoU=0.855、ID switch=0，負例測試 PASS。
- 這是人物框／短期追蹤 dataset 評估，不是跨鏡頭真人身分配對準確率；後者仍需人工標記兩台鏡頭的同人／不同人資料。

## 2026-11-04：新增同人配對分數測試入口

- 新增跨鏡頭配對評估程式，可計算同一人判斷的 accuracy、precision、recall、F1、TP/TN/FP/FN，並檢查人物框座標最大誤差是否小於 20 px。
- 目前 4 筆範例回歸結果為 accuracy=1.000、F1=1.000、最大框誤差 8 px；這些是合成資料，只能證明程式可重跑，不能宣稱真人雙鏡頭準確率。
- 後續只要把 `person_tracking/matching_dataset.json` 換成實拍且人工標記「同人／不同人」的案例，再執行 `python evaluate_matching_dataset.py` 即可得到正式分數。

## 2026-11-04：EPFL 小型公開多鏡頭資料實測

- 使用 EPFL 公開資料的 939 個人工標註影格，實際跑專題 YOLOX；ground truth 1,302 框，預測 1,565 框。
- IoU>=0.5 配對 1,035，漏抓 267，誤抓 530；recall=0.7949、precision=0.6613、平均 IoU=0.7963、最低 IoU=0.5007，執行 133.84 秒。
- 另計算框座標誤差：平均 5.7932 px、最大 37 px；`<20 px` 門檻為 FAIL，不能宣稱全部人物框都在 20 px 內。
- 若依「物體位置」採用 matched box center 的 Euclidean distance，最大中心誤差為 19.5256 px、平均 2.9939 px，`center_error_pass=true`；報告同時保留嚴格四邊最大誤差 37 px，兩種指標不可混稱。
- 比較 Raw、EMA 0.25/0.5/0.75、median3 後，Raw YOLOX 最好；平滑法在非連續 EPFL 標註影格上使中心最大誤差升至 28.0401–43.5115 px，已排除。
- 新增相機框座標校正與底部邊界修正：用 80% calibration、20% held-out validation，`clamp=460` 的 validation 最大邊界誤差為 19 px，mean IoU=0.8164、recall=0.7993、precision=0.6847，正式低於 20 px。
- 結果為 `EPFL_DATASET_PARTIAL`，完整逐案例數字保存在 `person_tracking/epfl_dataset_evaluation.json`；這是外部資料實測，不是合成回歸。
## 2026-11-04：雙鏡頭候選確認 Verilog 核心

- 實際雙 USB 鏡頭 localhost 網站已啟動；白牆連續抽樣顯示兩側亮度接近，最新量測平均差約 1.1/255。這只驗證當時的影像一致性，不是人物配對準確率。
- 新增 Verilog `cross_camera_pair_matcher.v`：對上層已選定的一組 A/B 人物色彩特徵，連續三個相似且有效的觀測才確認候選；不相似或缺少配對時重置。新增測試平台後以這台電腦的 Vivado 2024.2 XSim 實跑 10 項檢查通過。
- 本核心目前使用既有的簡化 24-bit 主色／比例特徵；尚未搬移 Python 的 YOLOX、HSV 15-bin 相似度、0.72 分數、多人物最佳配對或上板相機介面。因此不能把這次模擬當成真人跨鏡頭準確率或 FPGA 實機完成。
- 新增 `dual_camera_roi_match_top.v`，將兩路同步 RGB 串流、CPU/YOLOX 提供的 A/B 人物框、兩個完整解析度 ROI 特徵核心及三次候選確認串接；已以 Vivado XSim 編譯通過。YOLOX 神經網路、不同時脈 USB 相機 frame buffer、bbox 傳輸及多人物仲裁仍未改成 Verilog。
- 新增完整 640×480 雙串流 testbench，實測三個連續相似人物框會在第三張確認，下一張不同色人物框會歸零；Vivado XSim 16 項檢查 PASS。這是合成像素與 bbox 的 RTL 模擬，不是實體 USB/FPGA 或 YOLOX 網路硬體驗證。
- `dual_camera.py` 現在會把 CPU/YOLOX 已選定的 A/B 配對輸出成每次執行的本機 `rtl_yolox_packets.json`：包含 frame、同步狀態、A/B track ID、bbox、確認狀態與相容的 24-bit RTL 色彩特徵。此檔是 Python 到 Verilog bbox 介面的資料契約，不包含影像，且尚未直接寫入 FPGA。

## 2026-11-03：無鏡頭等待中的公開 HTTPS 網站

- 在本機沒有 USB 鏡頭的狀態下，雙鏡頭網站仍可啟動並回報 `stopped`；這是等待未來插入鏡頭的正常狀態，不是架設失敗。
- 為 Cloudflare Quick Tunnel 增加明確的 `--allow-trycloudflare` 選項；只有啟用時才接受 `https://*.trycloudflare.com` 的頁面/API 請求，平時 localhost/LAN 的原有來源限制不變。
- 已用新產生的 Quick Tunnel HTTPS 連結驗證首頁、`/api/health` 和 `/api/live`；未啟動相機、未保存相機照片，也未提交 tunnel 網址或任何權杖。
- 新增一鍵遠端啟動器。它會保存 CameraA/CameraB 的等待設定，建立新的私有連結，但沒有鏡頭時仍不嘗試連線相機。

## 2026-10-31：這台電腦的可執行環境已複核

- Python、NumPy、OpenCV、YOLOX 模型和公開測試圖片都已可用，不需要再安裝；程式回歸共 24 項通過。
- Vivado 2024.2 已安裝，且有內建 xsim；但沒有找到 ModelSim，因此目前不能跑專案的 ModelSim 驗證入口。
- 現在可雙擊 `開啟VivadoXSim驗證.cmd` 使用已安裝的 Vivado XSim 跑相同 RTL 回歸；本機已跑完 7 張測試影格、89 項檢查並通過。這是 XSim 驗證，並不表示 ModelSim 已安裝。
- 目前 Windows 未偵測到可用相機，所以雙鏡頭網站尚未做實拍驗證。接上兩台相機後即可用 `啟動即時追蹤網站.cmd` 開啟 localhost 網站測試。

## 2026-10-30：第三台電腦的雙鏡頭網站啟動環境

- 第三台電腦已安裝正式 Python 3.12、NumPy 1.26.4、OpenCV 4.11.0，以及專題所需的 YOLOX ONNX 模型與公開測試素材；VS Code 已安裝 Python 擴充套件。
- 修正雙鏡頭啟動腳本：不再誤用 Windows Store 的空白 `python.exe` 啟動器，會優先尋找已安裝的 CPython；`啟動即時追蹤網站.cmd` 改為開啟雙鏡頭 localhost 儀表板（預設 `http://127.0.0.1:8766/`）。
- 此次只完成執行環境與啟動流程準備；尚未確認兩個實體 USB 攝影機、ModelSim 或 Vivado 的實機流程。

## 2026-10-15：可直接開啟的 ModelSim 自動驗證

- 新增 `影像處理/ModelSim_YOLOX_PersonTracking/開啟ModelSim驗證.cmd`，雙擊即開啟 ModelSim、執行測試並保留波形與結果。詳細操作見同目錄 `person_tracking/RTL_REGRESSION.md`。
- 本機 ModelSim SE-64 2020.4 實跑：7 張完整 640×480 合成影像、89 項檢查 PASS；編譯及模擬 0 errors / 0 warnings。涵蓋色彩特徵、人物框邊界、輸入暫停、連續影格及比較門檻。
- 本次沒有修改原本運算 RTL 或即時網站。這是上板前的功能驗證，尚未完成 PYNQ/EGo1 上板、YOLOX 硬體化或整套雙鏡頭判斷電路。

更新日期：2026-10-02

## 2026-11-03：保存鏡頭電腦公開啟動 Prompt

- 新增 `CAMERA_PC_PUBLIC_SETUP_PROMPT.md`，讓連 USB 鏡頭的電腦可以直接依 Prompt 啟動網站與 Cloudflare HTTPS 通道。
- Prompt 要求回傳 `private-link.txt`，並禁止公開 access token；完成仍須在非同一個 Wi-Fi 的手機實測。

## 2026-11-03：兩台電腦協作方式

- GitHub `main` 是程式同步來源；有鏡頭的電腦新增 `live_site/sync_camera_pc.ps1`，會先 `fetch`、`pull --ff-only` 再啟動雙鏡頭網站。
- 雙鏡頭服務新增可設定 LAN bind/allowed Host；鏡頭電腦可用 `-Bind 0.0.0.0 -AllowHost <鏡頭電腦IP>:8766`，另一台以瀏覽器開該網址看即時結果。
- GitHub 不承載即時影像；目前仍要求同一可信任 LAN 與鏡頭電腦防火牆允許 TCP 8766，未做公開網際網路部署。

## 2026-10-26：新增 PYNQ/EGo1 共用板級 RTL 邊界

- 新增 `影像處理/ModelSim_YOLOX_PersonTracking/fpga/roi_feature_board_top.v`，把現有 640×480 ROI 特徵 RTL 包成可接 PYNQ 或 EGo1 的同步串流核心。
- 新增 `fpga/README.md` 說明要接的 RGB/frame/bbox 訊號與後續 XDC/相機或 AXI adapter 工作。尚未宣稱已產生 bitstream、完成腳位約束或完成實體上板。

## 2026-10-26：新增可重跑的跨鏡頭 matcher 回歸評估

- 新增 `影像處理/ModelSim_YOLOX_PersonTracking/person_tracking/evaluate_cross_camera.py`，固定測試同色連續確認、不同色拒絕、相同外觀競爭者判為 ambiguous 三種情況，並輸出 `cross_camera_evaluation.json`。
- 本次合成回歸 3/3 PASS，另有既有 `test_cross_camera.py` 6/6 PASS。這是演算法門檻回歸，不是真人雙鏡頭準確率；PYNQ/EGo1 上板、標記影像準確率與雙實體鏡頭仍未完成。
- 完整 unittest discovery 目前因執行環境缺少 `cv2`，既有 camera/tracking 測試無法載入；未把缺少依賴誤報為測試通過。

## 最新進度

2026-10-02 完整同步盤點：現有程式、網站與先前進度已在 GitHub `main`；本次再補上尚未上傳的兩份精簡驗證紀錄（早期 8×8 ModelSim transcript、6 項追蹤測試 PASS 摘要），並更新內容索引與進度。採新增提交保留舊版，不強制覆蓋。人物照片、審核 manifest、模型權重及大量模擬／相機產物仍只留本機，沒有公開上傳；這些排除項目不等於專案進度遺失。

2026-10-02 人工審核按 ✓／✕ 後，配對照片和沒有其他待審核配對的對應人物縮圖約 5 秒後淡出、收起，讓畫面不再被舊照片佔滿；精簡審核數字及「查看／修改已審核照片」仍可重新展開。這只是網頁顯示，照片仍保存到按「停止雙鏡頭」時才清除。勾叉不訓練模型：✕ 僅排除本次同一組追蹤 ID，✓ 僅記錄人工判斷及凍結審核照片，準確率不會因此自動提高。6 項程式測試、網頁語法與五秒時間邊界測試通過；目前本機網站已提供新頁面，重新整理即可載入。此次尚未用真人雙鏡頭現場驗證淡出流程。

2026-10-02 停止雙鏡頭時，現在連本網站以前工作階段保存的人物照片也會清除。只刪本網站照片清單中登記的 A/B 人物 JPG；其他檔案和舊工作階段的說明／審核清單不動。即使網站已停止，再按一次停止也能清舊照片。

本機實際清理回報刪除 549 張；複查 8 個工作階段後人物 JPG 剩 0 張，8 份舊清單仍在，雙鏡頭已停止。

2026-10-02 改善側面照與人工核對：同一追蹤 ID 的照片會在較清楚、較完整或偵測到正面臉時更新，不再永遠使用第一張；即時配對會參考最近五次外觀特徵。人工審核區可自行選 A/B 兩張照片，按 ✓ 同一人或 ✕ 不是同一人，判斷只作用於本次連線；否決的那組 ID 不再自動配對。這不是人臉身分辨識，仍可能漏配或誤配。

若自動挑照角度仍不理想，可等人轉正、仍出現在畫面中時按「用目前畫面重拍並鎖定」；頁面重整不會清空本次審核或重啟鏡頭。

兩台實體鏡頭 2/1 的新版網頁已跑起來，照片與審核按鈕正常顯示；仍需由你親自對真實配對按 ✓／✕，目前沒有宣稱辨識準確率已經驗證。

2026-10-02 依使用者要求，「停止雙鏡頭」現在會停止鏡頭並清除**本次**由網站保存的人物 JPEG 和配對記錄；不刪以前工作階段或資料夾中的其他檔案。閒置自動停鏡頭不觸發清除。

實機以鏡頭 2/1 測試，停止後清除本次 17 張照片，先前照片資料夾保留；單元測試亦通過。

2026-10-02 雙鏡頭網頁新增本機人物照片留存：每個鏡頭的已確認追蹤 ID 首次出現時保存一張人物裁切照；產生 P 外觀配對候選後，頁面並排顯示兩張照片、A/B ID 和分數供人工核對。照片及 `manifest.json` 保存在本機 `person_tracking/live_captures/`，不會推到 GitHub。P 仍只是候選，可能誤配；追蹤 ID 重新建立時也可能為同一人再存一張。

合成測試已通過；實體鏡頭 2/1 已確認人物照片存檔並能在網頁正常顯示。現場多人畫面暫時只有模糊候選，沒有產生 P 配對，因此尚未以實際同一人的雙照片核對正誤。

最新整合版已上傳到 `影像處理/ModelSim_YOLOX_PersonTracking/`：OpenCV Zoo YOLOX 偵測人物，專題自寫短期追蹤維護追蹤編號，ModelSim 處理完整 640×480 人物框內的色彩特徵；另有雙 USB 鏡頭候選配對程式和本機即時追蹤網站。

新增單鏡頭 A→B 時序交接模擬：前 10 秒保存鏡頭 A 的人物外觀特徵，第 11 秒起重置追蹤器並以該特徵庫重新辨認 B 段人物。符合條件時標示 `SAME-CANDIDATE`。

2026-10-02 新增雙鏡頭 localhost 儀表板 `live_site/dual_server.py` 與 `dual_index.html`：可同時顯示 A/B USB 畫面、兩側本地 Track ID 及跨鏡頭外觀候選。實機以內建鏡頭與 Logitech C270 擷取各 30 張，兩側各完成 30 個 ROI 的 ModelSim 驗證 PASS；本次未產生已確認 P 候選。

儀表板後續改為「最新相機影格」與「背景 AI 標註」分離更新。實機頁面約 9 FPS，AI 約 1.6 FPS、延遲約 0.7 秒；影像不再等待 YOLOX 完成才更新。

同一人跨鏡頭截圖曾只有 0.367 相似分數。現將外觀特徵改為容忍曝光差異的平滑色彩統計，並提高上半身在總分中的比重；該張截圖離線重算約 0.84，圖中另外兩位不同衣著人物約 0.46、0.60。這些數字僅代表該張截圖，仍需更多已標記同／不同人影像檢驗誤配率。

## 驗證狀況

- 單鏡頭已保存兩輪 USB 實拍紀錄，共 240 張；偵測/追蹤及 ModelSim 特徵核對通過。
- 雙鏡頭程式已用兩台實體 USB 鏡頭各擷取 30 張；兩側 ModelSim ROI 驗證通過，但該批沒有確認的 P 候選。
- 單鏡頭 A→B 新程式已用 USB camera 0 跑完 21 秒；A、B 都沒有偵測到人物，因此沒有可判斷的配對結果。要確認功能，需讓同一人留在畫面中再跑一次。
- 雙鏡頭配對只是衣著外觀候選，不是身份辨識；整體流程也不是即時 FPGA AI 推論。

## GitHub 版本差異

先前已補上四份舊版專題簡報、早期測試用合成圖樣、文件整理工具與 MCDPT 授權參考程式，並從目前共享檔案樹移除舊的 Vivado FPGA 原型；本機檔案保留。更早的 Git 提交仍留有該原型。

論文 PDF、模型權重、個人相機影像、模擬暫存與私人/無關檔案沒有上傳。

詳細交接與數據見 [PROGRESS_FOR_CODEX.md](PROGRESS_FOR_CODEX.md)。

## 2026-11-05：以後每次進度都記錄並上傳

- 新增 `CONVERSATION_PROGRESS_LOG.md`：每次完成一個可交付進度，都會留下精簡摘要並與變更一起上傳 GitHub；不會上傳私人連結、帳密、個人影像或逐字聊天。
- 已確認目前本機 `main` 與 GitHub `main` 同步。最近的 PYNQ-ZU、IRQ 與雙 USB 部署工作都已有提交。
- 現有未追蹤檔是 Vivado/XSim 與本機網站的暫存日誌，不是漏傳的原始碼，會維持不公開。

## 2026-11-05：PYNQ-ZU bring-up 已燒入

- 已確認板子是 PYNQ-ZU，Vivado 透過 JTAG 看得到 `xczu5_0`。
- 已成功產生並透過 JTAG 下載 bring-up bitstream；Hardware Manager 顯示 `Programmed`。此設定斷電會消失，沒有改寫 SD 卡。
- 為了可產生安全 bitstream，暫時把尚未接好的影像輸入固定為 idle，且不把輸出接到未設定腳位；PS、20 MHz PL clock 與 AXI-Lite mailbox 都在設計內。
- 尚未完成真正的雙攝影機：仍要決定 CSI、HDMI 或 DMA/USB 的影像來源，加入對應硬體/IP/XDC，並在 PYNQ Linux 驗證 Overlay/MMIO 與影像資料流。

## 2026-11-05：換電腦也可直接部署到 PYNQ-ZU

- 新增一條可直接貼到新 Windows 電腦 PowerShell 的部署命令：從 GitHub clone 後，填入 PYNQ 的 IP，即可打包、SSH/SCP 傳送與解壓雙 USB 網站；不依賴目前電腦的 Vivado 暫存或既有 tarball。
- 可選擇立刻檢查兩支 USB 鏡頭各能讀取一張影格；若另有相符的 Overlay 檔，也可執行 AXI-Lite mailbox 的寫入／讀回檢查。
- 本機已實際驗證部署包可建立，內含網站、YOLOX ONNX、追蹤程式與板端驗證程式；尚未因板子仍未 SD 開機而進行 SSH、USB、Overlay 或瀏覽器實機驗證。

### 2026-11-05：新電腦模型自動補齊

- 盤點發現 YOLOX 模型依容量規則沒有上傳 GitHub；現在首次部署會自動下載官方 OpenCV Zoo 模型並核對 SHA-256，下載正確才會打包，因此新電腦不用手動找模型檔。
- 本機已核對現有模型雜湊及部署包內容；第一次部署電腦需可連網下載約 35 MB 模型。板子 SSH 與實機相機仍待 SD 開機後驗證。

### 2026-11-05：板端環境先檢查再碰鏡頭

- 部署命令新增系統檢查：先列出板端 Python、NumPy、OpenCV、模型與 PYNQ 套件狀態，再檢查兩支 USB 鏡頭，方便立即看出 SD 映像缺什麼。
- 本機已跑過此檢查與完整打包；本機沒有 PYNQ 套件屬預期。板子的實際套件和鏡頭仍待 SD 開機後檢查。

### 2026-11-05：離線軟體與 RTL 回歸重新驗證

- 雙鏡頭配對、特徵與追蹤的 Python 測試共 18/18 通過；網站人物照片／人工審核資料流程合成測試 6/6 通過。
- Vivado XSim RTL 回歸完成 7 個影格、89 個檢查，結果 PASS。這些是本機合成／模擬驗證，還不能取代 PYNQ、USB 相機或 Overlay 的實機測試。

### 2026-11-05：可重跑 FPGA 指令／中斷模擬

- 新增 Windows 一鍵 XSim 指令，可在沒有板子的電腦重跑 PYNQ mailbox、影格對齊與 IRQ 清除測試；本機結果為 9 個檢查全部通過。
- 同時更正文檔中先前誤寫的 5 個檢查數；實際 testbench 是 9 個。這仍是模擬，不代表板端中斷已實際觸發。

### 2026-11-05：全新 GitHub clone 部署包實測

- 已從 GitHub 的最新 `main` clone 到全新暫存資料夾，沒有手動放入模型；部署打包器自動下載 YOLOX 模型並成功建立含 11 個必要檔的板端 tarball。
- 因此「換電腦 clone 後直接貼部署命令」已在本機以乾淨 clone 實測通過。仍未接觸板子、SSH 或 USB 相機。

### 2026-11-05：準備 SD 開機後的驗證包

- 已產出 PYNQ Overlay 要用的 `.bit` 與 `.hwh` 配對檔，並加入板端 AXI-Lite 讀寫驗證程式；開發電腦的 Python 語法檢查通過。
- 現在 PYNQ 網頁 `192.168.3.1` 無法連線，因板子仍在 JTAG 階段且這台電腦目前是 `192.168.50.x` 網段。下一步必須切回 SD、重新開機，才可啟動 PYNQ Linux 並上傳/執行驗證。

### 2026-11-05：中斷與雙 USB 鏡頭網站

- 已補上 PS IRQ：feature 完成、跨鏡頭確認、命令遺失與 mailbox 覆寫都能觸發；程式可讀取並清除中斷。RTL 模擬通過，包含中斷拉高與清除。
- IRQ 版 bitstream 已完成時序/DRC/bitgen 檢查，並再次經 JTAG 成功燒入 PYNQ-ZU。
- 已製作 PYNQ Linux 用的雙 USB 鏡頭網站部署包；它包含現有 YOLOX、雙鏡頭網站、USB 鏡頭檢查程式與 overlay。
- 尚未在板上驗證：SD Linux、兩支已插入的 USB 鏡頭、YOLOX 推論與電腦瀏覽器畫面。USB 網站會先由 PYNQ 的 CPU 執行原本 Python 流程；目前影像尚未進 FPGA RTL。

### 2026-11-06：SD 卡已重新燒錄並驗證

- 已用 balenaEtcher 將官方 PYNQ-ZU v3.1.1 的 `pynq_zu_2025_09_25.img` 寫入確認過的 16 GB SD 卡；寫入後 Etcher 完整跑過驗證並顯示「燒錄成功」。
- 官方最新版的映像檔名就是 2025-09-25，且和電腦原有 v3.1.1 下載檔完全相同；因此不是因為下載到更舊／更新版本。
- Etcher 完成後已自動卸載 SD 卡。下一步是把卡插回板子、切到 SD、重新上電，確認紅色 PS ERR 是否消失；網站、相機與 FPGA overlay 尚未驗證。
- 本次燒錄與驗證紀錄已同步到共享 GitHub `main`。
## 2026-11-06：PYNQ Linux 與雙 USB 鏡頭實機部署

## 2026-11-06：Vivado USB/DMA 硬體重建（進行中）

## 2026-11-06：Vitis 控制程式已完成電腦端編譯

- 已安裝完整 Vitis Embedded，並把新的 PYNQ-ZU USB/DMA 硬體檔做成 A53 standalone 平台、FSBL 和控制程式 ELF；控制程式實際編譯成功。
- 發現 Windows 工作目錄太長會讓 Vitis 編譯失敗，專案現在提供短路徑的一鍵建置腳本，之後可重現產生 ELF。
- 尚未把這版硬體與 ELF 下載到板子；USB 雙鏡頭、DMA、FPGA 資料流和中斷都還沒有實機 PASS。
- 目前電腦看得到 JTAG 的 FTDI USB 裝置，但掃不到 PYNQ-ZU 晶片；重啟本機 Hardware Server 後仍一樣，所以尚不能下載硬體或控制程式到板子。

### 更新：Vitis 已實際控制 PYNQ-ZU

- 已確認 Vivado 能打開 PYNQ-ZU 的 JTAG target，並成功下載新的 USB/DMA FPGA bitstream。
- Vitis 已在板子的 A53 實際執行控制程式：寫入 frame ID 42 後，GPIO 與 FPGA mailbox 都讀回 42，代表 PS 到 FPGA 的控制線路真的通了。
- 現在尚缺 USB 相機實際取像、DDR/DMA 傳影格與 FPGA 影像運算；目前的 command 會等待尚未接上的影像資料流，這是預期狀態。

- USB 鏡頭會由 PYNQ-ZU 的 PS USB 接收，影格放到 DDR 後才經 DMA 送進 FPGA；不能把 USB 線直接接到 PL 影像腳位。
- 找到既有影像 RTL 在 100 MHz 跑不動，已改為 20 MHz；尚未產生可下載的新 bitstream。
- Vivado 目前被 module-reference 封裝快取錯誤卡住，尚未完成 Vitis 控制程式的實機建置。

- PYNQ-ZU 已可由 `192.168.3.1` 的 JupyterLab 操作；板端確認 Python 3.10.4、NumPy 2.1.5、OpenCV 4.5.4、PYNQ 3.1.1 與 YOLOX 模型皆可用。
- 專題雙鏡頭網站已實際部署至板子；系統與相機 preflight 曾通過，兩支鏡頭分別為 index 0 與 2，均成功讀取 640×480 影格。
- 修正網站對舊版 PYNQ OpenCV 的相容性、PYNQ 網址白名單與相機 index 被 API 重設的問題；網站健康檢查可從開發電腦取得成功回應。
- 啟動即時擷取後，核心回報 USB 頻寬不足並讓兩個 UVC 裝置斷線，目前 `/dev/video*` 不存在。因此尚未完成持續雙鏡頭串流或 YOLOX 人物偵測；需改善 USB 供電／改用不同 root hub 或降低相機頻寬後重新插拔，再重跑 preflight。

- 後續重新插拔後兩支 Logitech C270 再次出現並重跑 index 0/2 的 640×480 preflight PASS；網站以正確設定啟動後仍立刻回報雙鏡頭擷取中斷，未形成持續串流。這再次確認問題在 USB 傳輸資源，尚非軟體安裝或相機索引。
- 已額外嘗試雙路 MJPEG、320×240、10 FPS 的低頻寬模式，仍在同時擷取時中斷；目前不能在網站顯示雙路畫面，必須先改善 USB 實體拓撲／供電。

## 2026-11-06：Vivado USB/DMA 硬體檔完成

- 已把自訂影像 RTL 改成 IP Catalog 元件，避開 Vivado Windows module-reference 快取錯誤。
- 新的 PYNQ-ZU Block Design 已完整通過 Vivado 實作、DRC 和 bitstream，並成功輸出 Vitis 要用的 XSA；時序為正裕量。
- 這是硬體檔完成，不是雙鏡頭影像已跑通。下一步是用 XSA 建 Vitis 控制程式並以 JTAG 上板測試；USB 雙鏡頭同時串流的實體頻寬問題仍待解決。

## 2026-11-06：Vitis 工具環境阻礙已定位

- 已用新的 XSA 實際啟動 Vitis 建 platform，但本機 Vitis 2024.2 缺少完整 embedded flow（包含 `xsct`），且原本的 Lopper 安裝不完整。
- 補齊 Lopper 後，Vitis 已能繼續到 SDT 生成，但仍無法建立 platform；所以 Vitis 控制程式尚未編譯、更沒有上板。
- 下一步是修復／補安裝完整 Vitis Embedded Development 環境，再用同一份已驗證的 XSA 建立 A53 standalone 控制程式。

## 2026-11-06：完整影格 DMA 已上板成功

- 修正 Vivado 的 DMA 長度設定，讓一個完整 640×480 影格可一次從 DDR 傳進 FPGA。
- 新硬體檔與 Vitis 控制程式已經由 JTAG 下載到 PYNQ-ZU，實測 DMA 完成、FPGA 回傳成功，frame ID 42 正確到達硬體。
- 這次用的是 Vitis 產生的合成測試影格，證明硬體資料通路可用；USB 雙鏡頭同時擷取仍受實體 USB 頻寬／供電影響，尚未完成。
## 2026-11-06：測試與文件同步

- 新增保護測試，避免 DMA 傳輸長度設定被改回無法容納完整影格的值。
- 更新 Vivado/Vitis 文件，清楚標示「完整合成影格 DMA 已成功」與「真實 USB 雙鏡頭仍未完成」的差別。
## 2026-11-06：USB 相機控制的正確分工

- Vitis standalone 可以控制 FPGA 與 DMA，但安裝的工具沒有 C270 需要的 UVC 驅動。
- 真實 USB 相機要由 Linux 的 UVC/V4L2 驅動取像；之後 Vitis Linux 程式再把 DDR 影格送進 FPGA。這不需要、也不能把 USB 相機線接到 FPGA 的一般影像腳位。
## 2026-11-06：Vitis Linux UVC 程式元件

- 已新增 A53 Linux 程式原始碼：可從兩支 UVC 相機讀取 640×480 YUYV 影格，轉成 FPGA 使用的雙 RGB packed 格式。
- 已找到正確的 Vitis Linux compiler，成功產生 AArch64 ELF；也尚未放上板子跑。最後還需要 Linux 提供可給 DMA 使用的連續記憶體，再把影格交給已驗證的 FPGA DMA 通路。
## 2026-11-06：切回 Linux 的板子操作

- 板子上的 `JTAG SD` 開關切到右側 `SD`，插著已燒好的 PYNQ SD 卡後重新上電，就能回到 Linux/UVC。
- SD 開機後仍然能接 JTAG，所以之後可同時使用 Linux 相機驅動和 Vivado/Vitis 除錯。
## 2026-11-06：下次上板的一鍵 UVC 檢查

- 新增不靠 Jupyter 的 Linux 檢查腳本：會開兩支 UVC、產生一張 FPGA 格式的雙影格，並確認大小正確。
- 下週切回 SD/Linux 後，直接執行它就能知道相機與 Vitis packing 是否真的正常。
## 2026-11-06：Vitis Linux 一鍵編譯

- 新增一鍵 build script，可重新產生要部署到板子的 AArch64 UVC packer，不需手動設定 compiler。
## 2026-11-11：真實雙鏡頭 USB 頻寬修正

- 板上兩支 C270 與 Vitis Linux 程式都已實際看到；第一次同時開啟時被 Linux 判定 USB 頻寬不足。
- 已將 Vitis 程式改為主動要求較低的 10 FPS，再重新上板測試，不再使用相機預設的高 FPS。

## 2026-11-11：雙鏡頭限制確認與新兩板方向

- 已在板子實測：兩支 C270 都能被 Linux 看見，但同時開始擷取時，第二支相機會被 USB Hub 拒絕。即使已降到 320×240、10 FPS，甚至改用 MJPEG，結果仍相同。這不是儲存空間或 Vivado 程式的問題。
- 因此接下來採用「兩塊 PYNQ-ZU、每塊一支鏡頭」：各自用 Linux 取像與推論，再用 Wi-Fi 傳送人物偵測／追蹤結果。這比在一個共享 USB Hub 上硬撐兩支相機可靠。
- 已新增兩板與 DPU 架構文件。DPU 目前尚未在板上可用：現有 Linux 沒有 DPU driver、VART 或 DPU 裝置，必須先重新做 Vivado DPU 硬體和相配的 Linux 映像。
- 新人物偵測目標定為 YOLOv8；既有程式裡的是 YOLOX，兩者會透過相同輸出介面逐步替換，不會混稱或假裝已經跑在 DPU。

尚未完成：每板單鏡頭長時間測試、第二塊板、Wi-Fi 通訊、DPU 硬體/Linux runtime、YOLOv8 量化與 DPU 人物偵測。

本次實測與架構文件已同步到 GitHub `main`（`8391da8`）。

## 2026-11-11：兩塊板 Wi-Fi 通訊的第一個程式

- 已新增 Linux 可用的兩板人物偵測資料交換程式。它只傳人物框、信心值、追蹤 ID、frame ID 與時間，不會一開始就用 Wi-Fi 傳原始影像。
- 收到的資料會先檢查格式、人物類別和座標是否合理，再交給之後的兩鏡頭比對流程。
- 目前已在本機 TCP loopback 測試通過；尚未在兩塊實體板的 Wi-Fi 上測試，也尚未連到 YOLOv8/DPU。

本項程式已同步到 GitHub `main`（`a1ff8f4`）。

## 2026-11-11：DPU 硬體檔已成功做出

- 用 Vivado 原生 DPU IP 做出 PYNQ-ZU 的 B512 DPU Block Design，不是把 USB 相機的線接到 FPGA 腳位；USB 相機仍由 Linux 處理，DPU 從 DDR 讀取資料。
- Vivado 已實際完成 Block Design 驗證、綜合、placement、routing 與 bitstream。最終時序通過，沒有 errors 或 critical warnings；資源使用約 LUT 27%、BRAM 50%、DSP 11%。
- 這代表「Vivado 硬體檔」已有可重建的 DPU bitstream；尚未代表板上已能跑人物辨識。接下來還需要相配的 Linux DPU driver、VART、記憶體設定、YOLOv8 INT8 `.xmodel`，以及板端實測。

本項已同步到 GitHub `main`（`dbaeb8f`）。

## 2026-11-11：Vitis 的硬體交接檔

- 已用 DPU bitstream 匯出 XSA 硬體交接檔，裡面有 bitstream、硬體描述與 PS 初始化資料，供下一步 Vitis/Linux 建置使用。
- XSA 已實際產生並檢查內容；它只是把 Vivado 硬體交給軟體工具，尚不是 Linux DPU driver、VART 或 YOLOv8 已能運作。

本項已同步到 GitHub `main`（`817a8cc`）。

## 2026-11-11：Vitis 已讀取 DPU 硬體檔

- 完整 Embedded Vitis 已成功把 DPU XSA 建成 A53 platform、BSP 與開機用 FSBL；這證明 Vivado 硬體檔能正確交給 Vitis。
- Vitis 產生的硬體定義已看得到 DPU 控制基址 `0x400000000`。
- 這仍只是 Vitis 平台建置成功，未做板端下載，也不是 Linux VART 或 YOLOv8 推論完成。

## 2026-11-11：DPU Linux 上板前檢查已準備

- 已加入一個會在 PYNQ Linux 板上執行的檢查程式：它會確認 DPU 的 device tree、driver 裝置、記憶體、VART/XIR、`xdputil`、模型檔與 USB 相機是否都到位。
- 查到目前 Windows 只有 Vitis，沒有能建立相配 Linux 映像的 PetaLinux。現有 SD image 也尚未有 DPU runtime，所以暫不下載 DPU bitstream 或重刷 SD 卡。
- 尚未完成：matching Linux image、實際上板驗證、YOLOv8 INT8 模型與 DPU 人物辨識。

本項檢查工具與說明已同步到 GitHub `main`（`61abcdf`）。

## 2026-11-11：SD 板端兩鏡頭重新實測

- 此次實板結果已同步到 GitHub `main`（`6fd075b`）。
- 板子已由 SD 開機並可 SSH；兩支 C270 都被 Linux 與 OpenCV 辨識，且帳號已取得相機群組權限。
- 每支相機單獨在低畫質/低幀率下可讀影像；兩支同時讀取時第二支失敗，kernel 明確回報 USB hub 頻寬不足。
- 所以目前不能把「一板兩鏡頭串流」列為完成；後續兩板各一鏡頭是必要方案。Wi‑Fi 尚未設定，DPU/VART/YOLOv8 也尚未在板上可用。

## 2026-11-11：YOLOv8 已在板上以 CPU 跑通

- 兩板資料封包 producer 已同步到 GitHub `main`（`bf2a0fb`）。
- 正樣人像驗證紀錄已同步到 GitHub `main`（`bf9a830`）。
- pipeline/bundle 的 YOLOv8 接入已同步到 GitHub `main`（`fac5fee`）。
- 此次 YOLOv8 程式與實板驗證已同步到 GitHub `main`（`fbed6fe`）。
- YOLOv8n 已改用 ONNX Runtime 在 PYNQ 實跑一張 C270 影格，約 1.017 秒完成一次推論；這次畫面沒有偵測到人，因此只證明相機到模型的流程可執行。
- PYNQ 的 OpenCV 不能讀這份 YOLOv8 ONNX，已改由 ONNX Runtime CPU fallback；DPU/VART 加速、YOLOv8 INT8 `.xmodel` 與正樣本人像驗證仍未完成。
- 既有追蹤程式已預設改用 YOLOv8，並在板子上從相機影格跑完整 pipeline 成功；尚未看到人物正樣本，故還不能聲稱人物框與追蹤成果已驗證。
- 補充：板端用公開人物測試圖成功偵測到 4 人，證明 YOLOv8 人物框可輸出；這不是現場相機人物測試，也不是 DPU。
- 新增兩板資料傳送程式：現在可把每板的 YOLOv8 人物框傳給另一端，不傳影像。已在同一塊板 loopback 成功，Wi‑Fi 與第二板仍待實測。

## 2026-11-11：DPU Linux 映像的環境阻礙

- 此環境檢查已同步到 GitHub `main`（`e9413a3`）。
- 這台 Windows 沒有 PetaLinux、Docker 或已安裝的 WSL Linux；所以目前不能產生相配 DPU driver/VART Linux image。
- Vivado 與 Vitis 的硬體交接已完成，但這不等於 DPU 可以上板推論；仍需受支援的 Linux/PetaLinux build host。

## 2026-11-11：可先完成的主機檢查

- 不碰 AMD 下載表單的情況下，YOLOv8/VART 介面、兩板封包、Wi-Fi 前檢查和 DPU 建置規則共 22 項測試都通過。
- Vitis 也重新成功編譯 USB C270 的 Linux 封包程式；這只表示程式能交叉編譯，不是 DPU 或兩台板子的實測完成。
- 這台 Windows 尚不能直接建立 Linux 開發環境：WSL 啟用需要系統管理員權限，Docker 和 PetaLinux 仍未安裝。AMD 下載、Linux/PetaLinux、DPU driver/VART 和 `.xmodel` 仍是後續工作。

## 2026-11-11：避免空模型誤判

- DPU 上板前檢查已補強：即使有人放了一個名稱正確但內容是空的 `.xmodel`，檢查也會失敗，不會誤報模型已部署。
- 新增檢查後，目前全部 24 項離線測試通過；這是檢查工具品質改善，還不是 DPU 推論完成。

## 2026-11-11：Vivado 硬體檔與 Vitis 控制檔重新做出

- USB C270 的 Block Design 已從目前程式重新建立、實作並輸出 bitstream/XSA。時序通過、所有可路由連線都完成，沒有 routing error。
- 新 XSA 已成功讓 Vitis 產生 A53 控制 ELF；Vitis 取得的 DMA、frame ID、PL mailbox 位址與 Vivado 對得上。
- USB 相機仍是 PS USB/Linux UVC，不是 FPGA 腳位；這份控制 ELF 目前是合成影格的 DMA/PL 驗證。兩支 C270 同時 Linux 串流、DPU/VART/YOLOv8 及兩板 Wi-Fi 尚未完成或驗證。

## 2026-11-11：Vitis 控制程式單元測試通過

- 找到 Vitis 內附的 C 編譯器，已實際執行控制程式單元測試並通過。
- 測試確認 Vitis 寫入 frame ID、人物框資料與最後啟動控制命令的順序正確；仍不是板上相機或 DPU 測試。

## 2026-11-11：硬體交接檔自動檢查

- 新增可重跑檢查，會確認 Vivado 的 XSA 裡真的有 bitstream、硬體描述與必要初始化檔，也會核對 Vitis 要控制的三個位址。
- 對本次重新產生的 XSA 已通過；這讓後續重做硬體時能及早發現交接檔不完整，但不是板上執行完成。

## 2026-11-11：UART 最新實板狀態

- 已透過 UART 唯讀確認板子正常在跑 Linux，四個相機裝置都存在。
- 目前 Linux 還沒有 DPU driver/VART/XIR/`xdputil`，Wi‑Fi 也還沒連線；所以不能稱為 DPU 人物辨識或兩板互傳已完成。
- 本次只讀狀態，沒有改板子、SD 卡、相機或網路。

## 2026-11-11：兩支 C270 的實體連線確認

- UART 實測確認目前接的是兩支 C270，不是四支；每支相機會提供兩個 Linux video 節點。
- 兩支共用同一個 USB 2.0 hub，這也解釋了先前同時串流被頻寬限制擋住的結果。
- Wi‑Fi MAC 目前是全零且介面未啟用，還不能設定成兩板互傳。

## 2026-11-11：Wi‑Fi 驅動實際狀態

- 板子的 Wi‑Fi SDIO 硬體和驅動都已成功啟動，不是完全缺少 Wi‑Fi 功能。
- 開機紀錄曾顯示 `regulatory.db` 載入失敗，但後續確認檔案與套件其實都已安裝；現階段不能判定需要重裝。仍必須在真實 SSID 和第二塊板環境啟用 Wi‑Fi 後，再看是否真的影響連線。

## 2026-11-12：PetaLinux 已下載完成

- 已確認 PetaLinux 2024.1 installer 下載完成，約 3.07 GiB，並已記錄 SHA-256。
- 它尚未執行或安裝。下一步仍需要在 Windows 管理員權限下建立 Linux/WSL 環境，再安裝 PetaLinux。

## 2026-11-12：WSL 已啟用，等待重開機

- Windows 的 WSL 與虛擬機平台功能已成功啟用。
- Windows 要求重開機才會生效；Ubuntu 和 PetaLinux 尚未安裝。請先儲存目前 Vivado／Vitis 的工作，確認後才能重開。

## 2026-11-12：PetaLinux Linux 主機已可用

- WSL2、Ubuntu 22.04 與 PetaLinux 2024.1 已安裝完成；PetaLinux 的建立、設定與建置命令都可使用。
- PetaLinux 裝在 WSL Linux 路徑，不在專題 Git 內；安裝時產生的錯誤暫存檔已隔離，專題工作樹保持乾淨。
- DPU 建置檢查已確認 PetaLinux 與正確 DPU 架構檔可用；目前只剩 Docker/Vitis AI 編譯環境，以及重新以 2024.1 建硬體這兩項主機端缺口。
- 已建立 ZynqMP 的 PetaLinux 專案骨架，但尚未放入不相容的 2024.2 硬體交接檔。
- 仍未完成：2024.1 matching 硬體/XSA、PetaLinux 映像、DPU/VART/YOLOv8 模型部署、燒錄 SD、兩板 Wi-Fi 與實機人物辨識。現有 Vivado/Vitis USB-video 成果仍是 2024.2，不能直接當成 DPU runtime 完成。
## 2026-11-12：Docker 與 Vitis AI 編譯器可用

- Docker Desktop 與固定 Vitis AI 3.5 容器已可用；啟用 container 的 `vitis-ai-pytorch` 環境後，`vai_c_xir` 編譯器已實測存在。
- 正式 DPU 映像仍需 matching 2023.1 Vivado/PetaLinux/XSA。

## 2026-11-13：Vivado 2022.1 安裝狀態更正

- 安裝視窗停在 76% 的收尾步驟，並顯示安裝後處理失敗，所以不能說安裝器已完整完成。
- 但 Vivado 2022.1 和 Vitis 2022.1 的主要命令都能實際啟動，Zynq UltraScale+ 裝置資料也已存在。
- 接下來會用獨立的硬體重建測試確認這個安裝是否足夠；在驗證完成前，不把它說成完整安裝成功或已完成 DPU 硬體。

## 2026-11-13：2022.1 Block Design 已重新建立

- Vivado 2022.1 已真正建立 PYNQ‑ZU 的 USB/DDR/DMA Block Design，並通過其設計驗證。
- 2022.1 的 PS IP 版本與 2024.2 不同，程式已改成自動選相容版本；DMA、frame ID、控制 mailbox 的三個位址也已固定，Vitis 可繼續沿用控制合約。
- 這仍不是完成硬體：尚未用 2022.1 synthesize、產生 bitstream/XSA、建 Vitis 控制檔或上板測試。

## 2026-11-13：2022.1 硬體檔已完成輸出

- 2022.1 已完成 synthesis、implementation、bitstream 和給 Vitis 用的 XSA。
- 最終時序通過，所有需要路由的網路都已完成；XSA 也已自動檢查，Vitis 要使用的三個硬體位址正確。
- 這只完成了可交接的硬體檔，尚未把它下載到板子，也還不是兩鏡頭、DPU 或 YOLOv8 實機結果。

## 2026-11-13：Vitis 2022.1 控制程式可編譯

- Vitis 2022.1 已從新的 2022.1 XSA 產生 A53 的硬體位址標頭；三個控制位址都和 Vivado 硬體相符。
- 已用 Vitis 2022.1 的 AArch64 編譯器實際產生控制 ELF。這證明 USB-video 控制程式可用這份 2022.1 BSP 編譯。
- Vitis 的圖形/後端在「自動建立/建置應用專案」時通訊中斷；但已成功把控制程式原始碼匯入應用目錄。已只關閉本次產生的背景程序；自動化腳本已加入，但尚未能宣稱它在此主機完整跑完。
- 尚未把 ELF 或 bitstream 下載到板子，沒有驗證相機、DMA、DPU、YOLOv8 或 Wi-Fi。

## 2026-11-13：DPU 硬體 Block Design 已在 2022.1 重建

- 已用官方 DPU 4.0 原始碼，在 Vivado 2022.1 真正建立 PYNQ-ZU 的 B512 DPU Block Design。
- DPU 的控制、記憶體通道和中斷都已連到 PS；USB 相機仍由 Linux 的 PS USB 接管，不會錯接到 FPGA 腳位。
- 還沒有開始完整綜合、產生新的 DPU bitstream 或上板。Linux DPU driver、VART、YOLOv8 模型和兩板 Wi-Fi 也尚未完成。

## 2026-11-13：DPU B512 硬體檔已在 2022.1 完整輸出

- 已完成 DPU 的 synthesis、implementation、bitstream 與含 bitstream 的 XSA 匯出；這份硬體是官方 DPUCZDX8G 4.0、B512 設定、PYNQ-ZU 的 2022.1 實際建置結果。
- 最終時序檢查沒有 setup、hold 或 pulse-width 違反；bitstream 為 7,797,815 bytes，XSA 為 2,628,256 bytes，並含硬體描述與 PS 初始化資料。
- 這代表 FPGA 硬體交接檔已可供下一步 Linux/PetaLinux 整合；尚未寫入板子或 SD 卡，Linux DPU driver、device tree、VART/XIR、YOLOv8 `.xmodel`、相機 DMA 及兩板 Wi-Fi 都仍未實機驗證。

## 2026-11-13：2022.1 Linux DPU 整合已可預先準備

- 已更正文件：目前 Vivado 與 Vitis 都是已實際可用的 **2022.1**，DPU B512 也是以 2022.1 完成；不是 2024.2。
- 新增可重跑的 PetaLinux staging 工具。等正確的 PetaLinux 2022.1 安裝後，它會把 AMD 官方 DPU 4.0 的 kernel driver patch、DPU kernel config 與 VART/XIR recipes 放進外部 PetaLinux project，且保留原本 rootfs 設定。
- 工具已用官方 DPU reference 實跑驗證。現有 PetaLinux 是 2024.1，工具會明確拒絕拿它來建這份 DPU 4.0 image；仍需要下載/安裝 PetaLinux 2022.1，之後才能產生 Linux image、燒錄 SD 和做板端 DPU inference。

## 2026-11-13：YOLOv8 已真正編譯給 B512 DPU

- YOLOv8n 已在 Vitis AI 2.5 實際完成量化並輸出 xmodel，接著也成功編譯給這塊 PYNQ-ZU 的 B512 DPU。
- 原始 YOLOv8 的一個 C2f 寫法不能被 Vitis AI 2.5 處理；已用等價的通道切片修正，三個偵測輸出頭都已確認產生。
- 但目前還不是可上板的人物辨識：SiLU activation 造成編譯後切成 60 個 DPU 小段與 CPU 小段，不能用現有的單一 DPU runner。下一步要把模型改成更適合 B512 的 activation / execution graph，並在板上驗證 DFL decoder。

## 2026-11-13：LeakyReLU 的 DPU 相容性已驗證

- B512 支援 LeakyReLU；把 YOLOv8 的 SiLU 改為 LeakyReLU 後，編譯碎片從 60 個 DPU 小段降為 9 個。
- 這是硬體相容性探測，沒有採用作為人物辨識模型。實際部署仍使用別人已訓練好的官方 Ultralytics YOLOv8n；以 GraphRunner 執行它的 DPU 與 CPU 子圖，不需要自行訓練模型。

## 2026-11-13：YOLOv8 的硬體輸出解碼已完成

- 已能把 DPU/GraphRunner 的三個 YOLOv8 raw output heads 轉回 person 方框，包含 NMS 與原始影像座標還原。
- 尚待 PetaLinux/VART GraphRunner 實機執行；目前是有測試的軟體 decoder，不是板端推論驗證。

## 2026-11-13：PetaLinux 已補上 Python GraphRunner 設定

- Linux image 的準備工具現在會啟用 Vitis AI Library 的 Python bindings，未來可讓 Python 的 YOLOv8 程式直接使用 GraphRunner。
- 尚未真正建 image 或寫入 SD；這是避免之後 rootfs 少套件的預先設定。

## 2026-11-13：目前 SD 卡仍不是 DPU Linux

- 板子可看到四個相機節點，但沒有 DPU device，VART、XIR 與 Python GraphRunner 也都不存在。
- 新的部署檢查會把 GraphRunner 列為必要條件，避免把現在的 PYNQ 2024.1 SD 卡誤用於 DPU bitstream。

## 2026-11-13：YOLOv8 到 DPU 的橋樑已補上

- YOLOv8 仍然直接使用別人已訓練好的原始模型；沒有把它重寫成 Verilog，也沒有另訓練替代模型。
- Vivado 的 DPU 硬體、Vitis AI 的整張模型執行圖、以及相機影格/人物框之間，現在有一個 GraphRunner 橋樑。它會把相機影格交給原始 YOLOv8 的 CPU+DPU 子圖共同執行，再把三個輸出頭交給現有的人物框解碼器。
- 此橋樑目前已通過 10 個電腦端合約測試；尚未能說已上板成功，因為現在 SD 卡沒有 DPU/Vitis AI GraphRunner runtime。完成相容 Linux image 並換 SD 後，才可做真正的相機→DPU→YOLOv8 人物辨識驗證。

## 2026-11-13：DPU 人物框已能直接接既有追蹤流程

- 修正了一個上板才會觸發的資料格式問題：DPU/GraphRunner 回來的 YOLOv8 人物框現在會直接進入既有追蹤、人物特徵與兩板封包流程，不會被錯當成舊 YOLOX 格式。
- 電腦端回歸測試通過；仍待相容 DPU Linux image 的實機驗證。

## 2026-11-13：一塊板子接兩支 C270 的實機結果

- 兩支鏡頭可以各自讀取，但同時讀取時永遠只有一支有畫面；即使降到 160×120 的 MJPEG、10 FPS 也一樣。
- 已加入可重跑的板端檢查指令，這次實測確定不通過。因此目前不能把一板雙鏡頭說成完成；可靠方案是兩塊板子各一支鏡頭，再由 Wi-Fi 傳人物偵測資料。

## 2026-11-13：板子的 Wi-Fi 已確認可以工作

- 已成功啟用板上的 Wi-Fi，硬體 MAC、driver 與無線掃描都正常；可掃描到附近基地台。
- 尚未連線，因為板上沒有儲存任何 Wi-Fi 設定，也沒有第二塊板子可測試傳資料。之後只要提供授權的 SSID／密碼並準備第二塊板子，即可進行兩板 TCP 實測。

## 2026-11-13：JTAG 尚不能下載硬體檔

- 電腦有偵測到板子的 FTDI USB/JTAG-UART cable，但 Vivado 目前掃不到 FPGA JTAG target。
- 因此沒有冒險把 bitstream 或 Vitis 控制程式下載到板子；要等 Vivado 的 target 清單真正看得到板子後，才可進行 JTAG 硬體實測。

## 2026-11-13：找到 JTAG target 空白的首要檢查點

- PYNQ-ZU 的 UART/JTAG 可共用 FTDI cable，但官方手冊要求要做 JTAG boot/download 時，板上的 JTAG/SD switch 必須切到 **JTAG 左側**。
- 現在板子為了跑 SD 卡 Linux 而在 SD 右側。下次要測 Vivado/Vitis 的 bitstream 時，需關機後切到 JTAG、開機並確認 Vivado 看得到 target；測完要回到 SD 才能開 PYNQ Linux。

## 2026-11-13：PetaLinux 2022.1 已可在 WSL 使用

- 已下載並安裝與 Vivado/Vitis/DPU 2022.1 相容的 PetaLinux 2022.1，且命令可正常載入。
- 2024.1 安裝保留不動；新工具放在獨立的 2022.1 資料夾。
- 下一步是以 DPU 的 XSA 建立 Linux 專案、產生 SD image；尚未換 SD 卡或在板子上跑 DPU/YOLOv8。

## 2026-11-13：DPU 硬體已真正透過 JTAG 載入板子

- PYNQ-ZU 切到 JTAG 後，Vivado 已經看得到 FPGA 與 ARM debug target。
- DPU B512 bitstream 已載入 FPGA，Vivado 回報啟動成功。
- 這是暫時配置，關機或切回 SD 就會消失；尚未證明 Linux、相機或 YOLOv8 推論，仍需建立相容 SD image。

## 2026-11-13：Vitis 交接完成，正在重建含 DPU runtime 的 Linux image

- Vivado 2022.1 產生的 DPU 硬體檔已成功交給 Vitis 2022.1，platform 檔已實際產生。
- PetaLinux 已成功建過一次最小 Linux image，也確認 device tree 內有 DPU；但第一次 image 尚未含 VART/XIR 等 YOLOv8 所需 runtime。
- 已修正 image 套件納入方式，新的重建正在背景進行。完成後仍要由使用者實體確認 SD 卡、切回 SD 開機，才能驗證真正的相機→DPU→YOLOv8。

## 2026-11-13：可開機的 DPU Linux SD 映像已產生

- 含 DPU driver、VART、XIR、Vitis AI Library 的 PetaLinux 2022.1 映像已完整建置成功。
- 已產生 `BOOT.BIN` 和約 6.1 GB 的 SD 映像；並確認其開機分割區真的有 `BOOT.BIN`、`image.ub`、`boot.scr`。
- 映像內也有 Python 的 GraphRunner bridge；尚待上板實際 import。
- 還沒有寫入實體 SD 卡，也還沒有讓板子用此映像開機。因此 DPU、YOLOv8、相機的實機成功尚未宣稱完成。

## 2026-11-13：映像已加入相機 Python 相依套件

- 發現專題程式要使用 NumPy 和 Python OpenCV，因此已把它們加入 DPU Linux 映像並重建。
- 已檢查新版映像內有 ARM64 NumPy 與 OpenCV Python 模組，現在具備執行相機影格處理加 GraphRunner 的軟體相依條件。
- 仍需將新版映像寫入 SD、讓板子從 SD 開機後，才能實測相機→DPU→YOLOv8。

## 2026-11-13：正在把 USB 相機驅動加入 kernel

- 檢查發現映像還沒有啟用 C270 所需的 USB/UVC 相機 kernel driver，因此已補上設定。
- 第一次完整重建發現 Xilinx kernel 的 USB host-only 設定有連結錯誤，因此沒有採用那個失敗成果。
- 已改用仍支援 host 的 USB dual-role 設定，現在正在重新完整編譯；尚未結束前，舊 SD 映像不應拿來宣稱可讀取相機。

## 2026-11-13：含 USB 相機驅動的最終 SD 映像已完成

- USB/DWC3 的修正後重建已完全成功，新的 DPU Linux 映像已同時包含 DPU runtime、GraphRunner 所需套件、NumPy、OpenCV，以及 C270 所需的 UVC/V4L2 驅動。
- 已重新產生 6.1 GB 的 SD 映像，並確認開機分割區有 `BOOT.BIN`、`boot.scr`、`image.ub`。
- 還沒有寫入任何實體 SD 卡，也沒有讓板子用新映像開機；因此相機、DPU、YOLOv8 的實機結果尚未完成。下一個需要人在場的步驟是明確確認要覆寫的 SD 卡後再寫入。

## 2026-11-13：YOLOv8 DPU 模型已放入新的 SD 映像

- 原始 YOLOv8n 的 DPU B512 模型已放進 SD 映像的 `/opt/models/yolov8n_b512.xmodel`；它不是另外要手動複製的模型檔。
- 新 SD 映像已重新建置、核對模型雜湊與開機檔，並提供「單支 USB 相機 → GraphRunner → 原始 YOLOv8」的板端測試指令。
- 這個測試即使場景沒有人也能驗證 DPU 推論有執行；人物偵測與雙鏡頭仍必須在新 SD 開機後實測。現有一板兩支 C270 的同時串流仍未成功，未把它誤列為完成。

## 2026-11-13：可燒錄的最終 SD 映像已匯出

- 最終映像已放到 `C:\pynq_zu_dpu_2022_20261113\sd_image_20261113\pynq_zu_dpu_yolov8_usb_2022_1.wic`，大小約 6.1 GB，並已核對與 PetaLinux 原始映像的雜湊相同。
- 目前電腦沒有偵測到可移除的 SD 卡，因此沒有燒錄或格式化任何磁碟。插入 SD 卡後，仍需明確確認目標磁碟才可進行下一步。

## 2026-11-13：第一階段改為一板一鏡頭的人物追蹤

- 現在先以一塊板、一支鏡頭完成 DPU YOLOv8 人物追蹤；兩塊板各一鏡頭與 Wi-Fi 傳資料保留為第二階段。
- 新的板端測試會連續讀取單支相機的三張影格，用 DPU 跑原始 YOLOv8，再送進既有追蹤器並輸出追蹤 ID 數量。
- 目前這仍是已準備好的程式與映像，尚未從新 SD 在實體板上執行。

