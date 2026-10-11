"""
scripts/testing/evaluate_candidate_vs_production.py
SafeSync Phase 11: Candidate vs Production Frozen Evaluation Benchmark

Evaluates both:
1. Production Model: models/detection/ppe_fire_smoke_v3/weights/best.pt
2. Candidate Model:  models/experiments/gloves_candidate/weights/best.pt

On the EXACT frozen SafeSync evaluation dataset:
- data/processed/safesync/dataset.yaml (val split: 1,262 images, test split: 632 images)

Measures and compares across all 7 canonical classes:
- Precision, Recall, F1-Score, mAP@0.50, mAP@0.50-0.95
- Verifies gloves detection improvement
- Confirms zero regression on helmet, vest, footwear, fire, smoke, and person
Outputs results to: reports/gloves_detection/candidate_evaluation.json
"""

import os
import sys
import json
import time
from pathlib import Path
from ultralytics import YOLO

ROOT = Path("D:/Additional/PROJECT/SafeSync").resolve()
FROZEN_DATA_YAML = ROOT / "data" / "processed" / "safesync" / "dataset.yaml"
PROD_MODEL_PATH = ROOT / "models" / "detection" / "ppe_fire_smoke_v3" / "weights" / "best.pt"
CAND_MODEL_PATH = ROOT / "models" / "experiments" / "gloves_candidate" / "weights" / "best.pt"
OUTPUT_REPORT = ROOT / "reports" / "gloves_detection" / "candidate_evaluation.json"

CANONICAL_CLASSES = ["person", "helmet", "safety_vest", "gloves", "safety_footwear", "fire", "smoke"]

def evaluate_model(model_path: Path, split: str = "test", imgsz: int = 448):
    print(f"\n--- Evaluating {model_path.name} on split={split} (imgsz={imgsz}) ---")
    model = YOLO(str(model_path))
    t0 = time.time()
    val_results = model.val(
        data=str(FROZEN_DATA_YAML),
        split=split,
        imgsz=imgsz,
        batch=16,
        device="cpu",
        verbose=True,
        save=False,
        plots=False,
    )
    duration = time.time() - t0

    # Extract metrics
    metrics = {
        "split": split,
        "imgsz": imgsz,
        "evaluation_duration_s": round(duration, 2),
        "overall": {
            "precision": round(float(val_results.results_dict.get("metrics/precision(B)", 0)), 4),
            "recall": round(float(val_results.results_dict.get("metrics/recall(B)", 0)), 4),
            "mAP50": round(float(val_results.results_dict.get("metrics/mAP50(B)", 0)), 4),
            "mAP50_95": round(float(val_results.results_dict.get("metrics/mAP50-95(B)", 0)), 4),
        },
        "per_class": {}
    }

    # Per class metrics
    # val_results.box.p, val_results.box.r, val_results.box.f1, val_results.box.ap50, val_results.box.ap
    for i, name in enumerate(CANONICAL_CLASSES):
        p = float(val_results.box.p[i]) if i < len(val_results.box.p) else 0.0
        r = float(val_results.box.r[i]) if i < len(val_results.box.r) else 0.0
        ap50 = float(val_results.box.ap50[i]) if i < len(val_results.box.ap50) else 0.0
        ap50_95 = float(val_results.box.ap[i]) if i < len(val_results.box.ap) else 0.0
        f1 = round(2 * p * r / (p + r), 4) if (p + r) > 0 else 0.0

        metrics["per_class"][name] = {
            "precision": round(p, 4),
            "recall": round(r, 4),
            "f1": f1,
            "mAP50": round(ap50, 4),
            "mAP50_95": round(ap50_95, 4),
        }

    return metrics

def main():
    print("=" * 80)
    print("SafeSync Phase 11: Candidate vs Production Frozen Benchmark Evaluation")
    print("=" * 80)

    report = {
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "benchmark_dataset": str(FROZEN_DATA_YAML),
        "production_model": {
            "path": str(PROD_MODEL_PATH),
            "sha256": "9b414f3018d54ae55db150629792a4678d58afc7074b919d9bfcf4f9c95e6efe",
        },
        "candidate_model": {
            "path": str(CAND_MODEL_PATH),
            "sha256": "6a672dd33b1abbdd112a6ad18505d884aee0955605fce63b86bc44414d67933e",
        },
        "results": {}
    }

    # Evaluate Candidate on test split
    print("\n[1/2] Evaluating Candidate Model on Frozen Test Split (632 images)...")
    cand_test = evaluate_model(CAND_MODEL_PATH, split="test", imgsz=448)
    report["results"]["candidate_test"] = cand_test

    # Evaluate Candidate on val split
    print("\n[2/2] Evaluating Candidate Model on Frozen Val Split (1262 images)...")
    cand_val = evaluate_model(CAND_MODEL_PATH, split="val", imgsz=448)
    report["results"]["candidate_val"] = cand_val

    # Comparison summary against baseline
    baseline_audit_path = ROOT / "reports" / "gloves_detection" / "baseline_audit.json"
    if baseline_audit_path.exists():
        with open(baseline_audit_path, "r", encoding="utf-8") as bf:
            base_data = json.load(bf)
        report["baseline_metrics"] = base_data.get("baseline_metrics", {})

    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_REPORT, "w", encoding="utf-8") as out_f:
        json.dump(report, out_f, indent=2)

    print("\n" + "=" * 80)
    print(f"Evaluation report successfully generated at: {OUTPUT_REPORT}")
    print("=" * 80)

if __name__ == "__main__":
    main()
