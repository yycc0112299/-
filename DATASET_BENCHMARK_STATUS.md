# 外部 dataset 測試狀態

| Dataset | 狀態 | 證據／原因 |
|---|---|---|
| 公開 bus／zidane | 已跑模型 | 6 組亮度案例、105 個人工標註觀測；`dataset_evaluation.json` |
| EPFL Multi-view Multi-class | 已跑模型 | 939 個影格、1,302 個 ground-truth 框；recall 0.7949、precision 0.6613、mean IoU 0.7963；`person_tracking/epfl_dataset_evaluation.json` |
| MTA | 未跑模型 | 官方下載需寄信申請；最小 `MTA_ext_short` 約 1.7 GB，不能在未授權下抓取 |
| WILDTRACK | 未跑模型 | 官方標註包約 68 MB，依目前「大檔案不用」決定未下載 |
| AI City MTMC | 未跑模型 | 官方資料需申請／註冊，且資料量大；未繞過存取限制 |
| MOTChallenge | 未跑模型 | 單鏡頭 benchmark，與跨鏡頭目標不完全相同；未另下載大型資料 |

所有已跑模型的結果都保留總數、IoU、precision、recall、漏抓、誤抓與逐案例明細。`PARTIAL` 結果不改寫成 `PASS`。
