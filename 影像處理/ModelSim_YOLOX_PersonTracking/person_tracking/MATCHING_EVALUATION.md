# 跨鏡頭同人配對評估

執行：

```powershell
python evaluate_matching_dataset.py
```

`matching_dataset.json` 每筆資料代表一個人工標記案例：`same_person` 是人工答案，`a_id`／`b_ids` 是兩台鏡頭的 Track ID，`a_color`／`b_colors` 是目前 matcher 使用的外觀向量範例。程式會將 matcher 的 `confirmed_candidate` 視為「同一人」，並計算 TP、TN、FP、FN、accuracy、precision、recall、F1。

有 `a_box`／`b_box` 的案例另外計算四個框座標的最大像素誤差；目前以 `<20 px` 作為位置誤差通過條件。

目前附的資料是可重跑的合成回歸 fixture，不是真人資料集。要取得正式專題分數，請將案例替換為兩台鏡頭錄影中人工確認的同人／不同人配對，並保留測試集不參與門檻調整。

人物框 dataset 的既有結果可用以下命令彙總：

```powershell
python evaluate_detection_dataset.py
```

它讀取已保存的 `verification_report.json`，彙總 6 組公開圖片／亮度案例的人工標註觀測；目前結果為 105/105 配對、annotated recall=1.0、最低 IoU=0.855、ID switch=0。輸出也保留總影格數、總偵測數、總處理秒數，以及每個案例的 expected/matches/misses/recall/minimum IoU/edge frames/status，不只留下 PASS。這是人物框與短期追蹤的 dataset 評估，不是跨鏡頭身分準確率。
