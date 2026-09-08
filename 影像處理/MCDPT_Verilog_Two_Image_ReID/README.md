# 亮度版兩張影像比對

這份是目前先做到 testbench 的陽春版 Verilog。

原本專題的方向可以想成：

`影像 -> 抓特徵 -> 算距離 -> 判斷是不是同一個人`

現在沒有做到完整辨識，也沒有接螢幕顯示。這裡只用兩張很小的 8x8 RGB 人臉圖案，先模擬「亮度特徵可不可以拿來比較」。

## 目前檔案

| 檔案 | 功能 |
| --- | --- |
| `brightness_feature_extractor.v` | 把 RGB 像素轉成亮度，抓出簡單特徵 |
| `feature_distance.v` | 計算兩組特徵差多少 |
| `brightness_matcher.v` | 距離小於門檻就當作同一個 |
| `tb_brightness_matcher.v` | 用 function 畫出 8x8 人臉，放進去跑模擬 |

## 亮度公式

不是直接 `(R+G+B)/3`。

這裡使用比較常見的亮度權重：

`Y = 0.299R + 0.587G + 0.114B`

Verilog 裡面不能方便用小數，所以改成整數：

`gray = (77R + 150G + 29B) / 256`

程式用 `tmp[15:8]` 來取高 8 bits，效果就接近除以 256。

## 特徵內容

目前 feature 裡面放的是：

- 前景平均亮度
- 比較亮的點有幾個
- 比較暗的點有幾個
- 旁邊亮度差很大的邊界數量
- 前景面積
- 前景大概的 x 位置
- 前景大概的 y 位置

這些都只是簡化概念，重點是先把資料變成一串數字，然後用距離比較。

## 模擬方式

```tcl
xvlog brightness_feature_extractor.v feature_distance.v brightness_matcher.v tb_brightness_matcher.v
xelab tb_brightness_matcher
xsim tb_brightness_matcher -runall
```

預期結果：

- 兩張亮度接近的人臉，`same = 1`
- 兩張亮度差很多的人臉，`same = 0`
