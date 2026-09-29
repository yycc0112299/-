"""Capture both live trials first, then run detection/tracking and RTL."""
import json,time
import pipeline as p

if __name__=='__main__':
    root=p.ROOT/'runs'/('camera_validation_'+time.strftime('%Y%m%d_%H%M%S'));root.mkdir(parents=True)
    batches=[]
    for trial in range(2):
        frames,times=p.capture(120,0);batches.append(frames)
        (root/f'capture_{trial+1}.json').write_text(json.dumps(dict(source='live USB camera 0',timestamps=times,native_size=[640,480]),indent=2))
        print(f'CAPTURED live trial {trial+1}: {len(frames)} frames',flush=True)
    print('CAPTURE FINISHED; person may leave the camera now.',flush=True)
    detector=p.Detector();summaries=[]
    for trial,frames in enumerate(batches,1):
        records,summary=p.process(frames,detector,root/f'trial_{trial}',f'live USB camera trial {trial}')
        # Visibility and identity need visual review; these counts alone do not certify accuracy.
        summary['longest_observed_track']=max((sum(any(d['track_id']==tid for d in r['detections']) for r in records)
            for tid in summary['track_ids']),default=0)
        summary['needs_visual_review']=True
        (root/f'trial_{trial}'/'summary.json').write_text(json.dumps(summary,indent=2))
        p.report(root/f'trial_{trial}',records,summary);summaries.append(summary)
    (root/'validation.json').write_text(json.dumps(summaries,indent=2))
    print('CAMERA_VALIDATION_FOLDER='+str(root),flush=True)
