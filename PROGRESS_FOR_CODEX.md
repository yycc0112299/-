# 專題狀態與交接記錄（供 Codex）

## 2026-11-12：USB-video overlay 的板端下載／control-MMIO 檢查已接進 deployment bundle

- 新增 `person_tracking/verify_pynq_zu_usb_video_overlay.py`。它要求同目錄有 exact `pynq_zu_usb_video.bit/.hwh`、呼叫 PYNQ `Overlay(download=True)`，只對 frame-ID GPIO `0xA0010000` 與 mailbox frame-ID offset `0xA0020004` 作寫入／讀回，最後清回零；絕不寫 mailbox CONTROL，故不送 DMA command、不開始 UVC capture。host fake-MMIO tests 驗證正常流程與缺少 HWH 的 fail-fast 行為，2/2 PASS。
- `prepare_pynq_dual_bundle.py` 現包含這個 verifier，並新增 `--usb-video-overlay-dir`，把 matching pair 放入 archive 的 `overlay_usb_video/`。`deploy_pynq_zu.ps1` 新增 `-UsbVideoOverlayDir` 及 opt-in `-RunUsbVideoOverlayCheck`，在 authenticated transfer/unpack 後才將 USB pair 複製到 verifier 旁執行。PowerShell parse PASS；實際建立 external tar 並確認 verifier、bit、HWH 三項都在 archive。這條新流程與舊 `pynq_zu_yolox` bring-up overlay 明確分開。
- 未有可用 board authentication 時沒有 upload、Overlay download 或 MMIO 實機執行；這不是 UVC、DMA-BUF、雙鏡頭、DPU/YOLO 或 Wi-Fi 成功證據。tar 與 binary 都只留 external `%TEMP%`，不入 Git。

## 2026-11-12：USB-video 的 PYNQ Linux overlay 已可從正確 Vivado implementation 安全封裝

- 新增 `fpga/prepare_pynq_zu_usb_video_overlay.ps1` 和 static safety contract test。工具要求使用者提供 external Vivado build directory，只讀 `pynq_zu_usb_video_wrapper.bit` 與同一 BD 的 `pynq_zu_usb_video.hwh`，輸出同 stem 的 `pynq_zu_usb_video.bit/.hwh`，並輸出兩個 SHA-256。它不含 SSH/SCP/bootgen，絕不連線板子、寫 SD 或改 boot configuration。
- test-first：script 未建立時 test 如預期 FAIL；實作後 1/1 PASS。實際從 `C:\pynq_zu_usb_video_rebuild_20261111` 封裝到 external `%TEMP%` staging directory；bit=7,797,821 bytes、HWH=333,915 bytes，SHA-256 分別為 `e92ee2cc3f7493ea141e7e363a80893b393225e744562c33093b1011e34cd6c2` 與 `ac5497244a55b17810c6bc318dd050fec159c3e84005afe3eb91ce31b375c6b5`。
- 這提供未來 SD-boot Linux `Overlay()`／DMA driver bring-up 的正確 hardware pair，不證明它已被上傳、下載至 PL、UVC capture、DMA-BUF handoff、two-camera、DPU/YOLOv8 或 Wi-Fi 已運作。external staged binary 不入 Git。

## 2026-11-12：以完整 Embedded Vitis 2024.2 重新建立 USB-video A53 平台與 ELF

- 先前使用 `C:\Xilinx\Vitis\2024.2` 建 platform 時雖回傳 process exit 0，實際卻因 `Invalid Lopper Installation Directory path 'null'` 失敗；不可把該 exit code 當成功。唯讀比對既有成功 workspace 的 BSP metadata 後，找到完整安裝為 `C:\Xilinx_Embedded_2024_2\Vitis\2024.2`：含 `data\embeddedsw` 及可執行的 Lopper 1.2.0。另一套的自動 lopper 安裝紀錄也證實缺少 requirements 檔。
- 使用完整 Embedded Vitis，並以新、未重用的 external workspace `C:\pynq_vitis_usb_video_reverify_20261112b` 重跑 tracked `vitis/pynq_zu_usb_video/build_vitis_embedded.py`。實際生成 `pynq_zu_usb_video_app.elf`（352,344 bytes）。再以 tracked handoff verifier 對 external XSA 與這次 Vitis generated `xparameters.h` 驗證 PASS；DMA=`0xA0000000`、frame-ID GPIO=`0xA0010000`、mailbox=`0xA0020000`。verifier unit tests 3/3 PASS。
- 此為 host-side platform/application rebuild 與 hardware address contract 證據；workspace、ELF、Vitis logs 均為 external artifact，不入 Git。未 JTAG program、未改 SD/PL，也沒有 Linux UVC、DMA-BUF、two-camera、DPU/YOLOv8 或 Wi-Fi 實機驗證。

## 2026-11-12：Vivado-native USB Block Design reopen／address verification 已實際通過

- 新增 `fpga/verify_pynq_zu_usb_video_bd.tcl`，需要 external `PYNQ_ZU_BUILD_DIR`。它只開啟既有 `.xpr`／`.bd`、呼叫 Vivado `validate_bd_design`、從 `zynq_ultra_ps_e_0/Data` address space 檢查 `axi_dma_0=0xA0000000`、`frame_id_gpio_0=0xA0010000`、`yolox_video_rtl_0=0xA0020000`，輸出 `PYNQ_ZU_USB_VIDEO_BD_VERIFY_PASS`。不 export／implementation／program hardware。
- test-first：Tcl source contract test 先因檔案缺失 FAIL；實作後 1/1 PASS。實際以 Vivado 2024.2 batch 開啟 external `C:\pynq_zu_usb_video_rebuild_20261111` project，IP repo（含 packaged `dual_camera_yolox_axis`）成功載入，BD 成功讀入。`validate_bd_design` 表示設計已有 validated status；三個實際 address check 都 PASS，Vivado exit code=0。
- 外部 session log 為 `%TEMP%\vivado_usb_bd_verify_20261112.log`，不入 Git。此證據證實本機的 Vivado project/BD 可重新開啟且控制連線 address 正確；不是 Linux UVC capture、DMA-BUF/AXI ownership、PL programming、two-camera simultaneous 或 DPU inference 驗證。

## 2026-11-12：PYNQ SD Linux 的 SSH transport 可達，但目前無有效唯讀登入憑證

- Windows 對 `192.168.3.1:22` 的 TCP check PASS，表示目前 Composite/SSH transport 有回應。為避免 interactive terminal 阻塞，host 安裝 user-local Python `paramiko` 5.1.0，並以使用者先前提供的 `xilinx` 預設登入資料嘗試**一次** password authentication。
- 結果為 `paramiko.ssh_exception.AuthenticationException: Authentication failed.`。因此 remote command 沒有開始執行；沒有讀取板端 video/DPU/Wi-Fi 狀態，也沒有寫入 SD、PL、檔案、帳戶或網路。先前 shell 的 BatchMode 也曾得到 `Permission denied (publickey,password)`，兩者一致。
- 後續要再做板端 runtime check 時，需可用的既有 SSH key 或使用者提供／在本機互動輸入的目前密碼；不可猜測替代密碼。`paramiko` 是本機 user-site support dependency，不進 Git，也不構成 target Python runtime。

## 2026-11-12：DPU artifact identity gate 已實作並驗證現有 B512 hardware

- 新增 `vitis/pynq_zu_dpu/linux/verify_dpu_artifact_contract.py`。它唯讀讀取 DPU `component.xml`、generated `arch.json`、bitstream、XSA，解析 DPU IP version 和 hex fingerprint、產生四個 SHA-256，並且缺檔／無效 metadata 時 FAIL。此 gate 不將外部絕對路徑或 binary 放進 Git。
- test-first：synthetic complete artifact contract test 先因 module 不存在 FAIL；實作後 1/1 PASS。實際使用 external native build 實跑 PASS：DPU IP=`4.0`、fingerprint=`0x101000016010400`、component SHA-256=`70e6c6c4923b872d907d9b007c0308393eda30bbc0a30e515843b630f329fb3d`、bitstream=`1e173c9a707d050defca9a4d7235e8f2e51e680fd40040d976256b24ee46e29e`、XSA=`8b0f59c19d239de34dbe5366eb61f826a299c9caae78a671738407addeb9cc57`。
- 嚴格界線：hash/metadata identity 不驗證 bitstream 已燒入 PL、XSA Linux device tree、driver/VART、model compatibility 或 inference。未改 Vivado project/PL/SD/board。這是後續 2022.1 image/model deployment 防止選到錯 artifact 的證據記錄。

## 2026-11-12：兩板 PYNQ runtime bundle 已補齊 Wi-Fi／VART 元件並實際封裝驗證

- `live_site/prepare_pynq_dual_bundle.py` 將 runtime file list 提取為 `runtime_sources()`，bundle 現額外包含 `person_tracking/pynq_wifi_peer_preflight.py` 和 `person_tracking/assets/yolov8_vart.py`。這使 deployed CPU two-board Wi-Fi readiness gate 與未來 opt-in DPU backend source 隨同同一套板端程式，不會在 target import 時缺檔。
- test-first：新增 bundle contract test 後因 `runtime_sources` 不存在而 FAIL；最小實作後 test PASS。完整 person tracking tests 22/22 PASS。實際建立 tarball 時首次選 `C:\` root output 得 `PermissionError`；ACL 診斷確認 root 沒有一般 file-create 權限、`%TEMP%` 為使用者 FullControl，改用 `%TEMP%` 的 unique path 後 bundle 成功，`tar -tzf` 確認上述兩個檔案都在 archive。
- 外部驗證 artifact 為 `C:\Users\dsic\AppData\Local\Temp\pynq_bundle_validation_20261112120349.tar.gz`，不入 Git；沒有 SCP/upload、未改板子/SD/Wi-Fi。這只保證部署包包含 source，不證明 target VART 或 two-board Wi-Fi 已運作。

## 2026-11-12：兩板 Wi-Fi 文件已修正為可全雙工的 one-camera-per-board 啟動流程

- 更新 `person_tracking/README.md`：舊文字仍說 VART decoder 未接至 `pipeline.Detector`，現已改為實際 opt-in `PERSON_DETECTOR=yolov8_vart`／`PYNQ_VART_XMODEL` contract，並保留 `PYNQ_VART_STANDARD_OUTPUT=1` 必須先對真實 xmodel output 驗證的安全界線。
- 新增 full-duplex two-board deployment sequence：A/B 各自先啟動 `peer_protocol.py receive`、分別輸出 `/tmp/peer_from_<other>.json`，再在**兩台都** Wi-Fi preflight PASS 後，各以自己的 `--board-id`、`--camera` 和對方實際 IP 啟動 `pynq_yolov8_peer.py`。不將相機 index、IP、SSID 或 output path 硬寫到共享程式碼。
- 這只是可重跑操作文件，尚未擁有第二板／授權 Wi-Fi topology 或實機 full-duplex run；也未改 Wi-Fi、板子、SD、PL 或模型。現有 protocol loopback/retry tests 不能取代兩板驗證。

## 2026-11-12：Vivado USB Block Design 與 Vitis 控制位址已作實際交叉驗證

- 擴充 `fpga/verify_pynq_zu_usb_video_handoff.py`：除 XSA archive/HWH 必要物外，現在可收 Vitis auto-generated `xparameters.h`，要求 `XPAR_AXI_DMA_0_BASEADDR`、`XPAR_FRAME_ID_GPIO_0_BASEADDR`、`XPAR_YOLOX_VIDEO_RTL_0_BASEADDR` 分別等於 Vivado hardware contract 的 `0xA0000000`、`0xA0010000`、`0xA0020000`。CLI 用 `--xparameters` 啟用；unit tests 3/3 PASS。
- 實際用 external 已完成 Vivado XSA `C:\pynq_zu_usb_video_rebuild_20261111\pynq_zu_usb_video.xsa` 與 Vitis standalone platform generated header 跑 verifier，得到 `PYNQ_ZU_USB_VIDEO_XSA_PASS`；HWH 與 Vitis header 的 DMA/GPIO/mailbox 位址全相符。這是具體證據，證實本專案的 USB-camera Block Design export → Vitis generated platform → C controller macros 控制面一致。
- 限制：這仍是 hardware handoff/build artifact 檢查；未重新跑 Vivado implementation、未 JTAG program／改 SD，也不取代 Linux UVC、DMA-BUF ownership、雙 C270 simultaneous 或 DPU/YOLO inference 實機驗證。external XSA/Vitis workspaces 不入 Git。

## 2026-11-12：既有 Detector 已加入 opt-in `yolov8_vart` DPU backend

- `person_tracking/pipeline.py` 的 `Detector` 現支援 `PERSON_DETECTOR=yolov8_vart`。必須明確提供 `PYNQ_VART_XMODEL=/path/to/model.xmodel`；不存在或非 `.xmodel` 時明確失敗。它會 hash artifact、經 `VartYoloV8.from_xmodel()` 建立 VART runner，並把偵測結果送進既有 histogram/tracker/Wi-Fi packet flow。既有 default 仍為 CPU `yolov8`，`yolox` 仍是 explicit legacy backend。
- 為避免假設 compiled output，預設 `yolov8_vart` 只可取 tensor 而 `detect()` 會因未註冊 decoder 停止；只有使用者明確設 `PYNQ_VART_STANDARD_OUTPUT=1` **且實際 `.xmodel` 已驗證為單 raw standard output**，才綁定 `standard_yolov8_decoder()`。這避免把 feature-map/multi-head DPU graph 誤解碼為人物框。
- test-first：新 backend-without-xmodel test 先收到 unsupported backend，再實作 opt-in route；backend tests 3/3、完整 person_tracking 22/22 PASS。未載入 xmodel、未 import target VART、未改板子。真實 DPU route 仍等待 2022.1 Linux image、driver/runtime、compiled `.xmodel` 和 on-board validation。

## 2026-11-12：標準單頭 YOLOv8 的 VART→tracker 解碼接點已完成離線驗證

- `person_tracking/assets/yolov8_vart.py` 新增 `standard_yolov8_decoder()`：只接受已確認為 raw Ultralytics YOLOv8 layout 的單一輸出 tensor（`(1,84,N)` 或 `(1,N,84)`），復用 CPU adapter 的 de-letterbox、COCO person-class filtering 與 NMS，輸出既有 tracker/peer schema 所需的 `class_id`/`confidence`/`box`。
- test-first：先加 decoder import/test 而失敗，再實作；tests 現驗證 `(1,84,1)` raw person head 正確還原成 640×480 來源的 `[160,160,480,320]`，多 head ambiguous output 明確拒絕。VART adapter 5/5、完整 `person_tracking` 21/21 PASS。
- 嚴格界線：尚無此 B512 的 compiled `.xmodel`，故不知道其真正 DPU outputs 是否符合單頭 ONNX layout；此 decoder **不會**自動註冊為 runtime detector，仍必須先 inspect `.xmodel` tensor names/shapes 並用真實 frame 結果驗證。多 head／feature-map compile output 會維持需要 model-specific decoder，不能據此宣稱 DPU YOLOv8 inference。

## 2026-11-12：WSL compiler route 已接通，preflight 改採 PetaLinux 實際版本

- Docker Desktop 既有 official `xilinx/vitis-ai:2.5.0` image 在 Windows 端可正常使用，但 WSL 原先沒有 `docker` command。已在 external `/home/petalinux/.local/bin/docker` 建立指向 Docker Desktop CLI 的 user-only symbolic link；WSL 實測 image digest 為 `sha256:eaa85efb06924995ebdb973546e7f69169b003b8cc525764bd9524ad554dddbe`。未拉取新 image、未改 Docker image/board/SD。
- `preflight_dpu_build_host.py` 不再把「Docker command 存在」當作 compiler ready：DPU 4.0 現會 inspect fixed `xilinx/vitis-ai:2.5.0`，DPU 4.1 會 inspect fixed 3.5 image。另加 `--petalinux-root`，從 `settings.sh` 讀 `PETALINUX_VER`、確認 `scripts/petalinux-create`，不能以 CLI argument 偽稱另一個版本。新增 test-first tests，現在 6/6 PASS。
- 實跑 WSL preflight：exact 4.0 `arch.json`、Docker image、PetaLinux executable 都存在；但 selected root 是 **2024.1**，gate 正確 FAIL，原因為 4.0/2.5 要求 2022.1，且 root 明確宣告 2024.1。這是更強的 blocker evidence，不是可部署 image；仍未取得／安裝 2022.1 Vivado/PetaLinux、未建 image／xmodel 或上板。
- WSL bridge 也已用 noninteractive `docker run --rm` 實測：container 內 activate `vitis-ai-pytorch` 後，`vai_c_xir` 位於 `/opt/vitis_ai/conda/envs/vitis-ai-pytorch/bin/vai_c_xir` 並能輸出 compilation banner。此為 compiler container availability，不是量化／編譯或 target image 驗證。

## 2026-11-12：2022.1 SDK 的 VART 2.5 AArch64 連結驗證已通過

- 已在 WSL ext4 安裝 external `/home/petalinux/sdk_2022_1`（official 2022.1 SDK），其 `environment-setup-cortexa72-cortexa53-xilinx-linux` 提供 GCC 11.2.0 與 AArch64 sysroot。將已驗證的 Vitis AI 2.5 runtime bundle **overlay 到此 2022.1 sysroot** 後，確認 sysroot 內有 `xdputil`、`libvart-runner.so.2.5.0`、`libxir.so.2.5.0`。
- 新增 tracked `vitis/pynq_zu_dpu/linux/vart_link_smoke.cpp`、`build_vart_link_smoke.sh` 和 source-contract unit test。test-first 證據：實作前 test 因檔案不存在失敗；加入檔案後 test PASS。實際 source SDK environment 後交叉編譯 PASS，輸出為 ARM aarch64 PIE ELF；`readelf -d` 實測含 `libvart-runner.so.2`、`libxir.so.2` 與 `libunilog.so.2`。這驗證 host cross-link ABI，而非執行期。
- 嚴格界線：smoke source 故意給 `Runner::create_runner()` null subgraph，**不得在目標端執行**。本次未建 PetaLinux 2022.1 image、未安裝或啟動 DPU driver/VART 到 PYNQ SD、未寫 SD/PL、未 compile YOLOv8 `.xmodel`，也沒有 DPU inference。SDK、runtime bundle 和 ELF 都在外部路徑，未入 Git。

## 2026-11-12：DPU IP 版本與工具鏈契約再次校正

- 直接讀取目前外部 build 的 `DPUCZDX8G_v4_0_0/component.xml`，確認現有 B512 bitstream 的 **實際 DPU IP 是 4.0**，不是「v4.0 source branch」標籤。AMD official compatibility matrix 指定：DPU 4.0 → Vitis AI 2.5 → Vivado/Vitis/PetaLinux 2022.1；DPU 4.1 → Vitis AI 3.5 → 2023.1。故先前把現有 DPU 4.0 說成 Vitis AI 3.5/2023.1 的表述不正確，已以本段覆蓋。
- `preflight_dpu_build_host.py` 現需 `--dpu-ip-version`，將 4.0/2.5/2022.1 與 4.1/3.5/2023.1 明確分流，拒絕不明 IP 或將目前 4.0 bitstream 混接 3.5。test-first：先新增參數的 tests 失敗（舊函式無此參數），再完成 mapping；4/4 unit tests PASS。
- 決策仍待實作：若保留已完成的 4.0 B512 hardware，要取得 2022.1 Vivado/Vitis/PetaLinux 與 Vitis AI 2.5；若以 YOLOv8/Vitis AI 3.5 為優先，需取得 DPU 4.1 source 並以 2023.1 重建，不能重用當前 bitstream/`arch.json`。已安裝 PetaLinux 2024.1、現有 Vivado 2024.2，以及目前 Vitis AI 3.5 Docker image 都不構成任一路線的完整 deployment contract。

## 2026-11-12：官方 DPU TRD source 已取得並與既有硬體溯源比對

- 從 Vitis-AI v3.5 的 Zynq example 所指向、不需 AMD account 的 official URL `https://download.amd.com/opendownload/xlnx/DPUCZDX8G.tar.gz` 下載 61,086,986-byte archive，SHA-256=`2888c035f73c907e29de1ae524e2caf4474b05a59ba30aeac3ebe2c818557603`，解壓於外部 `C:\pynq_toolchain_sources\DPUCZDX8G_official`（不入 Git）。archive 的 `component.xml` 是 DPUCZDX8G 4.0，且 README/changelog 都指向 Vitis AI 2.5、Vivado/PetaLinux 2022.1。
- 實際比對新下載 source 與 `C:\pynq_zu_dpu_native_build\native_dpu_ip` 的 `DPUCZDX8G_v4_0_0/component.xml` SHA-256，兩者都是 `70e6c6c4923b872d907d9b007c0308393eda30bbc0a30e515843b630f329fb3d`（byte-identical）。所以現有 B512 bitstream 確實由官方 2022.1/2.5 DPU 4.0 source 派生，不能改以 source branch 名稱或 Vitis AI 3.5 說成相容。
- Vitis-AI v3.5 source tag（`7a0d5a695027b0dc1494c7299918959608c3fab2`）也已 clone 到同一外部資料夾供離線核查。其 compatibility matrix 提及 4.1/3.5/2023.1，但所引用的 public DPU TRD bundle 仍是上述 4.0/2022.1 bundle；現階段沒有取得可驗證的 4.1 source，不猜測或偽造 IP。

## 2026-11-12：現有 DPU 4.0 的 Vitis AI 2.5 編譯器已實際可用

- 已從 Docker Hub 拉取 official `xilinx/vitis-ai:2.5.0`；image digest=`sha256:eaa85efb06924995ebdb973546e7f69169b003b8cc525764bd9524ad554dddbe`，Docker inspect size=27,008,926,042 bytes。以 noninteractive container 啟動、activate `vitis-ai-pytorch` 後，`/opt/vitis_ai/conda/envs/vitis-ai-pytorch/bin/vai_c_xir` 可執行；`vaic`、`xcompiler`、`xir`、`vart`、`pytorch_nndct_cpu` 都列為 2.5.0。
- 這解除 **host model-compiler** blocker（可在後續有 exact 4.0 `arch.json` 時編譯相容模型）；未做 quantization／compile，因為尚未獲得要部署的 deterministic YOLOv8 INT8 model contract，且 Vitis AI 2.5 對 YOLOv8 非現成官方 model-library claim。它也不解除 2022.1 Vivado/PetaLinux、Linux DPU driver/runtime、target image、或板端驗證。

## 2026-11-12：DPU 4.0 的 2022.1 target SDK 與 runtime bundle 已取得、未誤部署

- 從 Vitis-AI v2.5 source 的 official public URLs 下載 `sdk-2022.1.0.0.sh`（942,561,547 bytes，SHA-256=`e2becdb06564f7f26ac1c61e81201d1ada78e9d7f6bb2aacc0969a0d63ba84e4`）與 `vitis_ai_2022.1-r2.5.0.tar.gz`（7,247,361 bytes，SHA-256=`cc04a31abc147b9936fa2cc15ec3a8348a3dc27ab5a52dbc2239326e31567511`），放在外部 `C:\pynq_toolchain_sources\vitis_ai_2_5_assets`，不入 Git。Vitis-AI v2.5 tag `c26eae36f034d5a2f9b2a7bfe816b8c43311a4f8` 亦已 external clone。
- runtime tar 在 Windows NTFS 展開時無法建立 Linux symlinks，故不把 Windows staging 當作 validation。已在 WSL Ubuntu 的 ext4 `/home/petalinux/vitis_ai_2_5_runtime_staging` 解壓確認 `libvart-runner.so -> libvart-runner.so.2`、`libvart-runner.so.2.5.0`、`libxir.so.2.5.0`、`xdputil` 與 13 個 `libvart*.so.2.5.0` 均存在。
- 限制：SDK installer 尚未執行；runtime 也未複製到板子或目前 PYNQ 2024.1 rootfs。它們只對日後 matching 2022.1 system/sysroot 有效，不可將存在的 aarch64 libraries 宣稱為已在 PYNQ-ZU 執行。

## 2026-11-11：Linux CMA 可用，但 Vitis/Linux AXI DMA 仍需 kernel DMA-BUF ownership layer

- 對 live PYNQ 做唯讀盤點，發現 `/dev/dma_heap/linux,cma`、`/dev/dma_heap/system`；`CmaTotal=524288 KiB`、`CmaFree=517188 KiB`。所以 Linux camera/packer 後有 contiguous-memory allocation source，這是正面硬體／kernel 證據。
- 關鍵界線：dma-heap 交出的是 DMA-BUF file descriptor，不是 user-space 可安全傳給 AXI DMA 的實體地址。先前 standalone Vitis JTAG DMA test 用的 DDR pointer 不可搬到 Linux；不可用 `/dev/mem` 迴避。下一步需 matching Linux DMA client/driver 將 DMA-BUF attach/map/sync 後送入 AXI DMA，或確認 image 有相容 DMAengine DMA-BUF importer。
- 本次沒有 allocate buffer、沒有寫 DMA register、沒有載入 module／改 kernel／bitstream。現有 `uvc_v4l2_packer` 仍只到 packed output file，DMA/PL/DPU 不可宣稱完成。

## 2026-11-11：同板雙 C270 的 Vitis/Linux sequential 格式驗證已通過

- `vitis/pynq_zu_usb_video/linux/uvc_v4l2_packer.c` 新增 `--sequential <camera-a> <camera-b> <output>`。它會完整關閉第一支 C270 後再開啟第二支、各 copy 一張 320×240 YUYV 到 user memory，最後用既有 `pack_dual_yuyv()` 形成 A/B 兩 lane 的 640×480、64-bit packed frame；程式註解與 README 明確禁止將此模式當作同步或同時擷取。
- Vitis 2024.2 AArch64 compile PASS。2026-11-11 實機執行 `--sequential /dev/video0 /dev/video2`：兩者各協商 320×240 YUYV、10 FPS，輸出 307,200 words，其中 A lane nonzero=307,168、B lane nonzero=307,112。`/tmp` ELF/output 已移除。
- 驗證界線：這證實一板兩支已連接 C270 能獨立被 Vitis/Linux C 程式讀取並填入雙 lane，不是 simultaneous STREAMON、共同 timestamp、AXI DMA/PL/DPU 或人物偵測。已知兩支同時 STREAMON 的 USB `ENOSPC` 失敗仍未解除。

## 2026-11-11：兩板 Wi-Fi 只讀 preflight 已完成並在未設定板端正確失敗

- 新增 `person_tracking/pynq_wifi_peer_preflight.py`：讀 `/sys/class/net/<interface>/operstate`、以 `ip -j addr` 列出 IPv4；指定 `--peer-host` 時只嘗試一次 TCP connect，沒有掃描、join SSID、寫入密碼或變更 interface。它輸出 JSON 和 `PYNQ_WIFI_PEER_PREFLIGHT_PASS/FAIL`，通過必須有 interface、operstate=up、IPv4，且指定 peer 時 TCP port 也可達。
- `tests/test_pynq_wifi_peer_preflight.py` 覆蓋 connected+peer PASS、沒有 IPv4、TCP peer failure 與自訂 interface 名稱；完整 `person_tracking` unit suite 為 19/19 PASS。板端暫傳腳本至 `/tmp` 執行，實際結果為 `wlan0` exists、operstate=down、IPv4=[]，因此正確輸出 FAIL；測後腳本已移除。
- 未改任何 Wi-Fi 設定、SSID、密碼、rfkill 或第二板。真正兩板 Wi-Fi 仍需要授權的共同網路／明確 AP topology、兩塊板和 receiver service 後以 `--peer-host` 實測。

## 2026-11-11：Vitis Linux 單 C270 → packed AXI-stream lane 已於板端驗證

- 因同板兩支 C270 已確定受共用 USB2 hub `ENOSPC` 限制，`vitis/pynq_zu_usb_video/linux/uvc_v4l2_packer.c` 新增 `--single-a <video> <output>`、`--single-b <video> <output>`。它們仍輸出既有 RTL 的 640×480、64-bit word 格式：A mode 僅填 `RGB[23:0]`，B mode 僅填 `RGB[55:32]`，未使用 lane 固定黑色；不複製一支相機來假裝雙來源。寫檔現在也會處理 partial write。
- Vitis 2024.2 AArch64 cross compile first因 `close_camera` 宣告順序被 `-Werror` 拒絕，修正 forward declaration 後 `build_linux_uvc_packer.ps1` 成功輸出 ELF。2026-11-11 將 ELF 暫傳至 live PYNQ 的 `/tmp`，以 `/dev/video0` 執行 `--single-a`：V4L2 協商 320×240 YUYV、10 FPS，產出 2,457,600 bytes（307,200 words）；板端檢查 low A lane 有 307,160 nonzero words、high B lane 為 0。以同一支 C270 重跑 `--single-b`，則 low A=0、high B 有 307,176 nonzero words，確認兩板角色不會填反 lane。`/tmp/uvc_v4l2_packer` 與輸出檔均已移除。
- 驗證界線：這是實機 Linux V4L2 + Vitis-built C + YUYV→RGB/64-bit packing；尚未配置 contiguous DMA buffer、未送 AXI DMA／PL、未執行 DPU，亦沒有第二板／Wi-Fi。兩 C270 同時 STREAMON 仍為已知失敗，不能以單 lane PASS 宣稱完成同板雙鏡頭。

## 2026-11-11：兩板 metadata sender 的 peer-restart 重試語意已完成離線測試

- `person_tracking/pynq_yolov8_peer.py` 現在以 `send_packet_with_retry()` 對每一張已擷取／追蹤的 metadata packet 預設送三次、間隔 0.5 秒。它只攔截 TCP `OSError` 類失敗，重傳**同一個** frame packet；payload schema 錯誤不會被錯誤重試。重試用盡後丟出 `ConnectionError`，故不會把未送達誤記成成功。
- CLI 增加 `--send-attempts`、`--retry-delay`；輸出會列出每次重試和實際使用 attempts。`tests/test_yolov8_peer.py` 現以 fake sender 覆蓋「兩次拒絕連線後成功」及「重試用盡失敗」；這只驗證送端復原語意，不驗證 Wi-Fi 封包實際抵達。
- 現有 `peer_protocol.py receive` 在每個 connection 結束後持續 accept，兩段合起來提供兩板各自執行 receiver + sender 時的重啟容忍設計。仍須有第二塊板、已授權 Wi-Fi 網路設定與實機連線測試；未修改板子／SSID／網路設定。

## 2026-11-11：VART Python 執行邊界已補上，尚未偽稱為 DPU 人物偵測

- 新增 `影像處理/ModelSim_YOLOX_PersonTracking/person_tracking/assets/yolov8_vart.py`。`VartYoloV8.from_xmodel()` 會在目標 Linux 的 VART/XIR 存在時，從 `.xmodel` 找到唯一 DPU subgraph；`infer_tensors()` 對照實際 VART tensor 的 NHWC shape／`fix_point` 完成 BGR→RGB letterbox、INT8 量化、VART job 與輸出反量化。這讓之後的 DPU YOLOv8 可把 tensor 結果交給既有 Python tracker／Wi-Fi schema，而不是發明裸金屬控制 API。
- 目前尚無由此 PYNQ-ZU B512 `arch.json` 編譯的 `.xmodel`，故尚不知道模型真實 output heads 與 decode/量化契約。`infer()` 在未注入並測過的 model-specific decoder 時會明確失敗；不得將此檔案描述成已完成 DPU 人物框。`tests/test_yolov8_vart_adapter.py` 使用 fake VART runner 驗證 input RGB/NHWC/fix-point、輸出反量化與上述拒絕行為；連同既有 YOLOv8 adapter/peer tests 共 7/7 PASS。
- 實機仍需要先取得 2024.1 PetaLinux/Vitis AI Linux host、重建相符 DPU/XSA、編譯確切 `.xmodel`，再把輸出 decoder 接到 `pipeline.Detector` 後在板上驗證。這次沒有安裝軟體、燒錄或改動板子。

## 2026-11-11：本機下載檔與 DPU Linux host 再稽核

- 重新盤點 `C:/Users/dsic/Downloads`：使用者提及的約 6.6GB 檔為 `Vitis_Embedded_Win_2024.2_1113_2356.tar`（實際 7,049,861,120 bytes），另有 Windows Unified 2024.2 installer/2024.2.2 archive；未找到 PetaLinux installer、Vitis AI Docker archive 或 2024.1 Vivado/PetaLinux installer。
- `wsl --status`／`wsl --list --verbose` 均要求先執行 `wsl --install`，故沒有任何已安裝 Linux distribution；未找到 Docker 或 Podman。這確認 6.6GB Vitis Embedded 下載不是可用的 PetaLinux/Vitis AI host。
- 未嘗試解壓 139GB Unified archive、安裝 WSL/Docker/PetaLinux 或變更系統，因這些會是重大系統變更且現有 DPU runtime 所需的 2024.1 toolchain 仍不在本機。下一步需取得受支援 Linux host 與 2024.1 PetaLinux/Vitis AI；在獲得該環境前可繼續 CPU YOLOv8/兩板 peer 路線。

## 2026-11-11：原生 B512 DPU 的精確 `arch.json` 已擷取

- 先前主機搜尋遺漏了 Vivado `pynq_zu_dpu.gen` 產物；現在在已完成的 native DPU build 找到 `project/pynq_zu_dpu.gen/sources_1/bd/pynq_zu_dpu/ip/pynq_zu_dpu_dpu_czdx8g_0_0/arch.json`。其精確 fingerprint 是 `0x101000016010400`。
- 新增 tracked host helper `fpga/export_pynq_zu_dpu_arch_json.py` 與兩個 unit tests。它從指定的 `PYNQ_ZU_DPU_BUILD_DIR` 提取 generated JSON、驗證 hex fingerprint、輸出最小 JSON；不會 Program FPGA、改寫板子或猜測 board-family architecture。實跑產物為外部 `C:/pynq_zu_dpu_native_build/pynq_zu_dpu_b512_arch.json`，不提交 Git。
- 重新執行 build-host gate，`has_arch_json=true`；其餘三個 blockers 不變：沒有 Docker/`vai_c_xir`、沒有 PetaLinux，且現有 DPU hardware 為 2024.2 而 Vitis AI 3.5/DPUCZDX8G 4.0 的已驗證矩陣是 2024.1。這個檔案不能替代 matching Linux/device-tree/driver/VART 或 `.xmodel`。

## 2026-11-11：重開後 DPU bitstream 仍在 PL，Linux runtime 仍不相配

- Vivado Hardware Manager 的目前 `xczu5_0` 狀態為 `Programmed`，Programming file 指向 `C:/pynq_zu_dpu_native_build/project/pynq_zu_dpu.runs/impl_1/pynq_zu_dpu_wrapper.bit`。Tcl Console 有明確 `set_property PROGRAM.FILE ...` 後的 `program_hw_devices [get_hw_devices xczu5_0]` 記錄；不是僅檔案欄位殘留。
- 同時，SD Linux 已實測正常 SSH、UVC 與 CPU YOLOv8；但 `/dev/dpu0` 仍 absent，`xdputil`、Python `vart`、`xir` 均不存在。故 bitstream 已載入的硬體事實不可延伸為 DPU runtime/YOLOv8 DPU inference 完成。
- 本次僅讀取 Hardware Manager 狀態，沒有重新 Program、Erase、寫 SD 或變更板端環境。後續在沒有 matching 2024.1 Linux/device tree/DPU driver/VART/.xmodel 前，不得以此 PL 現況做 DPU inference 測試。

## 2026-11-11：兩板 Wi-Fi 路徑的板端唯讀診斷

- 實機唯讀檢查：PYNQ-ZU Linux 有 `wlan0` managed interface（`phy#0`），kernel 在 boot 時載入 `wilc_sdio` 並初始化 `wlan0`；因此板載 Wi-Fi 路徑可供後續第二板 metadata peer 使用。
- 目前狀態：`wlan0` DOWN、沒有 IP；NetworkManager 與 wpa_supplicant 都 inactive，且未掃描或連線至任何 SSID。kernel 僅有 `Failed to get RSSI value`（尚未連線時）與 regulatory.db 缺失訊息；本次沒有網路設定、密碼、SSID、rfkill 或 driver 寫入操作。
- 下一步需取得使用者指定的受信任 SSID 與連線授權，或由使用者指定兩板 direct/AP 拓撲；之後才可設定兩塊板的不同 IP、啟動 `peer_protocol` receiver/producer，驗證 Wi-Fi packet transfer。既有 TCP schema/loopback 與單板 YOLOv8 不受影響。

## 2026-11-11：SD 重開後兩支 C270 依序 UVC recheck

- 在 `/home/xilinx/pynq_yolov8_20261111` 用 tracked `pynq_usb_camera_preflight.py` 實跑：列出 `/dev/video0`～`/dev/video3`，並依序以 MJPEG/320×240 開啟 index `0` 與 `2`；兩者皆成功讀到一張三通道影格。
- 結果是 `PYNQ_CAMERA_A_PASS=index=0 size=320x240` 與 `PYNQ_CAMERA_B_PASS=index=2 size=320x240`。它確認 SD restart 後兩支 C270 個別取像仍正常。
- 驗證界線：腳本是依序開／關相機，沒有同時擷取；不推翻先前 kernel `Not enough bandwidth` 的共用 hub 限制。未跑 YOLO/DPU/Wi-Fi/PL，未改寫板端資料或硬體設定。

## 2026-11-11：SD 重開後的持久 YOLOv8 CPU 部署與單鏡頭實測

- 使用者完成 SD restart 後，SSH 至 `192.168.3.1` 恢復正常。板端為 Linux `6.6.10-xilinx-v2024.1-gb6067dbebcc8`；`/dev/video0`～`/dev/video3` 存在；DPU `/dev/dpu0`、`xdputil`、Python `vart`/`xir` 仍不存在，故本次沒有 DPU inference claim。
- 實際部署：由 tracked `prepare_pynq_dual_bundle.py` 建置 13-member、11,104,503-byte bundle，將其解至新的 `/home/xilinx/pynq_yolov8_20261111`，不覆寫既有 `pynq_dual_dashboard_v6/v7`（YOLOX）目錄。system preflight PASS：Python 3.10.4、NumPy 1.21.6、OpenCV 4.5.4、ONNX Runtime 1.16.3、`yolov8n.onnx` 13,057,836 bytes。該 Python 環境沒有 `pynq` module；CPU ONNX 路徑不依賴它。
- 實際驗證：只開 C270 `video0`，設定 MJPEG/320×240，成功讀取 `(240,320,3)` frame 並以部署的 YOLOv8n ONNX 推論 0.964 s（當下 0 person）。將公開 `bus.jpg` 暫傳 `/tmp` 作正樣本，部署 detector 回傳 4 persons、1.654 s；測試圖已確定刪除。兩支相機未同時開啟，未測 Wi-Fi peer、tracker、dashboard 或 FPGA/DPU。
- 已經 SD 重開恢復 Composite/SSH；UART/JTAG 仍同時可供 Vivado 偵測 `xczu5`。本次不寫 bitstream、不安裝板端套件、不重刷 SD，也不保留公開圖於 `/tmp`。

## 2026-11-11：Composite 與 UART/JTAG 同時連線、JTAG target 已確認

- 使用者已同時接上 Composite 與 UART/JTAG。Windows 維持 Composite 的 PYNQ-USB、RNDIS 與 `COM4`；Vivado Hardware Manager 現在實際開啟 `localhost/xilinx_tcf/Xilinx/1234-tulA`，並偵測到 `xczu5_0`（part `xczu5`）及 `arm_dap_1`，證明 JTAG 路徑可用。
- Hardware Manager 顯示 `xczu5_0` status=`Programmed`、Programming file 欄位為 DPU wrapper `.bit`，但本輪沒有保留可證明「本輪 Program 成功」的獨立 Vivado log，故只能記錄目前觀測到的狀態，不能宣稱已安全部署 DPU runtime。
- 重要即時狀態：先前以 Composite/SSH 可唯讀登入；在 JTAG target 開啟後，TCP 22 仍可通但 SSH 在 server banner 前重設連線。這可能是板子/PL 正在重設或目前 PL 與 SD Linux 狀態不一致；未再做 program、下載、覆寫、重刷或板端寫入。下一步需保留兩條線，實體斷電重開並以 SD boot 回復乾淨 Linux，再以 SSH/UART 檢查。

## 2026-11-11：PYNQ-ZU Composite USB 已恢復，UART/JTAG 未偵測

- 實際硬體驗證：Windows 現在可辨識板子的 `PYNQ-USB` mass-storage gadget、`Remote NDIS Compatible Device`（VID `03FD:010C`）與 `乙太網路 3`。主機取得 `192.168.3.102`，`192.168.3.1:22` TCP 成功，故 SD Linux/Composite 網路連線已恢復。
- 明確界線：目前 PnP 沒有 Xilinx/FTDI UART/JTAG 裝置或新增 COM port；以 `ssh -o BatchMode=yes xilinx@192.168.3.1` 測試僅得到 `Permission denied (publickey,password)`，表示 SSH server reachable 但本機無可用 key，未登入、未執行板端指令。
- 結論：目前插回的是 Composite USB，而非可供 Vivado Hardware Manager 使用的 UART/JTAG 路徑。Linux/SSH 與 PYNQ-USB 可繼續使用 Composite；若要 Vivado/Vitis JTAG programming/debug，仍須另接 UART/JTAG 孔。未變更 boot switch、SD、bitstream 或板端檔案。

## 2026-11-11：DPU Linux build-host 版本契約與離線 gate

- 需求／決策：使用者暫未插 UART/JTAG，先完成不接板也能驗證的 DPU 部署準備；不以成功產生 Vivado 2024.2 bitstream 混稱為 DPU runtime 相容。
- 新增 `影像處理/ModelSim_YOLOX_PersonTracking/vitis/pynq_zu_dpu/linux/preflight_dpu_build_host.py` 與三個標準庫 unit tests。它不下載、不安裝、也不改動系統；只檢查 Docker 或 `vai_c_xir` 編譯入口、PetaLinux、精確 DPU `arch.json` 與版本契約，並輸出 JSON/sentinel。
- 依 AMD Vitis-AI `v4.0` release notes，DPUCZDX8G 4.0 與 Vitis AI 3.5 的已驗證配對是 Vivado/Vitis/PetaLinux **2024.1**。目前已成功實作的 DPU hardware/XSA 是 Vivado/Vitis 2024.2；其 Vivado implementation 成功仍屬未在官方矩陣驗證的 runtime 路線，不能用來產出/宣稱可部署的 DPU Linux image。後續應在 2024.1 重建 DPU/XSA，並以同版 PetaLinux 建 image。
- 本機實測 gate：沒有 Docker、`vai_c_xir`、PetaLinux 或 DPU-generated `arch.json`；Windows 只有 Vivado/Vitis 2024.2。因此輸出 `PYNQ_ZU_DPU_BUILD_HOST_FAIL`，列出四個明確 blockers。這是主機離線檢查，不是板端或模型驗證。
- 未完成：2024.1 build host、matching DPU bitstream/XSA、PetaLinux device-tree/driver/VART image、YOLOv8 INT8 quantization/`.xmodel`、板端 VART/person-inference。現有 CPU YOLOv8 fallback 與兩板 packet schema 不受影響。

## 2026-11-06：PYNQ-ZU USB Vivado Block Design 與 Vitis 控制骨架（進行中）

- 使用者決策：不再以 Jupyter 作為主控制流程，改採 Vivado 硬體檔（Block Design/XSA）與 Vitis C/C++ 控制檔。
- 新增 `fpga/create_pynq_zu_usb_video_project.tcl`：以 `tul.com.tw:pynqzu:part0:1.1` 建 project，並將 HDL stage 到短 ASCII build path。新增 `create_pynq_zu_usb_video_bd.tcl`：PS USB0/USB1 分別保留為 MIO 52–63/MIO 64–75，PS M_AXI_HPM0_FPD 經 SmartConnect 控制 AXI DMA、frame-id GPIO 與 `dual_camera_yolox_axis_top` mailbox；DMA MM2S 經 S_AXI_HP0_FPD 讀 DDR，輸出 64-bit AXI stream 至 RTL，DMA/mailbox IRQ OR 後送 `pl_ps_irq0`。
- 重要架構限制：Logitech C270 為 USB/UVC，D+/D− 由 PS 固定 USB MIO 和 USB host driver 處理；不能且不應在 PL XDC 把它假裝成 PCLK/VSYNC/D[ ]。Vitis/USB host 將 UVC frame 放入 DDR，再由 AXI DMA 送入 PL。
- 驗證：`fpga/tests/test_pynq_zu_usb_bd_contract.py` 2/2 PASS；本機 Vivado 2024.2 成功 `validate_bd_design` 並生成 wrapper/HWH。PS DMA mapping 修正為 `PSU__USE__S_AXI_GP2` 對應 `S_AXI_HP0_FPD`，此為 Vivado 3.5 PS IP 實際可用設定。
- 新增 `fpga/export_pynq_zu_usb_video_xsa.tcl`，僅在 synth、implementation 和 bitstream 成功後執行 `write_hw_platform -fixed -include_bit`。目前同一個 XSA export process 已啟動，但 synthesis child jobs 未產生 `runme.log`、仍在 Vivado queue；沒有 XSA/bitstream 成功證據。
- 新增 `vitis/pynq_zu_usb_video/src/video_control.[ch]`、`main.c` 和 host test。controller 拒絕缺少 base address，固定寫入順序為 frame-ID GPIO、mailbox frame ID、四個 bbox word、CONTROL=0x3；host test 以 Vitis bundled MinGW 編譯/執行。`main.c` 必須用已由 XSA 生成的 `xparameters.h`，且刻意不偽造 UVC host driver/DMA transfer。
- 未完成：XSA 產生、Vitis platform/BSP/application build、板端 USB UVC buffer/DMA/cache/IRQ 整合、兩鏡頭實機串流。未提交產物：`%TEMP%/pynq_zu_usb_video_test` 為可重建 Vivado 生成物與 log，不進 Git。

## 2026-11-05：換機前 GitHub 交接盤點

- 使用者要求讓下一台電腦可直接以 GitHub 接續。本次先執行 `git fetch origin`，確認本機 `main` 和 `origin/main` 同為 `46e9371`，且工作樹沒有已修改但未提交的版本控制檔；倉庫中已有 124 個受追蹤檔案，包括目前 PYNQ-ZU RTL/腳本、Python/YOLOX 網站、測試、啟動器與交接文件。
- 新增根目錄 `.gitignore` 規則以排除這台電腦本次遺留的 Vivado/XSim `.jou`、`.log`、`.pb`、`.wdb`、`.Xil/`、`xsim.dir/`，以及 `output/`、`tmp/` 和本機網站啟動／伺服器日誌。這些皆是可重建暫存、簽名文件預覽、硬體照片或含本機路徑的診斷資料，並非未同步的專題來源；不可將它們未上傳誤報為進度遺失。
- `tmp/LaunchVisionSite.cs`／`.exe` 是臨時 C# 桌面啟動器，假定特定本機目錄和 `%LOCALAPPDATA%\\Programs\\Python\\Python312`，不作共享入口。跨電腦請使用已追蹤、會避開 Windows Store Python alias 的 `live_site/start_dual.ps1` 或 `啟動即時追蹤網站.cmd`；透過 `PROJECT_PYTHON` 指定不同 Python 路徑。RTL 回歸使用已追蹤的 `person_tracking/open_xsim_regression.ps1`／`開啟VivadoXSim驗證.cmd`。
- 本次僅完成 Git 交接整理，沒有重跑相機、PYNQ Linux、Overlay/MMIO、FPGA 或網站實機測試；已驗證狀態仍以本檔較早的明確日期記錄為準。下一台電腦最小接手順序：clone `main` → 依 `person_tracking/requirements.txt` 建 Python 環境 → 執行 `setup_assets.ps1` 下載／核對 YOLOX → 先跑合成／XSim 回歸 → 再依實機有無設定相機、PYNQ 與 Vivado。相機索引、模型位置與工具路徑保持可設定，勿硬編碼。

## 2026-11-05：PYNQ-ZU 上板後的畫面與配對結果展示方案（僅規劃）

- 使用者指定先把下列方案存入 GitHub，暫不實作；未來收到明確指示「讀／做」時再依此執行。目標展示為電腦瀏覽器同時顯示 A/B 即時鏡頭畫面、YOLOX 人物框與各自 Track ID、A/B 候選配對分數／連續命中數，以及 FPGA 回傳的 candidate/confirmed 狀態。
- 建議最終拓撲：兩支相機接 PYNQ-ZU（先以 PS USB/OpenCV 為優先驗證路徑；CSI/HDMI 需另選定板級介面），板子 Ethernet 與觀看用電腦接同一可信任 LAN；板上 PYNQ Linux 的 Python 服務提供網頁，電腦以 `http://<板子-IP>:8766/` 觀看。原始影像留在板子/區網，FPGA 僅經 AXI/MMIO 回傳小量配對結果；JTAG/UART（目前曾見 COM7）只用於開機和除錯文字，不能作為即時雙影像傳輸通道。
- 第一階段順序： (1) 確認 PYNQ image 開機、Ethernet IP 與電腦可連線；(2) 板上以 OpenCV 驗證一支、再兩支 USB camera 可取 640×480 影格；(3) 將既有 `live_site/dual_server.py` 與相依模型部署到板上，先由 PS Python 完整產生網頁畫面與軟體配對結果；(4) 建立 AXI DMA/HP memory、overlay 與板上 MMIO，將已配對 frame/bbox 送入現有 RTL，並把 `candidate_valid`、`confirmed`、命中數回填網頁；(5) 若展示需要實體螢幕，再另做 HDMI 疊圖輸出，這不屬現有 RTL 或網站功能。
- 既有 `live_site/dual_server.py`/`dual_index.html` 已能在 Windows 端呈現雙 USB 畫面、人物框、Track ID、候選配對和人工核對；LAN 模式設計為由另一台電腦開 `http://<鏡頭主機-IP>:8766/`。它尚未在 PYNQ Linux 執行，也尚未接讀 FPGA 狀態，不能描述為板端完成。
- 本次沒有變更 RTL、網站或 PYNQ 環境，沒有接板、沒有網路/相機/bitstream/DMA/MMIO 實測；本項只是後續上板與展示的可追溯規劃。硬體介面、IP 位址、相機索引及套件相容性須於目標第三台電腦／實際板子現場設定，不能硬編碼。

## 2026-11-04：YOLOX 到 PYNQ-ZU RTL 的 AXI4-Lite bbox 資料邊界

- 已核對並沿用既有 Verilog 提交：`6317be2` 跨鏡頭確認 matcher、`83cbdfe` 雙路 ROI 串接、`df14947` 完整 640×480 testbench；本次不重寫已驗證的 ROI/matcher 核心。
- 新增 `fpga/yolox_bbox_axilite.v`，提供同一 PL clock 的 AXI4-Lite command mailbox。PS 先寫 frame ID 和 A/B bbox，最後 CONTROL.bit0 commit；matching frame 接收後清除 pending，未消耗前再 commit 會置 `overrun` 且保留舊命令。
- 新增 `fpga/yolox_frame_command_adapter.v`，只在 video `frame_start` 與 command frame ID 相同時鎖住 bbox；`fpga/dual_camera_yolox_axilite_top.v` 將此 adapter、mailbox 與既有 dual ROI top 串接。`create_pynq_zu_rtl_project.tcl` 已新增 sources 並將該整合 top 設為 top。
- 新增 `person_tracking/pynq_yolox_mmio.py`，可驗證和送出 `dual_camera.py` 的 `rtl-yolox-bbox-v1` packet 到 PYNQ MMIO；硬體 base address 必須由最終 Block Design 的 Address Editor 提供，不寫死在共享程式碼。
- 此電腦驗證：Vivado 2024.2 `xvlog` 成功編譯完整整合 top；`tb_yolox_command_path.v` 的 commit、錯影格保留、正確影格 latch 與 consume 模擬通過，輸出 `YOLOX_COMMAND_PATH_PASS checks=9`。Python fake-MMIO 合約測試也通過，產生正確的 6 次 payload/control 寫入。
- 當時尚未驗證項目已由下一節更新；目前仍未驗證 PYNQ-ZU 的 PYNQ image/network、camera/MIPI 或 USB frame-buffer、XDC、implementation、bitstream、實機 MMIO。YOLOX 仍在 CPU/PS Python；RTL 只接收已選 pair 的 bbox，不能宣稱 YOLOX 神經網路已用 Verilog 實現。

## 2026-11-04：PYNQ-ZU Zynq PS Block Design 與綜合

- 新增 `fpga/create_pynq_zu_yolox_bd.tcl`：建立 board preset 的 `zynq_ultra_ps_e`、開啟 `M_AXI_HPM0_FPD`，接至 `axi_smc_0` 再接 `dual_camera_yolox_axilite_top` 的推導 `S_AXI` 介面。加入 `proc_sys_reset`、PS reset invert 和 100 MHz `pl_clk0`，避免第一次 BD validate 報告的非同步 reset critical warnings。影像輸入/輸出保持 BD external ports，因尚未選定 CSI/HDMI/USB frame buffer 的真實板級路徑。
- `assign_bd_address` 在此設計中實際配置 `/yolox_rtl_0/S_AXI/reg0` 到 PS address space 的 `0xA000_0000`、4 KiB；這是本腳本已驗證產生的地址，若日後變更 BD，PYNQ 端仍須以 Address Editor/HWH 為準。
- 新增 `fpga/synthesize_pynq_zu_yolox.tcl`，生成 BD HDL wrapper 並跑 `synth_1`。初次在 repo 中文長路徑下 IP generate 失敗（檔案找不到），已改三個 script 以環境變數 `PYNQ_ZU_BUILD_DIR` 可覆寫、預設 `%TEMP%/pynq_zu_rtl` 的短 ASCII 生成路徑；原 repo 下的舊 build 未刪除。
- 短路徑實跑：BD `validate_bd_design` 完成，僅有 SmartConnect 對 AXI4-Lite low-area/WRAP burst 的一般 warning；wrapper synth 產生 `pynq_zu_yolox_wrapper.dcp`，日誌為 `synth_design completed successfully`，0 errors、0 critical warnings。這證明 PS/AXI/RTL 結構可綜合，不證明 IO 約束、implementation、bitstream、PYNQ overlay、camera 影像或板端 MMIO。

## 2026-11-04：可接 DMA 的同步雙 RGB AXI-Stream 資料面

- 新增 `fpga/axis_dual_rgb_stream_adapter.v` 與 `dual_camera_yolox_axis_top.v`。前者把一條 64-bit AXI stream 的 A `[23:0]`、B `[55:32]` RGB888 word 轉成既有 dual ROI core 所需的同 clock/同拍 pixel stream；每 307,200 word 形成 640×480 frame，檢查 TLAST 是否落在終點並鎖存 boundary error。後者將 AXI stream adapter 與已驗證的 PS AXI-Lite bbox top 串接。
- 單一合併 DMA stream 是刻意設計：兩支獨立 DMA 若有 valid gap，既有同步 core 不能保證每個 A pixel 對應同一個 B pixel。此介面允許 PS/camera 軟體先將同時間 pair 成為一個 frame-pair buffer，再送入 PL。
- `pynq_yolox_mmio.py` 新增 `pack_dual_rgb888_frames()` 和 `copy_dual_frame_to_dma_buffer()`；只接受 matching `uint8` RGB H×W×3 frames，依硬體位元布局產生 `uint64` DMA words。fake NumPy test 的輸出為 `0x00aabbcc00112233`；Vivado XSim 的 adapter test 結果為 `AXIS_DUAL_RGB_STREAM_ADAPTER_PASS checks=7`，完整 axis top `xvlog` 成功。
- 未驗證：尚未選定/接上 PYNQ-ZU 的實體 camera interface（CSI、HDMI 或 PS USB），也尚未把 AXI DMA/high-performance memory port 加到 BD、產生 bitstream 或用 PYNQ DMA 實機傳影像。故這是已測試的資料格式/RTL 入口，不是相機上板結果。

## 2026-11-04：PYNQ-ZU board repository 與 Vivado 驗證

- 使用者提供板子照片確認為 TUL PYNQ-ZU，官方 board part 為 `tul.com.tw:pynqzu:part0:1.1`、device `XCZU5EG-1SFVC784`。本機偵測到其 Xilinx USB JTAG/UART（FTDI VID 0403/PID 6010）於 COM7，但當次打開後未收到 UART boot 輸出，未證明 PYNQ image 已開機或網路可達。
- 使用者下載的 `C:\Users\dsic\Downloads\XilinxBoardStore-master.zip` 已解壓到被忽略的 `fpga/board_repos/`。新增 `fpga/configure_pynq_zu_board.tcl`：以 script 相對路徑設定 `board.repoPaths`，檢查 `TUL/pynqzu/1.1/board.xml` 存在並執行 `get_board_parts *pynqzu*`。Vivado 2024.2 batch 實跑印出 `PYNQ_ZU_BOARD_PARTS=tul.com.tw:pynqzu:part0:1.1`；其他 Board Store 中此 Vivado 沒安裝的 device 警告與 PYNQ-ZU 無關。
- 下載的 `pynqzu_master.xdc` 是 Rev 3.B 的完整約束範本，目前不直接加入設計；必須待確定使用哪一個 PL I/O（HDMI/CSI/LED 等）再挑選對應 constraint。`.gitignore` 現排除 `fpga/board_repos/`，不提交約 224 MB 的第三方 Board Store。尚未產生 PYNQ-ZU bitstream、PS block design、AXI bridge、PYNQ overlay 或板端實機驗證。
- 新增 `fpga/create_pynq_zu_rtl_project.tcl`。它設定本機 board repo、`create_project` 使用 `xczu5eg-sfvc784-1-e`、套用 `tul.com.tw:pynqzu:part0:1.1`，並加入 `person_roi_stream.v`、`cross_camera_pair_matcher.v`、`dual_camera_roi_match_top.v`，top 為 `dual_camera_roi_match_top`。2026-11-04 以 Vivado 2024.2 batch 實跑建立成功；Vivado 警告專案中文/長路徑可能影響日後 IP/BD，未出現 RTL 加檔錯誤。`fpga/build/` 已加入 Git ignore。尚未 run synthesis 或建立含 PS/AXI 的 block design。

## 2026-11-04：公開圖片 dataset 評估彙總

- 新增 `person_tracking/evaluate_detection_dataset.py`，以 `verification_report.json` 為來源彙總 6 組公開圖片／亮度案例。
- 實際輸出 `DATASET_EVALUATION_PASS cases=6 observations=105 recall=1.000 minimum_iou=0.855`：105/105 人工標註觀測配對成功、0 miss、0 ID switch，負例 PASS。
- 這證明人物偵測框與短期追蹤的 dataset 評估已可交付；不延伸宣稱跨鏡頭真人身分準確率，因目前仍缺人工同人／不同人標註集。

## 2026-11-04：跨鏡頭同人配對正式評估入口

- 新增 `影像處理/ModelSim_YOLOX_PersonTracking/person_tracking/evaluate_matching_dataset.py`、`matching_dataset.json` 與 `MATCHING_EVALUATION.md`。評估人工標記的同人／不同人案例，輸出 TP、TN、FP、FN、accuracy、precision、recall、F1；有框座標時另檢查最大像素誤差是否小於 20 px。
- 目前附帶的 4 筆資料是合成 regression fixture，結果為 `TP=1/TN=3/FP=0/FN=0`、accuracy/precision/recall/F1 均 1.0、最大框座標誤差 8 px。這證明評估器與現有 matcher 可重跑，不是真人雙鏡頭準確率。
- 要取得正式實拍分數，需把 `matching_dataset.json` 換成兩台鏡頭錄影後人工確認的同人／不同人案例；測試集不可用來調門檻。

## 2026-11-04：EPFL 外部資料實測

- 新增 `person_tracking/evaluate_epfl_dataset.py`，使用專案 YOLOX/OpenCV 對 EPFL 6-camera 人物框資料逐張推論，依縮放後 ground truth 計算 IoU。
- 939 cases、1,302 ground-truth boxes、1,565 predictions；matches=1,035、misses=267、false positives=530，recall=0.7949、precision=0.6613、mean IoU=0.7963、minimum IoU=0.5007，耗時 133.84 秒。
- 座標誤差同步計算：mean=5.7932 px、maximum=37 px；`coordinate_error_threshold_px=20` 且 `coordinate_error_pass=false`，因此部分框超過 20 px。
- 另依物體中心位置計算 Euclidean distance：mean=2.9939 px、maximum=19.5256 px，`center_error_pass=true`。中心位置指標符合 `<20 px`，但四邊框誤差仍保留為 37 px，不能聲稱框的每一條邊都低於 20 px。
- 新增 `benchmark_box_stabilizers.py` 比較 Raw/EMA/median3；Raw 的 mean IoU=0.7963、中心最大誤差=19.5256 px 最佳，其他平滑法降低 recall 並超過 20 px，故未改主演算法。
- 新增 `fit_epfl_box_regressor.py` 與 `benchmark_box_refinements.py`。以 frame % 5 != 0 的人工標註配對學 per-camera 線性框校正，於 frame % 5 == 0 的 held-out validation 測試；`clamp=460` 得 max edge error=19 px、max center error=10.7355 px、mean IoU=0.8164，通過 `<20 px`。
- 結果 `EPFL_DATASET_PARTIAL`；完整逐案例明細在 `person_tracking/epfl_dataset_evaluation.json`，不可把先前 bus/zidane 回歸結果替代這次外部資料分數。
## 2026-11-04：雙鏡頭單一候選 Verilog 確認核心

- 本機目前以兩支 USB 鏡頭執行 `live_site/dual_server.py`，`/api/live` 曾回報 `live`、cameras `[0, 1]`、人物偵測與候選分數。白牆 10 個即時樣本的平均亮度 A/B 差為約 `+1.1/255`；另一輪以低飽和高亮區測得近似白色的 Lab 色差。這些是 2026-11-04 當時實機畫面量測，不等於人物同一性或準確率驗證，現場變化／自動曝光仍可能改變結果。
- 新增 `person_tracking/cross_camera_pair_matcher.v`，為可綜合的固定點單一 A/B pair 確認核心。輸入：時脈、reset、`pair_observed`、雙方有效位元、既有 `{top_color,bottom_color,top_percent,bottom_percent}` 24-bit 特徵；輸出：組合 `feature_similar`、每個相似觀測的 `candidate_valid`、第三個連續命中時的 `confirmed`，以及飽和於 3 的 `consecutive_hits`。主色兩段相等、各比例差 <=35 是相似條件；black 色碼 0 可透過獨立 valid 正確處理。缺少 pair 或不相似會清除計數。
- 新增 `person_tracking/tb_cross_camera_pair_matcher.v`，覆蓋第一次/第二次候選、第三次確認、確認後飽和、色碼不符、缺失觀測、black feature、36 個百分點比例差及 reset。用 `C:\Xilinx\Vivado\2024.2\bin\xvlog.bat`、`xelab.bat`、`xsim.bat` 實跑，輸出 `CROSS_CAMERA_PAIR_MATCHER_PASS checks=10`，無編譯或模擬錯誤。這是本機第三台的 XSim 模擬，非 ModelSim，也非合成、時序、PYNQ/EGo1 或相機實機驗證。
- 與 Python `cross_camera.py` 的關係：此 RTL 只確認一個已由上層選定的 pair，未等價實作 15-bin HSV overlap、0.72 門檻、歷史平滑、互為最佳、0.08 次佳差或多人物仲裁。YOLOX/Tracker/bbox 和 pair 選擇仍在 CPU；下一個 RTL 範圍應在固定 feature contract 後新增 A/B 多候選緩衝與仲裁，而不是聲稱已完全硬體化現有網站 matcher。
- 同日新增 `fpga/dual_camera_roi_match_top.v`：同一 clock domain 的雙 RGB888 pixel stream + CPU/YOLOX bbox integration top。兩個 `person_roi_stream` 在完整 640×480 frame 結尾輸出 feature 後，top 緩衝 feature，下一個 clock 送一拍 `observation_valid` 給 `cross_camera_pair_matcher`，避免讀到 nonblocking 舊值且不讓兩影格之間的 pixel gap 清空 hit 計數。以 Vivado 2024.2 `xvlog` 編譯 `person_roi_stream.v`、`cross_camera_pair_matcher.v`、此 top 成功；尚未建立真實 YOLOX bbox 的 pair testbench，也未完成不同時脈 USB / frame buffer、CPU-FPGA bbox protocol、多人物仲裁或 YOLOX network RTL。
- 新增 `fpga/tb_dual_camera_roi_match_top.v`，每個案例逐拍送完整 307,200 pixel 的 A/B RGB888 frame 與 bbox（用來模擬 YOLOX 已完成的偵測）。三張紅色相似 ROI 必須產生連續 1/2/3 並在第三張 `confirmed`，第四張紅/藍 mismatch 必須清為 0。以 Vivado 2024.2 XSim 實跑 `DUAL_CAMERA_ROI_MATCH_TOP_PASS checks=16`。這是 top 級合成影格與 bbox 模擬，仍不等於真實 YOLOX output、USB 兩時脈或 FPGA 實機。
- `person_tracking/dual_camera.py` 現在對每個已由 Python matcher 選出的非 unmatched A/B pair 寫入被忽略的 run artifact `rtl_yolox_packets.json`。格式 `rtl-yolox-bbox-v1` 含 640×480 resolution、frame、pair timing、兩側 track ID/bbox/confirmed、以 `pipeline.color_reference` 產生的 24-bit feature、軟體 score/status；不含 raw frame。這建立 YOLOX/Tracker 對 RTL `dual_camera_roi_match_top` bbox input 的可檢查封包契約，但未直接控制 FPGA、未證明 USB 同步，且不將 YOLOX 網路硬體化。已以 Python 3.12 `py_compile` 通過。

## 2026-10-31：第三台電腦執行環境複核

- 以 `%LOCALAPPDATA%\\Programs\\Python\\Python312\\python.exe` 實測：Python 3.12.10、NumPy 1.26.4、OpenCV 4.11.0 均可匯入；`person_tracking/setup_assets.ps1` 已確認 YOLOX ONNX 與三張公開測試圖存在，模型 SHA-256 為預期的 `c5c2d13e59ae883e6af3b45daea64af4833a4951c92d116ec270d9ddbe998063`。不需重複下載或安裝 Python 相依套件。
- 實際以此 Python 執行 `evaluate_cross_camera.py` 為 `CROSS_CAMERA_EVALUATION_PASS cases=3`；`unittest discover -s person_tracking -p test_*.py` 為 18/18 PASS；在 `live_site` 目錄執行 `python -m unittest test_dual_server.py -v` 為 6/6 PASS。這些是合成／程式回歸，不是 USB 相機或 FPGA 實測。
- 已確認 `C:\\Xilinx\\Vivado\\2024.2` 與內建 `xsim` 存在，但沒有偵測到 ModelSim 的 `vsim.exe`、安裝目錄或安裝媒體；因此現有 ModelSim 啟動器尚不能在本機執行，且不可把 Vivado 的 xsim 當成已驗證的 ModelSim 替代品。ModelSim 安裝仍需授權及安裝程式來源。
- Windows 裝置清單沒有回報狀態 OK 的 Camera，故未執行實體 USB／內建相機與 localhost 頁面影像流程。接上兩台相機且未被其他程式占用後，才可在 `http://127.0.0.1:8766/` 驗證雙鏡頭。
- 為讓已安裝的 Vivado 可立即使用，新增 `person_tracking/open_xsim_regression.ps1` 和上層雙擊入口 `開啟VivadoXSim驗證.cmd`。腳本複製 RTL 到 ASCII `%TEMP%/project_xsim_rtl_regression`，以 `xvlog`、`xelab`、`xsim` 編譯、elaborate、模擬；可用 `-Batch` 取得非互動 PASS/FAIL，或預設開 XSim GUI。實測 Vivado 2024.2 批次結果為 `RTL_REGRESSION_PASS frames=7 checks=89`。可設 `VIVADO_XSIM_BIN` 指向其他 Vivado 的 `bin` 目錄，沒有硬編碼使用者專屬路徑。

## 2026-10-30：第三台電腦環境與雙鏡頭啟動流程

- 目標端為第三台電腦；已安裝使用者層級 CPython 3.12.10：`%LOCALAPPDATA%\\Programs\\Python\\Python312\\python.exe`。以該直譯器安裝 `person_tracking/requirements.txt`，驗證版本為 NumPy 1.26.4 與 OpenCV 4.11.0；`person_tracking/setup_assets.ps1` 的 YOLOX ONNX 和公開圖片亦已準備。VS Code 已安裝 Microsoft Python、Pylance、Python Environments 與 debugpy 擴充套件；此前只解析到 WindowsApps 的 Store alias，並非可用解譯器。
- 更新 `live_site/start_dual.ps1`：優先由 `%LOCALAPPDATA%\\Programs\\Python` 找 CPython，排除 `WindowsApps\\python.exe` alias，才回退至 PATH 或 `PROJECT_PYTHON`。這避免桌面端啟動雙鏡頭網站時把 Store alias 當成 Python。
- 更新上層 `啟動即時追蹤網站.cmd` 為呼叫 `live_site/start_dual.ps1`，所以雙擊會執行 `dual_server.py --browser`，預設服務為 loopback `127.0.0.1:8766`。這會開 Chrome 或預設瀏覽器，但畫面是否開始取決於使用者在網站按下連接雙鏡頭、兩個 USB 鏡頭存在且未被其他程式占用。
- 未聲稱 USB 攝影機、ModelSim 或 Vivado 上板流程已驗證；目前已確認 `C:\\Xilinx\\Vivado\\2024.2` 存在，ModelSim 尚未在第三台確認。

## 2026-10-15：ModelSim 可重跑自動檢查與 GUI 入口

- 使用者要求下一個進度直接做在 Vivado 或 ModelSim，之後開啟可見。選擇驗證現有 ROI RTL，未假設 PYNQ 型號或鏡頭介面，也未改動原 RTL/網站。
- 修改前 `git fetch origin`，main 與 origin/main 為 `9c2070e`，工作樹乾淨；核對本機 modelsim_draft 與共享路徑兩份運算 RTL SHA256 相同。新增檔案以 modelsim_draft 為本機入口，同步共享最新整合路徑。
- `person_tracking/tb_rtl_regression.v`：自動比較手算答案，7 張完整 640×480 frame：全紅、偏移奇數高紅藍分區（插入 stalls）、右下邊界、無人物、零寬、一列高度、全黑。每張檢查完成時機、像素數、上下區面積、特徵/有效訊號；不 reset 的連續 frame 檢查累積器清除。比較器測 35/36 雙向門檻、主色不符與 invalid，末尾測 reset。失敗用 $fatal，另有 watchdog。
- `person_tracking/open_rtl_regression.ps1`：預設 ModelSim GUI 或 `-Batch` CLI，複製三份 Verilog 到 ASCII `%TEMP%/project_rtl_regression`，產生 regression.do，compile、模擬、記錄 WLF 並配置波形。GUI 保留視窗，Batch 要求 exit code 0 與 PASS 標記。可用 MODELSIM_VSIM 指定工具。`開啟ModelSim驗證.cmd` 為雙擊入口；`RTL_REGRESSION.md` 說明訊號與限制。
- 實際使用 ModelSim SE-64 2020.4 批次重跑通過，`RTL_REGRESSION_PASS frames=7 checks=89`，0 errors / 0 warnings；原始文字輸出保存 `person_tracking/rtl_regression_console.txt`。7 frame 不等於 7 個 checks，89 包含插入停拍的時機檢查。
- 限制：合成資料，未窮舉全部色彩分類門檻、未做亂數與中途 reset 測試，未做 synthesis/時序/上板；不能代表 YOLOX 或 Python 跨鏡頭 matcher 已搬到硬體。GUI 暫存副本需透過啟動器重開更新，原始碼在 repo。既有舊進度日期保留作歷史。

最後核對：2026-10-02

## 2026-11-03 變更：鏡頭來源端公開啟動交接文件

- 新增根目錄 `CAMERA_PC_PUBLIC_SETUP_PROMPT.md`，集中保存來源端檢查、CameraA 選擇、`start_remote.ps1` 啟動、private link 讀取和完成驗收條件。
- 這是來源端操作交接，不代表另一台電腦已實際啟動；目前仍缺目標電腦回傳的鏡頭、health、live 與跨網路手機證據。

## 2026-11-03 變更：雙電腦程式與網站協作

- `live_site/sync_camera_pc.ps1` 是鏡頭電腦的同步入口：驗證 Git checkout、`git fetch`、`git pull --ff-only`，失敗時停止，不覆蓋本機未提交變更，再呼叫 `start_dual.ps1`。
- `dual_server.py` 新增 `--bind` 與可重複的 `--allow-host`。預設仍為 loopback；明確指定 LAN bind/allowed Host 後，另一台電腦可用瀏覽器看 `/api/live` 與影像。
- `start_dual.ps1` 保留原本環境變數／CPython 尋找邏輯，並接受 `-ServerArgs` 傳遞服務參數。
- 未驗證目標電腦的實際 IP、Windows 防火牆、USB 鏡頭、Python/OpenCV/YOLOX 安裝或跨電腦 HTTP；這些需在鏡頭電腦現場執行。不要把 GitHub 當即時影像通道，也不要把 8766 公開到網際網路。

## 2026-10-26 變更：PYNQ/EGo1 共用板級 RTL wrapper

- 新增 `影像處理/ModelSim_YOLOX_PersonTracking/fpga/roi_feature_board_top.v`。它不重寫 ROI 計算，直接例化 `person_tracking/person_roi_stream.v`，保留 `pixel_valid`、`frame_start`、RGB888、人物 bbox 與 frame 完成訊號，並以 `result_led = feature_valid && person_valid` 提供最小板級結果指示。
- 這是 board-neutral synthesizable boundary，不是任一特定板子的可直接燒錄專案。PYNQ-Z2/EGo1 的 clock、XDC 腳位、相機輸入與 PS/AXI adapter 必須等實際板型與輸入方式確認後補上。

## 2026-10-26 變更：跨鏡頭 matcher 可重跑回歸評估

- 新增 `person_tracking/evaluate_cross_camera.py`。它使用明確的 2×15 合成外觀向量，重跑三個固定案例：同色連續三次後應為 `confirmed_candidate`、不同色應為 `unmatched`、相同外觀競爭者應為 `ambiguous`；使用 `assert`，並輸出同目錄的 `cross_camera_evaluation.json`。
- 實際結果：`CROSS_CAMERA_EVALUATION_PASS cases=3`；既有 `test_cross_camera.py` 為 6 tests OK。
- 這只驗證目前 Python matcher 的門檻、連續命中與歧義保護，不能替代真人標記資料的 precision/recall、雙實體 USB 實拍或身份辨識驗收。
- 完整 `unittest discover` 另有既有 `test_dual_features.py`、`test_tracking.py` 因目前 Python 3.10 環境未安裝 `cv2` 而無法載入；沒有安裝依賴或改變環境。

## 2026-10-02 變更：停止時清除舊工作階段照片

- 使用者補充「舊照片也刪掉」。`live_site/dual_server.py` 的 `stop_and_clear()` 現在在停止後遍歷**僅** `person_tracking/live_captures/` 下名稱符合 `YYYYMMDD_HHMMSS_ffffff` 的直接子資料夾；資料夾須不是 symlink、解析後仍在預期根目錄。每個工作階段只依其非 symlink `manifest.json`、且 `session` 名稱匹配，刪除 `people[].file` 列出、檔名符合 `[AB]_[0-9]{4,}.jpg` 的直接 JPEG。未登記 JPEG、其他檔案／資料夾、舊 manifest 保留；本次 manifest 仍按先前停止規則移除。沒有目前 session 也可按停止清舊照。API `deleted_photos` 和頁面訊息回報所有工作階段的刪除張數。
- `dual_index.html` 按鈕與說明改成「停止雙鏡頭並清除全部人物照片」。`test_dual_server.py` 改驗本次+舊工作階段登記照片刪除，未登記同命名 JPG、不同目錄 JPG、舊 manifest／其他檔案保留，重複停止安全。
- 實機操作：先核對 `live_captures` 8 個工作階段各有合法 manifest，549 張 A/B JPG 均列於 `people[].file`，無未登記同命名 JPG；停止原服務防止繼續拍攝，啟動新版後在無 active session 下呼叫 `/api/stop`，回報 `deleted_photos=549`。事後以同一目錄範圍複查，剩餘人物 JPG 為 0、8 份舊 manifest 保留，`/api/live` 為 stopped 且 `saved_people=[]`。未觸及 repo 其他未追蹤檔案。新增無 active session 的舊照清除單元測試。

## 2026-10-02 變更：多影格特徵、最佳人物照與人工審核

- 原本保存的首張人物 JPEG **不參與**跨鏡頭分數計算；分數取當次推論影格的衣著特徵。因此首張是側面照主要妨礙人工判讀，不直接造成配對失敗；實際低分/模糊候選仍可能來自視角、裁切、曝光與多人衣著相近。`live_site/dual_server.py` 新增 `AppearanceHistory`，每個鏡頭／Track ID 將最近五次特徵平均後與當前特徵各占一半，再交給既有 matcher；0.72 門檻、0.08 歧義差與三次連續 P 規則未變，尚未宣稱配對準確率改善。
- `snapshot_quality()` 比較人物框面積、清晰度、完整度、偵測信心；每個 ID 首次及其後每三次處理影格使用 OpenCV 隨附的 frontal-face Haar cascade 查正面臉，加權挑選較佳照。更新時覆寫同一檔名但 `photo_url` 增加 `?v=` 版本，避免瀏覽器顯示舊圖；每 ID 仍僅保留一張 JPEG。臉偵測可能漏檢/誤檢，不是姿態模型。已人工審核配對所涉的照片凍結，避免審核證據變動。
- `POST /api/manual_pair` 接收本次存在照片的整數 A/B ID，建立 M 標籤人工候選；`POST /api/review` 接收 P/M 標籤及 `same|different`，記錄審核與時間到本次 manifest。`/api/live` 的 `matched_pairs` 帶 `source`、`review` 與更新版照片 URL；網頁卡顯示雙照、✓/✕ 按鈕與判斷狀態。`cross_camera.py` 的 `excluded_pairs` 只在本次 session 阻止已被人工否決的 A/B ID 再自動配對；肯定判斷不訓練或改動模型。人工核對紀錄依前次要求在明確按「停止」時與本次照片一併清除。
- 實機正面臉 Haar 偵測在當次多人畫面未命中（截至觀察時 56 張照片、17 張有擇優替換、0 張帶 `face_detected`）；因此另加 `POST /api/retake`：只准對目前確認可見、最近一次推論不超過三秒、尚未審核的本次人物 ID，使用最近同一推論影格的人物 crop 手動覆蓋並鎖定 JPEG。相應照片與配對卡 URL 升版；可再手動重拍但自動挑選不覆蓋鎖定照。頁面每張照片下有「用目前畫面重拍並鎖定」，未在畫面中的 ID 或已審核者按鈕停用。
- 網頁載入改為只輪詢 `/api/live`，不再隱式 `POST /api/start`；重整頁面不換 session、不遺失人工審核。初次或手動停止後須使用者按「連接雙鏡頭」。
- 驗證：`live_site/test_dual_server.py` 五項合成單元測試 PASS，涵蓋最佳照替換、手動重拍鎖定、審核後凍結、手動 M 候選、否決組合排除、多影格特徵及停止清除；兩段網頁 JavaScript 語法檢查 PASS。新版服務以鏡頭 2/1 實機運行、頁面顯示雙鏡頭與人工 A/B 選單、P 卡 ✓/✕ 按鈕、每張照片的重拍按鈕，圖片無破圖；當次 AI 約 1.8 FPS、延遲約 0.6 秒，部分照片帶正面臉偵測標誌。沒有代替使用者對真實人物按 ✓/✕，也沒有任意挑角度對真實人物按重拍；這兩項實際人為操作仍由使用者核對。未有標註資料驗證漏配/誤配率。

## 2026-10-02 變更：手動停止時只清除本次人物照片

- `live_site/dual_server.py` 新增 `stop_and_clear()`：`POST /api/stop` 先停鏡頭並切換 epoch，鎖內只刪目前 `session_id` 工作階段中 `self.photos` 已登記的 JPEG 及該次 `manifest.json`，清空本次照片／P 候選狀態；資料夾僅在已空時移除。舊工作階段、未登記檔案、其他專題資料均不碰。10 秒無頁面輪詢的自動停鏡頭仍走 `control(False)`，不刪照片。API 成功回傳 `deleted_photos`，頁面訊息顯示數量。
- 網頁停止按鈕與說明文字更新為「停止雙鏡頭並清除本次照片」。單元測試加入本次照片／manifest 刪除、舊工作階段與未登記檔案保留、重複停止，以及非手動停鏡頭不刪除等檢查。此變更不追溯刪除先前已有的本機照片，需使用者另行指定範圍。
- 驗證：兩項 `live_site/test_dual_server.py` 單元測試 PASS。新版服務用實體鏡頭 2/1 啟動工作階段 `20261002_160018_047057`，停止 API 回報刪除 17 張本次 JPEG；之後 `/api/live` 為 `stopped`、`saved_people=[]`、`session=null`，本次資料夾已移除，先前 `20261002_155716_106196` 資料夾仍存在。網頁按鈕沿用同一 `/api/stop` 路徑；未另外做手動 UI 點擊驗證。

## 2026-10-02 變更：雙鏡頭人物照片保存及配對核對

- `live_site/dual_server.py`：每次 `/api/start` 建立 `person_tracking/live_captures/<時間戳>/`；處理執行緒對每個鏡頭的每個 `status=confirmed` Track ID 首次出現時裁切人物框，存為一張 JPEG，並更新 `manifest.json`。原始連續影格仍只在記憶體中。`/api/live` 新增 `session`、`saved_people`、`matched_pairs`；`/api/photo/A|B/<track_id>` 只讀取目前工作階段已登記的照片，不接受任意檔案路徑。Host/Origin 防護及 loopback 限制保留。
- `live_site/dual_index.html`：顯示本次已保存照片；對 `confirmed_candidate` 且有 P 標籤、兩側照片均存在的配對，保留 A/B 並排照片、ID 與分數供人工檢查。新工作階段清空頁面舊卡片，但不刪硬碟照片。照片 DOM 節點不隨每次輪詢重建，避免反覆下載 JPEG。
- `.gitignore` 排除 `person_tracking/live_captures/`；相機照片與 manifest 不上傳 GitHub。限制：只存每個已確認 Track ID 的首張裁切照，並非連續錄影；遮擋/重建 ID 可使同一人有多張。P 是衣著外觀候選而非身分確認，人工仍須核對。ModelSim 不在即時網站迴圈中。
- 驗證：`live_site/test_dual_server.py` 以合成影格確認 A/B JPEG 各只存一張、manifest 及 P 配對含兩張照片 URL；單元測試 PASS。重啟本機服務後用實體鏡頭 2/1 檢查 `/api/live` 為 live、雙側人物照片有保存、`/api/photo/A/1` 回傳 JPEG 200、瀏覽器照片載入無破圖。當次多人場景只見 ambiguous 候選，尚無真實 P 配對可供現場人工正誤核對；並排照片的資料流程由合成測試確認，實機配對展示仍待兩鏡頭出現滿足門檻的同一人。

## 2026-10-02 變更：跨鏡頭外觀分數修正

- 使用者提供同一人出現在兩台鏡頭、A 鏡頭只見部分身體的截圖，舊版網頁分數約 0.367。舊特徵使用 192 格 HSV 直方圖，且取上下兩區較低的交集分數，對曝光及視角裁切敏感。
- `person_tracking/dual_camera.py` 改用 15 維平滑色彩統計：低彩度區依明暗柔性分配，彩色區依相鄰色相格分配；`cross_camera.py` 的總分改為上區 75%、下區 25% 的交集加權和。保留 0.72 門檻、互為最佳、次佳差 0.08 與三次連續確認。
- 對提供的截圖框位置離線重算，同一人約 0.84；圖中藍衣及白衣其他人物約 0.46、0.60。單張截圖有框線與壓縮，僅為針對該例的檢查，未建立一般化準確率。單元測試含明暗改變、只見上半身、黑白差異、上下衣交換及配對規則。
- 同步移除 `sequential_handoff.py` 對舊 192 維特徵的硬編碼，特徵庫依偵測結果的形狀建立；其 JSON 輸出欄位改為 `upper_lower_color_histograms`。既有外部讀取舊欄位的程式須對應更新。
- 重啟本機雙鏡頭服務後，以鏡頭 2/1 驗證 `/api/live` 為 live，兩側都有人物偵測；當次候選分數約 0.62–0.85，多人外觀相近的候選被標為 ambiguous，沒有被強制賦予 P 身分標籤。背景 AI 約 1.8 FPS。這是現場功能檢查，未逐一標記每個人的真實身分。

## 2026-10-02 變更：雙鏡頭即時 localhost 儀表板與實機驗證

- 新增 `影像處理/ModelSim_YOLOX_PersonTracking/live_site/dual_server.py`、`dual_index.html` 與 `start_dual.ps1`。Server 僅綁定 `127.0.0.1:8766`，以雙 DirectShow capture、兩個獨立 `Tracker` 和既有 `CrossCameraMatcher` 在記憶體中處理畫面；`/api/live` 回傳兩張 JPEG、各側人物和候選配對。閒置 10 秒後釋放兩台鏡頭。
- 實機確認鏡頭 0（Integrated Camera）與鏡頭 1（Logitech C270）可同時擷取 30 張 640×480 影格。兩側各自送入 `run_rtl`，均回傳 `PERSON_RTL_PASS: 30 person/empty regions`，ModelSim 編譯／模擬為零 error、零 warning。該批沒有 confirmed P 候選；這是外觀門檻未連續滿足的結果，非擷取或 RTL 失敗。
- 網頁即時模式不呼叫 ModelSim，避免在每一幀阻塞瀏覽器畫面；ModelSim 驗證仍由 `run_dual_camera.ps1 -Rtl` 的離線擷取流程負責。
- 儀表板初版把 AI 完成後的註記影格直接當作串流來源，雙鏡頭 CPU 推論約 1.7 FPS 時造成頁面卡頓。現改為 capture thread 每 0.1 秒最多 JPEG 編碼一次並即時回傳最新 A/B 影格，process thread 只更新人物／候選 metadata；`dual_index.html` 以 DOM overlay 繪製框線。實測網頁畫面約 9 FPS、背景 AI 1.6 FPS、AI 延遲約 0.7 秒。框線可比底圖落後一個推論循環，屬刻意的延遲／視覺流暢度取捨。

## 重要：目前最新版本在哪裡

使用者確認的最新工作方向，以及本機檔案/執行記錄所支持的最新整合版，源自 `C:\Users\USER\Desktop\codex\專題\modelsim_draft\`；已同步至本倉庫 `影像處理/ModelSim_YOLOX_PersonTracking/`。後續應以該路徑為共享程式碼基線，較早的 8×8 合成 testbench 不得覆蓋它。

2026-09-30 已把單鏡頭、雙鏡頭、RTL 與即時網站的必要原始碼同步進共享路徑。YOLOX 35 MB 權重、公開測試圖片、相機實拍圖、生成報告畫廊、ModelSim WLF/transcript 和本機 OpenCV binaries 均排除；以 `person_tracking/setup_assets.ps1` 下載模型及公開測試圖片，模型 SHA-256 會核對。`modelsim_draft` 本身不是 Git checkout；原始執行紀錄仍只存在本機，本次只同步程式/文件並整理可重建安裝方式，沒有上傳相機影像。

## 接手與同步規則

1. 每次工作先檢查共享倉庫 `git fetch origin`、目前本機/遠端分支與狀態，再檢查 `modelsim_draft` 最新檔案和結果時間；先判斷哪裡有較新的程式/紀錄。
2. 進行程式修改前，先明確選定最新源碼基線並檢視差異；不確定時保留兩邊，不做整批覆蓋。
3. 程式碼改動要同步至共享 GitHub `main`，同一變更更新本文件及 `PROGRESS_FOR_HUMANS.md`，提交並推送。
4. 模型權重和生成的個人相機/人物影像不要加入 Git；使用 `.gitignore` 與 `setup_assets.ps1` 的 hash 驗證下載模型。
5. 區分原始碼檢閱、已有 ModelSim/測試紀錄、USB 實拍，以及雙實體鏡頭驗證；不可互相代替。

## 最新整合版的組成（本機 `modelsim_draft`）

### 單鏡頭人物偵測、追蹤與 ModelSim RTL

使用說明：`modelsim_draft/person_tracking/README.md`；共享驗證摘要：`person_tracking/verification_report.json`。HTML 報告仰賴本機相機影格資料，僅留在來源機器。

- `person_tracking/pipeline.py`：使用 OpenCV Zoo 的 YOLOX ONNX 模型在 CPU 偵測人物；專題自寫 `Tracker` 依位置與 HSV 外觀做短期關聯、確認/維持/超時管理，輸出暫時性的 track ID。這不是 YOLOX 自帶的跨鏡頭 Re-ID。
- `person_tracking/person_roi_stream.v`：接收 640×480 完整 RGB888 影格（307,200 pixels/frame）及人物框座標，逐像素累積框內上/下兩區 8 色統計。這是 ModelSim RTL 特徵處理，外部偵測框由 CPU YOLOX 提供。
- `person_tracking/person_feature_compare.v`：比較同一 track ID 前次與本次的上下區域主色/比例特徵；最多 35 個百分點差異。
- `person_tracking/tb_person_roi.v`：將完整 RGB 與框座標交給 RTL。驗證報告記載每幀處理完 307,200 pixels；RTL testbench 暫存各 ID 歷史特徵供比較，範圍 ID 1–4095。
- `person_tracking/run_*` 與 `modelsim_draft/run_person_tracking.ps1`：拍攝/影像序列轉換、ModelSim 批次執行與輸出結果。

### 雙 USB 鏡頭候選配對

共享程式路徑：`影像處理/ModelSim_YOLOX_PersonTracking/`。操作文件 `person_tracking/DUAL_CAMERA.md`；入口 `run_dual_camera.ps1`；主要邏輯 `person_tracking/dual_camera.py`、`person_tracking/cross_camera.py`。

- `dual_camera.py` 使用兩個不同 USB 裝置索引，各自擷取 640×480 影格、呼叫相同 YOLOX detector、維護兩個互相獨立的本地 tracker；可用 `-Rtl` 對 A/B 各自執行 ModelSim ROI 特徵驗證。
- `cross_camera.py` 是自寫 Python 外觀候選配對：人物框中央 60% 寬度、上下區 HSV 直方圖；兩區相似度至少 0.72、雙方互為最佳候選且與次佳差至少 0.08，連續三次確認才分配 P 候選標籤。
- A:track_id 與 B:track_id 是鏡頭內局部 ID；P 標籤只代表同時觀測時衣著外觀相似候選，不是身份判定。
- 不是 YOLOX/CNN Re-ID，不含離開 A 後再於 B 出現的歷史資料庫；相機 `grab/retrieve` 只縮小主機讀取間隔，沒有硬體同步保證。整批先擷取再處理，沒有即時雙鏡頭 FPS 聲明。

### 單鏡頭即時網站

- `live_site/server.py` 直接匯入 `person_tracking/pipeline.py` 的 `Detector` 與 `Tracker`。它是既有偵測/追蹤器的 localhost 顯示介面，不另寫第二份推論器，也不在即時迴圈呼叫 ModelSim。
- `GET /api/health` 回報服務名稱/版本；`GET /api/live` 回傳狀態、人物框/ID、影格、FPS 與延遲；`POST /api/start`、`POST /api/stop` 控制相機。Host/Origin 僅允許 localhost/127.0.0.1；約 10 秒無頁面 heartbeat 後釋放相機。
- `live_site/README.md`、`start.ps1`、`index.html` 是說明、啟動器與 UI。歷史 `verification.json` 記錄 health、origin guard、停止、閒置釋放及 live frame integration check 通過；本次沒有重新連 USB 相機或啟動服務。

### 共享包的執行環境

- `requirements.txt` 宣告 NumPy/OpenCV Python 套件；`assets/yolox.py` 是 OpenCV Zoo 模型前處理/推論包裝；`setup_assets.ps1` 取得 YOLOX ONNX 及公開測試圖片並校驗模型 SHA-256。
- 檔案最初在使用者 Codex runtime 環境完成；`run_person_tracking.ps1`、`run_dual_camera.ps1`、`live_site/start.ps1` 現可用 `PROJECT_PYTHON` 或 PATH 的 `python`，並保留 Codex runtime 後備位置。ModelSim executable 可設 `MODELSIM_VSIM`，亦可從 PATH 解析，否則保留原安裝路徑後備。
- 本次只檢閱和同步程式碼，未安裝 dependencies、下載模型或執行腳本；以上安裝/可攜式 fallback 在本次未重新驗證。

## 已有驗證紀錄及其邊界

以下是本機保存的 2026-09-25 記錄，不是本次重新執行：

- ModelSim RTL `PERSON_RTL_PASS`：5 個人物/空景 ROI 手算案例，transcript 為零 compile error/warning。
- USB 單鏡頭實拍兩輪，共 240 幀，均為原生 640×480；報告記載 YOLOX 每輪 120/120 偵測，track ID 1 連續，ModelSim 每輪 120/120 特徵逐筆核對通過，完整 RGB 每幀 307,200 像素。
- 網路照片序列：兩張人物照片、三個亮度層級、每組七個位置；主要人工標記 105 次全匹配、無 ID 切換。三組黑/白/水果無人負例沒有誤報。追蹤單元邏輯 6 項 PASS。
- 已知漏抓：bus 圖中左側大幅裁切的人物，在 21 張變換影格只偵測到 4 張；這些未計入 105 次主要標記，因此不可宣稱任意畫面零漏抓。
- 雙鏡頭整合只看到兩個 `dual_runs` replay 紀錄，各 8 幀，來源是同一 USB 單鏡頭兩輪的已保存影格。兩組 A/B ModelSim RTL 都各核對 8 個 ROI PASS；其中一組有 1 幀出現確認的 P 候選。`dual_camera_capture_completed=false`，沒有接兩台實體攝影機的驗證結果。

## 共享倉庫內其他原型（不是最新整合版）

- `影像處理/MCDPT_Verilog_Two_Image_ReID/` 是 8×8 合成 RGB 色彩分類/閾值原型，最新倉庫提交歷史曾切換至 `person_color_feature.v`、`person_matcher.v` 與 `tb_two_camera_color.v`。它沒有 CPU 偵測器、短期 tracker、完整解析度串流或本機雙 USB 流程。
- MCDPT 為概念參考；舊 8×8 原型不等於 CNN/OpenVINO 深度 Re-ID。

## 專案來源與共享範圍盤點（2026-09-30）

- 最新可執行整合程式仍以 `影像處理/ModelSim_YOLOX_PersonTracking/` 為準；舊 8×8 Verilog 原型保留作歷史脈絡，不得誤稱為最新流程。
- `tools/` 收錄本機專題中的 PDF 頁面抽取、摘要/逐行說明與程式碼截圖輔助工具；`build_line_explanations.py` 預設引用未共享的舊 Vivado RTL，因此僅供歷史參考。其他工具需搭配使用者提供的來源檔或 PDF；目前沒有把論文 PDF 一起放入倉庫。
- `references/MCDPT/` 收錄本機專題引用的 MCDPT 參考實作子集，僅供閱讀，並非本專題執行相依；其上游 README 含 MIT 授權與引用資訊。
- `deliverables/presentations/` 收錄四份本機簡報成品。簡報 OOXML metadata 僅顯示 `Walnut Exporter`，沒有個人帳號名稱；這些是舊原型簡報，不代表最新 ModelSim 實作。
- `deliverables/synthetic-test-patterns/` 收錄四張早期 testbench 的 8×8 合成圖樣；不是相機影像或真實人物照片。
- 舊 `影像處理/MCDPT_FPGA/` EGo1/Artix-7 Vivado 原型已從目前共享檔案樹移除，因使用者明確限定不共享該 Vivado 程式碼；本機原始目錄保留。這次採一般刪除提交，未改寫 Git 歷史，因此較早提交仍包含該原型。
- 明確未納入：`verilog_demo/` Vivado 專案與截圖、`automation/join-weekly-google-meet.ps1`、Codex/應用程式狀態檔、Vivado/XSim 執行日誌、`.Xil`/`build`/套件快取、論文 PDF、個人相機影像、模型權重與生成模擬資料。這些分別是先前明確排除的 Vivado 內容、私人/無關資料、第三方文件或可由原始碼重建的暫存輸出。
- `output/rca_report/` 的畫面截圖未加入；它含本機路徑文字。`.codex-finalizer/` 內簡報候選稿與驗證中介檔和交付簡報重複，未加入。
- `modelsim_draft/person_tracking/verification_report.html` 會連結本機相機影像資料夾，單獨搬入後會形成失效/隱私風險連結，因此只分享其驗證 JSON 摘要，不分享該 HTML 和影像資料夾。

### 2026-09-30 共享內容整理

- 新增 `PROJECT_CONTENTS.md` 作為完整範圍索引、`tools/` 專題工具、`references/MCDPT/` 授權參考程式，以及簡報和合成 test pattern 等交付素材。
- 移除目前分支上的 `影像處理/MCDPT_FPGA/`，避免目前共享檔案樹包含使用者排除的 Vivado 原型；本機原始檔未刪除，Git 舊歷史仍可見。
- 更新本文件、人類摘要及 `影像處理/README.md`，並保留 ModelSim/YOLOX 整合版為唯一最新實作基線。

## 2026-09-30 變更紀錄：同步最新整合版本

- 核對共享遠端分支、本機 `modelsim_draft` README、RTL、單鏡頭驗證 JSON/HTML、ModelSim transcript、雙鏡頭程式/兩組 replay summary，以及即時網站狀態。
- 同步單鏡頭 YOLOX + 自寫短期追蹤 + 完整 640×480 ModelSim ROI RTL、雙 USB 外觀候選配對、本機即時網站及早期 RTL 基準原始碼。
- 增加可攜式 Python/ModelSim 執行路徑選擇、requirements 與模型/公開測試圖片下載腳本。該程式碼包尚未在本次重新執行模擬、相機或網站驗證。
- 排除大型模型權重、公開/私有圖片、相機輸出、生成報告畫廊、WLF 與本機 OpenCV 執行二進位；細節見專案 `.gitignore`。

## 2026-10-02 變更紀錄：單鏡頭 A→B 時序特徵交接

- 新增 `person_tracking/sequential_handoff.py` 與根目錄啟動器 `run_sequential_handoff.ps1`。預設使用同一台 640×480 USB 攝影機，0–10 秒標為 A，10–11 秒切換空檔，第 11 秒起標為 B，B 段再執行 10 秒；時間均可用參數調整。
- A 段用既有 YOLOX 偵測與自寫 tracker。對每個已確認 A track，計算中央 60% 人物框的上下區 HSV 直方圖並累積平均；切換時將特徵庫寫到本機 `person_tracking/runs/handoff_<timestamp>/camera_a_feature_gallery.json`，並重置 B 段局部 Tracker 以模擬新鏡頭 ID。
- B 段仍用同一 YOLOX 與全新 Tracker；新觀測與凍結 A 特徵庫透過既有 `CrossCameraMatcher` 比對。兩區相似度門檻 0.72、互為最佳候選、與次佳差至少 0.08，連續 3 次才顯示 `P<n> SAME-CANDIDATE`。逐影格匹配及摘要寫入本機 `handoff_matches.json`、`summary.json`；不保存影像，輸出路徑在 `.gitignore` 忽略的 `person_tracking/runs/`。
- 預覽視窗顯示 A/B 標籤、局部 track ID 和候選結果；`-NoDisplay` 可純文字執行，按 `q` 可提早結束。預設流程需同一人持續出現在畫面中；若 A 段沒有足夠已確認的 track，B 不會產生候選。
- 此設計測試保存特徵、重置 tracker、時間交接後重新關聯的資料流程；由於同一鏡頭視角/裝置不變，不能證明雙實體鏡頭視角、光照、色彩差異下可正確配對，更不能宣稱人物身分辨識已完成。
- 程式新增後已用本機 USB camera 0 跑完一次 21.125 秒現場流程：A 43 幀、切換 27 幀、B 45 幀；A/B 偵測數皆 0、A 特徵庫 0 個，沒有候選結果。因此此次只證明相機擷取迴圈及時間切段結束，無法判定特徵交接是否成功，也不能說辨認失敗。執行時畫面中未確認有可偵測人物。結果 JSON 在本機 `modelsim_draft/person_tracking/runs/handoff_20261002_100707/`，沒有保存/上傳影像。
- 第一次由 PowerShell 啟動時選到 WindowsApps Python alias，啟動失敗；`run_sequential_handoff.ps1` 已調整為優先選 Codex bundled Python，再退回 PATH，後續現場重跑應使用此啟動器。
- 需要同一人完整出現在 A 與 B 畫面中重跑，才可得到 `candidate_found` 或「B 有人物但未達配對」的有效結果。既有 2026-09-25 雙 USB replay 數據是歷史紀錄，不是此新模式的驗證。

## 2026-10-02 變更紀錄：人工審核照片自動淡出

- `影像處理/ModelSim_YOLOX_PersonTracking/live_site/dual_index.html`：本頁操作以 POST 成功的本機時間開始計算，重整後改用伺服器回傳的 `reviewed_at`。按 ✓／✕ 後，配對照片保留約 5 秒、再淡出約 0.6 秒，然後從 DOM 及版面移除。已審核人物縮圖在沒有其他待審核配對使用該 Track ID 時也收起；未配對人物照與待審核照片仍顯示。頁面保留已審核同／不同人計數及「查看／修改已審核照片」切換，可重新展開改判；頁面重整不會讓舊審核照片永久重現。
- `dual_server.py` 的 `review_pair` 將審核時間記為毫秒精度 ISO 本機時間，支援較準確的五秒 UI 倒數；舊 manifest 秒級時間仍可解析。`test_dual_server.py` 增加時間格式檢查。
- 資料流未加入訓練：UI 審核寫入本次工作階段的 `matched_pairs`／`manifest.json`，正面判斷只凍結配對照片，負面判斷另在 `process()` 中轉為同一組 A/B Track ID 的 `excluded_pairs`，傳給 `CrossCameraMatcher.update()`；新工作階段沒有讀回舊標籤，`appearance_similarity()` 仍是固定 HSV 直方圖加權，YOLOX 權重未更動。五秒收起只是網頁視覺行為，本機 JPEG 仍留存至明確按停止時按 manifest 清除。
- 驗證：`live_site/test_dual_server.py` 6 項合成單元測試 PASS；兩段網頁 JavaScript 語法檢查 PASS；純函數 `reviewPhase()` 的 4999／5000／5599／5600 ms 邊界測試 PASS；目前執行中的 localhost:8766 已從磁碟回傳含新版淡出／重看按鈕的 HTML。未用真人雙鏡頭實拍驗證淡出視覺效果或配對準確率。執行中的 Python 服務未重啟（環境拒絕重啟命令），因此該程序仍以舊版秒級時間寫新審核；頁面操作已用 POST 完成時間作精確倒數，重整後亦可解析舊秒級時間，新啟動服務才會使用毫秒時間。

## 2026-10-02 變更紀錄：保留既有版本並同步目前進度

- 同步前 `HEAD` 與 `origin/main` 均為 `47773ef`，工作樹只有兩份未追蹤的精簡測試紀錄；既有程式、雙鏡頭網站、人工審核與五秒淡出已在遠端。本次採追加提交，不 force push、不刪除或覆蓋既有內容。
- 新納入 `影像處理/MCDPT_Verilog_Two_Image_ReID/modelsim_transcript_20261002.txt`：2026-10-02 00:28 的早期 8×8 RTL testbench 執行紀錄，`vlog` 顯示 0 errors／0 warnings，`vsim` 印出 3 個同人 frame `same = 1`、1 個不同人 `same = 0`，最後 `two camera color test ok`、0 errors／0 warnings。此檔為已存在的本機紀錄，本次只檢查文字並歸檔，沒有重新執行 ModelSim；不可當成最新 640×480 YOLOX／雙實體 USB 流程通過的證據。
- 新納入 `影像處理/ModelSim_YOLOX_PersonTracking/person_tracking/tests/tracking_results.json`：既有測試摘要記載 `tests_run=6`、`failures=0`、`errors=0`、`status=PASS`；本次尚未確認其個別測試案例或重新執行。被 `.gitignore` 排除的 `tests/rtl_*/` 逐次輸出中另有 `summary.json` 記載 5 個手算區域、307200 pixels/frame、PASS，但它和 WLF、完整 run 產物仍不入 Git；歷史驗證請區分摘要與原始輸出。
- `PROJECT_CONTENTS.md` 與 `PROGRESS_FOR_HUMANS.md` 更新共享範圍。`person_tracking/live_captures/` 的人物 JPEG／審核 manifest、下載的 YOLOX 權重、相機影格、大型 replay／run 與 WLF 等仍保留本機，不因本次「同步全部」而上傳；這遵循既有隱私與產物排除決策。若後續確實需要共享含人物的標註資料，應另行界定同意、匿名化及存取方式。
## 2026-11-03：無鏡頭的 Cloudflare Quick Tunnel 等待模式

- `live_site/dual_server.py` 新增明確 opt-in 的 `--allow-trycloudflare`。服務在保留既有 localhost/LAN Host + `http` Origin 檢查的前提下，額外允許 `https://*.trycloudflare.com`；這處理 Quick Tunnel 每次重啟有不同主機名，且反向代理可能把 Host 改寫為 local origin 的情況。初始 HTML 導航沒有 `Origin` 時，僅在 Host 本身是 `*.trycloudflare.com` 才放行。沒有此旗標，遠端 Origin 一律維持拒絕。新增 `--camera-a`／`--camera-b`，可在尚未開啟擷取前把等待中的預設相機組合回報給 `/api/live`，`camera-b=-1` 代表目前未配置第二台。
- 新增 `live_site/start_remote.ps1`：以目前專題目錄啟動服務、等待本機 health 成功、啟動未登入的 Cloudflare Quick Tunnel、將當次 URL 寫入被忽略的 `work/remote_site/private-link.txt`。它不會呼叫 `/api/start`，所以沒有鏡頭時仍維持 stopped 等待；每次啟動會停止本專題原有的 8766 listener，以確保新 tunnel 指向新服務。Cloudflare 執行檔與所有 URL/log 都只放使用者本機。
- `live_site/README.md` 明確說明服務可在沒有相機時保持 `stopped`，只有 `/api/start`／網頁連接動作才會碰相機；Quick Tunnel 連結、token、模型和相機相片屬本機私密資料，不入 Git。
- 2026-11-03 已在此電腦以 CameraA 0／CameraB -1 的等待設定啟動新 Quick Tunnel；未呼叫 `/api/start`，因此沒有相機實測或照片產生。透過新 HTTPS URL 的首頁回應 HTTP 200，`/api/health` 回傳應用程式/版本，`/api/live` 回報 `stopped`、`enabled=false` 和 cameras `[0, -1]`；當時 cloudflared 程序仍在執行。連結、log 與 `cloudflared.exe` 均只在使用者本機，不加入此倉庫。

## 2026-11-05：對話／進度同步紀錄

## 2026-11-06：USB→DDR→DMA Block Design 時脈收斂工作（進行中）

## 2026-11-06：Vitis Embedded platform 與 A53 控制 ELF（host build PASS）

- 已以完整 Vitis Embedded Development 2024.2 安裝建立 `psu_cortexa53_0` / `standalone_domain` platform，從已匯出的 USB/DMA XSA 成功產生 BSP、ZynqMP FSBL 與 platform export（`export=SUCCESS`）。
- 實際編譯產生 `pynq_zu_usb_video_app.elf`（265,944 bytes）。生成的硬體標頭確認 mailbox 宏為 `XPAR_YOLOX_VIDEO_RTL_0_BASEADDR`，因此 `src/main.c` 已由舊的 `_S_AXI_BASEADDR` 名稱修正。Vitis 預設 hello-world 範本多出示範 main，建置腳本會從生成清單移除它。
- 新增 `vitis/pynq_zu_usb_video/build_vitis_embedded.py`；以 `PYNQ_ZU_USB_VIDEO_XSA` 提供 XSA，並從短、空的 `PYNQ_ZU_VITIS_WORKSPACE`（預設 `C:\pynq_vitis`）可重建 platform/app。Windows 長暫存路徑會使 GCC 無法建立相依檔，故不可使用長 `%TEMP%` workspace。
- 驗證界線：這是本電腦 host-side Vitis build；尚未把此 XSA/ELF JTAG 下載到 PYNQ-ZU，尚未啟動 USB UVC、DDR DMA、PL stream、mailbox 或 IRQ 實機測試。Embedded 安裝和 `C:\vw`/`C:\vc` temporary build 均不入 Git，第三台也尚未安裝或驗證。

### 2026-11-06 後續 JTAG 掃描

- `hw_server` 在 localhost:3121 運作、Windows 也可見 FTDI USB Serial Converter A/B 與 COM5，但 XSCT 連線後沒有列出任何 JTAG target；重啟 Hardware Server 再掃描結果相同。因此未對板子寫入 bitstream 或 ELF。下一個實機步驟需先使板子供電、JTAG boot switch 和 JTAG chain 可被 Hardware Server 枚舉，再執行下載與 mailbox read/write。

### 2026-11-06 後續：JTAG PL／A53 AXI 控制實機 PASS

- 更正先前 JTAG 診斷：Vivado Hardware Manager 一直可開啟 `Xilinx/1234-tulA` target，並列出 `xczu5_0` / `xczu5` 和 `arm_dap_1`；XSCT 必須用 `connect -host localhost -port 3121` 才會枚舉 PS TAP、PSU、APU 與 Cortex-A53 targets，先前的 `-url tcp:...` 形式在此環境沒有取得 target tree。
- 已以 Vivado 成功下載 `pynq_zu_usb_video.bit`（7,797,821 bytes）到實機 `xczu5_0`；Hardware Manager 回報 device programmed。再以 XSCT 實跑：system reset、`psu_init.tcl` PS/DDR init、PL bitstream、Cortex-A53 #0 ELF download/run/stop。
- `src/main.c` 現對實機提交 frame ID 42 的 bbox command，讀回 AXI GPIO 與 mailbox frame/status，並保存 JTAG 可讀的 volatile 結果。乾淨流程實測：result `0`、GPIO readback `42`、mailbox frame readback `42`、status `3`（唯一 command 的 pending/pair-present，沒有 overrun）。這是 Vitis A53→PS AXI→PL AXI GPIO/mailbox 的硬體 PASS。
- 限制仍明確：沒有 UVC frame producer 或 AXI DMA transfer，所以 command 停在 pending 是預期；尚未驗證 PS USB/UVC capture、DDR buffer、DMA MM2S、PL feature/result、IRQ 或雙攝影機實際影像。

- `fpga/create_pynq_zu_usb_video_bd.tcl` 的 USB 路徑仍正確限定於 MPSoC PS：USB0 為 MIO 52..63、USB1 為 MIO 64..75；UVC frame 必須先落 DDR，再由 AXI DMA 的 MM2S 64-bit AXI4-Stream 餵入 PL。USB D+/D- 不是 PL 可接的獨立影像腳位。
- 以乾淨 Vivado 2024.2 實作觀察到既有 ROI feature accumulator 在 100 MHz 的 post-placement WNS 約 -35 ns；尚未生成或下載該違反時序版本。BD 的 PL0 與 `dual_camera_yolox_axis_top.v` 介面宣告已一併改成 20 MHz，理論 AXI4-Stream 峰值為 160 MB/s。
- 20 MHz 的乾淨 project staging PASS，但 Vivado 在 `create_bd_cell -type module -reference dual_camera_yolox_axis_top` 建立 module-reference 的 GUI interpreter 時出現 `rodin:slave11` / Customization-object 錯誤；尚未完成 BD validation、implementation、bitstream、XSA 或 Vitis BSP build。下一步須改以可重現的自訂 IP 封裝或避開 module-reference cache，再重新檢驗時序。

- 新增根目錄 `CONVERSATION_PROGRESS_LOG.md`，以精簡、可交接方式記錄每次已完成進度的需求、變更、驗證界線、Git 提交／推送結果和未完成事項；不保存逐字聊天、帳密、私人連結、個人影像或模型權重。
- `AGENTS.md` 已規定未來每次可交付進度均須追加該紀錄，並與相關檔案同次 commit + push 至 `main`。純討論、沒有檔案變更或未完成工作不製造完成紀錄。
- 本次稽核時 `main` 與 `origin/main` 同為 `5fe1467`；最近的 PYNQ-ZU/IRQ/USB 部署工作已有遠端提交。沒有發現既有對話紀錄檔，故不能由 Git 判斷或還原未曾落檔的舊聊天內容。未追蹤的 Vivado/XSim 與本機網站日誌維持排除，並非待上傳的專案原始碼。

## 2026-11-05 變更紀錄：PYNQ-ZU 可重建 bring-up bitstream 與 JTAG 實機下載

- PYNQ 目標已確認為 **PYNQ-ZU**（`XCZU5EG-SFVC784-1-E`），不是 PYNQ-Z1。Vivado Hardware Manager 實機枚舉為 `XUPJTAG` 下的 `xczu5_0`；板子供電恢復後可讀到裝置。依 PYNQ-ZU 官方手冊，直接由 Vivado JTAG 下載時 boot switch 使用 **JTAG（左側）**；SD 是從 SD card 開機 PYNQ Linux 的模式，兩者用途不同。
- 新增 `fpga/implement_pynq_zu_yolox.tcl`，會驗證 project/BD/wrapper，執行 `impl_1` 至 `write_bitstream`，並只在 `write_bitstream Complete!` 及 `.bit` 實際存在時回報成功。腳本沒有降低 UCIO/NSTD DRC 嚴重度。
- Windows 原始路徑含中文使 Vivado 子綜合程序無法解析來源；`create_pynq_zu_rtl_project.tcl` 現將八個必要 HDL 檔 stage 到可設定短 ASCII build directory 的 `rtl_src/` 後再加入 project。`synthesize_pynq_zu_yolox.tcl` 會先 reset 舊 `synth_1` run，避免重用 run 時的 reset 要求。
- 100 MHz 設計實作時 WNS 約 -32.945 ns，未下載至板。時脈降至 20 MHz 後，完整 external-video 版本 route WNS +0.013 ns，但因外部 video/result ports 沒有 XDC 而被 UCIO-1 正確阻止 bitgen；沒有繞過該 DRC。
- 預設 bring-up Block Design 使用 PS→SmartConnect→AXI4-Lite mailbox（`0xA000_0000`，4 KiB）、20 MHz PL clock。尚未指定板級來源的 video inputs 以常數 idle 驅動，result ports 不外拉至未約束的 PL pins。這版可驗證 PS/PL clock、AXI-Lite 與 JTAG，不是雙攝影機資料流。
- 本機 `C:\\pynq_zu_bringup` 的實作/bitgen 已完成（0 errors、0 critical warnings）；產物為 `C:\\pynq_zu_bringup\\pynq_zu_rtl.runs\\impl_1\\pynq_zu_yolox_wrapper.bit`。2026-11-05 已在 Vivado Hardware Manager 對實機 `xczu5_0` 成功下載；狀態顯示 `Programmed`，Tcl console 回報該 JTAG device is programmed。這是易失性的 JTAG PL 設定，不會寫入 SD 或開機 flash，斷電後消失。
- 尚未驗證：PYNQ Linux 下的 Overlay/HWH + MMIO 存取、AXI mailbox 實際讀寫，以及相機/DMA/CSI/HDMI 影像路徑。要啟用真實 video ports，必須先選定介面並提供對應 IP、clock/reset/CDC、XDC，再以 `PYNQ_ZU_EXPORT_VIDEO_PORTS=1` 重建；不可把此 bring-up 成功誤稱為雙鏡頭功能完成。

### 2026-11-05 後續：SD-boot overlay 部署準備

- 新增 `fpga/prepare_pynq_zu_overlay.ps1`，從完成的短 ASCII build directory 複製 `.bit` 與 handoff `.hwh`，並統一命名成 PYNQ Overlay 所需的同 stem `pynq_zu_yolox.bit` / `pynq_zu_yolox.hwh`。本機已以 `C:\\pynq_zu_bringup` 實跑，輸出目錄 `C:\\pynq_zu_bringup\\overlay` 包含 7,797,817-byte bitstream 與 182,680-byte HWH；兩者是可部署產物，沒有加入 Git。
- 新增 `person_tracking/verify_pynq_zu_bringup.py`：在 PYNQ Linux 下載 Overlay，對 mailbox `0xA000_0000` 的 frame-ID 做 write/readback，再清回 0。已在開發電腦通過 Python syntax compile；尚未在板上執行，因此不能當成 MMIO 實機 PASS。
- 板子目前仍因 JTAG 模式/目前電腦網段為 `192.168.50.x` 而無法存取既有 `http://192.168.3.1/lab`（瀏覽器為 `ERR_CONNECTION_RESET`，ICMP 亦沒有回覆）。下一個實機步驟需切回 **SD**、重新上電使 PYNQ Linux 開機，再把 overlay 檔案與驗證腳本上傳到板端；這與已完成的 JTAG PL 下載是兩個不同階段。

## 2026-11-05 變更紀錄：PS IRQ 與 PYNQ-ZU 雙 USB 鏡頭網站部署包

- 盤點後確認先前設計沒有任何 RTL IRQ 或 PS IRQ 接線，故「中斷問題」是未實作而非 JTAG 連線故障。`yolox_bbox_axilite.v` 新增 `IRQ_STATUS` (`0x18`, W1C) 和 `IRQ_ENABLE` (`0x1c`)；bit 0=雙路 feature 完成、bit 1=confirmed、bit 2=frame command missing、bit 3=mailbox overrun。只要 enable 的 sticky bit 尚未清除，`irq` 維持 level high。
- `dual_camera_yolox_axilite_top.v` 匯出 annotated `irq`，`create_pynq_zu_yolox_bd.tcl` 啟用 PS `IRQ0` 並接到 `pl_ps_irq0`。`dual_camera_yolox_axis_top.v` 同步匯出 irq；`pynq_yolox_mmio.py` 加入 set/read/clear IRQ helpers。XSim `tb_yolox_command_path.v` 以 result 和 overrun 事件驗證 enable、assert、W1C clear，輸出 `YOLOX_COMMAND_PATH_PASS checks=9`。
- 在乾淨 `C:\\pynq_irq_build` 做了完整 project/BD/synth/impl：synthesis 0 error/0 critical warning；implementation 的 DRC 0 error，bitgen 0 warning/0 critical warning，post-placement WNS +47.095 ns。產物 `C:\\pynq_irq_build\\pynq_zu_rtl.runs\\impl_1\\pynq_zu_yolox_wrapper.bit` 已在 Hardware Manager 對實機 `xczu5_0` 成功下載，Tcl console 回報 device programmed。
- `live_site/dual_server.py` 現會依平台使用 Windows DirectShow 或 Linux V4L2，新增 `pynq_usb_camera_preflight.py`、`start_pynq_dual.sh` 和 `prepare_pynq_dual_bundle.py`。後者可把既有雙鏡頭網站、YOLOX ONNX、追蹤程式與可選 Overlay 打成 PYNQ 可傳送 tarball。本機已成功產生 `C:\\pynq_irq_build\\pynq_zu_dual_deploy.tar.gz`（33,467,184 bytes），列出的 12 個檔包含 `overlay/pynq_zu_yolox.bit/.hwh`；不把模型/bitstream 產物提交到 Git。
- 未驗證且仍必須完成：PYNQ SD-boot Linux 的 Python/OpenCV/V4L2 相依、兩支實際 USB webcam `/dev/video*`、YOLOX 推論、LAN 網站畫面、Overlay/MMIO/IRQ 實機事件。現行 FPGA bring-up 沒有 USB capture-to-RTL 資料路徑；雙 USB 網站是由 PYNQ PS CPU 取 UVC 影像、執行既有 YOLOX/Tracker，這符合原 Python 網站資料流但不能稱 USB frame 已進 FPGA ROI core。

## 2026-11-05 變更紀錄：可攜的 PYNQ-ZU SD-boot 一鍵部署

- 新增 `live_site/deploy_pynq_zu.ps1`。它以參數取得 `-BoardHost`、可選 `-BoardUser`（預設 `xilinx`）、`-RemoteDir`、兩個 camera index、板端 Python 指令與可選 Overlay 目錄；沒有硬編碼任何電腦 IP、使用者資料夾、Vivado build 或密碼。它先要求本機 Python/Windows OpenSSH `ssh`/`scp`，再呼叫 bundle builder，SSH 探測板端、SCP 上傳、解壓並驗證 ONNX 已到位。目標目錄存在即失敗，刻意不覆寫或遞迴刪除板上資料。
- `prepare_pynq_dual_bundle.py` 現也納入 `person_tracking/verify_pynq_zu_bringup.py`，所以同一個 tarball 可供板端 Overlay/MMIO bring-up；Overlay 仍是選配，只有指定 `-OverlayDir` 才隨包傳送。`-RunCameraPreflight` 在解壓後以 V4L2 檢查兩支 UVC；`-RunBringupCheck` 會將同包的 bit/hwh 複製到驗證程式旁、下載 Overlay，並檢查 mailbox `FRAME_ID` write/readback。兩種開關都會在失敗時保留部署資料供診斷。
- `live_site/README.md` 已提供從 clone 根目錄直接貼上的 PowerShell 命令。資料流程是：Git tracked source+YOLOX ONNX → 暫時 tarball → SSH/SCP → `~/pynq_dual_dashboard` → 可選 preflight/MMIO → 板端 `start_pynq_dual.sh`。此入口不讀取 `C:\pynq_*`、`%TEMP%` 既有產物或目前使用者的設定；暫時 tarball 僅在執行電腦的暫存區生成。
- 本機驗證：三支 Python 腳本 `py_compile` 通過；實際建立 tarball 並以 `tar -tzf` 核對 11 個必要檔（網站、YOLOX ONNX、追蹤程式、preflight、bring-up verifier）皆在包內；PowerShell AST parse 與 `git diff --check` 通過。未驗證：不同電腦的 Python/OpenSSH 安裝、板端 SSH 認證、PYNQ Linux/OpenCV/V4L2、USB 鏡頭、Overlay/MMIO 及 LAN dashboard；不可據此宣稱上板成功。

### 2026-11-05 後續：新 clone 的 YOLOX 模型取得與完整性

- 可攜性稽核發現 `person_tracking/assets/yolox.onnx` 已被專案 `.gitignore` 排除，原本的新 clone 無法通過 bundle builder 的檔案檢查。`prepare_pynq_dual_bundle.py` 現在以標準函式庫 `urllib.request` 於模型不存在或 SHA-256 不符時，從 `sources.json` 記錄的 OpenCV Zoo public model URL 下載到被忽略的 assets 路徑；只有 SHA-256 `c5c2d13e59ae883e6af3b45daea64af4833a4951c92d116ec270d9ddbe998063` 符合才以原子 replace 寫入並進入 tarball。暫存 `.onnx.download` 在成功、雜湊錯誤或下載失敗時均清除。
- 本機驗證：`prepare_pynq_dual_bundle.py` syntax compile 通過；本機現有模型 hash 與固定值一致；實際 bundle 建立並確認 `person_tracking/assets/yolox.onnx` 在 tarball 中。新電腦第一次打包必須可連網取得約 35 MB 公開模型，未在無模型的新電腦實測下載；此限制已在 README 明示。模型本體仍不進 Git。

### 2026-11-05 後續：板端依賴診斷

- 新增 `live_site/pynq_system_preflight.py`，僅讀取板端狀態：輸出 Python/platform，強制檢查 `numpy`、`cv2`、非空 YOLOX ONNX；另嘗試載入 `pynq`，缺少時輸出 `PYNQ_OVERLAY_NOTE` 但不把它誤判成 USB dashboard 的必要依賴。成功標記為 `PYNQ_SYSTEM_PREFLIGHT_PASS`。bundle builder 已納入此檔；`deploy_pynq_zu.ps1 -RunSystemPreflight` 會在 optional UVC preflight 前以板端 Python 執行它。
- 本機驗證：syntax compile、實際 Python 執行（NumPy/OpenCV/model PASS、預期 PYNQ module note）、tar listing 與 PowerShell AST parse 全部通過。此為 Windows 模擬環境檢查，不是 PYNQ Linux/PYNQ package/USB 實機證據。

### 2026-11-05 後續：離線端到端回歸

- 在工作樹乾淨且不接 PYNQ 的條件下執行 `python -m unittest discover -s person_tracking -p test_*.py -v`，結果 18 tests OK；覆蓋本地 tracker 交叉／遮擋、跨鏡頭候選連續確認／互斥、衣著特徵與相機 index 防護。於 `live_site` 執行 `python -m unittest test_dual_server.py -v`，結果 6 tests OK；覆蓋人物快照、人工配對、審核凍結、拒絕 pair 排除、照片清除與特徵歷史。
- 另實跑 `person_tracking/open_xsim_regression.ps1 -Batch`（Vivado 2024.2），XSim 編譯、elaborate 及模擬成功，輸出 `RTL_REGRESSION_PASS frames=7 checks=89`。暫存 XSim 輸出位於 `%TEMP%`，未納入 Git。上述皆為 host 模擬／合成測試；沒有呼叫 USB 相機、SSH、PYNQ Linux、Overlay/MMIO 或硬體 IRQ。

### 2026-11-05 後續：可重跑的 mailbox／IRQ XSim 回歸

- 新增 `fpga/open_xsim_yolox_command_path.ps1`，將 `yolox_bbox_axilite.v`、`yolox_frame_command_adapter.v` 與 testbench stage 至 `%TEMP%/project_xsim_yolox_command_path`，用 `xvlog`、`xelab`、`xsim` 執行。可傳 `-Batch` 供 CI/終端 PASS/FAIL，省略則開 GUI；`VIVADO_XSIM_BIN` 可覆寫 Vivado bin。這使新電腦能重跑 AXI-Lite payload commit、overrun、frame-ID 對齊、bbox latch／consume、result/overrun IRQ/W1C clear 測試，不需接 PYNQ。
- 本機實跑 Vivado 2024.2 結果為 `YOLOX_COMMAND_PATH_PASS checks=9`。更正先前文件誤載的 `checks=5`；目前 testbench 的 9 個 assert 才是可重現的實際輸出。此測試不包含 PS Block Design、Overlay 或硬體 IRQ 電氣連線。

### 2026-11-05 後續：乾淨 GitHub clone 的可攜部署驗證

- 使用 `git clone --depth 1 https://github.com/yycc0112299/-.git` 至全新 `%TEMP%/pynq_portable_clone_<GUID>/repo`，在該 clone 直接執行 `live_site/prepare_pynq_dual_bundle.py --output <temp>/pynq_dual_dashboard.tar.gz`。clone 內原本沒有 `.onnx`（ignore 規則生效），輸出明確顯示從 OpenCV Zoo URL 下載 YOLOX，並成功建立 tarball；`tar -tzf` 列出 11 個必要項目。這直接驗證了新電腦所需的 Git tracked source → model bootstrap → bundle 資料流，而不依賴原開發工作樹的模型或 Vivado 產物。
- 驗證界線：此為同一台 Windows 的全新目錄／遠端 clone 模擬，證明 GitHub snapshot 和公開模型來源可用；尚未驗證另一台實體電腦、Windows OpenSSH、PYNQ SSH 認證、Linux package、UVC、Overlay 或 LAN dashboard。暫存 clone、下載模型與 tarball 位於 `%TEMP%`，非專案原始碼，不納入 Git。

### 2026-11-06：PYNQ-ZU 官方 SD 映像重新燒錄（Etcher 驗證完成）

- 官方 AMD download 的 `pynq_zu_v3.1.1.zip`（2,250,235,183 bytes）SHA-256 為 `7F61F9F7D9B74DB2DE64B8AC443CE472894C3FA70426906367A4386928F5A810`，與本機既有同名 ZIP 完全一致。ZIP 中的唯一映像為 `pynq_zu_2025_09_25.img`（9,840,650,240 bytes），所以既有「2025-09」映像實際上就是目前官方 v3.1.1，不是另外一個舊版本。
- 使用 balenaEtcher 重新選取該 `.img` 與人工核對的 `Generic- Multi-Card USB Device`（15.9 GB；先前 Windows disk inventory 為 Disk 2），而非沿用 Etcher 的舊成功畫面。新一輪流程完成寫入後進入 Verify；即時觀察到驗證 6%、22%、37%、52%，速度約 19.5–19.8 MB/s，最後 Etcher 對本輪的 `pynq_zu_2025_09_25.img` 顯示「燒錄成功」，完成速度 23.2 MB/s。這是工具的整體寫入與驗證 PASS 證據。
- Etcher 成功後自動卸載目標；Windows 隨後對 Disk 2 顯示 `No Media`／0 bytes，故未把先前舊卡的分割區列舉誤當作本輪後驗證。需重新插回板子後，才能驗證 PS-STATUS、DONE/LED、USB Composite 網卡、`192.168.3.1/lab`、SSH、Overlay/MMIO 及 UVC；本次不宣稱這些板端功能已通過。
- 官方 ZIP、解壓 `.img` 和重複下載副本位於 `C:\Users\dsic\Downloads\`，是大型可重新取得的本機部署媒體，未加入 Git；本次只同步程式交接紀錄。
- 這次紀錄已在整合共享 `main` 的新增提交後，以 `65c36f8` 成功推送至 `origin/main`；沒有覆寫其他電腦先行推送的校正／benchmark 變更。

### 2026-11-06：PS USB→DDR→AXI DMA→PL Block Design 已完成可攜 XSA 匯出

- 新增 `fpga/package_pynq_zu_video_ip.tcl`：將 staged RTL 封裝為 `project.local:video:dual_camera_yolox_axis:1.0` 的 IP Catalog core。`create_pynq_zu_usb_video_bd.tcl` 先要求這個本機 build 目錄內的 IP repository，再由 IP Catalog 建立自訂 stream/AXI-Lite IP；此作法取代在 Windows batch 環境會失敗的 module-reference GUI cache。
- 以全新 `%TEMP%` build 實跑封裝與 `validate_bd_design` 成功。完整 Vivado 2024.2 synthesis、implementation、DRC、bitstream 和 `write_hw_platform -include_bit` 均完成：bitgen DRC 為 0 errors；routing 估算 WNS `+0.193 ns`、WHS `+0.012 ns`；XSA 已成功匯出。暫存 build/XSA/bitstream 位於 `%TEMP%`，可由 tracked TCL 重建，不納入 Git。
- 這證明可重建的硬體交付物包含 PS USB 設定、DDR HP0、AXI DMA MM2S、64-bit AXI4-Stream、AXI-Lite mailbox、frame-ID GPIO 與 PS IRQ 接線；不代表兩支 UVC 鏡頭、DDR frame producer、DMA 啟動、PL 演算法或 IRQ 已在實板端端驗證。下一階段須用此 XSA 建立 Vitis platform/BSP/application，再以 JTAG 對板端下載和觀察控制路徑。

### 2026-11-06：Vitis platform 建置環境診斷

- 以匯出的 XSA 實跑 Vitis 2024.2 Python CLI 建立 `psu_cortexa53_0` / `standalone` platform。初始錯誤為 Lopper installation path `null`；盤點確認隨附 Lopper 離線安裝包的 `requirements.txt` 失效，且系統不存在 `C:\Xilinx\lopper_package`。以隨附 wheels 建立本機 virtualenv 並驗證 `lopper -h`、YAML 與 libfdt imports 可執行後，Vitis 已能越過該空路徑檢查。
- 但平台仍在「generate SDT for XSA」階段失敗。此安裝沒有 `xsct`，也缺 Vitis 內的 embedded-software tree；已明確設定 `VITIS_LOPPER_INSTALL_LOC` 與指向 Vivado 隨附 `data/embeddedsw` 的 `ESW_REPO` 重試，結果相同。因此還沒有 Vitis-generated `xparameters.h`、BSP、ELF、JTAG application download 或實機 DMA 控制結果。
- 本機 Lopper virtualenv、Vitis workspace 與診斷暫存均不入 Git；它們是此電腦工具修復產物，不可當作第三台已完成的環境。下一步是在完整安裝 Vitis Embedded Development flow 後以相同 XSA 重跑 platform/app build。

### 2026-11-06：PYNQ SD-boot 實機環境、UVC 與 dashboard bring-up

- 板端透過 USB 網路 `192.168.3.1` 的 JupyterLab 可操作；實測 Linux `6.6.10-xilinx-v2024.1`、Python 3.10.4、NumPy 2.1.5、OpenCV 4.5.4、PYNQ 3.1.1。部署 tarball（含 35,858,002-byte YOLOX ONNX）由開發電腦臨時 HTTP server 傳至板子，不含帳密或私密資料。
- `pynq_system_preflight.py` 實板 PASS；`pynq_usb_camera_preflight.py --camera-a 0 --camera-b 2` 實板 PASS，index 0、2 都實際讀回 640×480 BGR frame。
- 修正 `live_site/dual_server.py`：PYNQ 內建 OpenCV 4.5.4 沒有 `cv2.data`，現在 Haar cascade 會依序找 pip 和系統路徑，找不到時回傳空 cascade，不會阻擋網站。另修正 Host 白名單的無 Origin 首頁導覽，以及 `/api/start`／`/api/stop` 未傳 camera 欄位時保留命令列設定。
- 修正 `start_pynq_dual.sh`、README、PowerShell 部署訊息：參數是瀏覽器使用的 PYNQ 位址（本次 `192.168.3.1`），不是觀看網站的電腦 IP；開發電腦對 `/api/health` 實測成功。
- 驗證限制：啟動後內核記錄 `Not enough bandwidth for new device state/altsetting 7`，接著 USB device 3/4 disconnect；重查 `/dev/video*` 已不存在。這是 USB bus 頻寬／供電或相機協商中斷的實機問題，不可宣稱持續雙鏡頭、YOLOX 或 FPGA video path 已完成。
- 重新插拔的複測：兩支 C270 再次列為 `/dev/video0`–`/dev/video3`；`pynq_usb_camera_preflight.py --camera-a 0 --camera-b 2` 再次 PASS（皆 640×480）。以 v5 dashboard 啟動並由電腦 POST `/api/start` 後，API 正確保留 `[0,2]`，但約 7 秒內狀態變為「雙鏡頭擷取中斷」、frame_id=0。這排除先前 API fallback 到 0/1 的程式錯誤，仍指向兩路同時 UVC 串流的實體 USB 資源問題。
- 為降低 bus load，Linux dashboard 現會協商 MJPEG、預設 320×240、10 FPS（可用 `PYNQ_UVC_FPS/WIDTH/HEIGHT` 覆寫）；preflight 同樣使用該設定。v7 實板仍於雙路開始擷取後 `frame_id=0` 且中斷，故尚未得到網站實際畫面。

### 2026-11-06：完整影格 AXI DMA 實板驗證（Vivado + Vitis + JTAG）

- 修正 `fpga/create_pynq_zu_usb_video_bd.tcl` 的 AXI DMA Simple Mode transfer-length width：由 14 (`0x0e`，單筆約 16 KiB) 提高至 23 (`0x17`，足以承載 640×480×8-byte = 2,457,600-byte packed stream)。先前 14-bit DMA 對完整合成影格回傳 halted (`DMA status=0x1`)，這是設定限制而非板子/JTAG 故障。
- `vitis/pynq_zu_usb_video/src/main.c` 現建立對齊的 640×480 synthetic packed RGB frame，flush cache 後以 `XAxiDma_SimpleTransfer` 由 DDR MM2S 送入 PL，並把結果、GPIO、mailbox、DMA status 保留在可由 JTAG 讀取的 globals。這是 bring-up 的可重現資料源，不是 USB UVC capture。
- 以全新 `C:\pynq_dma_len_build` 完成 Vivado 2024.2 IP Catalog、BD、synthesis、implementation、bitgen 與 XSA export；bitgen 為 0 errors。以新 XSA 建立 `C:\vg` Vitis Embedded platform/app；生成 BSP 的 `XPAR_AXI_DMA_0_SG_LENGTH_WIDTH` 實際為 `0x17`，ELF 為 351,048 bytes。
- 實板 JTAG 驗證：下載新 bitstream、A53 ELF 並執行 5 秒後，讀回 `result=0`、GPIO=`42`、mailbox frame=`42`、mailbox status=`2`、DMA status=`0x1002`；DMA MM2S status register 同為 `0x1002`（idle + IOC completion）。這已驗證 DDR→AXI DMA→PL stream 的一個完整 640×480 synthetic frame，以及 PS→PL control path。尚未驗證 PS USB UVC 擷取、雙 C270 的持續串流、真實 YOLOX inference 或 IRQ handler。
### 2026-11-06：DMA 長度契約與 Vitis 文件同步

- `fpga/tests/test_pynq_zu_usb_bd_contract.py` 現靜態鎖定 `CONFIG.c_sg_length_width {23}`，防止未來將 AXI DMA 退回不足以容納一張 640×480 packed dual-RGB frame 的 14-bit transfer-length 設定。
- 更新 FPGA/Vitis README，將已實證的 A53→DDR→AXI DMA→PL full-frame synthetic DMA 與未實證的 UVC capture／雙鏡頭／YOLOX／IRQ 清楚分開；避免文件仍誤稱 DMA/PL streaming 未上板。
### 2026-11-06：bare-metal UVC driver 可行性確認

- 實際搜尋完整 Vitis Embedded 2024.2 的 `embeddedsw` 後，未找到 UVC/USB Video Class host middleware；USB driver examples 為 storage、mouse、keyboard、microphone。故 standalone ELF 已驗證的角色是 A53 control/DMA，不能誤稱為 Logitech C270 UVC capture driver。
- 真實 C270 路線應改為 Vitis Linux A53 application：使用 PYNQ Linux 的 kernel UVC/V4L2 取得影格，再以 CMA/contiguous buffer、cache ownership 與 AXI DMA 餵給 PL。這仍符合「Vivado 硬體檔 + Vitis 控制檔」，但需要 Linux sysroot 和板端 DMA-buffer interface，不能用不存在的 PL USB camera pins 取代。
### 2026-11-06：Vitis Linux UVC frame packing component

- 新增 `vitis/pynq_zu_usb_video/linux/uvc_v4l2_packer.c`：以 Linux V4L2 MMAP 開啟兩個 YUYV UVC device，要求 640×480，dequeue 一張 frame 後轉成 RTL 合約的 uint64 words（A RGB 在 [23:0]、B RGB 在 [55:32]）。輸出普通檔案是刻意的安全 bring-up 路徑，不會把 heap/file pointer 冒充 DMA physical address。
- 嘗試用 Vitis 2024.2 隨附 `aarch64-xilinx-linux-gcc.exe` 和 AArch64 Linux sysroot 編譯，但 Windows host compiler 以 `0xC0000135`（loader dependency 缺失）在產生 ELF 前結束，即使載入 `settings64.bat` 亦相同；因此尚未把 source 誤列為 compiler-verified。尚未在 PYNQ Linux 執行，因板子目前停在 JTAG standalone 狀態；production handoff 仍需 Linux 的 CMA/dma-heap/udmabuf 或專用 driver 分配連續 buffer，之後才可把 physical address 交給已驗證的 AXI DMA。

### 2026-11-06：Vitis Linux UVC component compiler 修復

- 釐清上一項的 wrapper 問題：`x86_64-petalinux-mingw32/.../aarch64-xilinx-linux-gcc.exe` 確實以 `0xC0000135` 失敗，但同一 Vitis 安裝的直接 GNU binary `gnu/aarch64/nt/aarch64-linux/bin/aarch64-linux-gnu-gcc.exe` 可正常執行（target `aarch64-xilinx-linux`）。將其 `bin` 加到 PATH 後，以 `-std=c11 -Wall -Wextra -Werror -O2` 編譯 `linux/uvc_v4l2_packer.c` 成功。
- 以同工具鏈 `aarch64-linux-gnu-readelf -h` 驗證產物為 74,624-byte ELF64 little-endian AArch64 PIE。這只證明 cross compile；尚未在板端開 V4L2、未配置 contiguous DMA memory、未送到 AXI DMA。
### 2026-11-06：PYNQ-ZU SD boot 與 JTAG 可並用的板端操作確認

- 查閱 PYNQ-ZU Reference Manual v1.2 的 boot-mode selection：板上 `JTAG SD` switch 向左為 JTAG，向右為 MicroSD。要恢復 Linux UVC/V4L2，需將 switch 切至右側 SD、插入既有 PYNQ SD card 後 power-cycle。
- 這不表示之後不能使用 Vivado/Vitis JTAG；SD boot 的 Linux 可保留 JTAG 作除錯/下載。先前 network 消失是因載入 standalone ELF 後 system reset，而非 Vivado Block Design 無法與 Linux 共存。
### 2026-11-06：SD-boot 後的 Vitis Linux UVC preflight

- 新增 `vitis/pynq_zu_usb_video/linux/run_uvc_vitis_preflight.sh`。它不使用 Jupyter：檢查兩個指定 V4L2 character devices 和 packer executable，執行一次兩路 UVC capture/packing，並強制輸出為 2,457,600 bytes（640×480×8-byte dual-RGB words）。成功標記 `PYNQ_ZU_UVC_VITIS_PREFLIGHT_PASS`，可作為下週 SD boot 後的第一個 runtime gate。
- 此 Windows host 沒有 Git Bash/WSL 的可用 POSIX shell，故尚未做 shell syntax execution；尚未在板端 Linux 執行，也尚未做 AXI DMA/CMA handoff。
### 2026-11-06：可重跑的 Vitis Linux UVC build script

- 新增 `vitis/pynq_zu_usb_video/linux/build_linux_uvc_packer.ps1`，固定使用已驗證的 Vitis direct GNU compiler（非會 DLL 失敗的 wrapper），臨時將 tool `bin` 放入 PATH、以 warnings-as-errors 建置 `uvc_v4l2_packer`，並輸出 `PYNQ_ZU_UVC_PACKER_BUILD_PASS`。預設產物在 `linux/build/`，用於 SD/Linux 上板前複建。
### 2026-11-11：實板 UVC bandwith 診斷與 10-FPS Vitis capture 修正

- SD-boot Linux 已實際登入；板端列出兩支 `046d:0825` C270，對應 `/dev/video0..3`。交叉編譯的 AArch64 Vitis packer 已成功以 SCP 部署、並被板端 `file` 確認為 AArch64 ELF。`xilinx` 不在 `video` group，故本輪以單次 `sudo` 執行 preflight，沒有修改帳號群組。
- 真實雙路初測失敗的 errno 為 `ENOSPC`，排除 root filesystem 容量後，以 `sudo dmesg` 證實是 USB hub bandwidth：`usb 1-1.4: Not enough bandwidth for new device state`/`altsetting 7`。因此將 V4L2 packer 改成在 `VIDIOC_S_FMT` 後明確 `VIDIOC_S_PARM` 要求 640×480 YUYV 10 FPS，避免 driver high-FPS default。
- 此次修改尚待重新交叉編譯與實板重跑；仍未完成 AXI DMA/CMA handoff。

### 2026-11-11：雙 C270 V4L2 實測完成，改列兩板一鏡頭為必要架構

- 實板已完成重新 cross-build、SCP 與 Linux 執行：兩支 C270 的 capture nodes 是 `/dev/video0`、`/dev/video2`，都可協商為 `320x240`、`10/1 FPS`、`YUYV`；但第二支在 `VIDIOC_STREAMON` 固定失敗為 `ENOSPC`。程式的即時 diagnostics 與 `dmesg` 對應為 USB hub `Not enough bandwidth ... altsetting 7`，不是檔案空間、權限、DMA 或 Vivado bitstream 錯誤。
- 為排除未壓縮 YUYV 的假設，`uvc_v4l2_packer` 新增 `--probe`（枚舉 format/size/FPS）及 `--mjpeg-stream-test`。實機確認 C270 支援 YUYV/MJPG 和所需 frame interval；然而兩支同時協商 `320x240`、`10 FPS`、`MJPG` 時第二個 `VIDIOC_STREAMON` 仍為 `ENOSPC`。不能再將本板此 USB topology 說成可完成雙路持續擷取。
- 一般 packer 現以 QVGA YUYV source 的 2x2 pixel expansion 維持既有的 640x480、2,457,600-byte packed output contract；但因第二 camera 不能 STREAMON，現板尚未得到雙路 preflight PASS。`linux/build/` 是本機可重建 ELF，未納入 Git。
- 新增 `docs/pynq-zu-two-board-dpu-architecture.md`：目標改為每板一 C270、Linux UVC/V4L2、每板 DPU inference、Wi-Fi 傳 versioned detection/tracking message。raw video forwarding 是後續選項，不能阻擋第一個兩板推論里程碑。
- DPU board audit：目前 PYNQ Linux 為 AArch64，但沒有 `xdputil`、Python `vart` 或 `/dev/dpu`。所以現有 PYNQ image 既沒有 DPU IP/driver，也沒有 VART；不能把 YOLOX/YOLOv8 ONNX 直接稱為 DPU inference。下一硬體 gate 是依 `xczu5eg` 資源與相容 Vitis AI release 加入 DPUCZDX8G、DDR/IRQ/CMA/Linux driver/VART，然後以 matching `arch.json` 將 INT8 YOLOv8 編成 `.xmodel`。
- 模型名稱決策：現有 assets 是 YOLOX；新 detector target 是 YOLOv8。兩者不能混稱。保留一個 detector adapter output schema，先支援 CPU YOLOv8，再以 VART DPU implementation 取代 backend，避免重寫 tracker/Wi-Fi interface。
- 驗證邊界：Vitis Linux packer cross-build 和兩路 USB failure 都已實板驗證；單板單鏡頭持續 streaming、第二板、Wi-Fi、DPU Vivado build、VART、YOLOv8 quantization/compile/inference 尚未完成。
- 同步結果：本項程式、架構與交接文件已提交為 `8391da8`（`Diagnose PYNQ dual UVC and plan DPU architecture`）並成功推送至 `origin/main`。

### 2026-11-11：兩板 Linux Wi-Fi detection protocol 基礎實作

- 新增 `person_tracking/peer_protocol.py`：標準庫 TCP newline-JSON protocol，schema=`pynq-person-detections-v1`，傳送 `board_id`、frame/timestamp、影像尺寸與 person detections。接收端在寫出 `peer_latest.json` 前嚴格驗證 packet size、schema、person 類別、信心值、track ID 及 box 在畫面範圍內。設計上不傳 raw video，避免將其當成兩板初期通訊前提。
- CLI：`receive --bind --port --output` 持續接收並保留最新 validated result；`send --host --port --input` 傳送一個 JSON packet。此 module 可由既有 YOLOX 或未來 YOLOv8/VART adapter 產生相同 schema，不綁定目前 detector。
- 新增 `person_tracking/tests/test_peer_protocol.py`，實跑四項：normalization round-trip、out-of-range box rejection、非 person/schema rejection、localhost TCP framed send/read。實測 `python tests/test_peer_protocol.py` PASS（4 tests）與 `py_compile` PASS。
- 驗證邊界：尚未將 packet producer 接到實際 detector，尚未在兩塊 PYNQ Wi-Fi 上執行，且沒有聲稱 DPU/VART 已就緒。
- 同步結果：本項程式與文件已提交為 `a1ff8f4`（`Add two-board detection peer protocol`）並成功推送至 `origin/main`。

### 2026-11-11：PYNQ-ZU 原生 DPU B512 Block Design、實作與 bitstream

- 新增 `fpga/create_pynq_zu_dpu_bd.tcl`、`inspect_pynq_zu_dpu_ip.tcl`、`inspect_pynq_zu_dpu_bd.tcl`、`synthesize_pynq_zu_dpu_b512.tcl`、`implement_pynq_zu_dpu_b512.tcl` 和 `dpu_config_pynq_zu_b512.vh`。流程要求 `DPUCZDX8G_HOME` 指向官方 AMD DPUCZDX8G source root，選用 `PYNQ_ZU_DPU_BUILD_DIR` 指向短 ASCII build path；外部 AMD IP 會 stage 到 build output，不納入 Git。
- `create_pynq_zu_dpu_bd.tcl` 以原生 `xilinx.com:ip:dpuczdx8g:4.0` 建立一核心 B512 DPU。USB0/USB1 保持 PS MIO（不可作 PL camera pins）；AXI-Lite control 是 A53 HPM0→SmartConnect→DPU，DPU DATA0/DATA1 是 128-bit→HP0/HP1，INSTR 是 32-bit→SmartConnect→HP2，interrupt 接 PS IRQ0。PL0=100 MHz control、PL1=150 MHz data，clock wizard 提供 300 MHz DPU 2x clock。
- 實測 Vivado 2024.2：`validate_bd_design` 成功；top-level synthesis 成功（0 errors/0 critical warnings）；implementation route status 為 68,180/68,180 routable nets fully routed、0 routing errors；`write_bitstream` 成功（0 errors/0 critical warnings）。signoff timing report 為 WNS `+0.966 ns`、WHS `+0.010 ns`，並明示 all user specified timing constraints are met。implementation utilization：LUT 32,022/117,120（27.34%）、register 41,567/234,240（17.75%）、BRAM 72/144（50.00%）、DSP 134/1,248（10.74%）。本機 `.bit` 是 7,797,815 bytes 的可重建 build output，不上傳 Git。
- 驗證界線：這是 PYNQ-ZU DPU 硬體 feasibility 與 bitstream 證據，不是已上板的 DPU inference。SD PYNQ Linux 仍沒有 `/dev/dpu`、`xdputil`、VART、matching device-tree/CMA、B512 `arch.json`、YOLOv8 INT8 `.xmodel` 或 VART test；這些完成前不可聲稱人物偵測跑在 DPU。真實 C270 仍走 PS USB→Linux UVC/V4L2→DDR，之後由 VART 控制 DPU，不會改接 PL camera pins。
- 同步結果：本項 DPU Tcl、架構與交接文件已提交為 `dbaeb8f`（`Add PYNQ-ZU native DPU B512 Vivado flow`）並成功推送至 `origin/main`。

### 2026-11-11：DPU 硬體 handoff XSA 匯出

- 新增 `fpga/export_pynq_zu_dpu_xsa.tcl`。它只接受 `impl_1` 已達 `write_bitstream Complete!` 的 project，開啟已 routed 的 implementation run，執行 `write_hw_platform -fixed -include_bit`，並檢查輸出檔存在；輸出為 `$PYNQ_ZU_DPU_BUILD_DIR/pynq_zu_dpu_b512.xsa`。
- 實跑 Vivado 2024.2 成功輸出 2,586,044-byte XSA。以 `tar -tf` 檢查 archive，確認包含 `pynq_zu_dpu.hwh`、`pynq_zu_dpu_b512.bit`、`psu_init.*`、`sysdef.xml`、`xsa.json` 與 `xsa.xml`。這是後續 Vitis platform/Linux boot artifact 的硬體 handoff，不是 VART runtime 或 device-tree 已生成的證據。
- 驗證界線：XSA、bitstream 與 Vivado build output 均位於 `C:\pynq_zu_dpu_native_build`，可由 tracked Tcl 重建且不納入 Git。仍待以此 XSA 建立相配的 Linux/device-tree/CMA/DPU driver/VART image，並於板端驗證。
- 同步結果：XSA export script 與交接文件已提交為 `817a8cc`（`Export PYNQ-ZU DPU hardware handoff`）並成功推送至 `origin/main`。

### 2026-11-11：Vitis Embedded DPU platform handoff

- 新增 `vitis/pynq_zu_dpu/build_vitis_dpu_platform.py` 及 README。此 script 要求 `PYNQ_ZU_DPU_XSA` 和新的短路徑 `PYNQ_ZU_DPU_VITIS_WORKSPACE`，以完整 `C:\Xilinx_Embedded_2024_2\Vitis\2024.2\bin\vitis.bat -s` 建立 `psu_cortexa53_0`/`standalone_domain` platform；它刻意不建立 DPU bare-metal application，因 DPU inference 需要 Linux DPU driver/VART 而非未定義的 AXI register write。
- 實測使用 `pynq_zu_dpu_b512.xsa`：Vitis Embedded 2024.2 成功生成 SDT、A53 standalone domain、ZynqMP FSBL domain，platform build/export 成功並輸出 `pynq_zu_dpu_platform.xpfm`；生成 FSBL 為 445,080 bytes。生成的 `xparameters.h` 含 `XPAR_DPU_CZDX8G_0_BASEADDR` 及 canonical `XPAR_DPUCZDX8G_0_BASEADDR`，兩者均為 `0x400000000`，這與 Vivado address assignment 一致。
- 驗證界線：本機 Vitis platform/BSP/FSBL build 是 XSA handoff 驗證；build 期間有 embedded software source warnings，但 platform 最終 `Platform Build Finished successfully`。尚未 JTAG/SD 部署此 DPU bitstream/FSBL，未生成 matching Linux image、device tree/CMA/DPU driver/VART，亦未執行 `.xmodel` 或 inference。
- 同步結果：Vitis DPU platform script 與交接文件已提交為 `6fd4f9b`（`Build Vitis platform for PYNQ-ZU DPU`）並成功推送至 `origin/main`。

### 2026-11-11：DPU Linux runtime acceptance contract

- 同步結果：runtime gate、文件與本項紀錄已提交為 `61abcdf`（`Add PYNQ-ZU DPU Linux runtime gate`）並成功推送至 `origin/main`。

- 新增 `vitis/pynq_zu_dpu/linux/README.md` 與可在目標板執行的 `verify_dpu_runtime.py`。它不寫 register、不下載 bitstream；會以 live device tree 的 `xlnx,dpuczdx8g-4.0`、`/dev/dpu*`、CMA、Python `vart`/`xir`、`xdputil query`、指定 `.xmodel` 和可選 UVC `/dev/video*` 為 DPU Linux deployment gate，全部存在才輸出 `PYNQ_ZU_DPU_LINUX_RUNTIME_PASS`。
- 已檢查官方 DPUCZDX8G 4.0 source 的 ZCU102 參考：其 kernel patch 僅讓 `xlnx_dpu` 接受 `xlnx,dpuczdx8g-4.0`；VART 2.5 recipe 依賴 XIR、target-factory 且 Vitis flow 依賴 XRT。這些是相容性需求，不是可直接複製到 PYNQ-ZU 3.1.1 Linux 的 image/DT/ABI。

### 2026-11-11：DPU Linux build-host recheck

- 同步結果：環境 blocker 與進度文件已提交為 `e9413a3`（`Record DPU Linux build host blocker`）並成功推送至 `origin/main`。
- 實際 host audit：Windows 有 `wsl.exe` 但未安裝任何 Linux distribution，沒有 `docker` command；Xilinx 安裝樹沒有 PetaLinux executable/settings，僅見 installer EULA 與 lopper helper。這台主機目前不能作為 PetaLinux/Vitis-AI Linux image build host；安裝 WSL/PetaLinux 或使用受支援 Linux build host 是 B512 DPU driver/VART runtime 的外部前提，不能由目前 Vitis platform 成功推論出來。
- 驗證界線：未安裝 WSL/PetaLinux、未重刷 SD、未下載 DPU bitstream。這不影響已驗證 CPU YOLOv8 path，但 matching DPU Linux image 仍未完成。

### 2026-11-11：PYNQ CPU YOLOv8 fallback 實測

- peer producer 同步結果：已提交為 `bf2a0fb`（`Add PYNQ YOLOv8 peer producer`）並成功推送至 `origin/main`。
- 正樣人物實測同步結果：已提交為 `bf9a830`（`Record PYNQ YOLOv8 positive inference`）並成功推送至 `origin/main`。
- pipeline/bundle 接入同步結果：已提交為 `fac5fee`（`Use YOLOv8 in PYNQ tracking pipeline`）並成功推送至 `origin/main`。
- 同步結果：YOLOv8 adapter、exporter、tests 與進度文件已提交為 `fbed6fe`（`Add PYNQ CPU YOLOv8 fallback`）並成功推送至 `origin/main`。
- 新增 `person_tracking/assets/yolov8.py`、`prepare_yolov8_onnx.py` 和 adapter unit tests。adapter 支援 Ultralytics raw `(1,84,8400)`／`(1,8400,84)`，僅保留 COCO person、還原 letterbox 座標並保持既有 box/confidence contract；優先 ONNX Runtime、不可用時才嘗試 OpenCV DNN。export script 固定使用 YOLOv8n 640 static ONNX，並經 ONNX checker 將 IR metadata 設為 9，供 PYNQ ORT 1.16.3 使用；模型權重與 ONNX 都不納入 Git。
- 實板：原始 ONNX opset 18 在 OpenCV 4.5.4 的 Reshape parser 失敗；板端安裝 user-site `numpy==1.21.6`、`onnxruntime==1.16.3` 和依賴後，IR 9 artifact 成功輸出 `(1,84,8400)`，zero-input forward 0.845 s。從 C270 `video0` 讀取一張 320×240 frame 並以新增 adapter CPU inference 實跑 1.017 s、無 runtime error；當次畫面回傳 0 person，未驗證正樣本 detection。
- 驗證界線：這是 CPU ONNX Runtime fallback，不是 DPU、VART、INT8 `.xmodel` 或 YOLOv8 DPU inference。板上 Python 套件變更已在這台第三台設備完成；未在第一台執行端安裝 CPU runtime，且兩板 Wi-Fi/peer/DPU 尚未驗證。
- 已將 `pipeline.Detector` 預設切換至 `yolov8`，`PERSON_DETECTOR=yolox` 是明確 legacy 回退。PYNQ bundle 改僅包含 YOLOv8 adapter/model，preflight 要求 ONNX Runtime；已在板端暫存 bundle 實測 `pipeline.Detector()` 讀取 `video0` 320×240 後使用 `yolov8` backend 成功推論 1.255 s。修正了前次 bundle 雖選 YOLOv8、卻在 import time 強制要求未打包的 `yolox.py` 的缺陷。
- 此次 pipeline 實測畫面仍是 0 person，因此只能證明完整 capture→pipeline→YOLOv8 CPU path，尚未驗證正樣本人框、tracker 確認、dashboard 連線或 peer packet producer。
- 後續以專案既有公開 `bus.jpg` 在同一板端暫存 bundle 重跑：`pipeline.Detector()` 的 `yolov8` backend 對 810×1080 image 回傳 4 個 person boxes、耗時 0.950 s；這是正樣 person postprocess/pipeline 證據。公開測試圖未上傳或改動 Git，現場 C270 人物正樣本、tracker/dashboard/peer 仍未驗證。
- 新增 `person_tracking/pynq_yolov8_peer.py`：每板一個 C270、預設 YOLOv8、Tracker 後建構 versioned peer packet，只傳 person metadata。PYNQ loopback 以 `127.0.0.1` receiver 實測 C270 `video0`→YOLOv8→Tracker→TCP，receiver accepted `pynq-a:0` 且 JSON schema/dimensions 正確（當次 empty detections）。這不是第二板或 Wi-Fi 驗證；`wlan0` 仍未設定。

### 2026-11-11：SD 板端雙 C270 實測與 DPU recheck

- 同步結果：實板檢查結果、兩板架構與進度文件已提交為 `6fd075b`（`Record PYNQ dual camera hardware result`）並成功推送至 `origin/main`。
- 實板 SSH `192.168.3.1` 成功：PynqLinux 3.0（Ubuntu 22.04 base）、kernel `6.6.10-xilinx-v2024.1-gb6067dbebcc8`。兩支 C270 都經 USB2744 480-Mbit/s hub 的 `1-1.3`／`1-1.4`，分別提供 `video0/1`、`video2/3`。已將 `xilinx` 加入既有 `video` 群組；OpenCV/NumPy 存在，`v4l2-ctl` 不存在。
- 實際 OpenCV V4L2 capture：每支在單獨開啟的 MJPEG 320×240、5 FPS 下連續讀取三張均成功；雙開後 `video0` 五張成功而 `video2` 五張皆失敗。`dmesg` 同時有 `usb 1-1.4: Not enough bandwidth for altsetting 7`。因此一板兩支目前被同一 USB2 hub 的實體帶寬阻擋，不能視作完成的雙鏡頭串流；每板一鏡頭、兩板設計仍是 deployment route。
- `wlan0` 存在但 DOWN/unconfigured；尚未有兩板 Wi-Fi 實測。CMA 為 524288 KiB，但板端仍無 DPU compatible device-tree node、`/dev/dpu*`、`xdputil`、Python `vart` 或 `xir`，故仍非 DPU/VART/YOLOv8 實機完成。

### 2026-11-11：DPU Linux runtime acceptance contract（續）
- 實際 host audit：`C:\Xilinx_Embedded_2024_2`／`C:\Xilinx` 找不到 `petalinux.bat` 或 PetaLinux `settings.sh`。因此本機目前可驗證 Vivado→Vitis handoff，但無法建立 matching PetaLinux image；也尚未部署、重刷 SD、或在板端執行 verifier。保留現有 PYNQ image，不能聲稱 DPU/VART/YOLOv8 已可用。

### 2026-11-11：非 AMD 下載路徑的 host revalidation

- 在不填寫、送出或變更 AMD Download Center 資料的前提下，以 Python 內建 `unittest` 重跑 `person_tracking/tests` 的 19 項契約測試與 DPU build-host preflight 的 3 項測試，均 PASS；系統沒有安裝 `pytest`，故沒有額外安裝套件。
- 實跑 exact B512 `arch.json` 的 host preflight：仍正確列出三個 blockers：沒有 Docker/`vai_c_xir` compiler route、沒有 PetaLinux、且目前是 2024.2 而 DPUCZDX8G 4.0 + Vitis AI 3.5 所驗證的是 2024.1。
- 再次以 `build_linux_uvc_packer.ps1` 和 direct Vitis 2024.2 GNU AArch64 compiler 建置 `uvc_v4l2_packer.c` 成功；產物為外部 `C:\pynq_zu_dpu_native_build\checks\uvc_v4l2_packer_20261111\uvc_v4l2_packer`（75,272 bytes），未寫入 Git working tree。這是 cross-compile，不是板端 capture/DMA/PL/DPU 驗證。
- 嘗試建立 Ubuntu 22.04 WSL 基礎環境時，這台舊版 `wsl.exe` 僅提供系統層級 `--install`，而 Optional Feature 查詢回傳需要 elevated permission；本輪未取得或改動 Windows administrator setting、未安裝 distribution/Docker/PetaLinux。後續需在管理員權限下完成 WSL 啟用/重開機後再建立受支援 Linux host。
- 驗證界線：沒有改 tracked application/FPGA code、沒有登入或送出 AMD export/download form、沒有下載 PetaLinux、沒有接觸板端或相機；DPU runtime 仍未完成。

### 2026-11-11：DPU Linux runtime gate 的模型檔完整性修正

- 新增 `vitis/pynq_zu_dpu/linux/tests/test_verify_dpu_runtime.py`。先以 test 證實舊 gate 缺口：空白但副檔名為 `.xmodel` 的檔案會通過 model existence 條件。
- `verify_dpu_runtime.py` 現新增 `valid_xmodel()`：明確指定模型時，必須是可讀的正確副檔名、一般檔案且大小大於 0 bytes；空檔、錯誤副檔名和無法 stat 的 path 都會讓 runtime gate FAIL。device-tree test 也確認只接受 `xlnx,dpuczdx8g-4.0` compatible node。
- 驗證：先得到預期的 import/test failure，再完成修正；`person_tracking` 19 tests 加 DPU Linux tests 5 tests 共 24/24 PASS。沒有板端 DPU runtime claim，非空檔仍不代表它與 B512 architecture 相容或已經成功 VART inference。

### 2026-11-11：USB C270 PS→DDR→AXI DMA Block Design 與 Vitis 控制端重新建置

- 以目前 tracked Tcl 從零建立外部 `C:\pynq_zu_usb_video_rebuild_20261111`：建立 PYNQ-ZU project、package `dual_camera_yolox_axis` IP Catalog、建立 `pynq_zu_usb_video` Block Design、通過 `validate_bd_design`，再完成 synthesis、implementation、bitstream 與固定 XSA export。硬體 mapping 保持 USB0/USB1 在 PS MIO、Linux UVC/DDR 在 PS，AXI DMA MM2S 以 HP0 將 64-bit packed A/B RGB stream 送入 PL custom IP；沒有捏造 C270 的 PL D+/D− pins。
- 實作 evidence：bitstream 7,797,821 bytes；XSA 1,573,588 bytes，archive 含 `.bit`、`.hwh`、`psu_init.*`、`sysdef.xml`、`xsa.json` 與 `xsa.xml`。route report 為 16,007/16,007 routable nets fully routed、0 routing errors；routed signoff WNS `+0.752 ns`、WHS `+0.020 ns`，all user specified timing constraints met。
- 使用這份新 XSA 於 `C:\pynq_vitis_usb_video_rebuild_20261111` 實跑 Vitis Embedded 2024.2 build，輸出 352,272-byte `pynq_zu_usb_video_app.elf`。generated `xparameters.h` 與 BD 一致：AXI DMA `0xA0000000`、frame ID GPIO `0xA0010000`、YOLOX video RTL mailbox `0xA0020000`；readelf 確認為 ELF64 little-endian AArch64。`video_control.c` 另以 Vitis direct AArch64 GNU compiler `-Wall -Wextra -Werror` 產出外部 object 成功。
- 驗證界線：fpga Python contract tests 5/5 PASS。這台 Windows 沒有 host `gcc`/`clang`/`cl`，所以 `test_video_control.c` 的 host executable 未重跑；Vitis AArch64 ELF 已實際 build。此 standalone controller 是 synthetic DDR→DMA→PL bring-up，並不包含 Linux UVC capture、CMA DMA-BUF handoff、同步雙 C270、DPU/VART/YOLOv8 inference 或 Wi-Fi；新 bitstream/XSA/ELF 均在外部 build paths，沒有寫入板子、SD 或 Git。

### 2026-11-11：Vitis controller host unit test 補驗

- 先前僅檢查 PATH，因而誤以為 host C compiler 不存在；重新盤點已安裝的 Vitis tree 後找到 `C:\Xilinx\Vitis\2024.2\tps\mingw\10.0.0\win64.o\nt\bin\gcc.exe`。不需安裝或改系統，僅臨時加入 process PATH。
- 以 `-std=c11 -Wall -Wextra -Werror` 編譯 `video_control.c` 與 `tests/test_video_control.c`，執行結果 `VIDEO_CONTROL_TEST_PASS`。它實際檢查 frame ID → mailbox payload → CONTROL commit 的寫入順序與必要 AXI address validation；暫存 executable 已刪除。
- 驗證界線：這是 Windows host 的 pure-C controller contract test，不會執行 A53 ELF、AXI DMA、PL、Linux UVC 或 DPU；前項硬體/XSA/Vitis build 的界線不變。

### 2026-11-11：USB-video XSA 自動 handoff gate

- 新增 `fpga/verify_pynq_zu_usb_video_handoff.py` 與 offline tests。它唯讀開啟 XSA zip archive，要求 bitstream、HWH、`sysdef.xml`、`psu_init.c`，解析主 HWH 的 `C_BASEADDR`，並要求 DMA=`0xA0000000`、frame GPIO=`0xA0010000`、video mailbox=`0xA0020000`。
- 採 test-first：初始 import failure 後實作；第一次真實 XSA run 抓到 Vivado HWH 使用 `0X` prefix 的大小寫正規化缺口與不明確的 missing-bitstream 訊息。修正後 FPGA tests 7/7 PASS，對 `C:\pynq_zu_usb_video_rebuild_20261111\pynq_zu_usb_video.xsa` 實跑輸出 `PYNQ_ZU_USB_VIDEO_XSA_PASS`，三個 address 均與 Vitis generated `xparameters.h` 一致。
- 驗證界線：這證明 build artifact 的結構/AXI control mapping，並不執行 A53 ELF、板端 DMA/UVC/PL/DPU，亦不改 board/SD 或把 bitstream/XSA 加入 Git。

### 2026-11-11：UART 唯讀板端 runtime recheck

- Windows PnP 盤點確認 PYNQ USB CDC serial 在 COM4；以 115200 baud、DTR/RTS=false 開啟、全程不寫入或重設，讀到 PYNQ Linux console：Ubuntu 22.04 base、`Linux 6.6.10-xilinx-v2024.1-gb6067dbebcc8 aarch64`。
- 接著只執行 shell 查詢：`/dev/video0`～`/dev/video3` 存在；沒有 `/dev/dpu*`、live DT 中沒有 `xlnx,dpuczdx8g-4.0`、沒有 `xdputil`，Python `vart=False`、`xir=False`。`wlan0` 存在但 `DOWN`、MAC 為全零且沒有 IPv4。
- 驗證界線：UART session 僅送出讀取命令，沒有上傳檔案、program PL、reset、寫 SD、連 Wi-Fi 或開相機。這是在現有 SD Linux 上的 runtime evidence；DPU bitstream、VART/Linux image、兩支 simultaneous C270、Wi-Fi peer 與 YOLOv8 DPU inference 仍未完成。

### 2026-11-11：UART 唯讀 USB topology recheck

- 同一 UART read-only session 列舉 `/sys/class/video4linux/video*/name` 與 `lsusb`：`video0`～`video3` 全部為 Logitech C270 HD WEBCAM；USB bus 001 的兩支 C270 是 `046d:0825` device 006/007，並共用 `0424:2744` Microchip/SMSC USB 2.0 hub（bus 001），另有 `0424:5744` USB 3.0 hub（bus 002）。
- 這是 C270 一支會產生兩個 V4L2 nodes 的實物列舉，非四支相機；也與先前同一 USB2 hub `ENOSPC` simultaneous streaming 診斷一致。不能以 Vivado PL pin assignment 修復此 USB physical topology，兩板各一鏡頭仍是部署方案。
- 實際讀到 `/sys/class/net/wlan0/address` 為 `00:00:00:00:00:00`，與 interface DOWN/no IP 狀態相符；尚未有第二板/SSID，故沒有變更或連線 Wi-Fi。

### 2026-11-11：UART 唯讀 Wi-Fi driver diagnosis

- `wlan0` 對應 SDIO `mmc1:0001:1`，driver path 是 `/sys/bus/sdio/drivers/wilc_sdio`，network type=1；dmesg 顯示 `wilc_sdio ... Driver Initializing success`。因此目前不是缺失 Wi-Fi hardware/driver 的情況。
- kernel 同時記錄 `regulatory.db` direct firmware load error `-2`／`cfg80211: failed to load regulatory.db`，以及未連線時 `Failed to get RSSI value`。這些是 image/network-preparation blockers，不能把介面存在當成可直接 peer exchange。
- 驗證界線：只讀 sysfs/dmesg，未 `ip link set up`、scan/join SSID、寫 regulatory database 或改任何 Linux/board setting。未來兩板 Wi-Fi path 仍需合法 SSID credentials、第二板以及先解決/確認 regulatory database requirement。

### 2026-11-11：Wi-Fi regulatory.db package recheck（更正）

- 為驗證 dmesg 的 `regulatory.db` error -2，透過 UART 只讀查詢 `/lib/firmware/regulatory.db`、`.p7s`、`dpkg-query` 和 `apt-cache policy`。兩個檔案存在，`wireless-regdb` 為 `install ok installed` version `2021.08.28-0ubuntu1`，candidate 相同。
- 因此上一項不可描述為 root filesystem「缺少 regulatory.db」。正確事實是 kernel boot log 曾出現 direct firmware load failure，但 rootfs 上的 package/artifact 隨後可見；可能是 early-boot/rootfs availability 或 another load-time condition，尚未透過啟用 interface/association 實測。
- 驗證界線：仍未 `ip link up`、scan/join SSID、reload driver 或改 initramfs。後續不應盲目重裝 package；應先在授權 Wi-Fi environment 下啟用並取得 dmesg/association result，再決定是否需要 Linux image change。

### 2026-11-12：PetaLinux 2024.1 installer 已取得（尚未執行）

- 實際盤點 `C:\Users\dsic\Downloads`，確認 AMD installer `petalinux-v2024.1-05202009-installer.run` 存在且大小為 3,296,562,820 bytes（約 3.07 GiB）。SHA-256=`9EFB6191DC9A90AFEB374EAFD8733CBC8C27C2E5D54E2D388FA0302294B5BB93`。
- 這解除「尚未有 PetaLinux 2024.1 installer」的下載 blocker，但不解除 Linux build host blocker：PetaLinux installer 需要受支援的 Linux host；本機 WSL 尚未啟用／安裝 distribution，Docker/Vitis AI compiler route 和 matching 2024.1 hardware/image 仍未完成。
- 驗證界線：僅列檔與 hash，沒有執行 `.run`、未安裝/解壓 PetaLinux、未改 Windows、WSL、板子、SD 或 Git。installer 是外部下載資產，不納入 repository。

### 2026-11-12：Windows WSL platform feature 已啟用，等待重開機

- 在使用者確認在電腦前後，以 Windows administrator elevation 成功執行 `Enable-WindowsOptionalFeature`，啟用 `Microsoft-Windows-Subsystem-Linux` 與 `VirtualMachinePlatform`，兩項同一 elevated command exit code=0，且使用 `-NoRestart` 避免未告知即中斷 Vivado/Vitis。
- 讀取 Windows reboot markers：CBS `RebootPending=True`、`PendingFileRenameOperations=True`。因此必須重開機後才能建立/執行 WSL Linux distribution；目前 `wsl --list --verbose` 仍顯示沒有 distribution，屬預期的重開機前狀態。
- 驗證界線：尚未重開 Windows、未安裝 Ubuntu、未執行 PetaLinux installer、未改 Vivado/Vitis project 或板子。重開前必須由使用者儲存目前開啟的 Vivado/Vitis 工作。

### 2026-11-12：WSL2 Ubuntu 與 PetaLinux 2024.1 host 已實裝

- Windows 原本的 inbox WSL payload 不完整：雖然 Optional Feature 顯示 enabled，Ubuntu registration 仍為 `0x8007019e`，且 `%SystemRoot%\\System32\\lxss\\LxssManager.dll` 不存在。已完成 `DISM /RestoreHealth`、`SFC /scannow`、WSL feature disable/enable 與重開機；仍不能修復 inbox service。最後以官方 winget package 安裝並 hash-verified 的 `Microsoft.WSL` 3.0.5，重開機後確認 WSL kernel `6.18.58.1-1`、default version 2。
- 已安裝官方 Ubuntu 22.04 package，registered distro=`Ubuntu`、WSL version=2；建立 Linux non-root `petalinux` account（uid 1000，sudo group）。實測 `/etc/os-release` 為 Ubuntu 22.04.1 LTS、root filesystem 有約 937 GiB free space。PetaLinux 安裝與後續 commands 必須使用 `bash`，並在 install root 執行 `source settings.sh`；`/bin/sh` 為 dash 只造成 PetaLinux warning，非 blocker。
- 已以 apt 安裝 PetaLinux 2024.1 host prerequisites，installer preflight 只補了 `zlib1g-dev` 後通過。官方 installer 的 SHA-256 在 Windows 與 WSL copy 皆為 `9efb6191dc9a90afeb374eafd8733cbc8c27c2e5d54e2d388fa0302294b5bb93`。
- PetaLinux 2024.1 已完成安裝於外部 WSL path `/home/petalinux/xilinx/petalinux/2024.1`，採 `aarch64` platform（Zynq UltraScale+ target）。installer final log 回報 `PetaLinux SDK has been successfully set up and is ready to be used.`；Bash source 後已實測 `petalinux-create`、`petalinux-config`、`petalinux-build` 在 PATH。
- 安裝器實際以 current working directory 為 install root，`--dir` 在此 `.run` flow 未生效。第一次錯誤解壓到 repo 的未追蹤 `components/`、`scripts/` 已立即移到 `C:\\pynq_wsl_setup\\quarantine_peta_wrong_target_20261112`，未留在 Git worktree；第二次錯誤解壓到 `/home/petalinux` 的 7.8 GiB partial tree 亦已隔離至 `/home/petalinux/quarantine_partial_install_20261112`。它們均是外部暫存資產、未上傳 Git；正式 install root 約 11 GiB。
- 驗證界線：PetaLinux installer 警告 host 未提供 TFTP server，這不阻止 SDK setup，但若採 network boot 需另行配置。尚未以 2024.1 重建 matching XSA、建立 PetaLinux project/rootfs、加入 DPU device tree/driver、VART/XIR、Docker/Vitis AI compiler 或 `.xmodel`；也尚未寫 SD、program PL、改板端 Linux 或驗證 DPU/Wi-Fi/second board。現有已實作 USB-video XSA/ELF 是 2024.2，不能直接聲稱與 DPUCZDX8G 4.0 + Vitis AI 3.5 的 2024.1 deployment contract 相容。
- 在 WSL 中 source 2024.1 settings 後，以 exact generated `arch.json` 實跑 `preflight_dpu_build_host.py`：`petalinux-create=True`、`has_arch_json=True`、PetaLinux version=2024.1。gate 因此只剩兩個 blockers：尚無 Docker/`vai_c_xir` Vitis AI 3.5 compiler route，以及現有 DPU Vivado hardware 是 2024.2（不是 matching 2024.1）。這是 host preflight，非 target image/DPU runtime 驗證。
- 已在外部 WSL path `/home/petalinux/work/pynq_zu_dpu_2024_1` 成功執行 `petalinux-create project --template zynqMP --name pynq_zu_dpu_2024_1`。這只是 target family 正確的專案骨架；刻意未對它執行 `petalinux-config --get-hw-description` 或匯入現有 2024.2 XSA，因為那會破壞 2024.1 matching contract。project 是 generated external build state，不納入 Git。
### 2026-11-12：Docker Vitis AI 3.5 compiler route 已驗證

- Docker Desktop 4.99.0 已以 `hello-world` 實測 pull/run；固定 image `xilinx/vitis-ai-pytorch-cpu:ubuntu2004-3.5.0.306` 已 pull。container 預設 PATH 沒有 compiler，需 source conda profile 並 activate `vitis-ai-pytorch`；其後實測 `vai_c_xir`、`vaic`、`xcompiler`、`xir` 都是 3.5.0。
- 這解除 compiler-route blocker，不解除官方 Vitis AI 3.5 所需的 2023.1 Vivado/PetaLinux/XSA/rootfs/VART/image blocker。

