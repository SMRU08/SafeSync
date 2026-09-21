# RAKSHYA VISION — Phase 10 Step 9: Incident Evidence Archival

## 1. Executive Summary
Phase 10 Step 9 establishes a tamper-evident visual evidence archival engine for RAKSHYA VISION. When confirmed safety violations or environmental hazards trigger an incident or alert, the system securely archives high-fidelity visual evidence (video frames and detection metadata) to a structured directory hierarchy. Every evidence artifact is cryptographically hashed using SHA-256 upon write, allowing real-time tamper detection while enforcing storage quotas and defending against path traversal attacks.

---

## 2. Architectural Design

```
┌────────────────────────────────────────────────────────┐
│             AlertEngine / Incident Pipeline            │
└───────────────────────────┬────────────────────────────┘
                            │ (on Incident / Alert Created)
                            ▼
┌────────────────────────────────────────────────────────┐
│            EvidenceManager (Singleton)                 │
│  - Fetches frame from CameraWorker (or supplied frame) │
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

## 3. Database Schema

### Table: `evidence_items`
| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | No | Auto-increment primary key |
| `evidence_id` | `VARCHAR(64)` | No | Unique UUID for the evidence artifact |
| `incident_id` | `VARCHAR(64)` | No | Foreign key referencing `incidents.incident_id` |
| `camera_id` | `VARCHAR(32)` | No | Identifier of the camera originating the frame |
| `evidence_type` | `VARCHAR(32)` | No | Type of evidence (`SNAPSHOT`, `ANNOTATED_SNAPSHOT`, `CLIP`) |
| `file_path` | `VARCHAR(512)` | No | Normalized relative filesystem path |
| `file_size_bytes` | `INTEGER` | No | Physical file size in bytes |
| `sha256_checksum` | `VARCHAR(64)` | No | Cryptographic SHA-256 hex digest |
| `metadata_json` | `TEXT` | Yes | JSON string of bounding boxes, confidence, and tags |
| `created_at` | `DATETIME` | No | UTC timestamp of capture |

---

## 4. Key Security & Operational Guarantees

### 4.1 Tamper-Evident SHA-256 Hashing
Every image captured is hashed immediately before and upon write. The verification endpoint (`GET /api/evidence/{evidence_id}`) streams the on-disk file, computes a fresh SHA-256 digest, and compares it with the database record. If an attacker or corrupt sector alters even a single byte, `verified` evaluates to `False` and `tampered` evaluates to `True`.

### 4.2 Path Traversal Defense
The `EvidenceManager.resolve_secure_path()` method canonicalizes relative paths against `EVIDENCE_STORAGE_DIR` and verifies that the target path does not escape the storage root. Any attempt to access paths with `..`, absolute drive roots, or system directories raises a `PermissionError` that translates to an `HTTP 403 Forbidden` response.

### 4.3 Complete Fault Isolation
Safety monitoring is mission-critical:
- If a camera feed is temporarily unavailable, disabled, or dropped, evidence capture skips cleanly without blocking.
- If disk write fails or quota cannot be reclaimed, an error is logged, and the parent `Incident` and `Alert` are **always** persisted in the database.

### 4.4 Storage Quota & Retention Maintenance
- `MAX_EVIDENCE_STORAGE_GB` (configured in `configs/production.yaml`, default: 20 GB) caps disk usage.
- `enforce_storage_quota()` automatically prunes the oldest evidence artifacts associated with `RESOLVED` or `DISMISSED` incidents when the quota threshold is crossed. Active investigation evidence is preserved.
- `scripts/cleanup_retention.py` integrates evidence pruning into routine retention cycles.

---

## 5. API Reference

| Method | Endpoint | Auth Roles | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/incidents/{incident_id}/evidence` | `ADMIN`, `OPERATOR`, `VIEWER` | Lists all evidence artifacts linked to an incident |
| `GET` | `/api/evidence/{evidence_id}` | `ADMIN`, `OPERATOR`, `VIEWER` | Returns evidence metadata and live SHA-256 integrity verification |
| `GET` | `/api/evidence/{evidence_id}/download` | `ADMIN`, `OPERATOR`, `VIEWER` | Securely streams evidence image with path traversal guards |
| `GET` | `/api/evidence/storage/status` | `ADMIN`, `OPERATOR`, `VIEWER` | Returns storage usage, quota metrics, and retention policy |

---

## 6. Frontend Integration
The frontend `AlertDetailModal` now features an **Incident Visual Evidence & Tamper Verification** section:
- Renders high-resolution evidence snapshots associated with the incident.
- Displays camera origin tag and file size.
- Shows a cryptographic **SHA-256** badge verifying that the evidence has not been tampered with.
- Provides a direct secure download button.

---

## 7. Verification Summary
- **Unit & Integration Suite**: `backend/tests/test_evidence_phase10.py` (8/8 PASSED).
- **Frontend Production Build**: `npm run build` compiled cleanly with 0 TypeScript/Vite errors.
