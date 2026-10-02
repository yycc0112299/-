# 雙 USB 鏡頭草稿

接上兩台 USB 攝影機後，在 `modelsim_draft` 執行：

```powershell
.\run_dual_camera.ps1 -CameraA 0 -CameraB 1 -Frames 30
```

需要同時驗證兩邊人物框的 Verilog 色彩特徵時加 `-Rtl`。沒有第二台、兩個索引相同或無法讀到原生 640×480 時會報錯，不會偷偷以同一台冒充雙鏡頭。

## 保留原有追蹤

每台攝影機各有一個原本自行實作的 Tracker。`A:1` 與 `B:1` 是不同鏡頭的局部 ID，數字相同不代表同一個人。原本 `run_person_tracking.ps1` 單鏡頭程式可繼續使用。

人物偵測仍使用現有 YOLOX；沒有新增現成的 ReID 或跨鏡頭追蹤模型。新寫的 `cross_camera.py` 負責跨鏡頭配對，`dual_camera.py` 負責兩邊取圖、各自追蹤及結果輸出。

## 候選是如何判定的

外觀配對取人物框中央 60% 寬度以減少邊緣背景，再分上下兩區。每區使用平滑的明暗／色相統計，降低兩台鏡頭曝光和白平衡差異的影響；黑白衣服仍保留差別。上區佔總相似分數 75%、下區佔 25%，讓只拍到上半身的視角仍有配對機會。總分至少 0.72、雙方互為最佳候選、與第二名至少差 0.08，且連續三次成立後才顯示共用候選標記 P1、P2……。局部追蹤 ID 照常保留，ModelSim 仍處理原本完整人物框。

配對不清楚時顯示 ambiguous；外觀不同時 unmatched；確認次數尚不足時 candidate。人物離開或觀測中斷會重設連續確認次數。不會把未偵測到的人物位置當成真實觀測。

這版先處理兩邊當下都能看到的人物，不含「先從 A 離開、一段時間後出現在 B」的歷史身分資料庫。衣服相似、光線與角度不同都可能誤判；P 編號代表外觀候選，不是身分保證。框內仍含背景，只有上半身入鏡時分區不等於完整上下半身。

## 單鏡頭 A→B 時序交接模擬

若目前只有一台 USB 攝影機，可先用連續時間區段測試儲存特徵及重新關聯：

```powershell
.\run_sequential_handoff.ps1 -Camera 0 -ASeconds 10 -TransitionSeconds 1 -BSeconds 10
```

在本專案根目錄執行。0–10 秒做為 A 段，10–11 秒為切換空檔，第 11 秒開始做為 B 段。A 段追蹤到的已確認人物，其上/下區特徵會取平均後寫入 `camera_a_feature_gallery.json`。B 段使用全新的 tracker（局部 ID 重新編號），逐影格與凍結的 A 特徵庫比對；總相似分數、互為最佳候選、次佳差距及三次連續命中沿用 `cross_camera.py` 規則。B 段輸出 `P<n> SAME-CANDIDATE` 表示找到外觀候選。可在預覽視窗按 `q` 提前結束，或加 `-NoDisplay` 執行純文字模式。

此實驗要讓同一個人全程留在畫面中。結果資料在忽略的 `person_tracking/runs/handoff_日期_時間/`，包含 A 特徵庫、B 配對逐影格紀錄與 `summary.json`；不寫入影像。沒有 A 段特徵、B 段漏抓、衣著/光線改變、候選不唯一或未達連續命中門檻時，可能沒有配對。這只驗證單鏡頭同視角下的時間交接、tracker reset 與特徵比對資料流；不能代表兩台實體鏡頭、視角/色差差異或真正 Re-ID 系統的通過結果。

`summary.json` 的 `result_status` 可區分 `candidate_found`、`no_a_person_detected_or_confirmed`、`no_person_detected_in_b`、`b_tracks_seen_but_no_candidate_confirmed`；沒有候選時要先看 A/B 偵測數，不能直接解讀為外觀比對演算法失敗。

## 輸出與測試範圍

結果在 `person_tracking/dual_runs/日期_時間`：原始 A/B 照片、並排標註圖、`tracks_and_pairs.json`、`pairs.csv`、`summary.json`、`report.html`。加 `-Rtl` 時 A/B 各自保留 ModelSim 記錄與波形；跨鏡頭配對本身目前在 Python 執行。

USB 取圖使用兩台先 grab、再 retrieve 的方式，僅能縮小軟體讀取間隔，沒有宣稱硬體同步。流程先拍完再處理，不是即時多鏡頭系統。

2026-10-02 已用兩台實體鏡頭（內建與 Logitech C270）各擷取 30 張，A/B 的 ModelSim ROI 各 30 個 PASS。該批沒有確認的 P 候選；後續使用者提供的同一人雙鏡頭截圖顯示舊版分數偏低，因此更新了外觀分數計算。原始畫面與比對全部保存在本機。
