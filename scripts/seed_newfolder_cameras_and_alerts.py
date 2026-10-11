"""
scripts/seed_newfolder_cameras_and_alerts.py
============================================
Registers the 7 new annotated videos from 'D:\\Additional\\New folder (2)\\output'
as additional Surveillance Cameras in configs/cameras.yaml and the SafeSync
database, and seeds real PPE-violation / hazard alerts from the batch summaries.

Preserves ALL existing cameras in cameras.yaml (does NOT overwrite).
"""

import os
import sys
import json
import yaml
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.database.session import SessionLocal
from app.models.camera import CameraModel
from app.models.risk_alert import Incident, Alert, AlertHistory

NEWFOLDER_VIDEOS_DIR = Path(r"D:\Additional\New folder (2)\output\annotated_videos")
NEWFOLDER_REPORTS_DIR = Path(r"D:\Additional\New folder (2)\output\reports")
CONFIGS_CAMERAS_YAML = ROOT / "configs" / "cameras.yaml"

# Metadata for each new camera — zone and location chosen from incident content
VIDEO_METADATA = [
    {
        "cam_id": "cam_new_01",
        "cam_num": 19,
        "stem": "VID_20261009_131951",
        "name": "CAM-19 • Yard Gate Entry Check",
        "zone_id": "entry_gate",
        "location": "Exterior Site Gate A",
    },
    {
        "cam_id": "cam_new_02",
        "cam_num": 20,
        "stem": "VID_20261009_133226",
        "name": "CAM-20 • Logistics Staging Area",
        "zone_id": "loading_dock",
        "location": "Cargo Staging Bay 3",
    },
    {
        "cam_id": "cam_new_03",
        "cam_num": 21,
        "stem": "VID_20261009_133238",
        "name": "CAM-21 • Electrical Sub-Panel Room",
        "zone_id": "electrical_room",
        "location": "Secondary Substation East",
    },
    {
        "cam_id": "cam_new_04",
        "cam_num": 22,
        "stem": "VID_20261009_133245",
        "name": "CAM-22 • Assembly Compliance Station",
        "zone_id": "production_floor",
        "location": "Electronics Assembly Bay 4",
    },
    {
        "cam_id": "cam_new_05",
        "cam_num": 23,
        "stem": "VID_20261009_133302",
        "name": "CAM-23 • Perimeter Safety Patrol",
        "zone_id": "general_facility",
        "location": "Outdoor Perimeter Route B",
    },
    {
        "cam_id": "cam_new_06",
        "cam_num": 24,
        "stem": "VID_20261009_134021",
        "name": "CAM-24 • Workshop Tool Station",
        "zone_id": "production_floor",
        "location": "Mechanical Workshop Bay 5",
    },
    {
        "cam_id": "cam_new_07",
        "cam_num": 25,
        "stem": "VID_20261009_230104",
        "name": "CAM-25 • Night-Shift Overview",
        "zone_id": "general_facility",
        "location": "Facility Wide-Angle Night View",
    },
]


def seed():
    print("=" * 80)
    print("SafeSync — Seeding New Folder Videos as Surveillance Cameras with Alerts")
    print("=" * 80)

    seeded_alerts_count = 0
    seeded_incidents_count = 0
    new_yaml_cameras = []

    with SessionLocal() as db:
        for item in VIDEO_METADATA:
            cid = item["cam_id"]
            stem = item["stem"]
            cname = item["name"]
            zone_id = item["zone_id"]
            location = item["location"]

            video_file = NEWFOLDER_VIDEOS_DIR / f"{stem}_annotated.mp4"
            summary_file = NEWFOLDER_REPORTS_DIR / f"{stem}_summary.json"

            if not video_file.exists():
                print(f"[WARN] Video not found: {video_file}")
                continue

            summary_data = {}
            if summary_file.exists():
                try:
                    with open(summary_file, "r", encoding="utf-8") as sf:
                        summary_data = json.load(sf)
                except Exception as e:
                    print(f"[WARN] Could not parse {summary_file}: {e}")

            fps = summary_data.get("original_fps", 30)
            res = summary_data.get("resolution", "1080x1920")
            incidents = summary_data.get("incidents", [])
            haz_fire = summary_data.get("detections", {}).get("fire", 0)
            haz_smoke = summary_data.get("detections", {}).get("smoke", 0)

            # Build YAML entry
            yaml_item = {
                "id": cid,
                "name": cname,
                "zone_id": zone_id,
                "location": location,
                "source": str(video_file),
                "source_type": "file",
                "enabled": True,
                "fps_target": int(fps) if fps else 30,
                "resolution": res,
                "timeout_seconds": 5.0,
                "speaker_enabled": True,
                "reconnect_policy": {
                    "max_retries": 10,
                    "initial_delay_seconds": 0.5,
                    "max_delay_seconds": 5.0,
                },
            }
            new_yaml_cameras.append(yaml_item)

            # Upsert Camera in DB
            db_cam = db.query(CameraModel).filter_by(camera_id=cid).first()
            if not db_cam:
                db_cam = CameraModel(
                    camera_id=cid,
                    name=cname,
                    location=location,
                    zone_id=zone_id,
                    source=str(video_file),
                    source_type="file",
                    enabled=True,
                    fps_target=int(fps) if fps else 30,
                    resolution=res,
                    timeout_seconds=5.0,
                    speaker_enabled=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(db_cam)
            else:
                db_cam.name = cname
                db_cam.location = location
                db_cam.zone_id = zone_id
                db_cam.source = str(video_file)
                db_cam.source_type = "file"
                db_cam.enabled = True
                db_cam.fps_target = int(fps) if fps else 30
                db_cam.resolution = res
                db_cam.updated_at = datetime.now(timezone.utc)
            db.commit()

            # Seed Incidents & Alerts
            for inc_idx, inc in enumerate(incidents, start=1):
                inc_id = f"INC-{cid}-{inc_idx:03d}"
                alt_id = f"ALT-{cid}-{inc_idx:03d}"
                missing = inc.get("missing_equipment", [])
                wid = inc.get("worker_id", 1)
                missing_str = ", ".join(missing) if missing else "Required PPE"
                ts = inc.get("start_timestamp", "00:00")

                # Determine event_type from missing items
                if "helmet" in missing:
                    event_type = "MISSING_HELMET"
                    severity = "CRITICAL"
                elif "safety_vest" in missing:
                    event_type = "MISSING_SAFETY_VEST"
                    severity = "HIGH"
                elif "gloves" in missing:
                    event_type = "MISSING_GLOVES"
                    severity = "HIGH"
                elif "safety_footwear" in missing:
                    event_type = "MISSING_FOOTWEAR"
                    severity = "MEDIUM"
                else:
                    event_type = "MISSING_PPE"
                    severity = "HIGH"

                # Multiple missing → escalate severity
                if len(missing) >= 3:
                    severity = "CRITICAL"
                    event_type = "MISSING_PPE"

                existing_inc = db.query(Incident).filter_by(incident_id=inc_id).first()
                if not existing_inc:
                    new_inc = Incident(
                        incident_id=inc_id,
                        status="OPEN",
                        event_types=event_type,
                        camera_id=cid,
                        zone_id=zone_id,
                        affected_tracks=json.dumps([wid]),
                        risk_score=90 if severity == "CRITICAL" else 75,
                        risk_level=severity,
                        factors_json=json.dumps({
                            "missing": missing,
                            "worker_id": wid,
                            "timestamp": ts,
                            "duration_sec": inc.get("duration_sec", 0),
                        }),
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                    db.add(new_inc)
                    seeded_incidents_count += 1

                existing_alt = db.query(Alert).filter_by(alert_id=alt_id).first()
                if not existing_alt:
                    new_alt = Alert(
                        alert_id=alt_id,
                        incident_id=inc_id,
                        severity=severity,
                        title=f"PPE Violation: Missing {missing_str.title()}",
                        message=(
                            f"Worker #{wid} at {ts} in {location} ({cname}) — "
                            f"confirmed missing: {missing_str}."
                        ),
                        camera_id=cid,
                        zone_id=zone_id,
                        event_type=event_type,
                        status="ACTIVE",
                        created_at=datetime.now(timezone.utc),
                    )
                    db.add(new_alt)
                    seeded_alerts_count += 1

            # Hazard alerts (fire/smoke)
            if haz_smoke > 0 or haz_fire > 0:
                haz_inc_id = f"INC-{cid}-HAZ-001"
                haz_alt_id = f"ALT-{cid}-HAZ-001"
                haz_type = "SMOKE_DETECTED" if haz_smoke > 0 else "FIRE_DETECTED"
                existing_hinc = db.query(Incident).filter_by(incident_id=haz_inc_id).first()
                if not existing_hinc:
                    db.add(Incident(
                        incident_id=haz_inc_id,
                        status="OPEN",
                        event_types=haz_type,
                        camera_id=cid,
                        zone_id=zone_id,
                        affected_tracks="[]",
                        risk_score=95,
                        risk_level="CRITICAL",
                        factors_json=json.dumps({"fire_count": haz_fire, "smoke_count": haz_smoke}),
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    ))
                    seeded_incidents_count += 1
                existing_halt = db.query(Alert).filter_by(alert_id=haz_alt_id).first()
                if not existing_halt:
                    db.add(Alert(
                        alert_id=haz_alt_id,
                        incident_id=haz_inc_id,
                        severity="CRITICAL",
                        title="P0 EMERGENCY: Combustion / Smoke Hazard",
                        message=(
                            f"Optical hazard engine confirmed smoke/fire in "
                            f"{location} ({cname}). Immediate evacuation check required."
                        ),
                        camera_id=cid,
                        zone_id=zone_id,
                        event_type=haz_type,
                        status="ACTIVE",
                        created_at=datetime.now(timezone.utc),
                    ))
                    seeded_alerts_count += 1

            db.commit()
            print(
                f"  [OK] {cid}: {cname} -> {video_file.name} "
                f"(Incidents: {len(incidents)}, Hazards: {haz_smoke + haz_fire})"
            )

    # --------------------------------------------------------------------------
    # Merge new cameras into existing cameras.yaml (preserve all existing cams)
    # --------------------------------------------------------------------------
    existing_yaml = {"cameras": [], "zones": []}
    if CONFIGS_CAMERAS_YAML.exists():
        with open(CONFIGS_CAMERAS_YAML, "r", encoding="utf-8") as yf:
            try:
                existing_yaml = yaml.safe_load(yf) or {"cameras": [], "zones": []}
            except Exception as e:
                print(f"[WARN] Could not parse existing cameras.yaml: {e}")

    existing_ids = {c["id"] for c in existing_yaml.get("cameras", [])}
    added = 0
    for cam in new_yaml_cameras:
        if cam["id"] not in existing_ids:
            existing_yaml.setdefault("cameras", []).append(cam)
            added += 1
        else:
            # Update existing entry
            for i, c in enumerate(existing_yaml["cameras"]):
                if c["id"] == cam["id"]:
                    existing_yaml["cameras"][i] = cam
                    break

    # Ensure zones include new zone ids used
    existing_zone_ids = {z["id"] for z in existing_yaml.get("zones", [])}
    new_zones = [
        {"id": "general_facility", "name": "General Facility",
         "description": "Mezzanine corridors, observation walkways, and overview zones"},
    ]
    for z in new_zones:
        if z["id"] not in existing_zone_ids:
            existing_yaml.setdefault("zones", []).append(z)

    with open(CONFIGS_CAMERAS_YAML, "w", encoding="utf-8") as yf:
        yaml.dump(existing_yaml, yf, default_flow_style=False, sort_keys=False)

    print("\n" + "=" * 80)
    print(
        f"cameras.yaml updated: {len(existing_yaml['cameras'])} total cameras "
        f"({added} newly added from New folder)."
    )
    print(f"Created {seeded_incidents_count} new Incidents and {seeded_alerts_count} new Active Alerts.")
    print("=" * 80)
    print("\nNEXT STEP: Restart the backend to load the new cameras.")
    print("  cd backend && .venv\\Scripts\\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")


if __name__ == "__main__":
    seed()
