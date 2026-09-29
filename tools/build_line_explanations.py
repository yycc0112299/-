from pathlib import Path
import json


FILES = [
    "visual_channel_feature_extractor_rgb.v",
    "person_reid_matcher.v",
    "two_image_person_identifier_rgb.v",
    "tb_rgb_from_mem.v",
]


EXPLANATIONS = {
    "visual_channel_feature_extractor_rgb.v": [
        (1, 9, "Define the RGB feature extractor and its image size, pixel width, foreground threshold, color-edge threshold, and minimum object area."),
        (10, 20, "Declare one flattened RGB image input and the extracted feature outputs: upper/lower color, rod brightness, area, center, edge count, and present flag."),
        (23, 44, "Declare loop indices and temporary pixel values. These registers hold RGB channels, visual-channel values, color differences, and foreground/cone decisions."),
        (46, 57, "Declare accumulators and counters. The circuit scans the image, sums feature values, then divides by the counters to obtain compact descriptors."),
        (59, 75, "Implement max3 and min3. These functions find the largest and smallest RGB channel for the Visual Channel Model."),
        (77, 86, "Implement mid3. It calculates the middle RGB channel using a widened sum so the arithmetic does not overflow."),
        (88, 94, "Implement abs_diff. This gives absolute pixel or channel difference without signed arithmetic."),
        (96, 124, "Implement get_r/get_g/get_b helper functions. They read a neighbor pixel from the flattened RGB image."),
        (126, 138, "Start combinational logic and clear all sums and counters before scanning the image."),
        (140, 153, "Scan all 64 pixels. Each pixel is split into R/G/B, then converted into max, mid, min, grayscale, saturation difference, foreground, and cone/rod state."),
        (155, 173, "For foreground pixels, update object area and center sums. Cone pixels contribute upper/lower color features. Rod pixels contribute grayscale brightness."),
        (175, 197, "Compare the current pixel with the right and lower neighbors. The circuit uses RGB channel differences to find strong local color changes."),
        (199, 202, "If either neighbor difference exceeds the color-edge threshold, count this pixel as an edge or object-boundary point."),
        (207, 216, "Convert accumulated sums into final compact features and set person_present when enough foreground pixels exist."),
        (217, 219, "Close the combinational block and module."),
    ],
    "person_reid_matcher.v": [
        (1, 4, "Define the matcher module and the score threshold. A smaller score means two extracted feature vectors are more similar."),
        (5, 22, "Receive the full feature vector from image A and image B: body color, rod brightness, object area, center position, and edge count."),
        (24, 28, "Expose similarity_score and same_person. These are the final comparison outputs from this module."),
        (30, 56, "Define absolute-difference helpers for 8-bit, 7-bit, and 4-bit features so each feature can be compared safely."),
        (58, 66, "Calculate each feature distance separately. This keeps the result explainable and matches the paper idea of combining color, location, and area terms."),
        (68, 72, "Build the weighted score. Color features receive higher weight, while area, center, rod brightness, and edge count provide extra evidence."),
        (74, 76, "Compare the score with the threshold and close the module."),
    ],
    "two_image_person_identifier_rgb.v": [
        (1, 7, "Define the top-level RGB two-image identifier with image size, pixel width, score width, and threshold parameters."),
        (8, 14, "Receive two flattened RGB images and expose score, person-present flags, and the final same_person output."),
        (16, 35, "Declare internal wires for all features extracted from image A and image B."),
        (36, 53, "Instantiate the first visual-channel feature extractor for image A."),
        (55, 72, "Instantiate the second visual-channel feature extractor for image B."),
        (74, 98, "Instantiate the re-identification matcher and connect both images' feature vectors into it."),
        (100, 101, "Accept the match only when both images contain an object and the feature score passes the threshold."),
    ],
    "tb_rgb_from_mem.v": [
        (1, 10, "Define the simulation testbench and the 8x8 RGB image parameters."),
        (12, 20, "Declare memory arrays, flattened image buses, and wires for the outputs produced by the top module."),
        (22, 36, "Instantiate the RGB top module as the design under test."),
        (38, 41, "Read image_a_rgb.mem and image_b_rgb.mem. Each line in the file is one 24-bit RGB pixel."),
        (43, 50, "Pack the 64 RGB pixels into the flattened image buses expected by the top module."),
        (52, 59, "Wait for combinational logic to settle and print score, object-present flags, and same_person."),
        (61, 69, "Print a plain-language result and end the simulation."),
    ],
}


def main():
    base = Path("verilog_demo")
    screenshots = base / "screenshots"
    records = []
    for file_name in FILES:
        lines = (base / file_name).read_text(encoding="utf-8").splitlines()
        shots = sorted(screenshots.glob(f"{Path(file_name).stem}_*.png"))
        covered_end = 0
        for shot in shots:
            part = shot.stem.split("_")[-1]
            start_s, end_s = part.split("-")
            start, end = int(start_s), int(end_s)
            covered_end = max(covered_end, end)
            notes = [
                text for a, b, text in EXPLANATIONS[file_name]
                if not (b < start or a > end)
            ]
            records.append({
                "file": file_name,
                "start": start,
                "end": end,
                "line_count": len(lines),
                "image": str(shot.resolve()),
                "notes": notes,
                "code": "\n".join(f"{i:03d}: {lines[i-1]}" for i in range(start, end + 1)),
            })
        if covered_end < len(lines):
            raise RuntimeError(f"{file_name} is not fully covered by screenshots")

    Path("build/reid_deck/line_explanations.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
