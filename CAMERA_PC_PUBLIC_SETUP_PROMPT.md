# 鏡頭電腦公開 HTTPS 啟動 Prompt

把以下內容交給連 USB 鏡頭的電腦執行。網站與 Cloudflare Tunnel 必須由該電腦啟動；GitHub 只同步程式，不保存相機影像或 token。

```text
請把這台電腦設定成專題的鏡頭來源端。

專題路徑：C:\Users\USER\Desktop\codex\專題\本機鏡頭網站

1. 確認下列檔案存在：
   live_site\start_remote.ps1
   runtime\cloudflared.exe

2. 檢查鏡頭：
   $root = "C:\Users\USER\Desktop\codex\專題\本機鏡頭網站"
   $env:PYTHONPATH = "$root\camera_deps"
   py -3 -c "import cv2; print('OpenCV:', cv2.__version__); [print('CAMERA', i, cv2.VideoCapture(i).isOpened()) for i in range(4)]"

3. 選擇回傳 True 的鏡頭編號。若 CAMERA 0 為 True，執行：
   powershell -NoProfile -ExecutionPolicy Bypass -File "$root\live_site\start_remote.ps1" -CameraA 0 -CameraB -1 -NoBrowser

   若 CAMERA 1 為 True，把上面的 CameraA 0 改成 CameraA 1。

4. 啟動成功後讀取：
   Get-Content "$root\work\remote_site\private-link.txt"

5. 只回報 private-link.txt 的網址、鏡頭編號、畫面結果、/api/health 與 /api/live 結果。

禁止把 access.json、token、private-link.txt 內容上傳到 GitHub 或公開聊天室；不要直接開放 8766 埠。
```

## 完成判定

- `private-link.txt` 網址可從非同一個 Wi-Fi 的手機開啟。
- 網頁畫面確實來自這台連 USB 鏡頭的電腦。
- `/api/health` 和 `/api/live` 有回應。
- `cloudflared`、網站服務與鏡頭電腦必須持續執行。
- Quick Tunnel 重啟可能換網址；固定 `.com` 仍需要由使用者管理的網域與 DNS 權限。
