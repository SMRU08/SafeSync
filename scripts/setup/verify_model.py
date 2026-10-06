"""
scripts/setup/verify_model.py — SafeSync Production Model Setup & Verification Tool
==================================================================================
Verifies the existence and cryptographic SHA-256 integrity of the validated
SafeSync V3 production model weights on any cloned workstation.

Target Model:
  models/detection/ppe_fire_smoke_v3/weights/best.pt

Expected SHA-256 Checksum:
  9b414f3018d54ae55db150629792a4678d58afc7074b919d9bfcf4f9c95e6efe
==================================================================================
"""

import os
import sys
import hashlib
from pathlib import Path

# Resolve project root portably
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

EXPECTED_SHA256 = "9b414f3018d54ae55db150629792a4678d58afc7074b919d9bfcf4f9c95e6efe"
RELATIVE_MODEL_PATH = "models/detection/ppe_fire_smoke_v3/weights/best.pt"
ABSOLUTE_MODEL_PATH = PROJECT_ROOT / Path(RELATIVE_MODEL_PATH)


def compute_sha256(filepath: Path) -> str:
    """Computes SHA-256 hash in chunks."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def verify_model() -> bool:
    print("=" * 70)
    print("SAFESYNC — PRODUCTION MODEL SETUP & INTEGRITY VERIFICATION")
    print("=" * 70)
    print(f"Project Root:         {PROJECT_ROOT}")
    print(f"Target Relative Path: {RELATIVE_MODEL_PATH}")
    print(f"Resolved Local Path:  {ABSOLUTE_MODEL_PATH}")
    print(f"Expected SHA-256:     {EXPECTED_SHA256}")
    print("-" * 70)

    if not ABSOLUTE_MODEL_PATH.exists():
        print("[FAIL] MODEL FILE NOT FOUND!")
        print(f"\nThe required model file is missing at:")
        print(f"  {ABSOLUTE_MODEL_PATH}")
        print("\nSETUP INSTRUCTIONS FOR CLONED REPOSITORY:")
        print("  1. Obtain the SafeSync V3 production weights file ('best.pt').")
        print(f"  2. Create the destination directory if not present:")
        print(f"       mkdir -p {ABSOLUTE_MODEL_PATH.parent}")
        print(f"  3. Place 'best.pt' at:")
        print(f"       {RELATIVE_MODEL_PATH}")
        print("  4. Re-run this verification script:")
        print("       python scripts/setup/verify_model.py")
        print("=" * 70)
        return False

    size_bytes = ABSOLUTE_MODEL_PATH.stat().st_size
    print(f"Model File Found:     YES ({size_bytes:,} bytes)")

    print("Computing SHA-256 checksum...")
    actual_sha256 = compute_sha256(ABSOLUTE_MODEL_PATH)
    print(f"Actual SHA-256:       {actual_sha256}")

    if actual_sha256 != EXPECTED_SHA256:
        print("\n[FAIL] CHECKSUM MISMATCH!")
        print(f"  Expected: {EXPECTED_SHA256}")
        print(f"  Actual:   {actual_sha256}")
        print("The file at this path is not the validated SafeSync V3 production model.")
        print("Please replace it with the correct weights file.")
        print("=" * 70)
        return False

    print("\n[SUCCESS] SHA-256 INTEGRITY VERIFIED!")
    print("SafeSync V3 production model is ready for real-time AI inference.")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = verify_model()
    sys.exit(0 if success else 1)
