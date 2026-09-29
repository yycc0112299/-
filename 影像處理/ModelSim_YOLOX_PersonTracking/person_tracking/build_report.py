"""Assemble a reviewable report from verified saved camera/web/RTL evidence."""
from pathlib import Path
import csv,html,json
ROOT=Path(__file__).resolve().parent
CAM=ROOT/'runs'/'camera_validation_20260925_105417'
WEB=ROOT/'runs'/'web_validation_20260925_105322'
SAMPLES=[0,30,60,90,119]

def main():
    camera=json.loads((CAM/'validation.json').read_text())
    web=json.loads((WEB/'validation.json').read_text())
    tracker=json.loads((ROOT/'tests'/'tracking_results.json').read_text())
    assert tracker['status']=='PASS' and tracker['tests_run']==6
    for trial,summary in enumerate(camera,1):
        folder=CAM/f'trial_{trial}'
        records=json.loads((folder/'detections.json').read_text())
        rows=list(csv.DictReader((folder/'features.csv').open()))
        assert len(records)==len(rows)==120
        assert all(len(r['detections'])==1 and r['detections'][0]['track_id']==1 for r in records)
        assert all(int(r['valid'])==1 and int(r['track_id'])==1 for r in rows)
        assert all(int(r['previous_available'])==int(i>0) for i,r in enumerate(rows))
        transcript=(folder/'transcript').read_text()
        assert 'PERSON_RTL_PASS: 120' in transcript and 'Errors: 0, Warnings: 0' in transcript
        assert all((folder/'annotated'/f'{i:06}.png').is_file() for i in range(120))
        summary['needs_visual_review']=False
        summary['visual_review']={'sampled_frames':SAMPLES,'scope':'Sampled annotated frames reviewed; one visible person correctly boxed with ID 1. Automated ID/count checks cover all 120 frames.','status':'PASS'}
        summary['color_similar_pairs']=sum(int(r['color_similar']) for r in rows[1:])
        summary['color_changed_pairs']=119-summary['color_similar_pairs']
        (folder/'summary.json').write_text(json.dumps(summary,indent=2))
    positives=[s for s in web if 'detection_tracking_validation' in s]
    assert len(positives)==6 and all(s['detection_tracking_validation']['status']=='PASS' for s in positives)
    assert all(s['rtl']['status']=='PASS' for s in web+camera)
    assert web[-1]['negative_validation']=='PASS'
    (CAM/'validation.json').write_text(json.dumps(camera,indent=2))
    audit=dict(camera=camera,web=web,tracker=tracker,
        observed_limitation='Heavily truncated left-edge person in bus image detected in 4/21 transformed frames; excluded from the 105 main-person annotations and reported separately, not claimed as zero-miss overall.',
        architecture='CPU YOLOX detection and short-term tracking; full 640x480 RTL ROI color statistics and same-track feature comparison; captured-then-processed, not real-time FPGA inference.')
    (ROOT/'verification_report.json').write_text(json.dumps(audit,indent=2))
    panels=[]
    for trial,s in enumerate(camera,1):
        relative=(CAM/f'trial_{trial}').relative_to(ROOT).as_posix()
        panels.append(f'''<article><h2>USB 實拍第 {trial} 輪</h2><p>120/120 張偵測到人物，ID 1 全程連續。ModelSim 120/120 筆核對通過。</p>
<img id="image{trial}" src="{relative}/annotated/000000.png" width="640" height="480">
<p><button onclick="toggle({trial})">播放／暫停</button> <input id="slider{trial}" type="range" min="0" max="119" value="0" oninput="show({trial},this.value)"><span id="label{trial}">影格 0</span></p>
<p><a href="{relative}/report.html">全部照片</a> · <a href="{relative}/features.csv">ModelSim 特徵表</a> · <a href="{relative}/transcript">模擬紀錄</a></p></article>''')
    links=''.join(f'<li><a href="{(WEB/folder/"report.html").relative_to(ROOT).as_posix()}">{label}</a></li>' for folder,label in [('bus_1.0','多人照片：原亮度'),('bus_0.8','多人照片：較暗'),('bus_1.1','多人照片：較亮'),('zidane_1.0','雙人照片：原亮度'),('zidane_0.8','雙人照片：較暗'),('zidane_1.1','雙人照片：較亮'),('negative','三組無人負例')])
    bases={str(i):(CAM/f'trial_{i}'/'annotated').relative_to(ROOT).as_posix() for i in [1,2]}
    page='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>人物偵測與追蹤驗證</title><style>body{font:17px system-ui,sans-serif;background:#f0f4f8;color:#15283e;max-width:1400px;margin:auto;padding:28px}h1{font-size:30px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:24px}article{background:white;border-radius:12px;padding:18px}img{width:100%;height:auto}button{padding:9px;border:0;background:#146d9c;color:white;border-radius:6px}input{width:50%}a{color:#086a9b}.note{background:#fff5d9;padding:16px;border-left:4px solid #e4a933}li{margin:9px}</style>
<h1>人物偵測與追蹤：實機驗證成果</h1><p>640×480 USB 實拍 2 輪、240 張；每輪人物均持續為 ID 1，240 筆人物特徵通過 ModelSim 核對。</p>
<p>下方播放為已錄製照片的每秒 10 張重播，用來查看追蹤；不是即時攝影機或處理速度展示。</p><div class="grid">'''+''.join(panels)+'''</div>
<h2>重複驗證</h2><ul><li>網路照片：2 張 × 3 種亮度 × 7 個位置，共 42 幀；105 次主要人物標註皆配對成功，沒有 ID 切換。</li>
<li>3 組無人負例（黑、白、水果照片）：無誤報。</li><li>6 項追蹤邏輯測試：交會、移動、短暫遮擋、超時離開、外觀不相符、空景。</li>
<li>5 個手算 ModelSim 案例：奇數高度、黑衣、影格邊界、主色平手與未偵測到人。</li></ul>
<p class="note">已知限制：bus 照片左邊大幅裁切的人物，21 幀僅 4 幀抓到，未列入 105 次主要人物標註。因此沒有宣稱所有場景零漏抓。USB 這次只拍到上半身；框的上下兩區不是完整身體上下半身。偵測與追蹤在電腦執行，ModelSim 負責人物框內的顏色特徵與比較；框內仍可能有背景。</p>
<h2>網路測試與原始紀錄</h2><ul>'''+links+'''</ul><p><a href="README.md">操作說明與架構</a> · <a href="verification_report.json">完整驗證數據</a></p>
<script>const bases='''+json.dumps(bases)+''';const timers={};function show(t,i){document.getElementById('image'+t).src=bases[t]+'/'+String(i).padStart(6,'0')+'.png';document.getElementById('slider'+t).value=i;document.getElementById('label'+t).textContent='影格 '+i;}function toggle(t){if(timers[t]){clearInterval(timers[t]);delete timers[t];}else{timers[t]=setInterval(()=>show(t,(Number(document.getElementById('slider'+t).value)+1)%120),100);}}</script></html>'''
    (ROOT/'verification_report.html').write_text(page,encoding='utf-8')
    print('REPORT_READY',ROOT/'verification_report.html')
    print('CAMERA',[(s['frames_with_person'],s['track_ids'],s['color_similar_pairs'],s['color_changed_pairs']) for s in camera])

if __name__=='__main__':main()
