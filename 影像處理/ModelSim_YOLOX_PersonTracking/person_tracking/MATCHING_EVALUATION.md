# 跨鏡頭同人配對評估

執行：

```powershell
python evaluate_matching_dataset.py
```

`matching_dataset.json` 每筆資料代表一個人工標記案例：`same_person` 是人工答案，`a_id`／`b_ids` 是兩台鏡頭的 Track ID，`a_color`／`b_colors` 是目前 matcher 使用的外觀向量範例。程式會將 matcher 的 `confirmed_candidate` 視為「同一人」，並計算 TP、TN、FP、FN、accuracy、precision、recall、F1。

有 `a_box`／`b_box` 的案例另外計算四個框座標的最大像素誤差；目前以 `<20 px` 作為位置誤差通過條件。

目前附的資料是可重跑的合成回歸 fixture，不是真人資料集。要取得正式專題分數，請將案例替換為兩台鏡頭錄影中人工確認的同人／不同人配對，並保留測試集不參與門檻調整。
