# Security Model & Threat Mitigation

This document details the security principles, threat boundaries, and defensive countermeasures engineered into RAKSHYA VISION.

---

## 1. Threat Model & Trust Boundaries

```
[ Untrusted External Zone ]
  - Camera Network / RTSP Feeds
  - Public Web Clients / Mobile Users
         │
         │ (Input Validation, Auth, TLS)
         ▼
[ DMZ / Reverse Proxy ]
  - Nginx HTTPS / WSS Termination
  - Rate Limiting & Header Sanitization
         │
         │ (Authenticated Loopback)
         ▼
[ Trusted Application Core ]
  - FastAPI Backend & Camera Workers
  - YOLOv8 Inference & Tracking Engine
  - SQLite WAL Database & Evidence Store
```

---

## 2. Countermeasure Specifications

### 2.1 Credential & Secret Protection
- **Zero Cleartext Credentials in Logs:** Camera RTSP passwords (`rtsp://admin:pass@...`) are automatically masked as `rtsp://admin:********@...` across standard output, structured JSON logs, and REST API telemetry.
- **Environment Variable Isolation:** Secrets (`SECRET_KEY`, `JWT_SECRET_KEY`, `WEBHOOK_SECRET`) are never hardcoded into source code or tracked in version control.
- **Production Startup Check:** In production mode, the application halts startup if default or trivial secrets are detected.

### 2.2 Input Validation & Denial-of-Service Defenses
1. **Zero-Byte File Rejection:** Any uploaded image or video packet containing 0 bytes is rejected with `HTTP 400 Bad Request` before reaching image decoding libraries.
2. **Unsupported Format Rejection:** Uploads must pass strict MIME type checks (`image/jpeg`, `image/png`, `video/mp4`). Arbitrary binary payloads return `HTTP 415 Unsupported Media Type`.
3. **Payload Size Limits:** HTTP requests are capped at 50 MB to prevent memory exhaustion attacks.

### 2.3 Path Traversal Countermeasures
- All file retrieval endpoints (`/api/evidence/{id}`, `/api/detection/image`) resolve canonical absolute paths using `os.path.realpath`.
- Paths containing dot-dot sequences (`../`, `..\`) or pointing outside configured root directories (`outputs/evidence/`) are rejected immediately with `HTTP 400/404`.

### 2.4 Cryptographic Evidence Integrity
- Evidence snapshots are hashed with SHA-256 upon write and recorded in the database.
- Read operations allow on-demand hash verification to detect filesystem tampering, bit rot, or unauthorized modifications.
