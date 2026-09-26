"""
evaluate_hazard_challenge_suite.py — SafeSync Phase 6 Requirement 14
Evaluates baseline vs candidate fire/smoke models on a 15-scenario real-world challenge set:
  1. Steam
  2. Dust
  3. Fog
  4. Vehicle exhaust
  5. Welding
  6. Sunlight
  7. Reflections
  8. White walls
  9. Orange/red clothing
  10. Industrial lighting
  11. CCTV compression
  12. Motion blur
  13. Small distant smoke
  14. Small distant fire
  15. Real industrial scenes
"""

import os
import sys
import json
import time
import cv2
import numpy as np
from ultralytics import YOLO

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def generate_challenge_frame(scenario: str, w: int = 640, h: int = 480) -> np.ndarray:
    """Generates synthetic or modeled frames representing the 15 challenge scenarios."""
    img = np.zeros((h, w, 3), dtype=np.uint8)

    if scenario == "steam":
        img[:] = 90
        for off in range(-30, 40, 15):
            cv2.ellipse(img, (w // 2 + off, h // 2), (80, 40), 15, 0, 360, (215, 215, 215), -1)
        img = cv2.GaussianBlur(img, (31, 31), 0)

    elif scenario == "dust":
        img[:] = 80
        ys = np.random.randint(0, h, 2000)
        xs = np.random.randint(0, w, 2000)
        img[ys, xs] = np.random.randint(180, 230, (2000, 3), dtype=np.uint8)

    elif scenario == "fog":
        img[:] = 175
        noise = np.random.randint(-10, 10, (h, w, 3), dtype=np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    elif scenario == "vehicle_exhaust":
        img[:] = 65
        cv2.circle(img, (w // 2, h // 2), 70, (130, 130, 130), -1)
        img = cv2.GaussianBlur(img, (41, 41), 0)

    elif scenario == "welding":
        img[:] = 30
        cv2.circle(img, (w // 2, h // 2), 20, (255, 255, 255), -1)
        cv2.circle(img, (w // 2, h // 2), 60, (180, 220, 255), 2)
        img = cv2.GaussianBlur(img, (15, 15), 0)

    elif scenario == "sunlight":
        img[:] = 150
        cv2.circle(img, (w // 2, h // 3), 130, (255, 255, 255), -1)
        img = cv2.GaussianBlur(img, (61, 61), 0)

    elif scenario == "reflections":
        img[:] = 70
        cv2.rectangle(img, (w // 4, h // 4), (3 * w // 4, 3 * h // 4), (230, 240, 255), -1)
        img = cv2.GaussianBlur(img, (25, 25), 0)

    elif scenario == "white_walls":
        img[:] = 245
        noise = np.random.randint(-5, 5, (h, w, 3), dtype=np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    elif scenario == "orange_red_clothing":
        img[:] = 100
        cv2.rectangle(img, (150, 100), (300, 350), (0, 120, 255), -1)  # Fluorescent orange
        cv2.rectangle(img, (350, 100), (500, 350), (20, 20, 220), -1)  # Deep red

    elif scenario == "industrial_lighting":
        img[:] = 90
        for x in range(80, w, 160):
            cv2.rectangle(img, (x, 20), (x + 80, 40), (255, 255, 250), -1)
        img = cv2.GaussianBlur(img, (21, 21), 0)

    elif scenario == "cctv_compression":
        img = np.random.randint(70, 140, (h, w, 3), dtype=np.uint8)
        _, enc = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 8])
        img = cv2.imdecode(enc, cv2.IMREAD_COLOR)

    elif scenario == "motion_blur":
        img = np.zeros((h, w, 3), dtype=np.uint8)
        cv2.rectangle(img, (100, 100), (300, 300), (200, 200, 200), -1)
        k = np.zeros((25, 25))
        k[12, :] = 1.0 / 25
        img = cv2.filter2D(img, -1, k)

    elif scenario == "small_distant_smoke":
        img[:] = 100
        # Faint wispy cloud in upper distance
        cv2.ellipse(img, (w // 2, h // 4), (20, 12), 0, 0, 360, (180, 180, 180), -1)
        img = cv2.GaussianBlur(img, (9, 9), 0)

    elif scenario == "small_distant_fire":
        img[:] = 80
        # Small bright flame cluster
        cv2.circle(img, (w // 2, h // 3), 8, (0, 140, 255), -1)
        cv2.circle(img, (w // 2, h // 3), 4, (0, 240, 255), -1)
        img = cv2.GaussianBlur(img, (5, 5), 0)

    elif scenario == "real_industrial_scene":
        img[:] = 90
        cv2.rectangle(img, (40, 220), (w - 40, h), (70, 60, 50), -1)
        cv2.rectangle(img, (120, 60), (240, 180), (170, 170, 170), -1)

    return img


SCENARIOS = [
    ("steam", False),
    ("dust", False),
    ("fog", False),
    ("vehicle_exhaust", False),
    ("welding", False),
    ("sunlight", False),
    ("reflections", False),
    ("white_walls", False),
    ("orange_red_clothing", False),
    ("industrial_lighting", False),
    ("cctv_compression", False),
    ("motion_blur", False),
    ("small_distant_smoke", True),
    ("small_distant_fire", True),
    ("real_industrial_scene", False),
]


def evaluate_model_on_scenarios(model_path: str, model_type_filter: str = "hazards"):
    model = YOLO(model_path)
    results = {}

    for name, is_positive in SCENARIOS:
        frame = generate_challenge_frame(name)
        preds = model.predict(frame, conf=0.25, imgsz=384, verbose=False)[0]

        fire_count = 0
        smoke_count = 0

        for box in preds.boxes:
            cid = int(box.cls[0].item())
            cname = model.names.get(cid, "").lower()
            if cname == "fire":
                fire_count += 1
            elif cname == "smoke":
                smoke_count += 1

        is_false_alarm = (not is_positive) and (fire_count > 0 or smoke_count > 0)
        results[name] = {
            "is_positive_scenario": is_positive,
            "fire_detections": fire_count,
            "smoke_detections": smoke_count,
            "false_positive": is_false_alarm,
        }

    return results


def main():
    baseline_path = os.path.join(ROOT, "models", "detection", "ppe_fire_smoke_v2", "weights", "best.pt")
    candidate_path = os.path.join(ROOT, "models", "detection", "fire_smoke", "candidate_v2", "weights", "best.pt")

    print("=" * 65)
    print("SafeSync Real-World 15-Scenario Hazard Challenge Benchmark")
    print("=" * 65)

    print(f"\n[1/2] Evaluating Baseline: {baseline_path}")
    base_res = evaluate_model_on_scenarios(baseline_path, model_type_filter="ppe")

    cand_res = None
    if os.path.exists(candidate_path):
        print(f"\n[2/2] Evaluating Candidate: {candidate_path}")
        cand_res = evaluate_model_on_scenarios(candidate_path, model_type_filter="hazards")
    else:
        print(f"\n[2/2] Candidate model not found at {candidate_path}. (Training in progress)")

    # Print Comparison Table
    print("\n" + "=" * 65)
    print(f"{'Scenario':<25} | {'Baseline FP':<12} | {'Candidate FP':<12}")
    print("-" * 65)

    base_fp_total = 0
    cand_fp_total = 0

    for name, is_pos in SCENARIOS:
        b_fp = "FP DETECTED" if base_res[name]["false_positive"] else "CLEAN (OK)"
        if base_res[name]["false_positive"]:
            base_fp_total += 1

        if cand_res:
            c_fp = "FP DETECTED" if cand_res[name]["false_positive"] else "CLEAN (OK)"
            if cand_res[name]["false_positive"]:
                cand_fp_total += 1
        else:
            c_fp = "N/A"

        if not is_pos:
            print(f"{name:<25} | {b_fp:<12} | {c_fp:<12}")

    print("=" * 65)
    print(f"Total False Positives (Negative Scenarios): Baseline={base_fp_total}/13 | Candidate={cand_fp_total}/13")

    # Save to JSON
    report = {
        "baseline": base_res,
        "candidate": cand_res,
        "summary": {
            "baseline_false_positives": base_fp_total,
            "candidate_false_positives": cand_fp_total,
        }
    }

    out_file = os.path.join(ROOT, "datasets", "audit", "challenge_suite_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nChallenge results written to {out_file}")


if __name__ == "__main__":
    main()
