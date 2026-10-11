"""
scripts/seed_output2_cameras_and_alerts.py
===========================================
Registers all 18 Output2 annotated CCTV videos as active Surveillance Cameras
in configs/cameras.yaml and the SafeSync database, and seeds real-time
PPE compliance & hazard alerts derived from batch analysis summaries.
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

OUTPUT2_VIDEOS_DIR = Path(r"D:\Additional\Safesync\output2\annotated_videos")
OUTPUT2_REPORTS_DIR = Path(r"D:\Additional\Safesync\output2\reports")
CONFIGS_CAMERAS_YAML = ROOT / "configs" / "cameras.yaml"

VIDEO_METADATA = [
    {
        "cam_id": "cam_output2_01",
        "cam_num": 1,
        "stem": "VID_20261009_131951",
        "name": "CAM-01 • Production Assembly South",
        "zone_id": "production_floor",
        "location": "Fabrication Bay A1",
        "purpose": "PRODUCTION FLOOR",
    },
    {
        "cam_id": "cam_output2_02",
        "cam_num": 2,
        "stem": "VID_20261009_132045",
        "name": "CAM-02 • Fabrication Line North",
        "zone_id": "production_floor",
        "location": "Sheet Metal Station",
        "purpose": "PRODUCTION FLOOR",
    },
    {
        "cam_id": "cam_output2_03",
        "cam_num": 3,
        "stem": "VID_20261009_132102",
        "name": "CAM-03 • Heavy Machinery Unit",
        "zone_id": "production_floor",
        "location": "Press & Stamping Bay",
        "purpose": "PRODUCTION FLOOR",
    },
    {
        "cam_id": "cam_output2_04",
        "cam_num": 4,
        "stem": "VID_20261009_132240",
        "name": "CAM-04 • Multi-Worker Inspection",
        "zone_id": "production_floor",
        "location": "QA Audit Station",
        "purpose": "PRODUCTION FLOOR",
    },
    {
        "cam_id": "cam_output2_05",
        "cam_num": 5,
        "stem": "VID_20261009_132302",
        "name": "CAM-05 • Warehouse Storage Corridor",
        "zone_id": "storage_area",
        "location": "Aisle 4 Storage Racks",
        "purpose": "STORAGE AREA",
    },
    {
        "cam_id": "cam_output2_06",
        "cam_num": 6,
        "stem": "VID_20261009_132435",
        "name": "CAM-06 • Industrial Bay Thermal & Smoke",
        "zone_id": "hazard_zone",
        "location": "Exhaust & Ventilation Shaft",
        "purpose": "HAZARD ZONE",
    },
    {
        "cam_id": "cam_output2_07",
        "cam_num": 7,
        "stem": "VID_20261009_132820",
        "name": "CAM-07 • Turnstile Entry Gate Access",
        "zone_id": "entry_gate",
        "location": "Main Facility Turnstiles",
        "purpose": "ENTRY GATE",
    },
    {
        "cam_id": "cam_output2_08",
        "cam_num": 8,
        "stem": "VID_20261009_133226",
        "name": "CAM-08 • Loading Dock Receiving Bay",
        "zone_id": "loading_dock",
        "location": "Cargo Bay 1",
        "purpose": "LOADING DOCK",
    },
    {
        "cam_id": "cam_output2_09",
        "cam_num": 9,
        "stem": "VID_20261009_133238",
        "name": "CAM-09 • High Voltage Electrical Room",
        "zone_id": "electrical_room",
        "location": "Substation Switchgear",
        "purpose": "ELECTRICAL ROOM",
    },
    {
        "cam_id": "cam_output2_10",
        "cam_num": 10,
        "stem": "VID_20261009_133245",
        "name": "CAM-10 • Assembly Compliant Station",
        "zone_id": "production_floor",
        "location": "Precision Electronics Assembly",
        "purpose": "PRODUCTION FLOOR",
    },
    {
        "cam_id": "cam_output2_11",
        "cam_num": 11,
        "stem": "VID_20261009_133302",
        "name": "CAM-11 • Facility Maintenance Corridor",
        "zone_id": "production_floor",
        "location": "Utility Passage North",
        "purpose": "PRODUCTION FLOOR",
    },
    {
        "cam_id": "cam_output2_12",
        "cam_num": 12,
        "stem": "VID_20261009_134021",
        "name": "CAM-12 • Fabrication Bay Multi-Worker",
        "zone_id": "production_floor",
        "location": "Mechanical Fabrication Bay 2",
        "purpose": "PRODUCTION FLOOR",
    },
    {
        "cam_id": "cam_output2_13",
        "cam_num": 13,
        "stem": "VID_20261009_134122",
        "name": "CAM-13 • Welding & Hot Work Station",
        "zone_id": "production_floor",
        "location": "Arc Welding Booth 3",
        "purpose": "PRODUCTION FLOOR",
    },
    {
        "cam_id": "cam_output2_14",
        "cam_num": 14,
        "stem": "VID_20261009_134149",
        "name": "CAM-14 • Dispatch & Cargo Dock",
        "zone_id": "loading_dock",
        "location": "Logistics Outbound Bay 2",
        "purpose": "LOADING DOCK",
    },
    {
        "cam_id": "cam_output2_15",
        "cam_num": 15,
        "stem": "VID_20261009_134204",
        "name": "CAM-15 • Component Assembly Line",
        "zone_id": "production_floor",
        "location": "Conveyor Station 5",
        "purpose": "PRODUCTION FLOOR",
    },
    {
        "cam_id": "cam_output2_16",
        "cam_num": 16,
        "stem": "VID_20261009_134222",
        "name": "CAM-16 • Furnace Combustion Hazard Zone",
        "zone_id": "hazard_zone",
        "location": "High-Temp Smelting Furnace",
        "purpose": "HAZARD ZONE",
    },
    {
        "cam_id": "cam_output2_17",
        "cam_num": 17,
        "stem": "VID_20261009_134251",
        "name": "CAM-17 • High-Bay Storage & Forklift Route",
        "zone_id": "storage_area",
        "location": "Forklift Crossing Zone",
        "purpose": "STORAGE AREA",
    },
    {
        "cam_id": "cam_output2_18",
        "cam_num": 18,
        "stem": "VID_20261009_134306",
        "name": "CAM-18 • Facility Wide-Angle Overview",
        "zone_id": "general_facility",
        "location": "Mezzanine Observation Deck",
        "purpose": "GENERAL MONITORING",
    },
]


def seed():
    print("=" * 80)
    print("SafeSync — Seeding All Output2 Videos as Surveillance Cameras with Alerts")
    print("=" * 80)

    # 1. Prepare YAML configuration structure
    yaml_cameras = []
    seeded_alerts_count = 0
    seeded_incidents_count = 0

    with SessionLocal() as db:
        for item in VIDEO_METADATA:
            cid = item["cam_id"]
            stem = item["stem"]
            cname = item["name"]
            zone_id = item["zone_id"]
            location = item["location"]

            video_file = OUTPUT2_VIDEOS_DIR / f"{stem}_annotated.mp4"
            summary_file = OUTPUT2_REPORTS_DIR / f"{stem}_summary.json"

            if not video_file.exists():
                print(f"[WARN] Video file not found: {video_file}")
                continue

            summary_data = {}
            if summary_file.exists():
                try:
                    with open(summary_file, "r", encoding="utf-8") as sf:
                        summary_data = json.load(sf)
                except Exception as e:
                    print(f"[WARN] Could not parse summary {summary_file}: {e}")

            fps = summary_data.get("original_fps", 30)
            res = summary_data.get("resolution", "1280x720")
            incidents = summary_data.get("incidents", [])
            haz_fire = summary_data.get("detections", {}).get("fire", 0)
            haz_smoke = summary_data.get("detections", {}).get("smoke", 0)

            # YAML config item
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
            yaml_cameras.append(yaml_item)

            # Upsert Camera in Database
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

            # Seed Real Incidents & Alerts for this Camera
            for inc_idx, inc in enumerate(incidents, start=1):
                inc_id = f"INC-{cid}-{inc_idx:03d}"
                alt_id = f"ALT-{cid}-{inc_idx:03d}"
                missing = inc.get("missing_equipment", [])
                wid = inc.get("worker_id", 1)
                missing_str = ", ".join(missing) if missing else "Required PPE"

                event_type = "MISSING_PPE"
                if "gloves" in missing: event_type = "MISSING_GLOVES"
                elif "helmet" in missing: event_type = "MISSING_HELMET"
                elif "safety_vest" in missing: event_type = "MISSING_SAFETY_VEST"
                elif "safety_footwear" in missing: event_type = "MISSING_FOOTWEAR"

                # Check existing incident
                existing_inc = db.query(Incident).filter_by(incident_id=inc_id).first()
                if not existing_inc:
                    new_inc = Incident(
                        incident_id=inc_id,
                        status="OPEN",
                        event_types=event_type,
                        camera_id=cid,
                        zone_id=zone_id,
                        affected_tracks=json.dumps([wid]),
                        risk_score=75,
                        risk_level="HIGH",
                        factors_json=json.dumps({"missing": missing, "worker_id": wid, "timestamp": inc.get("start_timestamp")}),
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                    db.add(new_inc)
                    seeded_incidents_count += 1

                # Check existing alert
                existing_alt = db.query(Alert).filter_by(alert_id=alt_id).first()
                if not existing_alt:
                    new_alt = Alert(
                        alert_id=alt_id,
                        incident_id=inc_id,
                        severity="HIGH",
                        title=f"PPE Violation: Missing {missing_str.title()}",
                        message=f"Worker #{wid} in {location} ({cname}) confirmed missing required: {missing_str}.",
                        camera_id=cid,
                        zone_id=zone_id,
                        event_type=event_type,
                        status="ACTIVE",
                        created_at=datetime.now(timezone.utc),
                    )
                    db.add(new_alt)
                    seeded_alerts_count += 1

            # Seed Combustion / Smoke Alerts for hazard cameras
            if haz_smoke > 0 or haz_fire > 0:
                haz_inc_id = f"INC-{cid}-HAZ-001"
                haz_alt_id = f"ALT-{cid}-HAZ-001"
                haz_type = "SMOKE_DETECTED" if haz_smoke > 0 else "FIRE_DETECTED"
                existing_hinc = db.query(Incident).filter_by(incident_id=haz_inc_id).first()
                if not existing_hinc:
                    new_hinc = Incident(
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
                    )
                    db.add(new_hinc)
                    seeded_incidents_count += 1

                existing_halt = db.query(Alert).filter_by(alert_id=haz_alt_id).first()
                if not existing_halt:
                    new_halt = Alert(
                        alert_id=haz_alt_id,
                        incident_id=haz_inc_id,
                        severity="CRITICAL",
                        title="P0 EMERGENCY: Combustion & Smoke Hazard",
                        message=f"Optical hazard engine confirmed atmospheric smoke plume in {location} ({cname}). Immediate inspection required.",
                        camera_id=cid,
                        zone_id=zone_id,
                        event_type=haz_type,
                        status="ACTIVE",
                        created_at=datetime.now(timezone.utc),
                    )
                    db.add(new_halt)
                    seeded_alerts_count += 1

            db.commit()
            print(f"  [OK] {cid}: {cname} -> {video_file.name} (Incidents: {len(incidents)}, Hazards: {haz_smoke + haz_fire})")

    # 2. Write updated configs/cameras.yaml
    full_yaml = {
        "cameras": yaml_cameras,
        "zones": [
            {"id": "production_floor", "name": "Production Floor", "description": "Main manufacturing, fabrication, and assembly areas"},
            {"id": "storage_area", "name": "Warehouse Storage", "description": "High-bay storage racks, forklift routes, and inventory aisles"},
            {"id": "hazard_zone", "name": "Hazard & Combustion Zone", "description": "Thermal smelting, furnace operations, and exhaust shafts"},
            {"id": "entry_gate", "name": "Entry Turnstile & Access", "description": "Personnel access gates and PPE clearance checkpoint"},
            {"id": "loading_dock", "name": "Loading & Logistics Dock", "description": "Inbound receiving and outbound shipping cargo bays"},
            {"id": "electrical_room", "name": "Electrical Switchgear Room", "description": "High-voltage substations and transformer units"},
            {"id": "general_facility", "name": "General Facility", "description": "Mezzanine corridors, observation walkways, and overview zones"},
        ]
    }

    with open(CONFIGS_CAMERAS_YAML, "w", encoding="utf-8") as yf:
        yaml.dump(full_yaml, yf, default_flow_style=False, sort_keys=False)

    print("\n" + "=" * 80)
    print(f"Successfully seeded {len(yaml_cameras)} cameras into {CONFIGS_CAMERAS_YAML} and SQLite database.")
    print(f"Created {seeded_incidents_count} new Incidents and {seeded_alerts_count} new Active Alerts.")
    print("=" * 80)


if __name__ == "__main__":
    seed()
