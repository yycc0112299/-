# Simplified MCDPT Verilog Testbench Prototype

This folder is a smaller Verilog implementation based on the uploaded NTUT MCDPT GitHub project:

`https://github.com/ChienHsuan/MCDPT`

The original project uses OpenVINO to detect people, extract a person re-identification embedding, and compare tracks across cameras with cosine distance. This Verilog prototype only reaches the testbench stage. It keeps the re-ID feature matching idea but removes neural-network inference, MQTT, Hungarian assignment, VGA output, FPGA constraints, and multi-person tracking.

## Mapping To MCDPT

| MCDPT idea | Python location | Verilog simplification |
| --- | --- | --- |
| Re-ID feature vector | `_get_embeddings()` in `sct.py` | `mcdpt_feature_extractor.v` builds a 16-value compact RGB feature vector |
| Average feature in a track | `Track.f_avg` in `sct.py` | `mcdpt_track_average.v` keeps a running average |
| Cosine distance | `cosine_distance()` in `sct.py` | `mcdpt_feature_distance.v` uses hardware-friendly sum of absolute differences |
| Global match threshold | `global_match_thresh=0.4` in `configs/person.py` | `GLOBAL_MATCH_THRESH=190` in fixed-point integer style |
| Cross-camera merge | `_merge_all()` in `mct.py` | `mcdpt_global_matcher.v` outputs `same_person` |

## Current Stage

This project is intentionally limited to simulation:

- RTL modules are written.
- A testbench creates two small synthetic RGB images.
- Vivado simulator checks one similar-person case and one different-person case.
- The code does not yet read real camera frames or run on an FPGA board.

## How To Simulate

1. Put two 8x8 RGB images into `image_a_rgb` and `image_b_rgb`.
2. Pulse `load_image_a` and `load_image_b` for one clock.
3. Read `global_distance` and `same_person`.

For the included testbench:

```tcl
xvlog mcdpt_feature_extractor.v mcdpt_feature_distance.v mcdpt_track_average.v mcdpt_global_matcher.v mcdpt_two_image_reid_top.v tb_mcdpt_two_image_reid.v
xelab tb_mcdpt_two_image_reid
xsim tb_mcdpt_two_image_reid -runall
```

Expected result:

- Similar reddish person blocks match.
- Red/brown versus blue person blocks do not match.

## Why This Is Still A Simplification

The real MCDPT project uses a trained re-ID model to produce strong embeddings. Verilog cannot realistically reproduce that whole neural network for a short course project, so this version imitates the algorithm structure:

`image -> compact feature vector -> track average -> distance -> threshold -> same person`

## What To Tell The Professor

This version is not a finished product. It is a first Verilog testbench prototype that translates the MCDPT concept into a smaller hardware-friendly form. The next possible step would be improving the feature extractor or replacing the synthetic testbench images with memory files converted from real pictures.
