# Simplified MCDPT Brightness-Only Verilog Testbench

This folder is a very small Verilog testbench prototype based on the idea of the uploaded MCDPT project:

`https://github.com/ChienHsuan/MCDPT`

The original MCDPT project uses a trained person re-identification model to turn each person image into a feature vector, then compares feature distance across cameras. This version only keeps that basic framework and makes the feature extractor much simpler.

## Current Scope

This is only a testbench-stage prototype:

- no real camera input
- no neural network
- no true person detector
- no FPGA board output
- no multi-camera communication

The current goal is just to prove the simplest flow:

`two images -> brightness features -> distance -> threshold -> same_person`

## Mapping To MCDPT

| MCDPT idea | Verilog simplification |
| --- | --- |
| Re-ID feature vector | A small brightness-only feature vector |
| Average feature in a track | `mcdpt_track_average.v` keeps a running average |
| Cosine distance | `mcdpt_feature_distance.v` uses sum of absolute differences |
| Global match threshold | `GLOBAL_MATCH_THRESH` decides same or different person |
| Cross-camera match | `mcdpt_global_matcher.v` outputs `same_person` |

## Brightness Features

`mcdpt_feature_extractor.v` converts each RGB pixel to grayscale:

`gray = (R + G + B) / 3`

Then it extracts only simple brightness-related features:

- average foreground brightness
- upper-half average brightness
- lower-half average brightness
- bright pixel count
- dark pixel count
- brightness edge count
- foreground area
- foreground center x/y position

The rest of the 16-value feature vector is left as zero.

## How To Simulate

```tcl
xvlog mcdpt_feature_extractor.v mcdpt_feature_distance.v mcdpt_track_average.v mcdpt_global_matcher.v mcdpt_two_image_reid_top.v tb_mcdpt_two_image_reid.v
xelab tb_mcdpt_two_image_reid
xsim tb_mcdpt_two_image_reid -runall
```

Expected result:

- Similar brightness blocks match.
- Very different brightness blocks do not match.

