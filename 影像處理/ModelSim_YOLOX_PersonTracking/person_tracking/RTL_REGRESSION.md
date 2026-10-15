# ModelSim 電路自動驗證

更新：2026-10-15。雙擊上一層的 `開啟ModelSim驗證.cmd`，會開啟 ModelSim、編譯並執行測試，保留 Transcript 與 Wave 視窗。原始測試程式為本目錄的 `tb_rtl_regression.v`。

成功時 Transcript 顯示 `RTL_REGRESSION_PASS frames=7 checks=89`。任何檢查不符即以 FAIL / fatal 停止；不能只以編譯沒有錯誤判斷通過。

## 波形怎麼看

- `pixel_valid`：本拍有輸入像素；為 0 時應暫停計數。
- `frame_start`：一張新影像的第一個有效像素。
- `x0/y0/x1/y1`：人物框，右、下邊界不包含在框內。
- `pixel_count`：每張影像共接收 307200 個有效像素。
- `feature_valid`：完整影像完成時，只拉高一拍。
- `top_pixels/bottom_pixels`：人物框上下區域的像素數。
- `feature`：上區主色、下區主色、上區比例、下區比例；全紅預期 `226464`，上紅下藍預期 `246464`（比例 0x64 = 100%）。
- `color_similar`：兩份有效特徵主色相同且上下區比例差都不超過 35 個百分點。

GUI 會保留全程波形，可在 Wave 放大各影格結尾。這是合成影像電路測試，不會啟動鏡頭或網站，也沒有在 FPGA 上執行。

## 測試範圍

7 張完整 640×480 影像：全紅、偏移且奇數高度的上紅下藍人物框（含輸入暫停）、影像右下角小框、無人物、零寬框、只有一列的框、全黑。影格間不重置，檢查歷史統計有清除。另檢查輸出時機、有效脈衝、reset 清除，以及相似度 35/36 的雙向邊界、不同主色、無效特徵。

預期面積與色彩結果由 testbench 手算常數給定，不呼叫 DUT 色彩函式建立答案。仍未涵蓋全部八類色彩分類門檻、任意亂數資料、影格中途重置、時序收斂或完整 YOLOX/跨鏡頭硬體化。

批次重跑：`powershell -NoProfile -ExecutionPolicy Bypass -File .\open_rtl_regression.ps1 -Batch`

啟動器會將三份 Verilog 複製到 `%TEMP%\project_rtl_regression` 再執行，避免 ModelSim 中文路徑問題；修改原始碼後請重新啟動以更新副本。原始碼保留在專題資料夾，暫存資料可重建。ModelSim 預設路徑為 `C:\modeltech64_2020.4\win64\vsim.exe`，也可用 `MODELSIM_VSIM` 指定。

## 本機實測

2026-10-15 使用 ModelSim SE-64 2020.4 實際批次執行，7 frames、89 checks PASS，編譯及模擬 0 errors / 0 warnings。精簡原始輸出見 `rtl_regression_console.txt`。這不等於 PYNQ/EGo1 上板驗證，也不代表完整偵測或配對準確率通過。
