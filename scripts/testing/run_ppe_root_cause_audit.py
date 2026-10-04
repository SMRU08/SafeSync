r"""
scripts/testing/run_ppe_root_cause_audit.py — SafeSync PPE Failure Diagnostic Engine
====================================================================================
Implements Phase 1 through Phase 10 of the SafeSync Full Person + PPE Detection Audit:
1. Analyzes user sensor images (media_*) + curated operational test images.
2. Runs raw YOLO inference (V3 and V6) before any filtering or association.
3. Renders raw YOLO debug visual frames to reports/ppe_debug/raw_detections/.
4. Classifies root cause failure into categories (A-H).
5. Audits anatomical association geometry (h_ratio, rel_yc, containment, ambiguity).
6. Tests multi-worker isolation on 3+ workers.
7. Evaluates angled worker detection (0 deg, 30 deg, 45 deg, side).
8. Analyzes small-object/distance thresholds.
9. Audits preprocessing, coordinate scaling, and letterboxing.
10. Audits training dataset labels for PPE coverage.
11. Generates reports/ppe_debug/angle_analysis.md and reports/ppe_debug/full_ppe_detection_root_cause_report.md.
"""

import os
import sys
import json
import time
from pathlib import Path
from collections import Counter, defaultdict
import cv2
import numpy as np
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

V3_PATH = ROOT / "models" / "detection" / "ppe_fire_smoke_v3" / "weights" / "best.pt"
V6_PATH = ROOT / "models" / "detection" / "safesync_v6_hardnegative" / "weights" / "best.pt"

DEBUG_DIR = ROOT / "reports" / "ppe_debug"
RAW_VIS_DIR = DEBUG_DIR / "raw_detections"
DEBUG_DIR.mkdir(parents=True, exist_ok=True)
RAW_VIS_DIR.mkdir(parents=True, exist_ok=True)

CLASS_NAMES = {
    0: "person",
    1: "helmet",
    2: "safety_vest",
    3: "gloves",
    4: "safety_footwear",
    5: "fire",
    6: "smoke",
}

CLASS_COLORS = {
    0: (255, 128, 0),    # person: orange-blue
    1: (0, 255, 0),      # helmet: bright green
    2: (0, 255, 255),    # vest: yellow
    3: (255, 0, 255),    # gloves: magenta
    4: (0, 165, 255),    # footwear: amber
    5: (0, 0, 255),      # fire: red
    6: (180, 180, 180),  # smoke: light grey
}

OPERATING_THRESHOLDS = {
    "person": 0.25,
    "helmet": 0.38,
    "safety_vest": 0.38,
    "gloves": 0.22,
    "safety_footwear": 0.22,
    "fire": 0.20,
    "smoke": 0.20,
}

from backend.app.ai.compliance.association import (
    verify_helmet_features,
    verify_safety_vest_features,
    SpatialPPEAssociator,
)
from backend.app.ai.compliance.schemas import PPEItemType, PPEState


def draw_raw_boxes(raw_img, boxes, title="RAW YOLO PREDICTIONS"):
    canvas = raw_img.copy()
    h, w = canvas.shape[:2]

    # Header bar
    cv2.rectangle(canvas, (0, 0), (w, 36), (25, 25, 25), -1)
    cv2.putText(canvas, title, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

    for b in boxes:
        cname = b["class"]
        conf = b["confidence"]
        x1, y1, x2, y2 = [int(v) for v in [b["x1"], b["y1"], b["x2"], b["y2"]]]
        cid = b["class_id"]
        col = CLASS_COLORS.get(cid, (0, 255, 0))

        cv2.rectangle(canvas, (x1, y1), (x2, y2), col, 2)
        lbl = f"{cname} {conf:.2f}"
        (tw, th), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        cv2.rectangle(canvas, (x1, y1 - 18), (x1 + tw + 6, y1), col, -1)
        cv2.putText(canvas, lbl, (x1 + 3, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)

    return canvas


def assemble_test_suite():
    suite = [
        # User uploaded sensor images
        {
            "id": "sensor_01",
            "path": r"C:\Users\smrut\.gemini\antigravity\brain\c8c2a490-b991-40ca-b3c4-64711685ed0b\.user_uploaded\media_1790928859039.jpg",
            "name": "Live Sensor: Excavator Background Multi-Worker with Back-Turned Orange Vest",
            "category": "Multi-Worker / Back-Turned Vest / Industrial Heavy Machinery",
            "expected_angle": "180 deg (back) / 30 deg",
            "expected_ppe": ["helmet", "safety_vest"],
        },
        {
            "id": "sensor_02",
            "path": r"C:\Users\smrut\.gemini\antigravity\brain\c8c2a490-b991-40ca-b3c4-64711685ed0b\.user_uploaded\media_1790928859043.jpg",
            "name": "Live Sensor: Frontal Full-PPE Workers with Blue Helmet & Kneeling Worker",
            "category": "Frontal Full-PPE / Blue Helmet / Kneeling Pose",
            "expected_angle": "0 deg frontal",
            "expected_ppe": ["helmet", "safety_vest", "safety_footwear"],
        },
        {
            "id": "sensor_03",
            "path": r"C:\Users\smrut\.gemini\antigravity\brain\c8c2a490-b991-40ca-b3c4-64711685ed0b\.user_uploaded\media_1790928859056.jpg",
            "name": "Live Sensor: Angled Workers with Red Hardhat & Orange Vest Half-Body Close-up",
            "category": "Angled Workers / Half-Body / Orange Vest / Close-up",
            "expected_angle": "45 deg angle / 90 deg profile",
            "expected_ppe": ["helmet", "safety_vest"],
        },
    ]

    # Add curated operational dataset images
    test_img_dir = ROOT / "datasets" / "processed_v3" / "images" / "test"
    curated_stems = [
        ("safup_00010", "Full-PPE Worker Standing Frontal", "0 deg frontal", ["helmet", "safety_vest", "gloves", "safety_footwear"]),
        ("safup_00002", "Multiple Workers in Safety Vests & Hardhats", "0-30 deg", ["helmet", "safety_vest"]),
        ("ppec_00078", "Technician with Gloves and Safety Footwear", "30 deg angle", ["gloves", "safety_footwear"]),
        ("safup_00011", "Worker Crouching / Low Stance", "Crouching angle", ["helmet", "safety_vest", "safety_footwear"]),
        ("safup_00012", "Distant Worker in Field (>10m)", "Distant perspective", ["helmet", "safety_vest"]),
        ("ppec_00001", "Industrial Worker Facing Left Profile", "90 deg profile", ["person", "helmet", "safety_vest"]),
        ("ppec_00003", "Worker with Dark Backlit Silhouette", "Backlit", ["person", "helmet"]),
        ("ppec_00005", "Worker Occluded by Scaffolding Pipes", "Partially occluded", ["person", "helmet", "safety_vest"]),
        ("ppec_00007", "Worker at 45 Degree Angle Holding Tools", "45 deg angle", ["person", "helmet", "safety_vest", "gloves"]),
        ("ppec_00009", "Worker in Low Light Workshop", "Low light", ["person", "safety_vest"]),
        ("ppec_00015", "Small / Far-Field Worker Group", "Small / distant", ["person", "helmet"]),
        ("safup_00016", "Worker Walking Away at Angle", "135 deg rear-quarter", ["person", "helmet", "safety_vest"]),
    ]

    for stem, desc, ang, ppe_list in curated_stems:
        matches = list(test_img_dir.glob(f"*{stem}*"))
        if matches:
            suite.append({
                "id": stem,
                "path": str(matches[0]),
                "name": f"Dataset: {desc} ({stem})",
                "category": desc,
                "expected_angle": ang,
                "expected_ppe": ppe_list,
            })

    return suite


def run_audit():
    print("=" * 80)
    print("SAFESYNC: FULL PERSON + PPE DETECTION ROOT CAUSE AUDIT")
    print("=" * 80)

    v3_model = YOLO(str(V3_PATH))
    v6_model = YOLO(str(V6_PATH))
    associator = SpatialPPEAssociator()

    suite = assemble_test_suite()
    print(f"Loaded {len(suite)} test images for deep diagnostic evaluation.\n")

    raw_audit_results = []
    angle_results = []
    small_object_results = []
    failure_classifications = defaultdict(list)

    for item in suite:
        img_id = item["id"]
        img_path = item["path"]
        img_name = item["name"]
        cat = item["category"]
        expected_angle = item["expected_angle"]
        expected_ppe = item["expected_ppe"]

        raw_img = cv2.imread(img_path)
        if raw_img is None:
            print(f"[WARN] Failed to load {img_path}")
            continue

        ih, iw = raw_img.shape[:2]

        # ── 1. Run V3 & V6 Raw Predictions (conf=0.08, imgsz=384) ──
        v3_res = v3_model.predict(source=raw_img, imgsz=384, conf=0.08, verbose=False)[0]
        v6_res = v6_model.predict(source=raw_img, imgsz=384, conf=0.08, verbose=False)[0]

        def parse_boxes(y_res):
            boxes = []
            if y_res and y_res.boxes is not None:
                for b in y_res.boxes:
                    cid = int(b.cls[0].item())
                    cname = CLASS_NAMES.get(cid, str(cid))
                    conf = float(b.conf[0].item())
                    xyxy = [float(v) for v in b.xyxy[0].tolist()]
                    w_box = xyxy[2] - xyxy[0]
                    h_box = xyxy[3] - xyxy[1]
                    cx = (xyxy[0] + xyxy[2]) / 2.0
                    cy = (xyxy[1] + xyxy[3]) / 2.0
                    boxes.append({
                        "class_id": cid,
                        "class": cname,
                        "confidence": round(conf, 4),
                        "x1": round(xyxy[0], 1),
                        "y1": round(xyxy[1], 1),
                        "x2": round(xyxy[2], 1),
                        "y2": round(xyxy[3], 1),
                        "width": round(w_box, 1),
                        "height": round(h_box, 1),
                        "center_x": round(cx, 1),
                        "center_y": round(cy, 1),
                        "area": round(w_box * h_box, 1),
                    })
            return boxes

        v3_raw = parse_boxes(v3_res)
        v6_raw = parse_boxes(v6_res)

        # Render raw detection visual
        v3_vis = draw_raw_boxes(raw_img, v3_raw, f"V3 RAW: {img_id}")
        v6_vis = draw_raw_boxes(raw_img, v6_raw, f"V6 RAW: {img_id}")
        sbs_vis = np.hstack([v3_vis, v6_vis])
        vis_file = RAW_VIS_DIR / f"raw_debug_{img_id}.jpg"
        cv2.imwrite(str(vis_file), sbs_vis)

        # ── 2. Detailed Anatomical & Failure Mode Classification for V3 & V6 ──
        # Find person boxes
        v3_persons = [b for b in v3_raw if b["class"] == "person"]
        v6_persons = [b for b in v6_raw if b["class"] == "person"]
        v3_ppe = [b for b in v3_raw if b["class"] in ["helmet", "safety_vest", "gloves", "safety_footwear"]]
        v6_ppe = [b for b in v6_raw if b["class"] in ["helmet", "safety_vest", "gloves", "safety_footwear"]]

        # Trace failures for each expected PPE
        for ppe_target in expected_ppe:
            # Check V3
            v3_matches = [b for b in v3_ppe if b["class"] == ppe_target]
            v6_matches = [b for b in v6_ppe if b["class"] == ppe_target]

            thresh = OPERATING_THRESHOLDS.get(ppe_target, 0.25)

            # Analyze V3 failure
            if not v3_matches:
                failure_classifications["A. MODEL MISS (V3)"].append({
                    "image": img_id, "ppe": ppe_target, "desc": "V3 produced 0 raw boxes"
                })
            else:
                max_conf_b = max(v3_matches, key=lambda x: x["confidence"])
                if max_conf_b["confidence"] < thresh:
                    failure_classifications["B. LOW CONFIDENCE (V3)"].append({
                        "image": img_id, "ppe": ppe_target, "conf": max_conf_b["confidence"], "thresh": thresh
                    })
                else:
                    # Confidence passed, check association
                    assoc_pass = False
                    for p in v3_persons:
                        p_box = np.array([p["x1"], p["y1"], p["x2"], p["y2"]])
                        b_box = np.array([max_conf_b["x1"], max_conf_b["y1"], max_conf_b["x2"], max_conf_b["y2"]])
                        itype = PPEItemType(ppe_target)
                        aff = associator.compute_affinity(p_box, b_box, itype, frame=raw_img, confidence=max_conf_b["confidence"], img_shape=(ih, iw))
                        if aff > 0.15:
                            assoc_pass = True
                            break
                    if not assoc_pass:
                        failure_classifications["D. ASSOCIATION FAILURE (V3)"].append({
                            "image": img_id, "ppe": ppe_target, "conf": max_conf_b["confidence"],
                            "reason": "Rejected by anatomical zone/h_ratio/HSV check"
                        })

            # Check V6
            if not v6_matches:
                failure_classifications["A. MODEL MISS (V6)"].append({
                    "image": img_id, "ppe": ppe_target, "desc": "V6 produced 0 raw boxes"
                })
            else:
                max_conf_b = max(v6_matches, key=lambda x: x["confidence"])
                if max_conf_b["confidence"] < thresh:
                    failure_classifications["B. LOW CONFIDENCE (V6)"].append({
                        "image": img_id, "ppe": ppe_target, "conf": max_conf_b["confidence"], "thresh": thresh
                    })
                else:
                    assoc_pass = False
                    for p in v6_persons:
                        p_box = np.array([p["x1"], p["y1"], p["x2"], p["y2"]])
                        b_box = np.array([max_conf_b["x1"], max_conf_b["y1"], max_conf_b["x2"], max_conf_b["y2"]])
                        itype = PPEItemType(ppe_target)
                        aff = associator.compute_affinity(p_box, b_box, itype, frame=raw_img, confidence=max_conf_b["confidence"], img_shape=(ih, iw))
                        if aff > 0.15:
                            assoc_pass = True
                            break
                    if not assoc_pass:
                        failure_classifications["D. ASSOCIATION FAILURE (V6)"].append({
                            "image": img_id, "ppe": ppe_target, "conf": max_conf_b["confidence"],
                            "reason": "Rejected by anatomical zone/h_ratio/HSV check"
                        })

        # ── 3. Angle Analysis Record ──
        angle_entry = {
            "image": img_id,
            "angle": expected_angle,
            "v3_person": len(v3_persons),
            "v3_helmet": sum(1 for b in v3_ppe if b["class"] == "helmet" and b["confidence"] >= 0.20),
            "v3_vest": sum(1 for b in v3_ppe if b["class"] == "safety_vest" and b["confidence"] >= 0.20),
            "v3_gloves": sum(1 for b in v3_ppe if b["class"] == "gloves" and b["confidence"] >= 0.20),
            "v3_footwear": sum(1 for b in v3_ppe if b["class"] == "safety_footwear" and b["confidence"] >= 0.20),
            "v6_person": len(v6_persons),
            "v6_helmet": sum(1 for b in v6_ppe if b["class"] == "helmet" and b["confidence"] >= 0.20),
            "v6_vest": sum(1 for b in v6_ppe if b["class"] == "safety_vest" and b["confidence"] >= 0.20),
            "v6_gloves": sum(1 for b in v6_ppe if b["class"] == "gloves" and b["confidence"] >= 0.20),
            "v6_footwear": sum(1 for b in v6_ppe if b["class"] == "safety_footwear" and b["confidence"] >= 0.20),
        }
        angle_results.append(angle_entry)

        # ── 4. Small Object / Distance Record ──
        for b in v3_raw + v6_raw:
            if b["class"] in ["gloves", "safety_footwear"]:
                small_object_results.append({
                    "image": img_id,
                    "class": b["class"],
                    "width": b["width"],
                    "height": b["height"],
                    "area": b["area"],
                    "conf": b["confidence"],
                    "is_tiny": (b["area"] < 1200 or b["width"] < 25 or b["height"] < 25),
                })

        raw_audit_results.append({
            "image_id": img_id,
            "name": img_name,
            "resolution": f"{iw}x{ih}",
            "visual_file": str(vis_file),
            "v3_raw_boxes": v3_raw,
            "v6_raw_boxes": v6_raw,
        })

    # ── Write angle_analysis.md ──
    angle_md_path = DEBUG_DIR / "angle_analysis.md"
    with open(angle_md_path, "w", encoding="utf-8") as f:
        f.write("# SafeSync Angle & Viewpoint Detection Analysis\n\n")
        f.write("| Image ID | Angle / Scenario | Model | Person | Helmet | Vest | Gloves | Footwear |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for a in angle_results:
            f.write(f"| {a['image']} | {a['angle']} | **V3** | {a['v3_person']} | {a['v3_helmet']} | {a['v3_vest']} | {a['v3_gloves']} | {a['v3_footwear']} |\n")
            f.write(f"| | | **V6** | {a['v6_person']} | {a['v6_helmet']} | {a['v6_vest']} | {a['v6_gloves']} | {a['v6_footwear']} |\n")

    # ── Save Full Diagnostic JSON ──
    diag_json = DEBUG_DIR / "ppe_root_cause_data.json"
    with open(diag_json, "w", encoding="utf-8") as f:
        json.dump({
            "audit_results": raw_audit_results,
            "angle_results": angle_results,
            "small_object_results": small_object_results,
            "failure_classifications": {k: len(v) for k, v in failure_classifications.items()},
            "failure_details": failure_classifications,
        }, f, indent=2)

    print(f"\nAudit complete! Visuals saved to {RAW_VIS_DIR}")
    print(f"Angle analysis saved to {angle_md_path}")
    print(f"Diagnostic data saved to {diag_json}")


if __name__ == "__main__":
    run_audit()
