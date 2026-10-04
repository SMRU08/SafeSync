r"""
scripts/testing/evaluate_v3_vs_v5_master.py — SafeSync V3 vs V5 Master Evaluation Engine
======================================================================================
Performs strict, side-by-side comparative evaluation of:
  - Baseline V3: models/detection/ppe_fire_smoke_v3/weights/best.pt
  - Candidate V5: models/detection/safesync_v5_unified/weights/best.pt

Evaluates:
  1. Standard validation metrics on val split (Precision, Recall, mAP50, mAP50-95, GT counts, Pred counts).
  2. 24-scenario real-world validation suite (helmet views, colors, vests, gloves, boots, fire/smoke FPs).
  3. CPU inference latency benchmark (Mean, P50, P95, FPS).
  4. False positive and false negative analysis across negative & edge-case samples.
"""

import os
import sys
import time
import json
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
import yaml
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
V3_PATH = ROOT / "models" / "detection" / "ppe_fire_smoke_v3" / "weights" / "best.pt"
V5_PATH = ROOT / "models" / "detection" / "safesync_v5_unified" / "weights" / "best.pt"
DATA_YAML = ROOT / "data.yaml"
OUTPUT_REPORT = ROOT / "reports" / "v3_vs_v5_evaluation_report.json"

CLASS_NAMES = {
    0: "person",
    1: "helmet",
    2: "safety_vest",
    3: "gloves",
    4: "safety_footwear",
    5: "fire",
    6: "smoke",
}

OPERATING_THRESHOLDS = {
    "person": 0.22,
    "helmet": 0.30,
    "safety_vest": 0.30,
    "gloves": 0.22,
    "safety_footwear": 0.22,
    "fire": 0.20,
    "smoke": 0.20,
}


def run_val_metrics(model_path: Path, data_yaml: Path, split: str = "val", imgsz: int = 384):
    """Runs YOLO validation and returns per-class and overall metrics."""
    print(f"\n--- Running YOLO val on {model_path.name} (split={split}) ---")
    model = YOLO(str(model_path))
    val_res = model.val(
        data=str(data_yaml),
        split=split,
        imgsz=imgsz,
        device="cpu",
        verbose=False,
    )

    box = val_res.box
    names = val_res.names

    overall = {
        "precision": round(float(box.mp), 4),
        "recall": round(float(box.mr), 4),
        "mAP50": round(float(box.map50), 4),
        "mAP50_95": round(float(box.map), 4),
    }

    per_class = {}
    # Extract per-class metrics
    p_curve = box.p
    r_curve = box.r
    ap50_curve = box.ap50
    ap_curve = box.ap

    # Extract class target ground-truth counts from confusion matrix or stats
    nt_per_class = getattr(val_res, "nt_per_class", None)

    for i in range(len(names)):
        cname = names[i]
        p_val = float(p_curve[i]) if (p_curve is not None and len(p_curve) > i) else 0.0
        r_val = float(r_curve[i]) if (r_curve is not None and len(r_curve) > i) else 0.0
        ap50_val = float(ap50_curve[i]) if (ap50_curve is not None and len(ap50_curve) > i) else 0.0
        ap_val = float(ap_curve[i]) if (ap_curve is not None and len(ap_curve) > i) else 0.0
        gt_cnt = int(nt_per_class[i]) if (nt_per_class is not None and len(nt_per_class) > i) else 0

        # Estimated prediction count based on precision and recall
        pred_cnt = int(round(r_val * gt_cnt / max(1e-5, p_val))) if (p_val > 0 and gt_cnt > 0) else 0

        per_class[cname] = {
            "class_id": i,
            "precision": round(p_val, 4),
            "recall": round(r_val, 4),
            "mAP50": round(ap50_val, 4),
            "mAP50_95": round(ap_val, 4),
            "ground_truth_count": gt_cnt,
            "prediction_count": pred_cnt,
        }

    return overall, per_class


def benchmark_latency(model_path: Path, imgsz: int = 384, runs: int = 60):
    """Measures CPU inference latency over consecutive runs."""
    model = YOLO(str(model_path))
    dummy = np.zeros((imgsz, imgsz, 3), dtype=np.uint8)

    # Warmup
    for _ in range(10):
        _ = model.predict(source=dummy, imgsz=imgsz, device="cpu", verbose=False)

    latencies = []
    for _ in range(runs):
        t0 = time.perf_counter()
        _ = model.predict(source=dummy, imgsz=imgsz, device="cpu", verbose=False)
        dt = (time.perf_counter() - t0) * 1000.0
        latencies.append(dt)

    lat_arr = np.array(latencies)
    return {
        "mean_ms": round(float(np.mean(lat_arr)), 2),
        "median_p50_ms": round(float(np.median(lat_arr)), 2),
        "p95_ms": round(float(np.percentile(lat_arr, 95)), 2),
        "min_ms": round(float(np.min(lat_arr)), 2),
        "max_ms": round(float(np.max(lat_arr)), 2),
        "fps_throughput": round(1000.0 / float(np.mean(lat_arr)), 1),
    }


def evaluate_realworld_suite(model_path: Path):
    """Evaluates the 24-scenario challenge suite."""
    from scripts.testing.run_realworld_validation_suite import SCENARIOS_SPEC

    test_img_dir = ROOT / "datasets" / "processed_v3" / "images" / "test"
    test_lbl_dir = ROOT / "datasets" / "processed_v3" / "labels" / "test"

    if not test_img_dir.exists():
        return {"scenarios_tested": 0, "passed": 0, "pass_rate": 0.0, "details": []}

    all_test_imgs = sorted(list(test_img_dir.glob("*.jpg")) + list(test_img_dir.glob("*.png")))
    img_by_classes = {}
    for img_p in all_test_imgs:
        lbl_p = test_lbl_dir / f"{img_p.stem}.txt"
        classes_present = set()
        if lbl_p.exists():
            for line in lbl_p.read_text().strip().splitlines():
                if line:
                    c_id = int(line.split()[0])
                    classes_present.add(CLASS_NAMES.get(c_id, str(c_id)))
        img_by_classes[img_p] = classes_present

    model = YOLO(str(model_path))
    scenario_results = []
    passed_total = 0

    for spec in SCENARIOS_SPEC:
        s_id = spec["id"]
        group = spec["group"]
        s_name = spec["name"]
        targets = spec["target_classes"]
        forbids = spec["forbid_classes"]

        # Select candidate test images
        candidates = []
        for img_p, cls_set in img_by_classes.items():
            if targets:
                if all(t in cls_set for t in targets):
                    candidates.append(img_p)
            else:
                # Negative sample
                if not any(f in cls_set for f in forbids):
                    candidates.append(img_p)

        eval_imgs = candidates[:3] if candidates else all_test_imgs[:2]
        scenario_passed = True
        detected_classes = Counter()

        for test_img in eval_imgs:
            preds = model.predict(source=str(test_img), imgsz=384, conf=0.20, device="cpu", verbose=False)
            boxes = preds[0].boxes if preds else None
            frame_classes = set()
            if boxes is not None:
                for b in boxes:
                    cls_id = int(b.cls[0].item())
                    conf_score = float(b.conf[0].item())
                    cls_name = CLASS_NAMES.get(cls_id, f"c{cls_id}")
                    if conf_score >= OPERATING_THRESHOLDS.get(cls_name, 0.20):
                        detected_classes[cls_name] += 1
                        frame_classes.add(cls_name)

            for f_cls in forbids:
                if f_cls in frame_classes:
                    scenario_passed = False

            if targets:
                if not any(t in frame_classes for t in targets):
                    scenario_passed = False

        if scenario_passed:
            passed_total += 1

        scenario_results.append({
            "id": s_id,
            "group": group,
            "name": s_name,
            "passed": scenario_passed,
            "detected_classes": dict(detected_classes),
        })

    return {
        "total_scenarios": len(SCENARIOS_SPEC),
        "passed": passed_total,
        "pass_rate_pct": round((passed_total / len(SCENARIOS_SPEC)) * 100.0, 1),
        "scenarios": scenario_results,
    }


def main():
    print("=" * 80)
    print("SAFESYNC: V3 VS V5 MASTER EVALUATION BENCHMARK")
    print("=" * 80)
    print(f"V3 Model Path: {V3_PATH}")
    print(f"V5 Model Path: {V5_PATH}")
    print(f"Dataset YAML:  {DATA_YAML}")

    # 1. Validation metrics
    v3_overall, v3_per_class = run_val_metrics(V3_PATH, DATA_YAML, split="val")
    v5_overall, v5_per_class = run_val_metrics(V5_PATH, DATA_YAML, split="val")

    # 2. CPU Latency benchmarks
    print("\nBenchmarking CPU inference latencies ...")
    v3_latency = benchmark_latency(V3_PATH, imgsz=384, runs=60)
    v5_latency = benchmark_latency(V5_PATH, imgsz=384, runs=60)

    # 3. 24-Scenario Real-World Suite
    print("\nRunning 24-Scenario Real-World Evaluation Suite ...")
    v3_scenarios = evaluate_realworld_suite(V3_PATH)
    v5_scenarios = evaluate_realworld_suite(V5_PATH)

    master_report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "v3": {
            "name": "ppe_fire_smoke_v3",
            "weights_path": str(V3_PATH),
            "overall_metrics": v3_overall,
            "per_class_metrics": v3_per_class,
            "latency_cpu": v3_latency,
            "realworld_scenarios": v3_scenarios,
        },
        "v5": {
            "name": "safesync_v5_unified",
            "weights_path": str(V5_PATH),
            "overall_metrics": v5_overall,
            "per_class_metrics": v5_per_class,
            "latency_cpu": v5_latency,
            "realworld_scenarios": v5_scenarios,
        },
    }

    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(master_report, f, indent=2)

    print("\n" + "=" * 80)
    print(f"EVALUATION COMPLETE. Report written to {OUTPUT_REPORT}")
    print("=" * 80)


if __name__ == "__main__":
    main()
