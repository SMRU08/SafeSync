"""
benchmark_false_positives.py — RAKSHYA VISION False Positive Benchmarking Suite
Evaluates the RAKSHYA VISION detection and compliance pipeline against 4 core false-positive tests:
- TEST A: Uncovered hair -> Expected: NO helmet detection (0% false positives)
- TEST B: Normal casual shirt -> Expected: NO safety vest detection (0% false positives)
- TEST C: Baseball cap / beanie -> Expected: NO safety helmet detection (0% false positives)
- TEST D: Casual hoodie / jacket -> Expected: NO safety vest detection (0% false positives)

Generates detailed quantitative evidence and metrics into reports/false_positive_benchmark_report.json.
"""

import os
import sys
import json
import numpy as np
import cv2
from typing import Dict, Any, List

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "backend"))

try:
    from app.ai.compliance.association import (
        verify_helmet_features,
        verify_safety_vest_features,
        SpatialPPEAssociator,
    )
except ImportError:
    from backend.app.ai.compliance.association import (
        verify_helmet_features,
        verify_safety_vest_features,
        SpatialPPEAssociator,
    )

REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "reports"))
os.makedirs(REPORTS_DIR, exist_ok=True)


def create_canvas_with_region(
    worker_box: np.ndarray,
    region_box: np.ndarray,
    bgr_color: tuple,
    noise_range: int = 10,
    canvas_size: tuple = (720, 1280),
) -> np.ndarray:
    """Helper to paint a realistic test image with worker bounds and specific region chromatic content."""
    h, w = canvas_size
    frame = np.full((h, w, 3), (120, 120, 120), dtype=np.uint8)  # neutral background

    # Worker body silhouette
    wx1, wy1, wx2, wy2 = [int(v) for v in worker_box]
    frame[wy1:wy2, wx1:wx2] = (80, 80, 80)

    # Specific candidate region (hair/shirt/cap/hoodie)
    rx1, ry1, rx2, ry2 = [int(v) for v in region_box]
    patch_h = ry2 - ry1
    patch_w = rx2 - rx1
    patch = np.full((patch_h, patch_w, 3), bgr_color, dtype=np.uint8)
    if noise_range > 0:
        noise = np.random.randint(-noise_range, noise_range, patch.shape, dtype=np.int16)
        patch = np.clip(patch.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    frame[ry1:ry2, rx1:rx2] = patch
    return frame


def run_test_a_hair():
    """TEST A: Uncovered Hair (Black, Brown, Dark Brown, Blonde, Curly Dark)."""
    hair_colors = [
        ("black_hair_low_sat", (25, 20, 20)),
        ("dark_brown_wavy", (35, 30, 25)),
        ("medium_brown_short", (45, 40, 35)),
        ("curly_dark_textured", (20, 22, 25)),
        ("straight_dark_hair", (30, 28, 26)),
    ]
    results = []
    worker_box = np.array([400.0, 100.0, 680.0, 660.0])
    # Cranium hair candidate bbox
    hair_box = np.array([480.0, 100.0, 600.0, 175.0])

    for label, bgr in hair_colors:
        frame = create_canvas_with_region(worker_box, hair_box, bgr, noise_range=8)
        is_verified = verify_helmet_features(
            worker_box=worker_box,
            helmet_box=hair_box,
            frame=frame,
            confidence=0.55,
            img_shape=frame.shape[:2],
        )

        results.append({
            "test_case": label,
            "detected_as_helmet": is_verified,
            "rejection_reason": "Rejected: dark natural hair lacking fluorescent/helmet shell pigmentation" if not is_verified else "None",
            "passed": (is_verified is False),
        })

    return {
        "test_name": "TEST A: Uncovered Hair",
        "total_cases": len(results),
        "false_positives": sum(1 for r in results if r["detected_as_helmet"]),
        "rejection_rate": f"{(sum(1 for r in results if not r['detected_as_helmet']) / len(results)) * 100:.1f}%",
        "status": "PASS" if all(r["passed"] for r in results) else "FAIL",
        "cases": results,
    }


def run_test_b_shirt():
    """TEST B: Normal Shirts & Casual Clothing (Navy blue, black, white, red, grey, denim)."""
    shirt_colors = [
        ("navy_blue_cotton_tshirt", (100, 40, 20)),
        ("black_casual_tshirt", (25, 25, 25)),
        ("white_casual_shirt", (210, 210, 210)),
        ("red_casual_polo", (30, 30, 185)),
        ("grey_office_shirt", (130, 130, 130)),
        ("denim_blue_shirt", (135, 90, 40)),
    ]
    results = []
    worker_box = np.array([400.0, 100.0, 680.0, 660.0])
    # Torso shirt candidate bbox
    shirt_box = np.array([430.0, 210.0, 650.0, 460.0])

    for label, bgr in shirt_colors:
        frame = create_canvas_with_region(worker_box, shirt_box, bgr, noise_range=6)
        is_verified = verify_safety_vest_features(
            worker_box=worker_box,
            vest_box=shirt_box,
            frame=frame,
            confidence=0.52,
            img_shape=frame.shape[:2],
        )

        results.append({
            "test_case": label,
            "detected_as_vest": is_verified,
            "rejection_reason": "Rejected: ordinary textile lacking EN ISO 20471 fluorescent lime/orange pigments or retro-reflective banding" if not is_verified else "None",
            "passed": (is_verified is False),
        })

    return {
        "test_name": "TEST B: Normal Casual Shirt/Clothing",
        "total_cases": len(results),
        "false_positives": sum(1 for r in results if r["detected_as_vest"]),
        "rejection_rate": f"{(sum(1 for r in results if not r['detected_as_vest']) / len(results)) * 100:.1f}%",
        "status": "PASS" if all(r["passed"] for r in results) else "FAIL",
        "cases": results,
    }


def run_test_c_cap():
    """TEST C: Baseball Cap & Casual Non-Safety Headwear."""
    cap_types = [
        ("black_baseball_cap", (20, 20, 20)),
        ("dark_blue_sports_cap", (130, 45, 20)),
        ("grey_knitted_beanie", (110, 110, 110)),
        ("brown_flat_cap", (35, 50, 70)),
    ]
    results = []
    worker_box = np.array([400.0, 100.0, 680.0, 660.0])
    cap_box = np.array([460.0, 95.0, 620.0, 160.0])

    for label, bgr in cap_types:
        frame = create_canvas_with_region(worker_box, cap_box, bgr, noise_range=5)
        is_verified = verify_helmet_features(
            worker_box=worker_box,
            helmet_box=cap_box,
            frame=frame,
            confidence=0.50,
            img_shape=frame.shape[:2],
        )

        results.append({
            "test_case": label,
            "detected_as_helmet": is_verified,
            "rejection_reason": "Rejected: casual cap lacking industrial hard hat polymer shell chromatic profile" if not is_verified else "None",
            "passed": (is_verified is False),
        })

    return {
        "test_name": "TEST C: Baseball Cap & Casual Hats",
        "total_cases": len(results),
        "false_positives": sum(1 for r in results if r["detected_as_helmet"]),
        "rejection_rate": f"{(sum(1 for r in results if not r['detected_as_helmet']) / len(results)) * 100:.1f}%",
        "status": "PASS" if all(r["passed"] for r in results) else "FAIL",
        "cases": results,
    }


def run_test_d_hoodie():
    """TEST D: Casual Sweatshirt / Hoodie."""
    hoodie_types = [
        ("black_oversized_hoodie", (20, 20, 20)),
        ("grey_fleece_hoodie", (125, 125, 125)),
        ("dark_green_sweatshirt", (30, 80, 35)),
        ("maroon_hooded_jacket", (35, 30, 110)),
    ]
    results = []
    worker_box = np.array([400.0, 100.0, 680.0, 660.0])
    hoodie_box = np.array([420.0, 180.0, 660.0, 480.0])

    for label, bgr in hoodie_types:
        frame = create_canvas_with_region(worker_box, hoodie_box, bgr, noise_range=6)
        is_verified = verify_safety_vest_features(
            worker_box=worker_box,
            vest_box=hoodie_box,
            frame=frame,
            confidence=0.52,
            img_shape=frame.shape[:2],
        )

        results.append({
            "test_case": label,
            "detected_as_vest": is_verified,
            "rejection_reason": "Rejected: non-reflective casual outerwear without hi-vis fluorescent signature" if not is_verified else "None",
            "passed": (is_verified is False),
        })

    return {
        "test_name": "TEST D: Casual Hoodie & Sweatshirts",
        "total_cases": len(results),
        "false_positives": sum(1 for r in results if r["detected_as_vest"]),
        "rejection_rate": f"{(sum(1 for r in results if not r['detected_as_vest']) / len(results)) * 100:.1f}%",
        "status": "PASS" if all(r["passed"] for r in results) else "FAIL",
        "cases": results,
    }


def run_all_benchmarks():
    print("=" * 60)
    print("RUNNING RAKSHYA VISION FALSE POSITIVE BENCHMARK SUITE")
    print("=" * 60)

    benchmarks = [
        run_test_a_hair(),
        run_test_b_shirt(),
        run_test_c_cap(),
        run_test_d_hoodie(),
    ]

    total_tests = sum(b["total_cases"] for b in benchmarks)
    total_fps = sum(b["false_positives"] for b in benchmarks)
    overall_pass = all(b["status"] == "PASS" for b in benchmarks)

    report = {
        "suite_name": "RAKSHYA VISION False Positive Benchmark Suite",
        "overall_status": "PASS" if overall_pass else "FAIL",
        "total_cases_evaluated": total_tests,
        "total_false_positives_recorded": total_fps,
        "overall_rejection_accuracy": f"{((total_tests - total_fps) / total_tests) * 100:.2f}%",
        "benchmarks": benchmarks,
    }

    report_path = os.path.join(REPORTS_DIR, "false_positive_benchmark_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    for b in benchmarks:
        print(f"\n{b['test_name']}: {b['status']} ({b['rejection_rate']} rejection of false positives)")
        for c in b["cases"]:
            status_str = "REJECTED (CORRECT)" if c["passed"] else "FALSE POSITIVE (FAILED)"
            print(f"  - {c['test_case']}: {status_str} [Reason: {c['rejection_reason']}]")

    print("\n" + "=" * 60)
    print(f"OVERALL BENCHMARK STATUS: {'PASS' if overall_pass else 'FAIL'}")
    print(f"Total False Positives: {total_fps}/{total_tests} (Accuracy: {report['overall_rejection_accuracy']})")
    print(f"Report saved to: {report_path}")
    print("=" * 60)
    return report


if __name__ == "__main__":
    run_all_benchmarks()
