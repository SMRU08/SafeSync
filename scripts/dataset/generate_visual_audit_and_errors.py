"""
generate_visual_audit_and_errors.py — Ground-truth inspection and prediction error analysis
1. Generates 20 train, 20 val, 20 test ground-truth visual annotations in datasets/reports/phase3_1_samples/
2. Runs v1 model inference to identify false positives, false negatives, missed persons, helmets, vests, gloves, boots, fire, smoke in models/detection/ppe_fire_smoke_v1/error_samples/
"""

import os
import random
from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO

ROOT = Path("D:/Additional/PROJECT/RAKSHYA-VISION")
PROCESSED_DIR = ROOT / "datasets" / "processed"
GT_SAMPLES_DIR = ROOT / "datasets" / "reports" / "phase3_1_samples"
ERROR_SAMPLES_DIR = ROOT / "models" / "detection" / "ppe_fire_smoke_v1" / "error_samples"
MODEL_PATH = ROOT / "models" / "detection" / "ppe_fire_smoke_v1" / "weights" / "best.pt"

CANONICAL_CLASSES = {
    0: "person",
    1: "helmet",
    2: "safety_vest",
    3: "gloves",
    4: "safety_footwear",
    5: "fire",
    6: "smoke",
}

CLASS_COLORS = {
    0: (0, 215, 255),   # person - Yellow
    1: (0, 255, 0),     # helmet - Lime
    2: (0, 140, 255),   # safety_vest - Orange
    3: (255, 255, 0),   # gloves - Cyan
    4: (255, 100, 0),   # safety_footwear - Blue
    5: (0, 0, 255),     # fire - Red
    6: (128, 128, 128), # smoke - Gray
}

def load_boxes(lbl_path, w, h):
    boxes = []
    if not lbl_path.exists():
        return boxes
    with open(lbl_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 5:
                cid = int(parts[0])
                cx, cy, bw, bh = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
                x1 = int((cx - bw / 2) * w)
                y1 = int((cy - bh / 2) * h)
                x2 = int((cx + bw / 2) * w)
                y2 = int((cy + bh / 2) * h)
                boxes.append((cid, x1, y1, x2, y2))
    return boxes

def draw_boxes(img, boxes, is_pred=False):
    out = img.copy()
    for item in boxes:
        if is_pred:
            cid, conf, x1, y1, x2, y2 = item
            label = f"{CANONICAL_CLASSES.get(cid, str(cid))} {conf:.2f}"
        else:
            cid, x1, y1, x2, y2 = item
            label = f"GT: {CANONICAL_CLASSES.get(cid, str(cid))}"
        
        color = CLASS_COLORS.get(cid, (255, 255, 255))
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        
        (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        ty1 = max(0, y1 - th - baseline - 2)
        cv2.rectangle(out, (x1, ty1), (x1 + tw + 4, ty1 + th + baseline + 2), color, -1)
        cv2.putText(out, label, (x1 + 2, ty1 + th), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    return out

def generate_gt_samples():
    random.seed(42)
    splits = ["train", "val", "test"]
    for split in splits:
        img_dir = PROCESSED_DIR / "images" / split
        lbl_dir = PROCESSED_DIR / "labels" / split
        out_dir = GT_SAMPLES_DIR / split
        out_dir.mkdir(parents=True, exist_ok=True)
        
        all_imgs = sorted(list(img_dir.glob("*.*")))
        # Filter to images that have at least one annotation for informative samples
        annotated_imgs = []
        for p in all_imgs:
            lbl_p = lbl_dir / f"{p.stem}.txt"
            if lbl_p.exists() and lbl_p.stat().st_size > 0:
                annotated_imgs.append(p)
                
        selected = random.sample(annotated_imgs, min(20, len(annotated_imgs)))
        print(f"Generating 20 GT samples for {split}...")
        for p in selected:
            img = cv2.imread(str(p))
            if img is None:
                continue
            h, w = img.shape[:2]
            lbl_p = lbl_dir / f"{p.stem}.txt"
            boxes = load_boxes(lbl_p, w, h)
            rendered = draw_boxes(img, boxes)
            out_path = out_dir / f"{p.stem}_gt.jpg"
            cv2.imwrite(str(out_path), rendered)
    print("GT samples generated successfully!")

def generate_error_samples():
    print("Loading YOLO model for prediction error analysis...")
    model = YOLO(str(MODEL_PATH))
    ERROR_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    
    val_img_dir = PROCESSED_DIR / "images" / "val"
    val_lbl_dir = PROCESSED_DIR / "labels" / "val"
    all_val_imgs = sorted(list(val_img_dir.glob("*.*")))
    
    # We want to capture errors for:
    # - missed person
    # - missed helmet
    # - missed vest
    # - missed gloves
    # - missed footwear
    # - missed fire
    # - missed smoke
    # - false positive detections
    errors_found = {cname: 0 for cname in CANONICAL_CLASSES.values()}
    errors_found["false_positive"] = 0
    
    target_per_category = 2
    
    for img_p in all_val_imgs:
        if all(v >= target_per_category for v in errors_found.values()):
            break
            
        img = cv2.imread(str(img_p))
        if img is None:
            continue
        h, w = img.shape[:2]
        lbl_p = val_lbl_dir / f"{img_p.stem}.txt"
        gt_boxes = load_boxes(lbl_p, w, h)
        
        # Run inference
        results = model.predict(img, conf=0.25, imgsz=384, verbose=False)
        pred_boxes = []
        if len(results) > 0 and results[0].boxes is not None:
            for b in results[0].boxes:
                cid = int(b.cls[0].item())
                cnf = float(b.conf[0].item())
                xyxy = b.xyxy[0].cpu().numpy().astype(int)
                pred_boxes.append((cid, cnf, xyxy[0], xyxy[1], xyxy[2], xyxy[3]))
                
        gt_cids = set(b[0] for b in gt_boxes)
        pred_cids = set(b[0] for b in pred_boxes)
        
        # Check for missed classes (False Negatives)
        missed = gt_cids - pred_cids
        # Check for False Positives
        fps = pred_cids - gt_cids
        
        needed = False
        reason = []
        for cid in missed:
            cname = CANONICAL_CLASSES.get(cid)
            if cname and errors_found[cname] < target_per_category:
                errors_found[cname] += 1
                needed = True
                reason.append(f"missed_{cname}")
                
        if fps and errors_found["false_positive"] < target_per_category:
            errors_found["false_positive"] += 1
            needed = True
            reason.append("false_positive")
            
        if needed:
            # Create side-by-side visualization: Left = Ground Truth, Right = Prediction
            img_gt = draw_boxes(img, gt_boxes)
            img_pred = draw_boxes(img, pred_boxes, is_pred=True)
            
            # Header bars
            header_gt = np.zeros((30, w, 3), dtype=np.uint8)
            cv2.putText(header_gt, "GROUND TRUTH", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            header_pred = np.zeros((30, w, 3), dtype=np.uint8)
            cv2.putText(header_pred, f"PREDICTION (v1) - Reason: {', '.join(reason)}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1)
            
            gt_combo = np.vstack([header_gt, img_gt])
            pred_combo = np.vstack([header_pred, img_pred])
            
            combined = np.hstack([gt_combo, pred_combo])
            out_file = ERROR_SAMPLES_DIR / f"{img_p.stem}_err_{'_'.join(reason)[:40]}.jpg"
            cv2.imwrite(str(out_file), combined)
            print(f"Saved error sample: {out_file.name}")
            
    print("Prediction error analysis completed! Samples saved to:", ERROR_SAMPLES_DIR)
    print("Error counts captured:", errors_found)

if __name__ == "__main__":
    generate_gt_samples()
    generate_error_samples()
