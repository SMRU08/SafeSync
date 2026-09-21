# RAKSHYA VISION — Phase 10 Step 4: Database Productionization, SQLite WAL & Data Retention

## 1. Overview & Objectives

In **Phase 10 Step 4**, the database tier for **RAKSHYA VISION — AI Vision-Based Safety Monitoring** has been upgraded from development defaults to a hardened edge-production standard. 

The edge architecture of RAKSHYA VISION features multiple concurrent consumers (camera ingest streams, YOLO inference workers, worker tracking pipelines, hazard analyzers, and REST/WebSocket dashboard handlers) interacting with the persistent store. Under SQLite's default rollback journal mode, concurrent read/write operations frequently resulted in `database is locked` errors and thread contention. 

Step 4 resolves this by enforcing **Write-Ahead Logging (WAL)**, strict foreign key enforcement, thread-safe busy timeouts, normal synchronous durability, active database health reporting, and a deterministic retention cleanup engine.

---

## 2. SQLite WAL Architecture & PRAGMA Configuration

Every connection initialized by SQLAlchemy hooks directly into SQLite's low-level C API via `@event.listens_for(engine, "connect")` in `backend/app/database/session.py`.

The active PRAGMAs configured are:
- `PRAGMA journal_mode=WAL;`: Enables Write-Ahead Logging. Readers and writers do not block each other. Multiple processes/threads can read concurrently while a single writer appends changes to the `-wal` file.
- `PRAGMA synchronous=NORMAL;`: Safe for WAL mode, reduces disk sync overhead without risking database corruption across typical OS/app crashes.
- `PRAGMA foreign_keys=ON;`: Strictly enforces relational referential integrity across parent and child tables (e.g. `Incident` -> `Alert`, `HazardEvent` -> `HazardObservation`, `WorkerTracking` -> `ComplianceObservation`).
- `PRAGMA busy_timeout=5000;`: Blocks contending threads for up to 5,000 milliseconds before raising a timeout, drastically reducing transient edge lock errors.

### Verified Diagnostic Endpoint

The database health and PRAGMA settings are verified via `GET /health/database`:
```json
{
  "status": "healthy",
  "reachable": true,
  "query_ok": true,
  "dialect": "sqlite",
  "database_url": "./rakshya_vision.db",
  "tables_available": [
    "incidents",
    "alerts",
    "alert_history",
    "hazard_events",
    "hazard_observations",
    "worker_tracking",
    "ppe_observations",
    "compliance_observations"
  ],
  "expected_tables_found": true,
  "pragmas": {
    "journal_mode": "wal",
    "foreign_keys": 1,
    "busy_timeout": 5000,
    "synchronous": "NORMAL"
  }
}
```

---

## 3. Data Retention & Incident Preservation Engine

Long-running camera monitoring can generate high-volume temporal observations and alerts. Step 4 provides a centralized maintenance script:
`scripts/cleanup_retention.py`

### Safety Guarantees
1. **Never deletes active safety incidents:** Records with status `OPEN` or `ACKNOWLEDGED` are **strictly protected** regardless of how long ago they were recorded.
2. **Never deletes unresolved hazards:** `HazardEvent` records in `SUSPECTED` or `CONFIRMED` states are never pruned. Only `CLEARED` or `NO_HAZARD` events older than the cutoff threshold can be deleted.
3. **Never deletes active worker tracks:** Workers currently marked `is_active == True` remain untouched.
4. **Relational Deletion Order:** Adheres to foreign key hierarchy:
   - `alert_history` -> `alerts` -> `incidents`
   - `hazard_observations` -> `hazard_events`
   - `compliance_observations` -> `worker_tracking`
5. **Atomic Transactions:** All deletions occur inside an atomic transaction. Any transient failure triggers an immediate `session.rollback()`.

### Retention CLI Modes
- **Dry-Run (Default):**
  ```bash
  python scripts/cleanup_retention.py --dry-run
  ```
  Scans all candidate tables, evaluates cutoff windows from `configs/production.yaml`, and prints detailed counts without deleting any rows.
- **Execute Mode:**
  ```bash
  python scripts/cleanup_retention.py --execute
  ```
  Applies deletion rules within a database transaction and commits changes.
- **Optional Storage Reclamation:**
  ```bash
  python scripts/cleanup_retention.py --execute --vacuum
  ```

---

## 4. SQLite vs. PostgreSQL Deployment Guidance

| Criterion | SQLite (WAL Mode) | PostgreSQL |
| :--- | :--- | :--- |
| **Recommended Deployment Target** | Single-node edge servers, on-premise industrial gateways, NVIDIA Jetson devices, disconnected field kits. | Multi-node enterprise deployments, cloud clusters, centralized multi-facility aggregation. |
| **Concurrency Characteristics** | Single-writer, multi-reader with zero network overhead. Concurrent readers never block writers. | Multi-writer, multi-reader MVCC with row-level locks. |
| **Operational Overhead** | Zero-configuration. Single file `rakshya_vision.db` + `-wal` + `-shm`. No separate daemon to manage or monitor. | Requires dedicated database server process, user management, connection pools, and replication configuration. |
| **Scale Limits** | Optimal up to ~50–100 GB database size and single-box ingest rates. | Effectively limitless storage, petabyte-scale horizontal scaling. |
| **Migration Path** | RAKSHYA VISION uses standard SQLAlchemy ORM models. Upgrading to PostgreSQL only requires configuring `DATABASE_URL=postgresql://user:pass@host:5432/rakshya` without rewriting queries. | N/A |

---

## 5. WAL Maintenance & Edge Storage Best Practices

1. **Checkpointing:** By default, SQLite triggers a passive WAL checkpoint when the log reaches 1000 pages (~4 MB). For high-frequency frame tracking, periodic `PRAGMA wal_checkpoint(PASSIVE);` or `PRAGMA wal_checkpoint(TRUNCATE);` can be run during scheduled low-activity windows.
2. **Storage Pruning:** Running `python scripts/cleanup_retention.py --execute` via a daily cron job keeps table sizes lean.
3. **Backups:** Because SQLite WAL allows live reading, backups should be performed using SQLite's online backup API or `sqlite3 rakshya_vision.db ".backup backup.db"` rather than simple raw file copy commands to avoid reading mid-commit WAL states.
