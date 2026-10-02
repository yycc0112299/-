import unittest
import numpy as np
from dual_camera import appearance,capture_pair
from cross_camera import appearance_similarity

class FeatureTests(unittest.TestCase):
    def similarity(self,a,b):
        return appearance_similarity(appearance(a,[0,0,640,480]),appearance(b,[0,0,640,480]))
    def test_white_and_black_stay_different(self):
        self.assertEqual(self.similarity(np.zeros((480,640,3),np.uint8),np.full((480,640,3),255,np.uint8)),0)
    def test_neutral_hue_noise_is_ignored(self):
        a=np.full((480,640,3),(230,240,240),np.uint8)
        b=np.full((480,640,3),(240,230,240),np.uint8)
        self.assertAlmostEqual(self.similarity(a,b),1)
    def test_upper_lower_clothing_swap_is_not_match(self):
        a=np.zeros((480,640,3),np.uint8);a[:240]=(0,0,220);a[240:]=(220,0,0)
        self.assertLess(self.similarity(a,a[::-1].copy()),.3)
    def test_dark_clothing_survives_exposure_shift(self):
        a=np.full((480,640,3),35,np.uint8)
        b=np.full((480,640,3),75,np.uint8)
        self.assertGreater(self.similarity(a,b),.72)
    def test_visible_upper_body_can_match_full_body(self):
        upper_only=np.full((480,640,3),35,np.uint8)
        full_body=upper_only.copy();full_body[240:]=(220,0,0)
        self.assertGreater(self.similarity(upper_only,full_body),.72)
    def test_duplicate_camera_index_is_rejected_before_open(self):
        with self.assertRaises(ValueError):capture_pair(0,0,2)

if __name__=='__main__':unittest.main(verbosity=2)
