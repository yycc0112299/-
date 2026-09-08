# MCDPT Mapping For The Brightness-Only Verilog Version

## Original MCDPT Flow

The uploaded MCDPT GitHub project works roughly like this:

1. Detect a person in a camera frame.
2. Crop the person image.
3. Use a re-identification model to generate a feature vector.
4. Save the feature in a track.
5. Compare features from different cameras.
6. If the distance is small enough, treat the two detections as the same person.

## Current Verilog Flow

This version is intentionally much simpler:

1. The testbench creates two small 8x8 RGB images.
2. The feature extractor converts RGB pixels to grayscale brightness.
3. It builds a small brightness feature vector.
4. Track modules save the feature vector.
5. A distance module compares the two vectors.
6. A threshold decides `same_person`.

## Why This Version Uses Only Brightness

This is the first testbench-stage version. The purpose is not accuracy. The purpose is to show that the MCDPT-style structure can be written in Verilog:

`image -> feature vector -> distance -> threshold`

So the feature vector uses only easy brightness information:

- average brightness
- upper and lower brightness
- bright and dark pixel counts
- brightness edge count
- foreground area
- rough center position

## Difference From The Real MCDPT Project

The real MCDPT feature vector comes from a neural network. This Verilog version replaces that neural network with a simple brightness feature extractor. The real MCDPT uses cosine distance. This version uses sum of absolute differences because it is easier to explain and easier to write in Verilog.

## Verified Simulation Result

Vivado simulation checks two cases:

| Case | Expected result |
| --- | --- |
| Similar brightness blocks | `same_person = 1` |
| Very different brightness blocks | `same_person = 0` |

