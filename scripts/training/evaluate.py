"""
evaluate.py — RAKSHYA VISION Phase 3
Evaluates the trained model on both val and test splits.
Records Precision, Recall, mAP50, mAP50-95 per class.
Generates visual predictions in validation_samples/.
Exports confidence_analysis.csv across thresholds.
"""

import os
import sys
import json
import csv
import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXPERIMENT = "ppe_fire_smoke_v1"
MODEL_DIR = os.path.join(ROOT, "models", "detection", EXPERIMENT)
DATA_YAML = os.path.join(ROOT, "datasets", "processed", "data.yaml")
CLASS_NAMES = ["person", "helmet", "safety_vest", "gloves",
               "safety_footwear", "fire", "smoke"]
CONFIDENCE_THRESHOLDS = [0.25, 0.35, 0.50, 0.60, 0.70]


def find_best_pt():
    candidates = [
        os.path.join(MODEL_DIR, "weights", "best.pt"),
        os.path.join(ROOT, "models", "detection", EXPERIMENT, "weights", "best.pt"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    raise FileNotFoundError(
        f"best.pt not found. Expected at: {candidates[0]}\n"
        "Run train.py first."
    )


def evaluate_split(model, split_name, data_yaml, conf=0.25):
    """Run YOLO val on a specific split."""
    log.info(f"Evaluating on {split_name} split (conf={conf}) ...")
    metrics = model.val(
        data=data_yaml,
        split=split_name,
        conf=conf,
        iou=0.5,
        imgsz=384,
        batch=16,
        workers=0,
        plots=True,
        save_json=True,
        verbose=True,
    )
    return metrics


def extract_per_class_metrics(metrics, split_name):
    """Extract per-class precision, recall, mAP50, mAP50-95."""
    results = []
    try:
        # Ultralytics stores per-class metrics in metrics.box
        box = metrics.box
        # names() returns class name list
        names = CLASS_NAMES

        # Try to get per-class arrays
        # Different Ultralytics versions expose these differently
        try:
            p_per_cls = box.p.tolist() if hasattr(box, 'p') else []
            r_per_cls = box.r.tolist() if hasattr(box, 'r') else []
            map50_per_cls = box.ap50.tolist() if hasattr(box, 'ap50') else []
            map_per_cls = box.ap.tolist() if hasattr(box, 'ap') else []
        except Exception:
            p_per_cls = []
            r_per_cls = []
            map50_per_cls = []
            map_per_cls = []

        for i, cls in enumerate(names):
            p, r, ap50, ap = None, None, None, None
            try:
                p, r, ap50, ap = box.class_result(i)
                p = round(float(p), 4)
                r = round(float(r), 4)
                ap50 = round(float(ap50), 4)
                ap = round(float(ap), 4)
            except Exception:
                p = round(p_per_cls[i], 4) if i < len(p_per_cls) else None
                r = round(r_per_cls[i], 4) if i < len(r_per_cls) else None
                ap50 = round(map50_per_cls[i], 4) if i < len(map50_per_cls) else None
                ap = round(map_per_cls[i], 4) if i < len(map_per_cls) else None

            row = {
                "split": split_name,
                "class": cls,
                "class_id": i,
                "precision": p,
                "recall": r,
                "mAP50": ap50,
                "mAP50_95": ap,
            }
            results.append(row)

        # Overall metrics
        results.append({
            "split": split_name,
            "class": "ALL",
            "class_id": -1,
            "precision": round(float(box.mp), 4) if hasattr(box, 'mp') else None,
            "recall": round(float(box.mr), 4) if hasattr(box, 'mr') else None,
            "mAP50": round(float(box.map50), 4) if hasattr(box, 'map50') else None,
            "mAP50_95": round(float(box.map), 4) if hasattr(box, 'map') else None,
        })
    except Exception as e:
        log.warning(f"Could not extract per-class metrics: {e}")
        results.append({
            "split": split_name, "class": "ALL", "class_id": -1,
            "precision": None, "recall": None, "mAP50": None, "mAP50_95": None,
            "error": str(e),
        })
    return results


def generate_validation_samples(model, n_samples=20):
    """Run inference on sample val images and save annotated outputs."""
    import glob
    import random
    import cv2

    sample_dir = os.path.join(MODEL_DIR, "validation_samples")
    os.makedirs(sample_dir, exist_ok=True)

    val_img_dir = os.path.join(ROOT, "datasets", "processed", "images", "val")
    img_files = glob.glob(os.path.join(val_img_dir, "*.jpg")) + \
                glob.glob(os.path.join(val_img_dir, "*.png"))

    if not img_files:
        log.warning("No validation images found for sample generation.")
        return

    random.seed(42)
    sampled = random.sample(img_files, min(n_samples, len(img_files)))

    for i, img_path in enumerate(sampled):
        results = model.predict(img_path, conf=0.25, imgsz=384, verbose=False)
        if results:
            out_path = os.path.join(sample_dir, f"sample_{i:03d}.jpg")
            results[0].save(filename=out_path)

    log.info(f"Saved {len(sampled)} validation samples to: {sample_dir}")


def confidence_analysis(model):
    """Evaluate model at multiple confidence thresholds and export CSV."""
    log.info("Running confidence threshold analysis ...")
    rows = []
    for thresh in CONFIDENCE_THRESHOLDS:
        log.info(f"  threshold={thresh}")
        try:
            metrics = model.val(
                data=DATA_YAML,
                split="val",
                conf=thresh,
                iou=0.5,
                imgsz=384,
                batch=16,
                workers=0,
                fraction=0.25,
                plots=False,
                verbose=False,
            )
            box = metrics.box
            rows.append({
                "confidence_threshold": thresh,
                "precision": round(float(box.mp), 4) if hasattr(box, 'mp') else None,
                "recall": round(float(box.mr), 4) if hasattr(box, 'mr') else None,
                "mAP50": round(float(box.map50), 4) if hasattr(box, 'map50') else None,
                "mAP50_95": round(float(box.map), 4) if hasattr(box, 'map') else None,
            })
        except Exception as e:
            log.warning(f"  threshold={thresh} failed: {e}")
            rows.append({
                "confidence_threshold": thresh,
                "precision": None, "recall": None,
                "mAP50": None, "mAP50_95": None, "error": str(e)
            })

    csv_path = os.path.join(MODEL_DIR, "confidence_analysis.csv")
    if rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    log.info(f"Confidence analysis saved: {csv_path}")
    return rows


def write_error_analysis(val_metrics, test_metrics):
    """Write error_analysis.md summarizing findings."""
    path = os.path.join(MODEL_DIR, "error_analysis.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Error Analysis — {EXPERIMENT}\n\n")
        f.write(f"**Generated:** {datetime.datetime.utcnow().isoformat()} UTC\n\n")
        f.write("## Known Dataset Biases\n\n")
        f.write("| Class | Boxes | % of Total | Risk |\n")
        f.write("|-------|-------|------------|------|\n")
        f.write("| helmet | 24,531 | 47.92% | Overrepresented — model may be biased |\n")
        f.write("| safety_vest | 6,272 | 12.25% | Moderate |\n")
        f.write("| person | 5,545 | 10.83% | Moderate |\n")
        f.write("| smoke | 5,373 | 10.50% | Moderate |\n")
        f.write("| fire | 5,333 | 10.42% | Moderate |\n")
        f.write("| gloves | 2,634 | 5.15% | Underrepresented — may underperform |\n")
        f.write("| safety_footwear | 1,507 | 2.94% | Most underrepresented — highest recall risk |\n\n")
        f.write("## Validation Metrics\n\n")
        f.write("See `MODEL_EVALUATION_REPORT.md` for full per-class results.\n\n")
        f.write("## Recommendations\n\n")
        f.write("- If `safety_footwear` recall < 0.5: consider weighted sampling or synthetic augmentation in Phase 4.\n")
        f.write("- If `gloves` precision < 0.5: collect more diverse glove images.\n")
        f.write("- Monitor confusion between `helmet` / `head` (absent from ground truth but common visual false positive).\n")
        f.write("- Fire/smoke domain shift: d_fire dataset images may differ from industrial CCTV.\n")
        f.write("  Consider site-specific fine-tuning in Phase 4.\n")
    log.info(f"Error analysis written: {path}")


def write_evaluation_report(all_metrics, conf_rows):
    """Write MODEL_EVALUATION_REPORT.md."""
    path = os.path.join(MODEL_DIR, "MODEL_EVALUATION_REPORT.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Model Evaluation Report — {EXPERIMENT}\n\n")
        f.write(f"**Date:** {datetime.datetime.utcnow().isoformat()} UTC\n\n")
        f.write("## Per-Class Metrics\n\n")
        f.write("| Split | Class | Precision | Recall | mAP50 | mAP50-95 |\n")
        f.write("|-------|-------|-----------|--------|-------|----------|\n")
        for row in all_metrics:
            p = f"{row['precision']:.4f}" if row['precision'] is not None else "N/A"
            r = f"{row['recall']:.4f}" if row['recall'] is not None else "N/A"
            m50 = f"{row['mAP50']:.4f}" if row['mAP50'] is not None else "N/A"
            m = f"{row['mAP50_95']:.4f}" if row['mAP50_95'] is not None else "N/A"
            f.write(f"| {row['split']} | {row['class']} | {p} | {r} | {m50} | {m} |\n")

        f.write("\n## Confidence Threshold Analysis\n\n")
        f.write("| Threshold | Precision | Recall | mAP50 | mAP50-95 |\n")
        f.write("|-----------|-----------|--------|-------|----------|\n")
        for row in conf_rows:
            p = f"{row['precision']:.4f}" if row.get('precision') is not None else "N/A"
            r = f"{row['recall']:.4f}" if row.get('recall') is not None else "N/A"
            m50 = f"{row['mAP50']:.4f}" if row.get('mAP50') is not None else "N/A"
            m = f"{row['mAP50_95']:.4f}" if row.get('mAP50_95') is not None else "N/A"
            f.write(f"| {row['confidence_threshold']} | {p} | {r} | {m50} | {m} |\n")

        f.write("\n## Notes\n\n")
        f.write("- Metrics are on the held-out validation and test sets only.\n")
        f.write("- Test set was NOT used for hyperparameter tuning.\n")
        f.write("- See `error_analysis.md` for class imbalance analysis.\n")
        f.write("- See `confidence_analysis.csv` for full threshold data.\n")
    log.info(f"Evaluation report written: {path}")


def main():
    from ultralytics import YOLO

    best_pt = find_best_pt()
    log.info(f"Loading model: {best_pt}")
    model = YOLO(best_pt)

    all_metrics = []

    # Evaluate on val
    val_metrics = evaluate_split(model, "val", DATA_YAML, conf=0.25)
    all_metrics.extend(extract_per_class_metrics(val_metrics, "val"))

    # Evaluate on test (held-out — no hyperparameter influence)
    test_metrics = evaluate_split(model, "test", DATA_YAML, conf=0.25)
    all_metrics.extend(extract_per_class_metrics(test_metrics, "test"))

    # Save full metrics JSON
    metrics_path = os.path.join(MODEL_DIR, "evaluation_metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump({
            "experiment": EXPERIMENT,
            "evaluated_utc": datetime.datetime.utcnow().isoformat(),
            "metrics": all_metrics,
        }, f, indent=2)
    log.info(f"Evaluation metrics saved: {metrics_path}")

    # Generate validation sample images
    generate_validation_samples(model)

    # Confidence threshold analysis
    conf_rows = confidence_analysis(model)

    # Write reports
    write_error_analysis(val_metrics, test_metrics)
    write_evaluation_report(all_metrics, conf_rows)

    log.info("Evaluation complete. Run benchmark.py next.")


if __name__ == "__main__":
    main()
