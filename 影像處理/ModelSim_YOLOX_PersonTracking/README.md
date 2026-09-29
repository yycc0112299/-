# 人物偵測、追蹤與 ModelSim 專題

本專題包含兩條相關但不同的流程：單鏡頭人物偵測/短期追蹤並送完整人物框給 ModelSim 做 ROI 色彩特徵；以及雙 USB 鏡頭各自追蹤後，以自寫外觀規則產生同時可見人物的跨鏡頭候選。另保留較早的 8×8 RTL、全畫面顏色比較基準，以及一個沿用既有 YOLOX tracker 的本機即時網站。

## 環境準備

需要 Windows、Python 3、ModelSim SE 2020.4（執行 RTL 流程時），以及 USB 攝影機（實拍流程時）。在此資料夾開啟 PowerShell：

```powershell
python -m pip install -r .\person_tracking\requirements.txt
Set-Location .\person_tracking
.\setup_assets.ps1
```

`setup_assets.ps1` 下載 OpenCV Zoo YOLOX ONNX 模型和公開測試圖片；模型下載後會驗證 SHA-256。模型權重/測試圖片不放在 GitHub，請每位使用者在本機取得。模型程式來源與 Apache 2.0 授權見 `person_tracking/assets/sources.json` 和 `LICENSE_YOLOX`。

執行前確認 `vsim.exe` 在 PATH；否則設定環境變數，例如：

```powershell
$env:MODELSIM_VSIM='C:\modeltech64_2020.4\win64\vsim.exe'
```

腳本使用 PATH 中的 `python`；若需指定直譯器，設定 `$env:PROJECT_PYTHON`。Codex 本機 runtime 若存在，也會作為 Python PATH 不可用時的後備選項。

## 單鏡頭人物追蹤與 ModelSim

在本資料夾執行：

```powershell
.\run_person_tracking.ps1 -Mode camera -Frames 90
.\run_person_tracking.ps1 -Mode web
```

使用已保存影格重播時：

```powershell
.\run_person_tracking.ps1 -Mode replay -InputDir 'path\to\frames' -Frames 30
```

架構、訊號和限制見 `person_tracking/README.md`。CPU 上的 YOLOX 提供人物框；`pipeline.py` 的專題自寫 tracker 維護短期 ID；ModelSim RTL 接收 640×480 RGB 影格及框座標，計算框內上/下區域色彩特徵。偵測器不在 Verilog/FPGA 執行。

## 雙 USB 鏡頭候選配對

在本資料夾執行：

```powershell
.\run_dual_camera.ps1 -CameraA 0 -CameraB 1 -Frames 30 -Rtl
```

需兩台不同裝置索引。兩側獨立 YOLOX 偵測與 tracker；`cross_camera.py` 以 HSV 外觀相似度產生候選 P 標籤。候選不是人物身份保證，也不含跨時間人物資料庫。詳細流程及已知限制見 `person_tracking/DUAL_CAMERA.md`。

目前保存的雙鏡頭紀錄是已保存畫面的 replay，並非兩台實體相機實測；見 `person_tracking/verification_report.json` 及共享倉庫 `PROGRESS_FOR_CODEX.md`。

## 本機即時網站

雙擊 `啟動即時追蹤網站.cmd`。網站僅監聽 `127.0.0.1:8765`，透過既有 `person_tracking/pipeline.py` 的 YOLOX 偵測與 Tracker 顯示單鏡頭即時畫面。它不執行 ModelSim 或雙鏡頭配對。細節見 `live_site/README.md`。

## 較早的 RTL / 全畫面基準

`two_camera_top.v`、`color_feature.v` 與對應 testbench 是小型合成輸入功能測試；`color_feature_stream.v`、`tb_camera_file.v`、`camera_bridge.py` 是完整尺寸全畫面顏色比較基準。它們不包含最新人物偵測/追蹤邏輯。ModelSim 腳本會在英文暫存路徑執行，以避開資料庫對中文路徑的限制。

## 證據和分享界線

單鏡頭兩輪 USB 實拍與 ModelSim 輸出、照片驗證資料及雙鏡頭 replay 資料曾保存在 `person_tracking/runs/`、`dual_runs/` 和 `camera_runs/`。這些資料可能含相機/人物畫面，均不納入版本控制。報告數值與執行限制摘要記錄在共享倉庫的 `PROGRESS_FOR_CODEX.md` 和 `PROGRESS_FOR_HUMANS.md`。歷史驗證紀錄不等於在其他電腦重新驗證。
