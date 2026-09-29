"""HTTP integration checks against the live local adapter, not browser automation."""
import base64,json,time,urllib.request,urllib.error
from pathlib import Path
URL='http://127.0.0.1:8765'
def call(path,data=None,headers=None):
    payload=json.dumps(data).encode() if data is not None else None
    h={'Content-Type':'application/json'} if payload is not None else {}
    h.update(headers or {})
    with urllib.request.urlopen(urllib.request.Request(URL+path,data=payload,headers=h),timeout=10) as response:
        return json.load(response)

assert call('/api/health')['app']=='usb-person-live'
try:
    call('/api/start',{'camera':0},{'Origin':'https://untrusted.example'})
    raise AssertionError('Cross-origin start must fail')
except urllib.error.HTTPError as e:assert e.code==403
call('/api/start',{'camera':0})
frames=[];last={}
for _ in range(60):
    last=call('/api/live')
    if last['status']=='live':
        assert base64.b64decode(last['image']).startswith(b'\xff\xd8')
        frames.append(last['frame_id'])
        if len(set(frames))>=3:break
    time.sleep(.25)
call('/api/stop',{'camera':0})
stopped=call('/api/live');assert stopped['status']=='stopped' and stopped['image'] is None and not stopped['people']
call('/api/start',{'camera':0})
time.sleep(12)
idle=call('/api/live');assert not idle['enabled'] and idle['image'] is None,'Camera not released after viewer disconnected'
result=dict(health='PASS',origin_guard='PASS',stop='PASS',idle_release='PASS',
    live_frames='PASS' if len(set(frames))>=3 else 'NOT_VERIFIED',
    frame_ids=frames,status=last['status'],message=last['message'],people=last.get('people',[]),fps=last.get('fps'))
(Path(__file__).parent/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
