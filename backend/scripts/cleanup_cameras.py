"""
cleanup_cameras.py — SafeSync Camera Surveillance Matrix Sanitizer
Validates all registered cameras, pings connections, and cleans up false or broken entries.
"""

import sys
import os
import logging

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cleanup_cameras")


def main():
    from app.camera.manager import CameraManager

    logger.info("Initializing SafeSync CameraManager for cleanup...")
    manager = CameraManager.get_instance()
    logger.info("Evaluating %d registered camera configurations...", len(manager.configs))

    results = manager.validate_and_cleanup_cameras(remove_broken=True)

    print("\n" + "=" * 60)
    print("SAFESYNC CAMERA MATRIX CLEANUP REPORT")
    print("=" * 60)
    print(f"Total Evaluated: {results['total_evaluated']}")
    print(f"Verified Active: {results['verified_active']}")
    print(f"Cleaned/Removed: {results['cleaned_removed']}")
    print("\nActions Taken:")
    for entry in results.get("report", []):
        cid = entry.get("camera_id")
        action = entry.get("action") or entry.get("status")
        reason = entry.get("reason") or entry.get("details") or entry.get("error") or ""
        print(f" - [{action}] {cid}: {reason}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
