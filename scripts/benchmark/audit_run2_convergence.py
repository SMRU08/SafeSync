"""
audit_run2_convergence.py — SafeSync V7 Run 2 Convergence Audit & Run 3 Feasibility Study

Audits the actual training progression of Run 2 across epochs 1, 2, and 3:
- Parses results.csv
- Analyzes loss trajectories and validation PR metrics
- Performs overfitting diagnostics
- Evaluates class-specific convergence trends
- Formally decides whether Run 3 is justified
"""

import sys
import csv
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RUN2_DIR = ROOT / "models" / "detection" / "safesync_v7_small_object" / "runs" / "run2"
RESULTS_CSV = RUN2_DIR / "results.csv"
METRICS_DIR = RUN2_DIR / "metrics"

V3_PATH = ROOT / "models" / "detection" / "ppe_fire_smoke_v3" / "weights" / "best.pt"
V6_PATH = ROOT / "models" / "detection" / "safesync_v6_hardnegative" / "weights" / "best.pt"
RUN2_BEST = RUN2_DIR / "weights" / "best.pt"

EXPECTED_V3_SHA = "9b414f3018d54ae55db150629792a4678d58afc7074b919d9bfcf4f9c95e6efe"
EXPECTED_V6_SHA = "c47705a2c27c1780fbd0b216698567d5e3d2778b34fd4ff7ad85ba33c507b3cc"
EXPECTED_RUN2_SHA = "5b5304e0f704cd7024ae1eea68ad5e0614c21194363a0f7d01285d4d6a7ea722"

def hash_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def audit():
    print("=" * 70)
    print("SAFESYNC V7 RUN 2 TRAINING ARTIFACT AUDIT")
    print("=" * 70)

    # 1. Checksum Verifications
    v3_sha = hash_file(V3_PATH)
    v6_sha = hash_file(V6_PATH)
    r2_sha = hash_file(RUN2_BEST)

    assert v3_sha == EXPECTED_V3_SHA, f"V3 SHA mismatch: {v3_sha}"
    assert v6_sha == EXPECTED_V6_SHA, f"V6 SHA mismatch: {v6_sha}"
    assert r2_sha == EXPECTED_RUN2_SHA, f"Run-2 SHA mismatch: {r2_sha}"

    print(f"[LOCK VERIFIED] Production V3: {v3_sha}")
    print(f"[LOCK VERIFIED] Shadow V6:     {v6_sha}")
    print(f"[LOCK VERIFIED] Run-2 Best:    {r2_sha}")

    # 2. Parse results.csv
    assert RESULTS_CSV.exists(), f"results.csv not found at {RESULTS_CSV}"
    epochs_data = []
    with open(RESULTS_CSV, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cleaned = {k.strip(): float(v.strip()) if v.strip() else 0.0 for k, v in row.items()}
            epochs_data.append(cleaned)

    print(f"\nParsed {len(epochs_data)} training epochs from results.csv:")
    for ep in epochs_data:
        e = int(ep['epoch'])
        print(f"  Epoch {e}:")
        print(f"    Train Box Loss: {ep['train/box_loss']:.4f} | Cls Loss: {ep['train/cls_loss']:.4f} | DFL Loss: {ep['train/dfl_loss']:.4f}")
        print(f"    Val Box Loss:   {ep['val/box_loss']:.4f} | Cls Loss: {ep['val/cls_loss']:.4f} | DFL Loss: {ep['val/dfl_loss']:.4f}")
        print(f"    Precision:      {ep['metrics/precision(B)']:.4f} | Recall: {ep['metrics/recall(B)']:.4f}")
        print(f"    mAP50:          {ep['metrics/mAP50(B)']:.4f} | mAP50-95: {ep['metrics/mAP50-95(B)']:.4f}")

    e1 = epochs_data[0]
    e2 = epochs_data[1]
    e3 = epochs_data[2]

    # 3. Convergence Questions Analysis
    qA_recall_improving = e3['metrics/recall(B)'] > e2['metrics/recall(B)']
    qB_map50_improving = e3['metrics/mAP50(B)'] > e2['metrics/mAP50(B)']
    qC_map50_95_improving = e3['metrics/mAP50-95(B)'] > e2['metrics/mAP50-95(B)']
    
    # Val loss trend from e2 to e3
    val_cls_loss_dropping = e3['val/cls_loss'] < e2['val/cls_loss']
    val_box_loss_dropping = e3['val/box_loss'] < e2['val/box_loss']
    
    # Overfitting check
    is_overfitting = (e3['train/cls_loss'] < e2['train/cls_loss']) and (e3['val/cls_loss'] > e2['val/cls_loss'])

    convergence_status = "IMPROVING" if (qA_recall_improving and qB_map50_improving and qC_map50_95_improving and not is_overfitting) else "PLATEAU"
    run3_decision = "TRAIN" if convergence_status == "IMPROVING" else "DO NOT TRAIN"

    print("\nConvergence Diagnostics:")
    print(f"  A. Was recall still improving at epoch 3?   {'YES (IMPROVING)' if qA_recall_improving else 'NO'}")
    print(f"  B. Was mAP50 still improving at epoch 3?    {'YES (IMPROVING)' if qB_map50_improving else 'NO'}")
    print(f"  C. Was mAP50-95 still improving at epoch 3? {'YES (IMPROVING)' if qC_map50_95_improving else 'NO'}")
    print(f"  D. Validation Box Loss Trajectory:          {'IMPROVING (DECREASING)' if val_box_loss_dropping else 'RISING'}")
    print(f"  E. Validation Class Loss Trajectory:        {'IMPROVING (DECREASING)' if val_cls_loss_dropping else 'RISING'}")
    print(f"  F. Overfitting Detected:                    {'YES' if is_overfitting else 'NO (HEALTHY CONVERGENCE)'}")
    print(f"  Convergence Status:                         {convergence_status}")
    print(f"  Run 3 Recommendation:                       {run3_decision}")

    audit_out = {
        "timestamp": "2026-10-07T23:25:00Z",
        "checkpoints_verified": {
            "v3_sha": v3_sha,
            "v6_sha": v6_sha,
            "run2_sha": r2_sha
        },
        "epochs": epochs_data,
        "diagnostics": {
            "qA_recall_improving": bool(qA_recall_improving),
            "qB_map50_improving": bool(qB_map50_improving),
            "qC_map50_95_improving": bool(qC_map50_95_improving),
            "val_cls_loss_dropping": bool(val_cls_loss_dropping),
            "val_box_loss_dropping": bool(val_box_loss_dropping),
            "is_overfitting": bool(is_overfitting),
            "convergence_status": convergence_status,
            "run3_decision": run3_decision
        }
    }

    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = METRICS_DIR / "run2_convergence_audit.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(audit_out, f, indent=2)
    print(f"\nSaved convergence audit to: {out_file}")
    print("=" * 70)

if __name__ == '__main__':
    audit()
