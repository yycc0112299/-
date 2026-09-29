"""Two independent local trackers + cross-camera candidate associations."""
import argparse,csv,json,time
from pathlib import Path
import pipeline as p
from cross_camera import CrossCameraMatcher
import numpy as np

def appearance(frame,box):
    x0,y0,x1,y1=box
    # Central 60% reduces background at box edges. Neutral colors have no reliable hue.
    margin=(x1-x0)//5
    roi=frame[y0:y1,x0+margin:x1-margin]
    hsv=p.cv2.cvtColor(roi,p.cv2.COLOR_BGR2HSV).astype(np.int32)
    hsv[:,:,0][hsv[:,:,1]<48]=0
    codes=(hsv[:,:,0]*12//180)*16+(hsv[:,:,1]*4//256)*4+hsv[:,:,2]*4//256
    half=roi.shape[0]//2
    rows=[]
    for part in [codes[:half],codes[half:]]:
        h=np.bincount(part.ravel(),minlength=192).astype(float);rows.append(h/max(1,h.sum()))
    return np.array(rows)

def capture_pair(camera_a,camera_b,count):
    if camera_a==camera_b:raise ValueError('A and B must be different USB device indexes')
    caps=[];frames=[];timestamps=[]
    try:
        for index in [camera_a,camera_b]:
            cap=p.cv2.VideoCapture(index,p.cv2.CAP_DSHOW);caps.append(cap)
            if not cap.isOpened():raise RuntimeError(f'Camera {index} unavailable; two real cameras are required')
            cap.set(p.cv2.CAP_PROP_FRAME_WIDTH,640);cap.set(p.cv2.CAP_PROP_FRAME_HEIGHT,480)
        for _ in range(count):
            if not all([c.grab() for c in caps]):raise RuntimeError('Camera grab failed')
            pair=[];times=[]
            for cap in caps:
                ok,image=cap.retrieve();times.append(time.monotonic())
                if not ok or image.shape!=(480,640,3):raise RuntimeError('Both cameras must deliver native 640x480')
                pair.append(image)
            frames.append(pair);timestamps.append(times)
    finally:
        for cap in caps:cap.release()
    return frames,timestamps

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--mode',choices=['camera','replay'],required=True)
    parser.add_argument('--camera-a',type=int,default=0);parser.add_argument('--camera-b',type=int,default=1)
    parser.add_argument('--input-a',type=Path);parser.add_argument('--input-b',type=Path)
    parser.add_argument('--frames',type=int,default=30)
    parser.add_argument('--rtl',action='store_true',help='Additionally verify each camera ROI through ModelSim')
    args=parser.parse_args()
    if not 2<=args.frames<=300:parser.error('--frames must be between 2 and 300')
    if args.mode=='camera':frames,times=capture_pair(args.camera_a,args.camera_b,args.frames)
    else:
        if not args.input_a or not args.input_b:parser.error('Replay requires --input-a and --input-b')
        paths=[sorted(folder.glob('*.png')) for folder in [args.input_a,args.input_b]]
        if min(map(len,paths))<args.frames:raise RuntimeError('Not enough PNG frames in both sources')
        frames=[[p.read_image(paths[0][i]),p.read_image(paths[1][i])] for i in range(args.frames)]
        if any(f.shape!=(480,640,3) for pair in frames for f in pair):raise RuntimeError('Replay frames must be 640x480')
        times=None
    root=p.ROOT/'dual_runs'/time.strftime('%Y%m%d_%H%M%S');root.mkdir(parents=True)
    for name in ['a','b','annotated']:(root/name).mkdir()
    detector=p.Detector();trackers=[p.Tracker(),p.Tracker()];matcher=CrossCameraMatcher()
    records=[];roi_records=[[],[]]
    for index,pair in enumerate(frames):
        observed=[]
        for camera,frame in enumerate(pair):
            ds=trackers[camera].update(detector.detect(frame))
            for d in ds:d['appearance']=appearance(frame,d['box'])
            observed.append(ds)
            roi_records[camera].append(dict(frame=index,detections=[{k:v for k,v in d.items() if k not in ['hist','appearance']} for d in ds]))
            p.save_image(root/['a','b'][camera]/f'{index:06}.png',frame)
        # Retrieval timestamps describe host read order, not hardware exposure synchronization.
        synced=times is None or abs(times[index][0]-times[index][1])<=.15
        matches=matcher.update(*observed) if synced else matcher.update([],[])
        record=dict(frame=index,a=roi_records[0][-1]['detections'],b=roi_records[1][-1]['detections'],pairs=matches,pair_timing_ok=synced)
        records.append(record);views=[]
        for camera,frame in enumerate(pair):
            vis=frame.copy();name='AB'[camera]
            for d in observed[camera]:
                labels=[m['pair_label'] for m in matches if m['status']=='confirmed_candidate' and m[['a_id','b_id'][camera]]==d['track_id']]
                x0,y0,x1,y1=d['box'];p.cv2.rectangle(vis,(x0,y0),(x1,y1),(0,230,80),2)
                p.cv2.putText(vis,f'{name}:{d["track_id"]} '+(' '.join(labels) or 'unpaired'),(x0,max(18,y0-5)),p.cv2.FONT_HERSHEY_SIMPLEX,.6,(0,230,80),2)
            views.append(vis)
        p.save_image(root/'annotated'/f'{index:06}.png',np.hstack(views))
    (root/'tracks_and_pairs.json').write_text(json.dumps(records,indent=2))
    with (root/'pairs.csv').open('w',newline='') as output:
        fields=['frame','a_id','b_id','score','status','consecutive_hits','pair_label']
        writer=csv.DictWriter(output,fieldnames=fields);writer.writeheader()
        for r in records:
            for m in r['pairs']:writer.writerow(dict(frame=r['frame'],**m))
    summary=dict(mode=args.mode,frames=len(frames),resolution=[640,480],source_a=str(args.input_a) if args.mode=='replay' else args.camera_a,
        source_b=str(args.input_b) if args.mode=='replay' else args.camera_b,host_retrieval_times=times,
        confirmed_candidate_frames=sum(any(m['status']=='confirmed_candidate' for m in r['pairs']) for r in records),
        dual_camera_capture_completed=args.mode=='camera',note='Appearance candidates only; similar clothes can match. Replay is not real two-camera validation.')
    if args.rtl:
        summary['rtl']=[]
        for camera in range(2):summary['rtl'].append(p.run_rtl(root/['a','b'][camera],[f[camera] for f in frames],roi_records[camera]))
    (root/'summary.json').write_text(json.dumps(summary,indent=2))
    cards=''.join(f'<figure><img loading="lazy" src="annotated/{i:06}.png"><figcaption>Frame {i}</figcaption></figure>' for i in range(len(frames)))
    (root/'report.html').write_text('<!doctype html><meta charset="utf-8"><title>雙鏡頭候選比對</title><style>body{font:18px sans-serif;margin:25px}img{max-width:100%}</style><h1>雙鏡頭追蹤與候選配對</h1><p>A、B 各自追蹤；P 編號只表示外觀相似的跨鏡頭候選。此批模式：'+args.mode+'</p>'+cards,encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False));print('RESULT='+str(root))

if __name__=='__main__':main()
