# 外部 dataset 測試狀態

| Dataset | 狀態 | 證據／原因 |
|---|---|---|
| 公開 bus／zidane | 已跑模型 | 6 組亮度案例、105 個人工標註觀測；`dataset_evaluation.json` |
| EPFL Multi-view Multi-class | 已跑模型 | 939 個影格、1,302 個 ground-truth 框；recall 0.7949、precision 0.6613、mean IoU 0.7963；中心位置最大誤差 19.5256 px（<20 PASS），四邊最大誤差 37 px；`person_tracking/epfl_dataset_evaluation.json` |
| MTA | 未跑模型 | 官方下載需寄信申請；最小 `MTA_ext_short` 約 1.7 GB，不能在未授權下抓取 |
| WILDTRACK | 未跑模型 | 官方標註包約 68 MB，依目前「大檔案不用」決定未下載 |
| AI City MTMC | 未跑模型 | 官方資料需申請／註冊，且資料量大；未繞過存取限制 |
| MOTChallenge | 未跑模型 | 單鏡頭 benchmark，與跨鏡頭目標不完全相同；未另下載大型資料 |

所有已跑模型的結果都保留總數、IoU、precision、recall、漏抓、誤抓與逐案例明細。`PARTIAL` 結果不改寫成 `PASS`。

## 框穩定化算法比較

在同一份 EPFL 預測輸出上比較 Raw、EMA 0.25/0.5/0.75 與 median3。Raw 最好：中心最大誤差 `19.5256 px`、mean IoU `0.7963`；EMA 與 median3 因 EPFL 標註影格非連續而把框拖偏，中心最大誤差分別為 `35.1283`、`38.5811`、`28.0401`、`43.5115 px`，因此沒有把它們併入主程式。完整數字見 `person_tracking/box_stabilizer_benchmark.json`。

研究上常見的 ByteTrack、OC-SORT、BoT-SORT 主要改善 detection-to-track association、遮擋與 ID 維持，不會自動修正單幀 detector 的 bounding-box 邊界；因此本次先以同一 detector 輸出的定位誤差比較，不把公開論文的 MOT 分數直接當成這份 EPFL 的 px 誤差。
