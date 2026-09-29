"""Loopback-only USB person tracking website. Frames stay in memory."""
import argparse,base64,json,sys,threading,time,webbrowser
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'person_tracking'))
import pipeline as p

class Engine:
    def __init__(self):
        self.lock=threading.RLock();self.enabled=False;self.index=0;self.epoch=0
        self.heartbeat=0;self.raw=None;self.raw_id=0;self.jpeg=None
        self.state=dict(status='stopped',message='攝影機尚未啟動',people=[],fps=0,latency_ms=0,frame_id=0)
        threading.Thread(target=self.capture,daemon=True).start()
        threading.Thread(target=self.process,daemon=True).start()
    def control(self,enabled,index=0):
        with self.lock:
            self.enabled=enabled;self.index=index;self.epoch+=1;self.raw=None;self.jpeg=None;self.heartbeat=time.monotonic()
            self.state.update(status='connecting' if enabled else 'stopped',message='正在連接 USB 攝影機…' if enabled else '攝影機已停止',people=[],fps=0,latency_ms=0)
    def snapshot(self):
        with self.lock:
            self.heartbeat=time.monotonic()
            return dict(self.state,image=self.jpeg,camera=self.index,enabled=self.enabled)
    def capture(self):
        while True:
            with self.lock:
                if self.enabled and time.monotonic()-self.heartbeat>10:self.control(False,self.index)
                active=self.enabled;epoch=self.epoch;index=self.index
            if not active:time.sleep(.1);continue
            cap=None
            try:
                cap=p.cv2.VideoCapture(index,p.cv2.CAP_DSHOW)
                if not cap.isOpened():raise RuntimeError('找不到這台攝影機。請插好 USB，或改選另一個鏡頭編號；也請關閉正在使用鏡頭的其他程式。')
                cap.set(p.cv2.CAP_PROP_FRAME_WIDTH,640);cap.set(p.cv2.CAP_PROP_FRAME_HEIGHT,480)
                while True:
                    with self.lock:
                        if self.epoch!=epoch or not self.enabled:break
                        if time.monotonic()-self.heartbeat>10:
                            self.control(False,index);break
                    ok,frame=cap.read();stamp=time.monotonic()
                    if not ok:raise RuntimeError('鏡頭已中斷，正在等待 USB 重新連接。')
                    if frame.shape!=(480,640,3):raise RuntimeError('這台鏡頭沒有回傳 640 × 480 影像，請改選其他鏡頭。')
                    with self.lock:
                        if self.epoch!=epoch:break
                        self.raw_id+=1;self.raw=(frame,self.raw_id,stamp,epoch)
            except Exception as error:
                with self.lock:
                    if self.epoch==epoch:
                        self.raw=None;self.jpeg=None;self.state.update(status='waiting',message=str(error),people=[],fps=0)
                time.sleep(2)
            finally:
                if cap is not None:cap.release()
    def process(self):
        detector=None;tracker=None;seen=-1;generation=-1;last=time.monotonic()
        while True:
            with self.lock:raw=self.raw;active=self.enabled
            if not active or raw is None or raw[1]==seen:time.sleep(.02);continue
            frame,seq,stamp,epoch=raw;seen=seq
            try:
                if detector is None:detector=p.Detector()
                if epoch!=generation:tracker=p.Tracker();generation=epoch;last=time.monotonic()
                started=time.monotonic();ds=tracker.update(detector.detect(frame));vis=frame.copy()
                people=[]
                for d in ds:
                    x0,y0,x1,y1=d['box'];color=(105,230,80)
                    p.cv2.rectangle(vis,(x0,y0),(x1,y1),color,2)
                    p.cv2.putText(vis,f'ID {d["track_id"]}  {d["confidence"]:.0%}',(x0,max(22,y0-8)),p.cv2.FONT_HERSHEY_SIMPLEX,.65,color,2)
                    people.append({k:v for k,v in d.items() if k!='hist'})
                ok,jpg=p.cv2.imencode('.jpg',vis,[p.cv2.IMWRITE_JPEG_QUALITY,85])
                if not ok:raise RuntimeError('影像編碼失敗')
                now=time.monotonic();fps=1/max(.001,now-last);last=now
                with self.lock:
                    if self.enabled and self.epoch==epoch and self.raw is not None:
                        self.jpeg=base64.b64encode(jpg).decode('ascii')
                        self.state.update(status='live',message='已偵測到人物' if people else '目前沒有偵測到人物',
                            people=people,fps=round(fps,1),latency_ms=round((now-stamp)*1000),
                            inference_ms=round((now-started)*1000),frame_id=seq)
            except Exception as error:
                with self.lock:
                    if self.epoch==epoch:self.jpeg=None;self.state.update(status='error',message='偵測程式暫時無法執行：'+str(error),people=[],fps=0)
                time.sleep(2)

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def allowed(self):
        hosts={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
        return self.headers.get('Host') in hosts and self.headers.get('Origin',f'http://127.0.0.1:{self.server.server_port}') in {'http://'+h for h in hosts}
    def send(self,code,body,kind='application/json; charset=utf-8'):
        if isinstance(body,dict):body=json.dumps(body,ensure_ascii=False).encode('utf-8')
        self.send_response(code);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('X-Frame-Options','DENY');self.end_headers()
        try:self.wfile.write(body)
        except (BrokenPipeError,ConnectionResetError):pass
    def do_GET(self):
        if not self.allowed():return self.send(403,{'error':'Local origin required'})
        if self.path=='/api/health':return self.send(200,{'app':'usb-person-live','version':1})
        if self.path=='/api/live':return self.send(200,self.server.engine.snapshot())
        if self.path=='/':return self.send(200,(ROOT/'index.html').read_bytes(),'text/html; charset=utf-8')
        self.send(404,{'error':'Not found'})
    def do_POST(self):
        if not self.allowed():return self.send(403,{'error':'Local origin required'})
        if self.headers.get('Content-Type')!='application/json':return self.send(415,{'error':'JSON required'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<1024:raise ValueError()
            data=json.loads(self.rfile.read(size));index=data.get('camera',0)
            if type(index)!=int or not 0<=index<=9:raise ValueError()
        except (ValueError,TypeError):return self.send(400,{'error':'Invalid request'})
        if self.path not in ['/api/start','/api/stop']:return self.send(404,{'error':'Not found'})
        self.server.engine.control(self.path=='/api/start',index)
        self.send(200,{'ok':True})

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8765);parser.add_argument('--browser',action='store_true')
    args=parser.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler);server.daemon_threads=True;server.engine=Engine()
    url=f'http://127.0.0.1:{args.port}/';print('READY '+url,flush=True)
    if args.browser:webbrowser.open(url)
    try:server.serve_forever()
    finally:server.engine.control(False);server.server_close()
if __name__=='__main__':main()
