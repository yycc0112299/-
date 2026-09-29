"""Local person detection/tracking and full-resolution ROI RTL verification."""
import argparse, csv, hashlib, html, json, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
sys.path[:0]=[str(BASE/'camera_deps'),str(ROOT/'assets')]
import cv2
import numpy as np
from yolox import YoloX

def read_image(path):
    image=cv2.imdecode(np.fromfile(str(path),dtype=np.uint8),cv2.IMREAD_COLOR)
    if image is None: raise RuntimeError(f'Cannot read {path}')
    return image

def save_image(path,image):
    ok,data=cv2.imencode('.png',image)
    if not ok: raise RuntimeError('PNG encoding failed')
    data.tofile(str(path))

def fit(image):
    h,w=image.shape[:2]; scale=min(640/w,480/h)
    out=np.zeros((480,640,3),dtype=np.uint8)
    resized=cv2.resize(image,(round(w*scale),round(h*scale)))
    out[:resized.shape[0],:resized.shape[1]]=resized
    return out

def histogram(frame,box):
    x0,y0,x1,y1=box
    crop=frame[y0:y1,x0:x1]
    hsv=cv2.cvtColor(crop,cv2.COLOR_BGR2HSV)
    h=cv2.calcHist([hsv],[0,1],None,[12,8],[0,180,0,256]).reshape(-1)
    return h/max(float(h.sum()),1)

def iou(a,b):
    x=max(a[0],b[0]); y=max(a[1],b[1]); xx=min(a[2],b[2]); yy=min(a[3],b[3])
    inter=max(0,xx-x)*max(0,yy-y)
    return inter/max(1,(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-inter)

class Tracker:
    """Short-term association; IDs are not biometric identities or cross-camera IDs."""
    def __init__(self,max_missing=8):
        self.tracks={};self.next_id=1;self.max_missing=max_missing
    def update(self,detections):
        candidates=[]
        for tid,t in self.tracks.items():
            predicted=np.array(t['box'],float)+t['velocity']*(t['missed']+1)
            for j,d in enumerate(detections):
                overlap=iou(predicted,d['box'])
                ca=(predicted[:2]+predicted[2:])/2
                cb=(np.array(d['box'][:2])+np.array(d['box'][2:]))/2
                distance=float(np.linalg.norm(ca-cb))
                scale=max(40,float(np.linalg.norm(predicted[2:]-predicted[:2])))
                appearance=float(np.minimum(t['hist'],d['hist']).sum())
                if (overlap>.05 or distance<scale*.55) and appearance>.15:
                    score=.55*overlap+.35*appearance+.1*max(0,1-distance/scale)
                    candidates.append((score,tid,j))
        assigned_t=set();assigned_d=set();result=[]
        for score,tid,j in sorted(candidates,reverse=True):
            if tid in assigned_t or j in assigned_d:continue
            t=self.tracks[tid];d=detections[j]
            delta=(np.array(d['box'])-np.array(t['box']))/(t['missed']+1)
            t.update(box=d['box'],velocity=.5*t['velocity']+.5*delta,
                     hist=.7*t['hist']+.3*d['hist'],missed=0,hits=t['hits']+1)
            assigned_t.add(tid);assigned_d.add(j)
            result.append(dict(d,track_id=tid,status='confirmed' if t['hits']>=2 else 'tentative'))
        for tid in list(self.tracks):
            if tid not in assigned_t:
                self.tracks[tid]['missed']+=1
                if self.tracks[tid]['missed']>self.max_missing:del self.tracks[tid]
        for j,d in enumerate(detections):
            if j in assigned_d:continue
            tid=self.next_id;self.next_id+=1
            self.tracks[tid]=dict(box=d['box'],hist=d['hist'],velocity=np.zeros(4),missed=0,hits=1)
            result.append(dict(d,track_id=tid,status='tentative'))
        return sorted(result,key=lambda d:d['track_id'])

class Detector:
    def __init__(self):
        model=ROOT/'assets'/'yolox.onnx'
        self.model_sha256=hashlib.sha256(model.read_bytes()).hexdigest()
        cache=Path(tempfile.gettempdir())/('codex_person_'+self.model_sha256[:16]+'.onnx')
        if not cache.exists() or hashlib.sha256(cache.read_bytes()).hexdigest()!=self.model_sha256:shutil.copy2(model,cache)
        self.model=YoloX(str(cache),confThreshold=.3,nmsThreshold=.45)
        cv2.setNumThreads(4)
    def detect(self,frame):
        # Native 640x480 is padded to the model's 640x640 tensor, never downsampled.
        canvas=np.full((640,640,3),114,dtype=np.float32)
        canvas[:480]=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        predictions=self.model.infer(canvas)
        result=[]
        for row in predictions:
            if int(row[5])!=0:continue
            x,y,w,h=map(float,row[:4])
            box=[max(0,int(np.floor(x))),max(0,int(np.floor(y))),min(640,int(np.ceil(x+w))),min(480,int(np.ceil(y+h)))]
            if box[2]-box[0]<4 or box[3]-box[1]<4:continue
            result.append(dict(box=box,confidence=float(row[4]),hist=histogram(frame,box)))
        return result

def color_reference(rgb,box):
    x0,y0,x1,y1=box;crop=rgb[y0:y1,x0:x1].astype(np.int32)
    r,g,b=crop[:,:,0],crop[:,:,1],crop[:,:,2]
    mx=crop.max(axis=2);mn=crop.min(axis=2)
    # np.select applies the first matching condition, independently of RTL histogram state.
    codes=np.select([mx<35,(mx>=170)&(mx-mn<45),(r>140)&(g>120)&(b<90),
        (r>g)&(g>b)&(r>80)&(g-b>20),(r>g+35)&(r>b+35),(g>r+30)&(g>b+30),
        (b>r+30)&(b>g+30)], [0,1,5,6,2,3,4],default=7)
    half=(y1-y0)//2
    top=np.bincount(codes[:half].ravel(),minlength=8)
    bot=np.bincount(codes[half:].ravel(),minlength=8)
    return (int(top.argmax())<<20)|(int(bot.argmax())<<16)|(int(top.max())*100//int(top.sum())<<8)|(int(bot.max())*100//int(bot.sum()))

def run_rtl(folder,frames,records):
    work=Path(tempfile.mkdtemp(prefix='person_rtl_'))
    for name in ('person_roi_stream.v','person_feature_compare.v','tb_person_roi.v'):shutil.copy2(ROOT/name,work/name)
    expected=[]
    with (work/'pixels.rgb').open('wb') as pixels,(work/'regions.txt').open('w') as regions:
        for idx,(frame,record) in enumerate(zip(frames,records)):
            rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB);pixels.write(rgb.tobytes())
            for d in record['detections'] or [dict(track_id=0,box=[0,0,0,0])]:
                box=d['box']; valid=int(d['track_id']!=0)
                regions.write(' '.join(map(str,[idx,d['track_id'],valid,*box]))+'\n')
                expected.append(dict(frame=idx,track_id=d['track_id'],valid=valid,
                    feature=color_reference(rgb,box) if valid else 0,
                    top_pixels=(box[2]-box[0])*((box[3]-box[1])//2),
                    bottom_pixels=(box[2]-box[0])*((box[3]-box[1])-((box[3]-box[1])//2))))
    macro='''onerror {quit -code 1 -force}
vlib work
vmap work work
vlog -sv person_roi_stream.v person_feature_compare.v tb_person_roi.v
vsim -onfinish stop -voptargs=+acc work.tb_person_roi
log /tb_person_roi/feature /tb_person_roi/feature_valid /tb_person_roi/track_id /tb_person_roi/frame_id /tb_person_roi/color_similar /tb_person_roi/previous_valid
run -all
quit -code 0 -force
'''
    (work/'run.do').write_text(macro,encoding='ascii')
    simulator=os.environ.get('MODELSIM_VSIM') or shutil.which('vsim.exe') or r'C:\modeltech64_2020.4\win64\vsim.exe'
    result=subprocess.run([simulator,'-c','-do','run.do'],cwd=work,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=max(120,len(expected)*3))
    (folder/'rtl_console.txt').write_bytes(result.stdout)
    for name in ('regions.txt','features.csv','transcript','vsim.wlf'):
        if(work/name).exists():shutil.copy2(work/name,folder/name)
    if result.returncode or b'PERSON_RTL_PASS' not in result.stdout:raise RuntimeError(f'RTL failed: {folder}')
    rows=list(csv.DictReader((folder/'features.csv').open()))
    assert len(rows)==len(expected),(len(rows),len(expected))
    history={}
    for row,e in zip(rows,expected):
        previous=history.get(e['track_id'])
        e['previous_available']=int(previous is not None)
        current=e['feature']
        e['color_similar']=int(e['valid'] and previous is not None and previous>>16==current>>16
            and abs(((previous>>8)&255)-((current>>8)&255))<=35 and abs((previous&255)-(current&255))<=35)
        actual={k:int(row[k],16 if k=='feature' else 10) for k in e}
        if actual!=e:raise AssertionError((actual,e))
        if e['valid']:history[e['track_id']]=current
    (folder/'rtl_directory.txt').write_text(str(work))
    return dict(status='PASS',checked_regions=len(rows),frame_pixels=307200)

def report(folder,records,summary):
    gallery=''.join(f'<figure><img loading="lazy" src="annotated/{r["frame"]:06}.png"><figcaption>Frame {r["frame"]}: '+
        ', '.join(f'ID {d["track_id"]} ({d["confidence"]:.2f})' for d in r['detections'])+'</figcaption></figure>' for r in records)
    (folder/'report.html').write_text('<!doctype html><meta charset="utf-8"><title>人物偵測與追蹤</title><style>body{font:16px sans-serif;margin:30px;background:#eef2f6}section{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}figure{margin:0;background:white;padding:8px}img{width:100%}pre{white-space:pre-wrap}</style><h1>640×480 人物偵測與追蹤</h1><p>YOLOX 人物框 + 短期追蹤 ID；人物框上下半部分色彩由 ModelSim 計算。框內仍可能含背景；ID 不是身分辨識。</p><pre>'+html.escape(json.dumps(summary,ensure_ascii=False,indent=2))+'</pre><section>'+gallery+'</section>',encoding='utf-8')

def process(frames,detector,folder,source):
    folder.mkdir(parents=True);(folder/'frames').mkdir();(folder/'annotated').mkdir()
    tracker=Tracker();records=[];start=time.perf_counter()
    for idx,frame in enumerate(frames):
        if frame.shape!=(480,640,3):raise ValueError('Native frame must be 640x480')
        detections=tracker.update(detector.detect(frame));vis=frame.copy();clean=[]
        for d in detections:
            x0,y0,x1,y1=d['box'];color=((d['track_id']*83)%200+55,230,60)
            cv2.rectangle(vis,(x0,y0),(x1,y1),color,2)
            cv2.line(vis,(x0,(y0+y1)//2),(x1,(y0+y1)//2),color,1)
            cv2.putText(vis,f'ID {d["track_id"]} {d["confidence"]:.2f}',(x0,max(18,y0-5)),cv2.FONT_HERSHEY_SIMPLEX,.55,color,2)
            clean.append({k:v for k,v in d.items() if k!='hist'})
        save_image(folder/'frames'/f'{idx:06}.png',frame);save_image(folder/'annotated'/f'{idx:06}.png',vis)
        records.append(dict(frame=idx,detections=clean))
        if(idx+1)%10==0:print(f'{source}: detected/tracked {idx+1}/{len(frames)}',flush=True)
    (folder/'detections.json').write_text(json.dumps(records,indent=2))
    summary=dict(source=source,frames=len(frames),frames_with_person=sum(bool(r['detections']) for r in records),
        detection_count=sum(len(r['detections']) for r in records),track_ids=sorted({d['track_id'] for r in records for d in r['detections']}),
        detection_seconds=round(time.perf_counter()-start,2),resolution=[640,480],
        model_sha256=detector.model_sha256,confidence_threshold=.3,association='motion + HSV histogram + IoU')
    summary['rtl']=run_rtl(folder,frames,records)
    (folder/'summary.json').write_text(json.dumps(summary,indent=2))
    report(folder,records,summary);print(json.dumps(summary),flush=True)
    return records,summary

def capture(count,camera):
    cap=cv2.VideoCapture(camera,cv2.CAP_DSHOW)
    if not cap.isOpened():raise RuntimeError('USB camera not available')
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,640);cap.set(cv2.CAP_PROP_FRAME_HEIGHT,480)
    frames=[];times=[];start=time.perf_counter()
    try:
        # Discard startup exposure frames, then save every delivered frame.
        for _ in range(10):cap.read()
        for _ in range(count):
            ok,image=cap.read()
            if not ok or image.shape!=(480,640,3):raise RuntimeError('Camera must deliver native 640x480')
            frames.append(image);times.append(time.perf_counter()-start)
    finally:cap.release()
    return frames,times

def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['web','camera','replay'],required=True)
    p.add_argument('--frames',type=int,default=45);p.add_argument('--camera',type=int,default=0)
    p.add_argument('--input-dir',type=Path)
    args=p.parse_args();detector=Detector();root=ROOT/'runs'/time.strftime('%Y%m%d_%H%M%S');root.mkdir(parents=True)
    if not 2<=args.frames<=600:p.error('--frames must be between 2 and 600')
    if args.mode=='camera':
        frames,times=capture(args.frames,args.camera)
        (root/'capture.json').write_text(json.dumps(dict(camera=args.camera,timestamps=times,native_size=[640,480])))
        process(frames,detector,root/'camera','USB camera live capture')
    elif args.mode=='replay':
        if args.input_dir is None:p.error('--input-dir is required for replay')
        paths=sorted(args.input_dir.glob('*.png'))[:args.frames]
        if not paths:raise RuntimeError('No replay PNG frames')
        frames=[read_image(path) for path in paths]
        (root/'replay.json').write_text(json.dumps(dict(source=str(args.input_dir),files=[str(x) for x in paths]),indent=2))
        process(frames,detector,root/'replay','previous USB capture replay')
    else:
        for name in ['bus','zidane']:
            original=fit(read_image(ROOT/'assets'/f'{name}.jpg'));frames=[]
            for dx in [0,4,8,12,16,12,8,4,0]:
                frame=cv2.warpAffine(original,np.float32([[1,0,dx],[0,1,0]]),(640,480))
                frames.append(frame)
            process(frames,detector,root/name,'web photo translated sequence: '+name)
        process([np.zeros((480,640,3),np.uint8),np.full((480,640,3),255,np.uint8)],detector,root/'empty','empty black/white negative controls')
    print('RUN_FOLDER='+str(root),flush=True)

if __name__=='__main__':main()
