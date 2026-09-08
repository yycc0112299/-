# Professor Questions

## 1. 原始專題大概在做什麼？

原始 MCDPT 是先偵測人物，再把人物影像轉成 feature vector，最後用距離判斷不同影像中的目標是不是同一個人。

## 2. 目前做到哪裡？

目前只做到 Verilog module 加 testbench。testbench 會建立兩張 8x8 RGB 圖，轉成亮度特徵後比較距離。

## 3. 為什麼只看亮度？

因為目前是第一版 testbench。先用最小方法確認資料流程跑得通：RGB 轉亮度、抽特徵、算距離、用門檻判斷。之後才會考慮加入顏色或更完整的特徵。

## 4. RGB 怎麼轉亮度？

不是直接平均，而是使用亮度加權公式：

`Y = 0.299R + 0.587G + 0.114B`

Verilog 版寫成：

`gray = (77R + 150G + 29B) >> 8`

這樣可以避免小數運算，也比 `(R+G+B)/3` 更合理。

## 5. 為什麼刪掉 average？

average 主要用在影片或連續 frame，因為同一個人會出現在很多張畫面中。目前只比較兩張靜態測試圖，沒有時間序列，所以先刪掉 average，讓 testbench 更單純。

## 6. 為什麼刪掉 two image re-id top？

原本 top module 只是把 extractor、average、matcher 接起來。現在 average 已經移除，testbench 可以直接接 extractor 和 matcher，所以先刪掉這層包裝，讓教授看 code 時更直接。

## 7. 這版的限制是什麼？

它不是完整辨識系統，沒有真實圖片讀取、沒有自動偵測、沒有影片追蹤，也沒有 FPGA 顯示。它只是最小 testbench 原型，用來證明亮度特徵比對流程可以用 Verilog 寫出來。

