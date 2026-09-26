# Incident Evidence Management

SafeSync implements a tamper-evident visual evidence archival engine (`EvidenceManager`) to securely preserve visual records and detection telemetry for safety incident investigations.

---

## 1. Evidence Capture Architecture

When a confirmed safety violation or environmental hazard triggers an incident, the system archives high-fidelity visual evidence:

```
Incident Created / Escalated
            │
            ▼
┌────────────────────────────────────────────────────────┐
│            EvidenceManager (Singleton)                 │
│  - Fetches annotated frame from CameraWorker           │
│  - Formats: JPEG (Quality 85)                          │
│  - Cryptography: SHA-256 Checksum Computation          │
│  - Storage Quota: MAX_EVIDENCE_STORAGE_GB Enforcement  │
│  - Fault Isolation: Wrapped in non-blocking try/except │
└───────┬────────────────────────────────────────┬───────┘
        │                                        │
        ▼                                        ▼
┌───────────────────────────┐      ┌───────────────────────────┐
│     Disk Evidence Store   │      │  SQLite DB (evidence_items)│
│ outputs/evidence/         │      │ - evidence_id (UUID)      │
│   YYYY/MM/DD/{camera_id}/ │      │ - incident_id (FK)        │
│     {incident}_{uuid}.jpg │      │ - sha256_checksum         │
└───────────────────────────┘      │ - file_size_bytes         │
                                   └───────────────────────────┘
```

---

## 2. Directory Hierarchy & File Naming

Evidence artifacts are partitioned chronologically by date and camera ID to optimize filesystem performance:

```
outputs/evidence/
└── 2026/
    └── 09/
        └── 21/
            └── camera_01/
                ├── INC-00124_7c9a2e81.jpg
                └── INC-00125_b4f109a2.jpg
```

---

## 3. Cryptographic Tamper-Evidence

1. **Immediate SHA-256 Hashing:**
   Before writing to disk, the raw byte stream of each evidence snapshot is hashed using SHA-256. The hexadecimal digest is recorded permanently in the `evidence_items` table.
2. **On-Demand Tamper Verification:**
   The verification API (`GET /api/evidence/{evidence_id}`) streams the on-disk file, recomputes its SHA-256 hash in real time, and compares it with the database record:
   - If the file has been modified by a single byte, `verified` evaluates to `false` and `tampered` evaluates to `true`.
3. **Path Traversal Defense:**
   All evidence retrieval routes strictly resolve the canonical absolute path (`os.path.realpath`) and verify that the target file resides within `outputs/evidence/`. Requests attempting directory traversal (e.g. `../../etc/passwd`) are rejected with HTTP 400/404.

---

## 4. Storage Quota & Pruning Policy

To prevent unbounded disk usage during continuous recording, `EvidenceManager` enforces a configurable storage quota (default: 10 GB):

```yaml
evidence:
  max_storage_gb: 10.0
  image_quality: 85
  retention_days: 90
```

- **Rolling Pruning:** When total evidence disk usage exceeds `max_storage_gb`, the oldest verified snapshots are deleted first until disk usage drops below 90% of the quota.
- **Database Synchronization:** Deleted files have their database records updated with `file_deleted = true`, preserving incident audit metadata even if raw images are rotated out.
