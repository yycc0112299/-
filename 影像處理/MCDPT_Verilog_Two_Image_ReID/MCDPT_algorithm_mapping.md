# MCDPT Algorithm Mapping For The Verilog Version

## Original MCDPT Flow

The uploaded GitHub project `ChienHsuan/MCDPT` solves multi-camera person tracking with this flow:

1. Detect people in each camera frame.
2. Crop each detected person.
3. Run a person re-identification model to produce a feature vector.
4. Keep features inside each single-camera track.
5. Send average and cluster features to other cameras.
6. Compare local and remote tracks with cosine distance.
7. If the distance is below the global threshold, treat them as the same person.

## Simplified Verilog Flow

The Verilog version keeps the same framework but replaces the neural network with a small hardware-friendly feature extractor:

1. Read two small RGB images.
2. Convert each image into a 16-value feature vector.
3. Store each feature vector as a track average.
4. Compute feature distance between the two track averages.
5. Compare the distance with `GLOBAL_MATCH_THRESH`.
6. Output `same_person`.

## Why The Feature Extractor Is Not Just Brightness

The new extractor uses several signals:

- upper-body RGB average
- lower-body RGB average
- dark and bright pixel counts
- red/green/blue dominant pixel counts
- saturation average
- edge count
- foreground area
- center position

This imitates the role of the MCDPT re-ID embedding: it turns an image into a compact identity descriptor. It is still much simpler than a neural network, but the later matching flow is intentionally close to the GitHub algorithm.

## Why Sum Of Absolute Difference Replaces Cosine Distance

MCDPT uses:

`distance = 1 - dot(normalize(feature_a), normalize(feature_b))`

That requires normalization, multiplication, and division. For a beginner Verilog prototype, the implementation uses:

`distance = sum(abs(feature_a[i] - feature_b[i]))`

This is easier to explain and easier to synthesize, while still preserving the same decision idea:

`small distance = likely same person`

`large distance = likely different person`

## Module Responsibilities

| Module | Responsibility |
| --- | --- |
| `mcdpt_feature_extractor.v` | Builds the compact 16-value RGB identity feature vector |
| `mcdpt_track_average.v` | Mimics MCDPT `Track.f_avg` with a running average |
| `mcdpt_feature_distance.v` | Computes hardware-friendly feature distance |
| `mcdpt_global_matcher.v` | Applies the global match threshold |
| `mcdpt_two_image_reid_top.v` | Connects the full two-image demo |
| `tb_mcdpt_two_image_reid.v` | Proves one similar-person case and one different-person case |

## Verified Simulation Result

Vivado 2017.2 simulation passed:

| Case | Distance | `same_person` |
| --- | ---: | ---: |
| Similar reddish person blocks | 31 | 1 |
| Red/brown versus blue person blocks | 631 | 0 |

