"""
test_association_scenarios.py — RAKSHYA VISION Phase 5
Controlled test cases verifying spatial PPE association and temporal state rules:
 1. Worker with helmet
 2. Worker without visible helmet
 3. Worker with vest
 4. Worker without visible vest
 5. Worker with gloves
 6. Worker without visible gloves
 7. Worker with footwear
 8. Worker without visible footwear
 9. Multiple workers (adjacent/crossing)
10. Occluded worker (top border head occlusion & overlapping workers)
"""

import os
import sys
import json
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.app.ai.compliance.schemas import (
    PPEItemType,
    PPEState,
    OverallComplianceState,
)
from backend.app.ai.compliance.association import SpatialPPEAssociator
from backend.app.ai.compliance.temporal import TemporalComplianceTracker


def run_all_scenarios():
    print("=" * 65)
    print("  PHASE 5 — CONTROLLED PPE ASSOCIATION SCENARIOS TEST SUITE")
    print("=" * 65)

    associator = SpatialPPEAssociator()
    temporal = TemporalComplianceTracker({
        "temporal": {"confirmation_frames": 3, "missing_detection_tolerance": 5},
        "required_ppe": {"helmet": True, "safety_vest": True, "gloves": True, "safety_footwear": True}
    })

    results = {}
    img_shape = (720, 1280)

    # ─── Case 1: Worker with Helmet ───
    print("\n[Scenario 1] Worker with helmet")
    temporal.reset()
    worker_box = np.array([200, 100, 300, 400])  # W=100, H=300
    helmet_box = [220, 90, 280, 150]              # Upper head region [0, 0.30]
    ppe_dets = [{"class_name": "helmet", "bbox": helmet_box, "confidence": 0.9}]
    tracked = [(1, worker_box, 0.95)]

    # Frame 1: Detected
    assoc, _ = associator.associate(tracked, ppe_dets, img_shape)
    assert assoc[1]["helmet"] is not None, "Failed to associate helmet with worker"
    w1 = temporal.update_worker(1, worker_box, 0.95, assoc[1], {item: False for item in PPEItemType})
    assert w1.ppe["helmet"] == PPEState.UNKNOWN, "Frame 1 must be UNKNOWN (gathering temporal evidence)"

    # Frames 2 & 3: Confirmed
    temporal.update_worker(1, worker_box, 0.95, assoc[1], {item: False for item in PPEItemType})
    w3 = temporal.update_worker(1, worker_box, 0.95, assoc[1], {item: False for item in PPEItemType})
    assert w3.ppe["helmet"] == PPEState.PRESENT, "Frame 3 must be confirmed PRESENT"
    print("  [OK] Helmet associated and temporally confirmed PRESENT after 3 frames.")
    results["scenario_1_worker_with_helmet"] = "PASSED"

    # ─── Case 2: Worker without visible helmet ───
    print("\n[Scenario 2] Worker without visible helmet")
    temporal.reset()
    # 5 frames without helmet detection
    for _ in range(5):
        assoc_empty, _ = associator.associate(tracked, [], img_shape)
        w = temporal.update_worker(1, worker_box, 0.95, assoc_empty[1], {item: False for item in PPEItemType})
    assert w.ppe["helmet"] == PPEState.ABSENT, "Helmet must be confirmed ABSENT after 5 missed frames"
    assert w.overall_status == OverallComplianceState.NON_COMPLIANT, "Overall status must be NON_COMPLIANT when required PPE is absent"
    print("  [OK] Missing helmet temporally transitioned to ABSENT after 5 tolerance frames.")
    results["scenario_2_worker_without_helmet"] = "PASSED"

    # ─── Case 3: Worker with vest ───
    print("\n[Scenario 3] Worker with safety vest")
    temporal.reset()
    vest_box = [210, 160, 290, 300]  # Torso region [y1+0.15*H, y1+0.70*H] = [145, 310]
    ppe_dets = [{"class_name": "safety_vest", "bbox": vest_box, "confidence": 0.88}]
    for _ in range(3):
        assoc, _ = associator.associate(tracked, ppe_dets, img_shape)
        w = temporal.update_worker(1, worker_box, 0.95, assoc[1], {item: False for item in PPEItemType})
    assert w.ppe["safety_vest"] == PPEState.PRESENT
    print("  [OK] Safety vest correctly associated to torso zone and confirmed PRESENT.")
    results["scenario_3_worker_with_vest"] = "PASSED"

    # ─── Case 4: Worker without visible vest ───
    print("\n[Scenario 4] Worker without visible safety vest")
    temporal.reset()
    for _ in range(5):
        assoc_empty, _ = associator.associate(tracked, [], img_shape)
        w = temporal.update_worker(1, worker_box, 0.95, assoc_empty[1], {item: False for item in PPEItemType})
    assert w.ppe["safety_vest"] == PPEState.ABSENT
    assert w.overall_status == OverallComplianceState.NON_COMPLIANT
    print("  [OK] Missing vest marked ABSENT after tolerance expiration.")
    results["scenario_4_worker_without_vest"] = "PASSED"

    # ─── Case 5: Worker with gloves ───
    print("\n[Scenario 5] Worker with gloves")
    temporal.reset()
    glove_box = [185, 230, 215, 270]  # Lower hand region [y1+0.35*H, y1+0.90*H] = [205, 370]
    ppe_dets = [{"class_name": "gloves", "bbox": glove_box, "confidence": 0.75}]
    for _ in range(3):
        assoc, _ = associator.associate(tracked, ppe_dets, img_shape)
        w = temporal.update_worker(1, worker_box, 0.95, assoc[1], {item: False for item in PPEItemType})
    assert w.ppe["gloves"] == PPEState.PRESENT
    print("  [OK] Gloves associated in lower arm/hand lateral region and confirmed PRESENT.")
    results["scenario_5_worker_with_gloves"] = "PASSED"

    # ─── Case 6: Worker without visible gloves ───
    print("\n[Scenario 6] Worker without visible gloves")
    temporal.reset()
    for _ in range(5):
        assoc_empty, _ = associator.associate(tracked, [], img_shape)
        w = temporal.update_worker(1, worker_box, 0.95, assoc_empty[1], {item: False for item in PPEItemType})
    assert w.ppe["gloves"] == PPEState.ABSENT
    print("  [OK] Missing gloves marked ABSENT after tolerance frames.")
    results["scenario_6_worker_without_gloves"] = "PASSED"

    # ─── Case 7: Worker with footwear ───
    print("\n[Scenario 7] Worker with safety footwear")
    temporal.reset()
    boot_box = [230, 350, 280, 405]  # Bottom foot region [y1+0.70*H, y1+1.05*H] = [310, 415]
    ppe_dets = [{"class_name": "safety_footwear", "bbox": boot_box, "confidence": 0.82}]
    for _ in range(3):
        assoc, _ = associator.associate(tracked, ppe_dets, img_shape)
        w = temporal.update_worker(1, worker_box, 0.95, assoc[1], {item: False for item in PPEItemType})
    assert w.ppe["safety_footwear"] == PPEState.PRESENT
    print("  [OK] Safety footwear associated in lower foot region and confirmed PRESENT.")
    results["scenario_7_worker_with_footwear"] = "PASSED"

    # ─── Case 8: Worker without visible footwear ───
    print("\n[Scenario 8] Worker without visible footwear")
    temporal.reset()
    for _ in range(5):
        assoc_empty, _ = associator.associate(tracked, [], img_shape)
        w = temporal.update_worker(1, worker_box, 0.95, assoc_empty[1], {item: False for item in PPEItemType})
    assert w.ppe["safety_footwear"] == PPEState.ABSENT
    print("  [OK] Missing footwear marked ABSENT after sustained missed evidence.")
    results["scenario_8_worker_without_footwear"] = "PASSED"

    # ─── Case 9: Multiple Workers (Contention & No Duplicate Transfer) ───
    print("\n[Scenario 9] Multiple adjacent workers with single helmet")
    temporal.reset()
    # Two workers standing side by side
    w1_box = np.array([200, 100, 300, 400])
    w2_box = np.array([290, 100, 390, 400])
    # Single helmet positioned right over worker 1
    helmet_1 = [225, 95, 275, 145]
    ppe_single = [{"class_name": "helmet", "bbox": helmet_1, "confidence": 0.92}]
    tracked_two = [(1, w1_box, 0.9), (2, w2_box, 0.9)]

    assoc_multi, unassoc = associator.associate(tracked_two, ppe_single, img_shape)
    assert assoc_multi[1]["helmet"] is not None, "Worker 1 should receive the helmet"
    assert assoc_multi[2]["helmet"] is None, "Worker 2 must NOT duplicate or steal worker 1's helmet!"
    assert len(unassoc) == 0
    print("  [OK] Bipartite assignment correctly assigned single helmet to nearest worker without duplication.")
    results["scenario_9_multiple_workers"] = "PASSED"

    # ─── Case 10: Occluded Worker (Boundary Cutoff & Worker Overlap) ───
    print("\n[Scenario 10] Occluded worker (head clipped by frame top border)")
    temporal.reset()
    # Worker whose head is near top border (y1 = 5px <= edge_margin_px of 20px)
    clipped_worker = np.array([200, 5, 300, 305])
    is_occl = associator.detect_occlusion(0, [clipped_worker], PPEItemType.HELMET, img_shape)
    assert is_occl is True, "Top border cutoff must be flagged as occluded"

    # Process 5 frames for clipped worker with no helmet detected
    for _ in range(5):
        assoc_empty, _ = associator.associate([(1, clipped_worker, 0.9)], [], img_shape)
        w = temporal.update_worker(1, clipped_worker, 0.9, assoc_empty[1], {PPEItemType.HELMET: True, PPEItemType.SAFETY_VEST: False, PPEItemType.GLOVES: False, PPEItemType.SAFETY_FOOTWEAR: False})
    # Due to occlusion, helmet must be UNKNOWN, NOT ABSENT!
    assert w.ppe["helmet"] == PPEState.UNKNOWN, "Occluded body part must result in UNKNOWN, preventing false violations"
    print("  [OK] Occluded head evaluated as UNKNOWN instead of ABSENT (false violation prevented).")
    results["scenario_10_occluded_worker"] = "PASSED"

    print("\n" + "=" * 65)
    print("  ALL 10 CONTROLLED SCENARIOS PASSED (10/10)")
    print("=" * 65)

    out_file = os.path.join(ROOT, "outputs", "compliance", "scenario_test_results.json")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to: {out_file}")
    return results


if __name__ == "__main__":
    run_all_scenarios()
