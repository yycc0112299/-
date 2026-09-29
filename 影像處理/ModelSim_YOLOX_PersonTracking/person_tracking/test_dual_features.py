import unittest
import numpy as np
from dual_camera import appearance,capture_pair
from cross_camera import CrossCameraMatcher

class FeatureTests(unittest.TestCase):
    def similarity(self,a,b):
        return np.minimum(appearance(a,[0,0,640,480]),appearance(b,[0,0,640,480])).sum(axis=1).min()
    def test_white_and_black_stay_different(self):
        self.assertEqual(self.similarity(np.zeros((480,640,3),np.uint8),np.full((480,640,3),255,np.uint8)),0)
    def test_neutral_hue_noise_is_ignored(self):
        a=np.full((480,640,3),(230,240,240),np.uint8)
        b=np.full((480,640,3),(240,230,240),np.uint8)
        self.assertAlmostEqual(self.similarity(a,b),1)
    def test_upper_lower_clothing_swap_is_not_match(self):
        a=np.zeros((480,640,3),np.uint8);a[:240]=(0,0,220);a[240:]=(220,0,0)
        self.assertEqual(self.similarity(a,a[::-1].copy()),0)
    def test_duplicate_camera_index_is_rejected_before_open(self):
        with self.assertRaises(ValueError):capture_pair(0,0,2)

if __name__=='__main__':unittest.main(verbosity=2)
