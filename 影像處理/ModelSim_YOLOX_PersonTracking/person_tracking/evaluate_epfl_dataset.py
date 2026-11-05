"""Run the project YOLOX detector on EPFL annotated multi-view images."""
import argparse, json, math, re, time
from pathlib import Path

import cv2

import pipeline


def iou(a, b):
    x0, y0, x1, y1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x1 - x0) * max(0, y1 - y0)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union else 0.0


def run(images, annotations, output, threshold=0.5):
    detector = pipeline.Detector()
    rows, total_gt, total_pred, matches, misses, false_positives = [], 0, 0, 0, 0, 0
    ious, position_errors, center_errors = [], [], []
    start = time.perf_counter()
    for annotation in sorted(Path(annotations).glob("det_frame*_cam*.txt")):
        match = re.fullmatch(r"det_frame(\d+)_cam(\d+)\.txt", annotation.name)
        if not match:
            continue
        frame, camera = map(int, match.groups())
        image = Path(images) / f"c{camera}" / f"{frame:08}.jpg"
        source = cv2.imread(str(image))
        if source is None:
            raise FileNotFoundError(image)
        height, width = source.shape[:2]
        scale = min(640 / width, 480 / height)
        ground_truth = []
        for line in annotation.read_text().splitlines():
            values = [float(value) for value in line.split()]
            if len(values) >= 4:
                ground_truth.append([round(values[0] * scale), round(values[1] * scale),
                                     round(values[2] * scale), round(values[3] * scale)])
        predictions = detector.detect(pipeline.fit(source))
        predicted_boxes = [row["box"] for row in predictions]
        used = set()
        local_ious, local_position_errors, local_center_errors = [], [], []
        for target in ground_truth:
            candidates = [(iou(target, box), index) for index, box in enumerate(predicted_boxes) if index not in used]
            best = max(candidates, default=(0.0, None))
            if best[0] >= threshold:
                used.add(best[1]); matches += 1; ious.append(best[0]); local_ious.append(best[0])
                error = max(abs(a - b) for a, b in zip(target, predicted_boxes[best[1]]))
                center = math.hypot((target[0] + target[2] - predicted_boxes[best[1]][0] - predicted_boxes[best[1]][2]) / 2,
                                    (target[1] + target[3] - predicted_boxes[best[1]][1] - predicted_boxes[best[1]][3]) / 2)
                position_errors.append(error); local_position_errors.append(error)
                center_errors.append(center); local_center_errors.append(center)
            else:
                misses += 1
        total_gt += len(ground_truth); total_pred += len(predicted_boxes); false_positives += len(predicted_boxes) - len(used)
        rows.append({"camera": camera, "frame": frame, "ground_truth": len(ground_truth),
                     "predictions": len(predicted_boxes), "matches": len(local_ious),
                     "misses": len(ground_truth) - len(local_ious),
                     "false_positives": len(predicted_boxes) - len(used),
                     "minimum_iou": round(min(local_ious), 4) if local_ious else None,
                     "maximum_coordinate_error_px": max(local_position_errors) if local_position_errors else None,
                     "maximum_center_error_px": round(max(local_center_errors), 4) if local_center_errors else None,
                     "ground_truth_boxes": ground_truth, "predicted_boxes": predicted_boxes})
    summary = {"dataset": "EPFL Multi-view Multi-class", "cases": len(rows),
               "ground_truth_boxes": total_gt, "predicted_boxes": total_pred, "matches": matches,
               "misses": misses, "false_positives": false_positives,
               "recall": round(matches / total_gt, 4) if total_gt else 0,
               "precision": round(matches / total_pred, 4) if total_pred else 0,
               "minimum_iou": round(min(ious), 4) if ious else None,
               "mean_iou": round(sum(ious) / len(ious), 4) if ious else None,
               "maximum_coordinate_error_px": max(position_errors) if position_errors else None,
               "mean_coordinate_error_px": round(sum(position_errors) / len(position_errors), 4) if position_errors else None,
               "coordinate_error_threshold_px": 20,
               "coordinate_error_pass": all(error < 20 for error in position_errors),
               "maximum_center_error_px": round(max(center_errors), 4) if center_errors else None,
               "mean_center_error_px": round(sum(center_errors) / len(center_errors), 4) if center_errors else None,
               "center_error_threshold_px": 20,
               "center_error_pass": all(error < 20 for error in center_errors),
               "iou_threshold": threshold, "seconds": round(time.perf_counter() - start, 2),
               "status": "PASS" if misses == 0 else "PARTIAL", "cases_detail": rows}
    Path(output).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"EPFL_DATASET_{summary['status']} cases={len(rows)} gt={total_gt} matches={matches} recall={summary['recall']:.3f} minimum_iou={summary['minimum_iou']}")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", required=True)
    parser.add_argument("--annotations", required=True)
    parser.add_argument("--output", default="epfl_dataset_evaluation.json")
    args = parser.parse_args()
    run(args.images, args.annotations, args.output)
