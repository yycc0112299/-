"""Evaluate same-person cross-camera decisions against labeled cases."""
import json
from pathlib import Path

import numpy as np

from cross_camera import CrossCameraMatcher


ROOT = Path(__file__).parent


def person(track_id, color):
    appearance = np.zeros((2, 15), dtype=float)
    appearance[:, color] = 1.0
    return {"track_id": track_id, "status": "confirmed", "appearance": appearance}


def box_error(a, b):
    return max(abs(x - y) for x, y in zip(a, b))


def evaluate_case(case):
    a = [person(case["a_id"], case["a_color"])]
    b = [person(track_id, color) for track_id, color in zip(case["b_ids"], case["b_colors"])]
    matcher = CrossCameraMatcher(min_hits=3)
    final = []
    for _ in range(3):
        final = matcher.update(a, b)
    predicted_same = any(row["status"] == "confirmed_candidate" for row in final)
    expected = case["same_person"]
    result = {"name": case["name"], "expected_same_person": expected,
              "predicted_same_person": predicted_same, "final": final}
    if expected and predicted_same:
        result["classification"] = "TP"
    elif not expected and not predicted_same:
        result["classification"] = "TN"
    elif predicted_same:
        result["classification"] = "FP"
    else:
        result["classification"] = "FN"
    if "a_box" in case:
        result["max_box_coordinate_error_px"] = box_error(case["a_box"], case["b_box"])
    return result


def run(dataset_path=ROOT / "matching_dataset.json"):
    dataset = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    results = [evaluate_case(case) for case in dataset["cases"]]
    counts = {label: sum(r["classification"] == label for r in results) for label in ("TP", "TN", "FP", "FN")}
    total = len(results)
    accuracy = (counts["TP"] + counts["TN"]) / total if total else 0.0
    precision = counts["TP"] / (counts["TP"] + counts["FP"]) if counts["TP"] + counts["FP"] else 0.0
    recall = counts["TP"] / (counts["TP"] + counts["FN"]) if counts["TP"] + counts["FN"] else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    errors = [r["max_box_coordinate_error_px"] for r in results if "max_box_coordinate_error_px" in r]
    summary = {"cases": total, **counts, "accuracy": round(accuracy, 4),
               "precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4),
               "position_error_threshold_px": 20,
               "max_box_coordinate_error_px": max(errors) if errors else None,
               "position_error_pass": all(error < 20 for error in errors), "results": results}
    output = ROOT / "matching_dataset_evaluation.json"
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert counts["FP"] == counts["FN"] == 0
    assert summary["position_error_pass"]
    print(f"MATCHING_DATASET_PASS cases={total} accuracy={accuracy:.3f} f1={f1:.3f} output={output.name}")
    return summary


if __name__ == "__main__":
    run()
