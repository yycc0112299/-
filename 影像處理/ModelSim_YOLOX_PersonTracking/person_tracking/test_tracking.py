"""Deterministic association and full-resolution RTL boundary regression tests."""
import json, tempfile, unittest
from pathlib import Path
import pipeline as p
import numpy as np

def detection(x,color=0):
    hist=np.zeros(96);hist[color]=1
    return dict(box=[x,100,x+40,220],hist=hist,confidence=.9)

class TrackingTests(unittest.TestCase):
    def test_movement_and_reordered_detections(self):
        tracker=p.Tracker()
        first=tracker.update([detection(30,0),detection(180,1)])
        for i in range(1,12):
            ds=[detection(30+i*5,0),detection(180-i*5,1)]
            if i%2: ds.reverse()
            result=tracker.update(ds)
            self.assertEqual([d['track_id'] for d in result],[1,2])
            self.assertEqual([int(d['hist'].argmax()) for d in result],[0,1])
    def test_crossing_distinct_appearance(self):
        tracker=p.Tracker()
        for i in range(22):
            result=tracker.update([detection(20+i*8,0),detection(200-i*8,1)])
            self.assertEqual([d['track_id'] for d in result],[1,2])
            self.assertEqual([int(d['hist'].argmax()) for d in result],[0,1])
    def test_short_occlusion_keeps_id_without_ghost_detection(self):
        tracker=p.Tracker();tracker.update([detection(50)])
        tracker.update([detection(54)])
        for _ in range(3):self.assertEqual(tracker.update([]),[])
        self.assertEqual(tracker.update([detection(65)])[0]['track_id'],1)
    def test_expiration_creates_new_id(self):
        tracker=p.Tracker(max_missing=2);tracker.update([detection(50)])
        for _ in range(3):tracker.update([])
        self.assertEqual(tracker.update([detection(50)])[0]['track_id'],2)
    def test_no_reuse_for_incompatible_appearance(self):
        tracker=p.Tracker();tracker.update([detection(50,0)])
        self.assertEqual(tracker.update([detection(50,1)])[0]['track_id'],2)
    def test_empty_and_new_person(self):
        tracker=p.Tracker()
        for _ in range(12):self.assertEqual(tracker.update([]),[])
        self.assertEqual(tracker.update([detection(50)])[0]['track_id'],1)

def rtl_boundaries():
    frames=[];records=[];known=[]
    def add(frame,box,feature,nt,nb,valid=True):
        idx=len(frames);frames.append(frame)
        records.append(dict(frame=idx,detections=[dict(track_id=1,box=box)] if valid else []))
        known.append((feature,nt,nb))
    # Odd-height ROI must split 3 + 4 rows, excluding a contrasting background.
    f=np.full((480,640,3),255,np.uint8);f[13:16,17:28]=(210,80,40);f[16:20,17:28]=(40,40,190)
    add(f,[17,13,28,20],0x426464,33,44)
    # Black clothing is foreground, not removed as background.
    f=np.full((480,640,3),255,np.uint8);f[100:200,100:200]=0
    add(f,[100,100,200,200],0x006464,5000,5000)
    # Last pixel of the frame contributes to the lower-half count.
    f=np.zeros((480,640,3),np.uint8);f[478,639]=255
    add(f,[639,478,640,480],0x106464,1,1)
    # Tie chooses smaller class ID; proportions are integer percentages.
    f=np.zeros((480,640,3),np.uint8);f[0,0:5]=(40,40,190);f[0,5:10]=(210,80,40);f[1,0:10]=(40,40,190)
    add(f,[0,0,10,2],0x223264,10,10)
    # Colorful/bright data without a detected person must give invalid zero.
    add(np.full((480,640,3),255,np.uint8),[0,0,0,0],0,0,0,False)
    folder=p.ROOT/'tests'/('rtl_'+__import__('time').strftime('%Y%m%d_%H%M%S'));folder.mkdir(parents=True)
    summary=p.run_rtl(folder,frames,records)
    import csv
    rows=list(csv.DictReader((folder/'features.csv').open()))
    actual=[(int(r['feature'],16),int(r['top_pixels']),int(r['bottom_pixels'])) for r in rows]
    assert actual==known,(actual,known)
    summary['hand_calculated_cases']=len(known)
    (folder/'summary.json').write_text(json.dumps(summary,indent=2));print('RTL_BOUNDARIES_PASS',folder)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TrackingTests))
    (p.ROOT/'tests').mkdir(exist_ok=True)
    (p.ROOT/'tests'/'tracking_results.json').write_text(json.dumps(dict(
        tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),
        status='PASS' if result.wasSuccessful() else 'FAIL'),indent=2))
    if not result.wasSuccessful():raise SystemExit(1)
    rtl_boundaries()
