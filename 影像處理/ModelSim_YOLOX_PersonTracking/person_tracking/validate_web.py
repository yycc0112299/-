"""Repeated detection/tracking validation against manually marked visible people."""
import json,time
import pipeline as p
import numpy as np

# Approximate hand-marked boxes on the 640x480 letterboxed images.
# The heavily cropped person at the left bus-image edge is measured separately.
LABELS={
 'bus':[[20,175,104,407],[98,177,159,383],[297,186,360,389]],
 'zidane':[[67,99,508,359],[372,20,579,359]]
}

def evaluate(records,labels,shifts):
    last={};misses=[];switches=[];matches=0;ious=[];edge_hits=0
    for record,dx in zip(records,shifts):
        used=set()
        for identity,box in enumerate(labels):
            target=[box[0]+dx,box[1],box[2]+dx,box[3]]
            options=[(p.iou(target,d['box']),j,d) for j,d in enumerate(record['detections']) if j not in used]
            if not options or max(x[0] for x in options)<.5:
                misses.append([record['frame'],identity]);continue
            overlap,j,d=max(options,key=lambda x:x[0]);used.add(j);matches+=1;ious.append(overlap)
            if identity in last and last[identity]!=d['track_id']:switches.append([record['frame'],identity,last[identity],d['track_id']])
            last[identity]=d['track_id']
        if len(labels)==3:
            edge_hits+=int(any(p.iou([dx,249,28+dx,389],d['box'])>.4 for d in record['detections']))
    return dict(expected=len(records)*len(labels),matches=matches,misses=misses,id_switches=switches,
        minimum_matched_iou=round(min(ious),3) if ious else None,partial_edge_person_frames=edge_hits,
        status='PASS' if not misses and not switches else 'FAIL')

if __name__=='__main__':
    detector=p.Detector();root=p.ROOT/'runs'/('web_validation_'+time.strftime('%Y%m%d_%H%M%S'));root.mkdir(parents=True)
    summaries=[]
    for brightness in [1.0,.8,1.1]:
        for name,labels in LABELS.items():
            original=p.fit(p.read_image(p.ROOT/'assets'/f'{name}.jpg'))
            original=np.clip(original.astype(float)*brightness,0,255).astype(np.uint8)
            shifts=[0,4,8,12,8,4,0]
            frames=[p.cv2.warpAffine(original,np.float32([[1,0,dx],[0,1,0]]),(640,480)) for dx in shifts]
            folder=root/f'{name}_{brightness}'
            records,summary=p.process(frames,detector,folder,f'web {name}, brightness {brightness}')
            summary['detection_tracking_validation']=evaluate(records,labels,shifts)
            (folder/'summary.json').write_text(json.dumps(summary,indent=2));p.report(folder,records,summary)
            summaries.append(summary);print(json.dumps(summary['detection_tracking_validation']),flush=True)
    negatives=[np.zeros((480,640,3),np.uint8),np.full((480,640,3),255,np.uint8),p.fit(p.read_image(p.ROOT/'assets'/'fruits.jpg'))]
    records,summary=p.process(negatives,detector,root/'negative','black, white, real fruit photo negatives')
    summary['negative_validation']='PASS' if summary['detection_count']==0 else 'FAIL';summaries.append(summary)
    (root/'validation.json').write_text(json.dumps(summaries,indent=2))
    print('WEB_VALIDATION_FOLDER='+str(root),flush=True)
    if any(s.get('detection_tracking_validation',{}).get('status')=='FAIL' for s in summaries) or summary['negative_validation']!='PASS':raise SystemExit(1)
