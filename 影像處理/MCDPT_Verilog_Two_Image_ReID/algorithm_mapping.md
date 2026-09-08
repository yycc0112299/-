# Algorithm Mapping

## Original Reference Idea

The reference MCDPT project uses this broad structure:

1. Detect a person.
2. Convert the person image into a feature vector.
3. Compare feature vectors.
4. Use a threshold to decide whether the target is the same person.

## Current Simplified Verilog Idea

This version keeps only the smallest testbench-friendly part:

1. The testbench creates two 8x8 RGB images.
2. `brightness_feature_extractor.v` converts RGB pixels into brightness.
3. It builds a simple brightness feature vector.
4. `feature_distance.v` compares both feature vectors.
5. `brightness_matcher.v` checks whether the distance is below the threshold.

## Why Average Was Removed

Average feature memory is useful for video because the same person appears across many frames. This version only compares two still images, so there is no time sequence to average. Removing the average block makes the first testbench easier to explain.

## Why The Top Wrapper Was Removed

The previous top module only connected submodules together. Since the current goal is to show testbench-level code, the testbench now connects the extractor and matcher directly. This removes one extra layer that did not add new behavior.

## Current Limitation

This is not a complete recognition system. It is a small simulation that proves a basic idea:

`RGB pixels -> brightness features -> distance -> match result`

