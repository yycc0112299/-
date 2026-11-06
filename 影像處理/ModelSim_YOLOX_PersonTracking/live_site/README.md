# USB 即時人物追蹤網站

## 雙鏡頭即時儀表板

`dual_server.py` 與 `dual_index.html` 提供雙 USB 鏡頭的 localhost 儀表板。它會讓兩台鏡頭各自跑既有 YOLOX 偵測與短期 Tracker，並使用 `cross_camera.py` 顯示外觀候選；即時畫面只留在記憶體，服務僅監聽 `127.0.0.1`。在此資料夾以設定好相依套件的 Python 執行：

沒有鏡頭時，服務仍可啟動並維持 `stopped` 等待狀態；只有按頁面中的「連接雙鏡頭」或呼叫 `/api/start` 才會嘗試開啟指定的相機。若由 Cloudflare Quick Tunnel 公開這個服務，必須明確加上 `--allow-trycloudflare`。此選項只接受 `https://*.trycloudflare.com` 的請求，Quick Tunnel 網址重啟會更換，且不應把 `private-link.txt`、相片、權杖或模型權重提交到 Git。

```powershell
$env:PROJECT_PYTHON = 'C:\path\to\python.exe'
.\start_dual.ps1
```

預設使用鏡頭 0 與 1，頁面可改選兩個不同編號。A/B 影像、各自的本地 Track ID 與候選配對狀態會同時更新。候選必須連續三個處理循環符合衣著外觀門檻才有 P 標籤，並不代表身分辨識或硬體同步。

### PYNQ-ZU 的兩支 USB 鏡頭

`dual_server.py` 現在會在 Windows 使用 DirectShow、在 PYNQ Linux 使用 V4L2；同一套網站可在
PYNQ-ZU 上執行。開發電腦先執行 `python prepare_pynq_dual_bundle.py --output C:\\pynq_zu_bringup\\pynq_dual_dashboard.tar.gz`，
再把 tarball 複製到 PYNQ SD-boot Linux。解壓後，在 PYNQ 執行
`python3 live_site/pynq_usb_camera_preflight.py` 先確認兩支 UVC 鏡頭，再執行
`bash live_site/start_pynq_dual.sh <PYNQ-IP>`；電腦以 `http://<PYNQ-IP>:8766/` 開啟。
參數必須是瀏覽器連到網站時所用的 PYNQ 位址，因為它同時是網站的 HTTP Host
白名單；不是觀看網站的電腦 IP。

板上需要 Python 3、`numpy`、含 V4L2 的 `opencv-python`，且兩支 UVC 鏡頭必須可列為
`/dev/video0`、`/dev/video1`（或以 `PYNQ_CAMERA_A/B` 指定其他 index）。這是 PYNQ 的 CPU
執行 YOLOX / tracker 網站；目前 FPGA bitstream 的 video inputs 尚未接到 USB capture，不可宣稱
USB 影像已走入 FPGA RTL。

### SD 開機後的一鍵部署（Windows 開發電腦）

PYNQ-ZU 切至 **SD**、開機並取得 LAN IP 後，從已 clone 專案的 Windows PowerShell 執行（不會保存 SSH 密碼）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\影像處理\ModelSim_YOLOX_PersonTracking\live_site\deploy_pynq_zu.ps1" -BoardHost <PYNQ-IP> -RunSystemPreflight -RunCameraPreflight
```

此入口會在電腦建立 tarball、經 SSH/SCP 傳至板子、解壓並可選擇以 V4L2 開啟兩個 UVC 鏡頭各讀一張影格。
`-RunSystemPreflight` 只讀取並列出板端 Python、NumPy、OpenCV、PYNQ 套件及模型狀態，不會啟動鏡頭；
PYNQ 套件缺少時會列為 Overlay 提示，但雙 USB 網站仍需先以 NumPy/OpenCV 通過。
若同時已有由相同 Vivado build 匯出的 `pynq_zu_yolox.bit/.hwh` 目錄，可加上
`-OverlayDir C:\path\to\overlay -RunBringupCheck`，它才會下載 Overlay 並做 AXI-Lite mailbox 的
write/readback；此檢查不會測試 USB-to-FPGA 影像路徑。部署腳本為避免刪到板上既有資料，目標
`~/pynq_dual_dashboard` 已存在時會停止；請改用新的 `-RemoteDir`，或由操作者確認後自行處理舊目錄。
成功後在板端執行輸出的 `start_pynq_dual.sh` 指令，再於電腦開啟 `http://<PYNQ-IP>:8766/`。
此命令只要求 clone 內已追蹤的程式與模型、Windows 的 Python 3/內建 OpenSSH；不讀取本開發電腦的
Vivado 暫存、使用者資料夾或已產生的 tarball。YOLOX ONNX 依授權及容量規則不存 Git：第一次執行時會從
專案已記錄的 OpenCV Zoo 公開來源下載，並核對 SHA-256 後才打包，故該次電腦需要網路。缺少 Python 時先
安裝 Python 3；缺少 `ssh`/`scp` 時在 Windows「選用功能」安裝 OpenSSH Client。板端帳號預設為 `xilinx`，
可用 `-BoardUser` 覆寫。

### 兩台電腦協作

GitHub 只同步程式，不傳即時影像。把本目錄同步到有 USB 鏡頭的電腦後，在該電腦執行：

```powershell
.\sync_camera_pc.ps1 -Repo C:\path\to\github_shared_repo -AllowHost 192.168.1.50:8766
```

把 `192.168.1.50` 換成鏡頭電腦在區域網路的固定 IP。此指令會先 `fetch`、`pull --ff-only`，再以 LAN 模式啟動服務；另一台電腦用瀏覽器開 `http://192.168.1.50:8766/` 即可看結果。第一次使用需在鏡頭電腦防火牆允許 TCP 8766，兩台電腦也必須在同一個可信任 LAN。

不需要跨電腦時仍使用 `start_dual.ps1`，預設只在鏡頭電腦的 localhost 可見。不要把 8766 直接暴露到網際網路；跨網路應改用 VPN 或受控 tunnel。

雙鏡頭頁面啟動新連線時，會在 `person_tracking/live_captures/<時間戳>/` 建立本機工作階段；每個鏡頭的每個已確認 Track ID 第一次出現時，將人物框裁切成一張 JPEG，並在 `manifest.json` 記錄。符合 P 候選條件時，頁面會保留並排的 A/B 人物照片、Track ID 與相似分數，讓人核對；底下也有本次所有已保存人物照片。按停止時，會清除本網站登記的本次和舊工作階段人物照片，詳細範圍見下文。關閉網頁後因閒置自動停止鏡頭，不會自動刪除照片。該資料夾被 Git 忽略，不會隨程式碼上傳；請只在取得現場人物同意的情況下使用，並自行管理保存期限。Track ID 可能因遮擋/重新入鏡而變動，一人可能有多張照片；照片比對仍不是可靠的身分辨識。

人物照片不再固定為第一次偵測的畫面。同一個 Track ID 持續被看到時，服務會比較裁切完整度、面積、清晰度與偵測信心；OpenCV 正面臉偵測成功時額外優先保留該張。較好的照片覆蓋本次同 ID 的舊 JPEG，網頁與配對卡會更新。若已人工審核某一配對，該配對所涉照片會凍結，避免審核後證據又變動。正面臉偵測並非可靠的姿態估計，無法保證每次都找到正面照。

若自動挑選的照片仍不是想要的角度，可讓該人物保持在對應鏡頭畫面中、轉正後按照片下方「用目前畫面重拍並鎖定」。網站會用最近一次已處理、且不超過三秒的人物裁切影格取代這個 ID 的照片；已人工審核的配對照片不可重拍。頁面重整只重新載入目前工作階段，不會再自行重啟鏡頭或清空審核；首次使用或已停止時需手動按「連接雙鏡頭」。

2026-10-02 起，按「停止雙鏡頭並清除全部人物照片」會連以前工作階段的網站照片一起刪除。刪除範圍只限 `person_tracking/live_captures/` 內符合時間戳命名的工作階段，以及各自 `manifest.json` 中明確登記、名稱符合 `A_####.jpg`／`B_####.jpg` 的檔案；未登記圖片、其他檔案及舊 `manifest.json` 保留。本次 `manifest.json` 仍依先前停止規則清除。沒有正在執行的工作階段時，按停止也會清理舊照片。這不會刪除網站以外的相機影像或專題資料。

即時跨鏡頭分數現在使用同一追蹤 ID 最近五次衣著特徵的平滑值，避免某一幀視角或曝光波動單獨左右結果；原本的門檻與連續三次 P 規則不變。人工審核區可自行從已存的 A/B 照片選一組「加入人工核對」，即使演算法沒產生 P 也可以查看兩張照片。按「同一人」或「不是同一人」會在本次 `manifest.json` 記下判斷；否決的 A/B ID 組合在本次工作階段不再被自動配對。人工判斷不訓練模型、不能證明其他時間或其他 ID 的身分。

人工按 ✓／✕ 後，該組並排照片與沒有其他待審核配對的對應人物縮圖會保留約 5 秒，再於約 0.6 秒內淡出並從版面收起。頁面會留下精簡的已審核組數及「查看／修改已審核照片」按鈕；點擊可重新展開、改判後再次自動收起。重整頁面仍以本次工作階段的審核時間判斷收起狀態。這只改變畫面顯示，不會在五秒後刪除本機 JPEG；照片仍依上述「停止雙鏡頭」規則清除。✓ 只記錄判斷並凍結已審核照片，✕ 另排除本次工作階段相同 A/B Track ID 組合；兩者都不更新 YOLOX 權重或建立跨工作階段學習資料，因此準確率不會因按勾叉自動逐漸提高。

為降低延遲，攝影機畫面以最新擷取的 JPEG 影格獨立更新（最多約 10 FPS），YOLOX/Tracker 則在背景更新框線、ID 與配對資料。兩者不再互相阻塞；框線可能比底下畫面晚一個 AI 推論週期，這是以標註新鮮度換取畫面即時性。

雙擊上一層的 `啟動即時追蹤網站.cmd`。它會啟動本機服務並開啟 `http://127.0.0.1:8765/`；服務已在執行時直接開啟同一網址，不另開一份。

頁面自動連接鏡頭 0。可以切換鏡頭編號、重新連線或停止攝影機。插上 USB 後連線失敗會自動重試；沒有偵測到人時顯示 0 人，並不代表程式故障。關閉所有使用此頁面的分頁約 10 秒後會釋放鏡頭；頁面在背景被瀏覽器暫停時可能也會停止，可按重新連線恢復。

## 沿用現有系統

`server.py` 直接匯入既有 `person_tracking/pipeline.py` 的 `Detector` 和 `Tracker`。沒有改写 YOLOX、追蹤演算法或原本 ModelSim／雙鏡頭腳本；新增的只有取圖、網站 API 與畫面顯示連接層。

攝影機由讀取執行緒持續取圖，既有偵測器處理最新影格，避免等待舊影格堆積。頁面顯示同一處理影格的人物框與 ID，更新率取決於本機推論速度；保持原生 640×480。這個網站目前是單鏡頭即時追蹤視窗，ModelSim 不在即時畫面處理迴圈中。先前雙鏡頭程式仍獨立保留。

單鏡頭服務僅監聽本機 127.0.0.1，影像只放記憶體。雙鏡頭服務同樣只監聽本機，不上傳、不自動錄影，但會保存上文所述的人物裁切照。沒有連接公共網站或雲端主機。保留原本 YOLOX 人物偵測的限制，ID 是短期追蹤編號，不是真實身分識別。

若雙擊後沒有頁面，查看 `server.log`、`server-error.log`。若其他程式已占用鏡頭，先關閉該程式，然後按重新連線。
