import unittest
import numpy as np
from cross_camera import CrossCameraMatcher

def person(tid,color,status='confirmed'):
    appearance=np.zeros((2,192));appearance[:,color]=1
    return dict(track_id=tid,status=status,appearance=appearance)

class CrossCameraTests(unittest.TestCase):
    def test_same_appearance_requires_repeated_evidence(self):
        m=CrossCameraMatcher()
        for i in range(3):
            r=m.update([person(4,1)],[person(9,1)])[0]
            self.assertEqual(r['status'],'confirmed_candidate' if i==2 else 'candidate')
        self.assertEqual(r['pair_label'],'P1')
    def test_different_people_do_not_match(self):
        self.assertEqual(CrossCameraMatcher().update([person(1,0)],[person(1,1)])[0]['status'],'unmatched')
    def test_similar_competitors_are_ambiguous(self):
        r=CrossCameraMatcher().update([person(1,0)],[person(1,0),person(2,0)])
        self.assertEqual(r[0]['status'],'ambiguous')
    def test_one_to_one_with_reversed_order(self):
        m=CrossCameraMatcher(min_hits=1)
        r=m.update([person(1,0),person(2,1)],[person(1,1),person(2,0)])
        self.assertEqual([(x['a_id'],x['b_id']) for x in r],[(1,2),(2,1)])
    def test_missing_camera_breaks_confirmation(self):
        m=CrossCameraMatcher(min_hits=2)
        m.update([person(1,0)],[person(2,0)]);m.update([],[])
        self.assertEqual(m.update([person(1,0)],[person(2,0)])[0]['status'],'candidate')
    def test_tentative_tracks_cannot_pair(self):
        self.assertEqual(CrossCameraMatcher().update([person(1,0,'tentative')],[person(1,0)]),[])

if __name__=='__main__':unittest.main(verbosity=2)
