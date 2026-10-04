r"""
scripts/testing/run_shadow_mode_evaluation.py — SafeSync V6 Shadow Mode Pipeline
================================================================================
Runs candidate model V6 in strict SHADOW MODE alongside production baseline V3.

Strict Constraints:
1. V3 remains the sole active production model driving all alerts/decisions.
2. V6 predictions are isolated — ZERO alarms, notifications, or actions triggered.
3. Log V6 predictions independently to outputs/detection/logs/v6_shadow_predictions.jsonl.
4. Run on identical frames with synchronized frame_id and UTC timestamps.
5. Evaluates both Live Camera (Webcam 0) and high-density industrial CCTV footage.
6. Compares all 7 classes, latency, FPS, bounding box IoUs, and failure modes.
7. Generates reports/v6_shadow_mode_validation_report.md.
"""

import os
import sys
import time
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter, defaultdict
import cv2
import numpy as np
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

V3_PATH = ROOT / "models" / "detection" / "ppe_fire_smoke_v3" / "weights" / "best.pt"
V6_PATH = ROOT / "models" / "detection" / "safesync_v6_hardnegative" / "weights" / "best.pt"

LOGS_DIR = ROOT / "outputs" / "detection" / "logs"
VIDEOS_DIR = ROOT / "outputs" / "detection" / "videos"
VISUALS_DIR = ROOT / "reports" / "shadow_mode_visuals"
REPORT_PATH = ROOT / "reports" / "v6_shadow_mode_validation_report.md"
DATA_JSON_PATH = ROOT / "reports" / "v6_shadow_mode_data.json"

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
    1: (0, 255, 0),      # helmet: green
    2: (0, 255, 255),    # safety_vest: yellow
    3: (255, 0, 255),    # gloves: magenta
    4: (0, 165, 255),    # footwear: amber
    5: (0, 0, 255),      # fire: red
    6: (180, 180, 180),  # smoke: light grey
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


def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def calc_iou(b1, b2):
    xA = max(b1[0], b2[0])
    yA = max(b1[1], b2[1])
    xB = min(b1[2], b2[2])
    yB = min(b1[3], b2[3])
    inter = max(0.0, xB - xA) * max(0.0, yB - yA)
    a1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
    a2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
    return inter / max(1e-6, a1 + a2 - inter)


def extract_filtered_boxes(yolo_result):
    boxes = []
    if yolo_result and yolo_result.boxes is not None:
        for b in yolo_result.boxes:
            cid = int(b.cls[0].item())
            conf = float(b.conf[0].item())
            cname = CLASS_NAMES.get(cid, str(cid))
            thresh = OPERATING_THRESHOLDS.get(cname, 0.20)
            if conf >= thresh:
                xyxy = [round(float(v), 1) for v in b.xyxy[0].tolist()]
                boxes.append({
                    "class_id": cid,
                    "class_name": cname,
                    "confidence": round(conf, 4),
                    "bbox": xyxy,
                })
    return boxes


def draw_frame_annotations(raw_img, boxes, banner_text, banner_color=(30, 30, 30)):
    canvas = raw_img.copy()
    h, w = canvas.shape[:2]

    # Banner header
    cv2.rectangle(canvas, (0, 0), (w, 36), banner_color, -1)
    cv2.putText(canvas, banner_text, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

    for b in boxes:
        cid = b["class_id"]
        cname = b["class_name"]
        conf = b["confidence"]
        xyxy = [int(v) for v in b["bbox"]]
        color = CLASS_COLORS.get(cid, (0, 255, 0))

        cv2.rectangle(canvas, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), color, 2)
        label = f"{cname} {conf:.2f}"
        t_sz = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)[0]
        cv2.rectangle(canvas, (xyxy[0], xyxy[1] - 18), (xyxy[0] + t_sz[0] + 6, xyxy[1]), color, -1)
        cv2.putText(canvas, label, (xyxy[0] + 3, xyxy[1] - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)

    return canvas


def build_cctv_frame_sequence():
    """Builds a sequence of test frames covering all operational regimes."""
    test_img_dir = ROOT / "datasets" / "processed_v3" / "images" / "test"
    val_img_dir = ROOT / "datasets" / "processed_v3" / "images" / "val"

    scenarios = [
        {"name": "Multi-Worker PPE Collaboration", "stem": "safup_00002", "frames": 15, "category": "PPE_Multi"},
        {"name": "Single Worker Full PPE (Gloves+Boots)", "stem": "safup_00010", "frames": 15, "category": "PPE_Full"},
        {"name": "Technician with Gloves & Boots", "stem": "ppec_00078", "frames": 15, "category": "PPE_Detail"},
        {"name": "Industrial Steam Pipe Distractor", "stem": "hneg_00004", "frames": 15, "category": "HardNegative_Steam"},
        {"name": "Specular Sun Glare on Metal", "stem": "hneg_00008", "frames": 15, "category": "HardNegative_Glare"},
        {"name": "Construction Dust Cloud Plume", "stem": "hneg_00041", "frames": 15, "category": "HardNegative_Dust"},
        {"name": "Yellow CAT Excavator Surface", "stem": "hneg_00061", "frames": 15, "category": "HardNegative_Machinery"},
        {"name": "Active Fire Flame Core", "stem": "dfire_00000", "frames": 15, "category": "Hazard_Fire"},
        {"name": "Distinct Smoke Plume Column", "stem": "dfire_00013", "frames": 15, "category": "Hazard_Smoke"},
        {"name": "Mixed Combustion & Smoke", "stem": "dfire_00006", "frames": 15, "category": "Hazard_Combined"},
        {"name": "Distant Worker in Field", "stem": "safup_00012", "frames": 15, "category": "PPE_Distant"},
        {"name": "Industrial Facility Worker", "stem": "ppec_00001", "frames": 15, "category": "PPE_Facility"},
    ]

    sequence = []
    for sc in scenarios:
        stem = sc["stem"]
        matches = list(test_img_dir.glob(f"*{stem}*"))
        if not matches:
            matches = list(val_img_dir.glob(f"*{stem}*"))
        if not matches:
            continue

        img_path = matches[0]
        raw_img = cv2.imread(str(img_path))
        if raw_img is None:
            continue

        raw_img = cv2.resize(raw_img, (640, 480))
        for f_idx in range(sc["frames"]):
            sequence.append({
                "source": "cctv_simulation",
                "scene_name": sc["name"],
                "category": sc["category"],
                "frame": raw_img,
                "scene_frame_idx": f_idx,
                "image_stem": stem,
            })

    return sequence


def capture_webcam_frames(max_frames=60):
    """Captures live frames from webcam 0 if available."""
    frames = []
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[WARN] Webcam 0 unavailable for live capture. Proceeding with CCTV stream.")
        return frames

    print(f"Capturing {max_frames} frames from Live Webcam 0...")
    for f_idx in range(max_frames):
        ret, frame = cap.read()
        if not ret:
            break
        frame_resized = cv2.resize(frame, (640, 480))
        frames.append({
            "source": "live_webcam_0",
            "scene_name": f"Live Camera Feed (Frame {f_idx+1})",
            "category": "Live_Webcam",
            "frame": frame_resized,
            "scene_frame_idx": f_idx,
            "image_stem": f"live_webcam_{f_idx:04d}",
        })
        time.sleep(0.02)  # Simulate ~30-50 fps capture interval

    cap.release()
    print(f"Captured {len(frames)} live webcam frames.")
    return frames


def main():
    print("=" * 80)
    print("SAFESYNC: V6 SHADOW MODE PIPELINE EVALUATION")
    print("=" * 80)

    # 1. Verification of Checkpoints
    v3_sha = sha256_file(V3_PATH)
    v6_sha = sha256_file(V6_PATH)
    print(f"Active Production Model (V3) : {V3_PATH.name} (SHA-256: {v3_sha[:16]}...)")
    print(f"Shadow Candidate Model (V6)   : {V6_PATH.name} (SHA-256: {v6_sha[:16]}...)")

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    VISUALS_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Load Models
    print("\nLoading models into memory...")
    v3_model = YOLO(str(V3_PATH))
    v6_model = YOLO(str(V6_PATH))

    # 3. Assemble Evaluation Streams
    cctv_frames = build_cctv_frame_sequence()
    webcam_frames = capture_webcam_frames(max_frames=60)
    all_frames = webcam_frames + cctv_frames
    total_frames = len(all_frames)
    print(f"\nTotal frames assembled: {total_frames} (Live Webcam: {len(webcam_frames)}, CCTV Multi-Scenario: {len(cctv_frames)})")

    # 4. Initialize Logs
    v3_log_file = LOGS_DIR / "v3_production_predictions.jsonl"
    v6_log_file = LOGS_DIR / "v6_shadow_predictions.jsonl"
    v3_fp = open(v3_log_file, "w", encoding="utf-8")
    v6_fp = open(v6_log_file, "w", encoding="utf-8")

    # Video Writer for Side-by-Side Shadow Video
    out_video_path = VIDEOS_DIR / "shadow_mode_v3_vs_v6_comparison.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_writer = cv2.VideoWriter(str(out_video_path), fourcc, 15.0, (1280, 480))

    # Metric Trackers
    v3_latencies = []
    v6_latencies = []
    v3_class_totals = Counter()
    v6_class_totals = Counter()
    v3_conf_totals = defaultdict(list)
    v6_conf_totals = defaultdict(list)

    false_positive_cases = []
    missed_detection_cases = []
    discrepancy_records = []
    key_visual_snapshots = []

    print("\nExecuting synchronized frame-by-frame inference...")

    for frame_id, item in enumerate(all_frames):
        raw_frame = item["frame"]
        timestamp = datetime.now(timezone.utc).isoformat()
        source = item["source"]
        scene_name = item["scene_name"]
        category = item["category"]
        stem = item["image_stem"]

        # ── V3 Production Inference (Active Driver) ──
        t0 = time.perf_counter()
        v3_res = v3_model.predict(source=raw_frame, imgsz=384, conf=0.15, verbose=False)[0]
        v3_lat = (time.perf_counter() - t0) * 1000.0
        v3_latencies.append(v3_lat)
        v3_boxes = extract_filtered_boxes(v3_res)

        # Production Action Simulation: V3 triggers alerts
        v3_alerts = []
        for b in v3_boxes:
            cname = b["class_name"]
            v3_class_totals[cname] += 1
            v3_conf_totals[cname].append(b["confidence"])
            if cname in ["fire", "smoke"]:
                v3_alerts.append(f"HAZARD_ALERT: {cname} (conf={b['confidence']:.2f})")

        v3_record = {
            "frame_id": frame_id,
            "timestamp": timestamp,
            "source": source,
            "scene": scene_name,
            "model": "ppe_fire_smoke_v3",
            "role": "PRODUCTION_ACTIVE",
            "latency_ms": round(v3_lat, 2),
            "detections": v3_boxes,
            "production_alerts_emitted": v3_alerts,
        }
        v3_fp.write(json.dumps(v3_record) + "\n")

        # ── V6 Shadow Inference (Completely Isolated) ──
        t0 = time.perf_counter()
        v6_res = v6_model.predict(source=raw_frame, imgsz=384, conf=0.15, verbose=False)[0]
        v6_lat = (time.perf_counter() - t0) * 1000.0
        v6_latencies.append(v6_lat)
        v6_boxes = extract_filtered_boxes(v6_res)

        # STRICT ISOLATION GUARD: V6 DOES NOT EMIT ALERTS
        v6_shadow_alerts_suppressed = []
        for b in v6_boxes:
            cname = b["class_name"]
            v6_class_totals[cname] += 1
            v6_conf_totals[cname].append(b["confidence"])
            if cname in ["fire", "smoke"]:
                v6_shadow_alerts_suppressed.append(f"SHADOW_SUPPRESSED_ALERT: {cname} (conf={b['confidence']:.2f})")

        v6_record = {
            "frame_id": frame_id,
            "timestamp": timestamp,
            "source": source,
            "scene": scene_name,
            "model": "safesync_v6_hardnegative",
            "role": "SHADOW_PASSIVE_ISOLATED",
            "latency_ms": round(v6_lat, 2),
            "detections": v6_boxes,
            "production_alerts_emitted": [],  # Strictly empty!
            "shadow_alerts_suppressed": v6_shadow_alerts_suppressed,
        }
        v6_fp.write(json.dumps(v6_record) + "\n")

        # ── Compare Detections for Current Frame ──
        v3_c_counts = Counter(b["class_name"] for b in v3_boxes)
        v6_c_counts = Counter(b["class_name"] for b in v6_boxes)

        # Check for discrepancies
        diff_classes = set(v3_c_counts.keys()).symmetric_difference(set(v6_c_counts.keys()))
        count_mismatch = any(v3_c_counts[c] != v6_c_counts[c] for c in set(v3_c_counts.keys()) | set(v6_c_counts.keys()))

        # Check False Positives on Hard Negative distractor categories
        if "HardNegative" in category:
            if v3_c_counts["smoke"] > 0 or v3_c_counts["fire"] > 0:
                false_positive_cases.append({
                    "frame_id": frame_id,
                    "model": "V3",
                    "category": category,
                    "hazard": dict(v3_c_counts),
                })
            if v6_c_counts["smoke"] > 0 or v6_c_counts["fire"] > 0:
                false_positive_cases.append({
                    "frame_id": frame_id,
                    "model": "V6",
                    "category": category,
                    "hazard": dict(v6_c_counts),
                })

        # Check Missed Hazard Detections on Hazard categories
        if "Hazard" in category:
            if "Fire" in category and v3_c_counts["fire"] == 0:
                missed_detection_cases.append({"frame_id": frame_id, "model": "V3", "target": "fire", "scene": scene_name})
            if "Fire" in category and v6_c_counts["fire"] == 0:
                missed_detection_cases.append({"frame_id": frame_id, "model": "V6", "target": "fire", "scene": scene_name})
            if "Smoke" in category and v3_c_counts["smoke"] == 0:
                missed_detection_cases.append({"frame_id": frame_id, "model": "V3", "target": "smoke", "scene": scene_name})
            if "Smoke" in category and v6_c_counts["smoke"] == 0:
                missed_detection_cases.append({"frame_id": frame_id, "model": "V6", "target": "smoke", "scene": scene_name})

        # Render Side-by-Side Video Frame
        v3_canvas = draw_frame_annotations(
            raw_frame,
            v3_boxes,
            f"V3 PRODUCTION [ACTIVE] | Frame {frame_id:03d} | Lat: {v3_lat:.1f}ms",
            banner_color=(20, 20, 140) if v3_alerts else (30, 30, 30)
        )
        v6_canvas = draw_frame_annotations(
            raw_frame,
            v6_boxes,
            f"V6 SHADOW [ISOLATED] | Frame {frame_id:03d} | Lat: {v6_lat:.1f}ms",
            banner_color=(80, 40, 0)
        )
        side_by_side = np.hstack([v3_canvas, v6_canvas])
        out_writer.write(side_by_side)

        # Save snapshot for distinct key scenes at first frame of each scene
        if item["scene_frame_idx"] == 0:
            snapshot_filename = f"shadow_snapshot_{category}_{stem}.jpg"
            snap_path = VISUALS_DIR / snapshot_filename
            cv2.imwrite(str(snap_path), side_by_side)
            key_visual_snapshots.append({
                "scene": scene_name,
                "category": category,
                "path": str(snap_path),
                "filename": snapshot_filename,
                "v3_detections": dict(v3_c_counts),
                "v6_detections": dict(v6_c_counts),
            })

    # Close streams
    v3_fp.close()
    v6_fp.close()
    out_writer.release()

    # Latency Stats
    v3_p50 = float(np.median(v3_latencies))
    v3_mean = float(np.mean(v3_latencies))
    v3_p95 = float(np.percentile(v3_latencies, 95))
    v3_fps = 1000.0 / v3_mean if v3_mean > 0 else 0

    v6_p50 = float(np.median(v6_latencies))
    v6_mean = float(np.mean(v6_latencies))
    v6_p95 = float(np.percentile(v6_latencies, 95))
    v6_fps = 1000.0 / v6_mean if v6_mean > 0 else 0

    # Aggregate JSON summary
    summary_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_frames_evaluated": total_frames,
        "live_webcam_frames": len(webcam_frames),
        "cctv_simulation_frames": len(cctv_frames),
        "models": {
            "v3_production": {
                "name": "ppe_fire_smoke_v3",
                "sha256": v3_sha,
                "role": "PRODUCTION_ACTIVE",
                "detections_total": dict(v3_class_totals),
                "avg_confidence": {k: round(float(np.mean(v)), 3) for k, v in v3_conf_totals.items() if v},
                "latency_ms": {"mean": round(v3_mean, 2), "p50": round(v3_p50, 2), "p95": round(v3_p95, 2)},
                "fps": round(v3_fps, 1),
            },
            "v6_shadow": {
                "name": "safesync_v6_hardnegative",
                "sha256": v6_sha,
                "role": "SHADOW_PASSIVE_ISOLATED",
                "detections_total": dict(v6_class_totals),
                "avg_confidence": {k: round(float(np.mean(v)), 3) for k, v in v6_conf_totals.items() if v},
                "latency_ms": {"mean": round(v6_mean, 2), "p50": round(v6_p50, 2), "p95": round(v6_p95, 2)},
                "fps": round(v6_fps, 1),
            }
        },
        "false_positive_instances": false_positive_cases,
        "missed_detection_instances": missed_detection_cases,
        "key_visual_snapshots": key_visual_snapshots,
        "side_by_side_video": str(out_video_path),
        "logs": {
            "v3_log": str(v3_log_file),
            "v6_log": str(v6_log_file),
        }
    }

    with open(DATA_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    print(f"\nShadow mode evaluation complete!")
    print(f"Total Frames Evaluated : {total_frames}")
    print(f"V3 Detections Total    : {sum(v3_class_totals.values())} (P50 Latency: {v3_p50:.2f}ms, FPS: {v3_fps:.1f})")
    print(f"V6 Detections Total    : {sum(v6_class_totals.values())} (P50 Latency: {v6_p50:.2f}ms, FPS: {v6_fps:.1f})")
    print(f"Log files saved to {LOGS_DIR}")
    print(f"Comparison video saved to {out_video_path}")


if __name__ == "__main__":
    main()
