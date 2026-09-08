# Brightness-Only Verilog Testbench

This is a small testbench-stage Verilog prototype inspired by the MCDPT project idea:

`image -> feature -> distance -> threshold`

The code does not implement a full MCDPT system. It only shows how two small RGB images can be converted into brightness features and compared in simulation.

## Current Scope

- RGB input is still used because normal image pixels are RGB.
- The comparison uses brightness only.
- There is no video timing.
- There is no average feature memory.
- There is no top display module.
- There is no FPGA board output.

## Main Files

| File | Purpose |
| --- | --- |
| `brightness_feature_extractor.v` | Converts RGB pixels to brightness and builds a feature vector |
| `feature_distance.v` | Adds up absolute differences between two feature vectors |
| `brightness_matcher.v` | Compares the distance with a threshold |
| `tb_brightness_matcher.v` | Creates two test cases and checks the result |

## Brightness Formula

The extractor uses the weighted luminance formula:

`Y = 0.299R + 0.587G + 0.114B`

In Verilog, it becomes:

`gray = (77R + 150G + 29B) >> 8`

The weights are scaled by 256 so Verilog can use integers and a right shift instead of floating point numbers.

## Extracted Features

The feature vector keeps only simple brightness information:

- average foreground brightness
- bright pixel count
- dark pixel count
- brightness edge count
- foreground area
- foreground center x position
- foreground center y position

## How To Simulate

```tcl
xvlog brightness_feature_extractor.v feature_distance.v brightness_matcher.v tb_brightness_matcher.v
xelab tb_brightness_matcher
xsim tb_brightness_matcher -runall
```

Expected result:

- Similar brightness blocks match.
- Very different brightness blocks do not match.

