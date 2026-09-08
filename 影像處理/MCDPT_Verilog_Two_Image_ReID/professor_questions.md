# Professor Questions

## 1. 原始 MCDPT 用什麼方法？

原始 MCDPT 先偵測人物，再用 person re-identification model 把人物影像轉成 feature vector。不同 camera 的人物會用 feature distance 比較，距離小於門檻就判斷為同一個人。

## 2. 你們現在做到哪裡？

目前只做到 Verilog module 加 testbench。testbench 裡手動建立兩張 8x8 RGB 圖，但判斷時先轉成灰階亮度。亮度相近會輸出 `same_person = 1`，亮度差很多會輸出 `same_person = 0`。

## 3. 為什麼不用完整 OpenVINO 或 CNN？

完整 re-ID model 太大，不適合在一開始直接用 Verilog 手寫。我們先保留 MCDPT 的演算法骨架，也就是 feature vector、track average、distance matching 和 threshold decision。

## 4. 你們的 feature vector 是什麼？

我們先用純亮度特徵模擬 re-ID feature vector。每個 RGB pixel 會先轉成灰階亮度，接著統計平均亮度、上半部亮度、下半部亮度、亮暗像素數、亮度邊緣、前景面積和中心位置。

## 5. 為什麼不用 cosine distance？

cosine distance 需要正規化、乘法和除法，Verilog 初版會比較難。我們先用 sum of absolute differences 當成硬體友善的距離公式。概念一樣是距離小代表比較像。

## 6. 這版的限制是什麼？

目前沒有自動偵測人物框，沒有真實圖片輸入流程，沒有多攝影機通訊，也沒有上板，而且目前只看亮度，不看真正的衣服顏色。它只能證明最基本的 re-ID matching 流程可以用 Verilog testbench 表示。

## 7. 下一步可以做什麼？

下一步可以把 testbench 的人工色塊改成 `.mem` 圖片輸入，再調整 feature threshold。之後才考慮更完整的 FPGA pipeline 或 VGA 顯示。
