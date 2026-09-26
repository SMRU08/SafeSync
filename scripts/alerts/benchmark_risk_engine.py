"""
benchmark_risk_engine.py — SafeSync Phase 7
Measures actual execution latencies for Risk Analysis, Event Normalization,
Alert Deduplication, Cooldown, and Database Persistence.
Exports results to outputs/alerts/alert_benchmark.json.
"""

import os
import sys
import time
import json
import uuid
from datetime import datetime, timezone

# Ensure project root in sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.join(ROOT, "backend")
for p in [ROOT, BACKEND_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.database.session import engine, Base, SessionLocal
from app.ai.risk.schemas import EventType, NormalizedSafetyEvent
from app.services.risk_engine import RiskEngine
from app.services.alert_engine import AlertEngine


def run_benchmark(num_iterations: int = 200):
    print("=" * 68)
    print(f"  PHASE 7 — RISK & ALERT ENGINE BENCHMARK ({num_iterations} iterations)")
    print("=" * 68)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    risk_eng = RiskEngine()
    alert_eng = AlertEngine(risk_engine=risk_eng)

    risk_eval_latencies = []
    alert_creation_latencies = []
    db_write_latencies = []
    total_latencies = []

    test_events = [
        EventType.MISSING_HELMET,
        EventType.MISSING_SAFETY_VEST,
        EventType.MISSING_GLOVES,
        EventType.MISSING_SAFETY_FOOTWEAR,
        EventType.SMOKE_DETECTED,
        EventType.FIRE_DETECTED,
        EventType.MULTIPLE_HAZARDS,
    ]

    for i in range(num_iterations):
        ev_type = test_events[i % len(test_events)]
        ev = NormalizedSafetyEvent(
            event_id=str(uuid.uuid4()),
            event_type=ev_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            camera_id=f"camera_{1 + (i % 4):02d}",
            zone_id="production_floor" if (i % 2 == 0) else "electrical_room",
            track_id=100 + i,
            confidence=0.85,
            duration_seconds=float(i % 60),
            source="benchmark",
        )

        t_start = time.perf_counter()

        # 1. Risk Evaluation
        t0 = time.perf_counter()
        breakdown = risk_eng.evaluate(
            event_type=ev.event_type,
            duration_seconds=ev.duration_seconds,
            affected_workers_count=1 + (i % 3),
            zone_id=ev.zone_id,
            is_multi_hazard=(ev.event_type == EventType.MULTIPLE_HAZARDS),
        )
        t_risk = (time.perf_counter() - t0) * 1000.0
        risk_eval_latencies.append(t_risk)

        # 2. Alert Engine Processing + DB Persistence
        t1 = time.perf_counter()
        alert, incident, act = alert_eng.process_event(ev, db=db)
        t_alert_db = (time.perf_counter() - t1) * 1000.0
        alert_creation_latencies.append(t_alert_db)

        t_total = (time.perf_counter() - t_start) * 1000.0
        total_latencies.append(t_total)

    db.close()

    mean_risk_ms = sum(risk_eval_latencies) / len(risk_eval_latencies)
    mean_alert_ms = sum(alert_creation_latencies) / len(alert_creation_latencies)
    mean_total_ms = sum(total_latencies) / len(total_latencies)
    throughput_eps = 1000.0 / mean_total_ms if mean_total_ms > 0 else 0.0

    benchmark_record = {
        "iterations": num_iterations,
        "performance": {
            "mean_risk_evaluation_ms": round(mean_risk_ms, 3),
            "mean_alert_processing_and_db_ms": round(mean_alert_ms, 3),
            "mean_total_event_processing_ms": round(mean_total_ms, 3),
            "event_throughput_per_second": round(throughput_eps, 1),
        },
        "sample_risk_factors": breakdown.factors,
        "sample_final_score": breakdown.risk_score,
        "sample_level": breakdown.risk_level.value,
    }

    out_dir = os.path.join(ROOT, "outputs", "alerts")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "alert_benchmark.json")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(benchmark_record, f, indent=2)

    print("\n" + "=" * 68)
    print("  BENCHMARK COMPLETED SUCCESSFULLY")
    print("=" * 68)
    print(f"  Risk Evaluation Latency   : {mean_risk_ms:.3f} ms")
    print(f"  Alert Engine & DB Latency : {mean_alert_ms:.3f} ms")
    print(f"  Total Event Processing    : {mean_total_ms:.3f} ms")
    print(f"  Throughput                : {throughput_eps:.1f} events/sec")
    print(f"  Results saved to          : {out_file}")
    print("=" * 68)


if __name__ == "__main__":
    run_benchmark()
