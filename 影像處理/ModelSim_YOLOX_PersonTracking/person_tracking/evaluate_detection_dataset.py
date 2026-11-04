"""Aggregate the saved labeled public-image dataset evaluation."""
import json
from pathlib import Path

ROOT = Path(__file__).parent

def run(report_path=ROOT / "verification_report.json"):
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    rows = [row for row in report["web"] if "detection_tracking_validation" in row]
    expected = sum(row["detection_tracking_validation"]["expected"] for row in rows)
    matches = sum(row["detection_tracking_validation"]["matches"] for row in rows)
    misses = sum(len(row["detection_tracking_validation"]["misses"]) for row in rows)
    switches = sum(len(row["detection_tracking_validation"]["id_switches"]) for row in rows)
    minimum_iou = min(row["detection_tracking_validation"]["minimum_matched_iou"] for row in rows)
    negatives = [row for row in report["web"] if "negative_validation" in row]
    summary = {"dataset_cases": len(rows), "annotated_person_observations": expected,
               "matched_observations": matches, "misses": misses, "id_switches": switches,
               "annotated_recall": round(matches / expected, 4), "minimum_iou": minimum_iou,
               "iou_threshold": 0.5,
               "negative_cases_pass": all(row["negative_validation"] == "PASS" for row in negatives),
               "status": "PASS" if matches == expected and not misses and not switches and minimum_iou >= 0.5 else "FAIL",
               "source_artifact": Path(report_path).name}
    output = ROOT / "dataset_evaluation.json"
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert summary["status"] == "PASS"
    assert summary["negative_cases_pass"]
    print(f"DATASET_EVALUATION_PASS cases={len(rows)} observations={expected} recall={summary['annotated_recall']:.3f} minimum_iou={minimum_iou:.3f}")
    return summary

if __name__ == "__main__":
    run()
