# RAKSHYA VISION Documentation Index

Welcome to the technical documentation for **RAKSHYA VISION**, an automated edge AI safety monitoring system for industrial facilities.

---

## Architecture & System Design
- [System Architecture](architecture/system-architecture.md) — Subsystems, responsibilities, component decoupling, and high-level architecture diagram.
- [Processing Pipeline](architecture/processing-pipeline.md) — Step-by-step frame processing lifecycle from video decode to dashboard rendering.
- [Data Flow & Contracts](architecture/data-flow.md) — Data schemas, message envelopes, and inter-module contracts.
- [Database Architecture](architecture/database.md) — SQLite Write-Ahead Logging (WAL) mode, relational schema, and retention policies.

## AI & Computer Vision
- [AI Detection Model](ai/detection-model.md) — Ultralytics YOLOv8n detector, canonical 7-class ontology, and benchmark metrics.
- [Model Registry](ai/model-registry.md) — Cryptographic SHA-256 weight verification, model states, and loading safeguards.
- [PPE Compliance & Anatomy](ai/ppe-compliance.md) — Spatial anatomical zones, temporal validation, and the strict `UNKNOWN != VIOLATION` rule.
- [Worker Tracking](ai/worker-tracking.md) — ByteTrack engine, 8-state Kalman Filter motion model, and anonymous tracking.
- [Fire & Smoke Detection](ai/fire-smoke-detection.md) — Decoupled hazard tracking, multi-modal relationships, and false positive mitigation.
- [Explainable Risk Engine](ai/risk-engine.md) — Deterministic 0–100 risk scoring algorithm, factor weights, and severity tiers.

## Operations & Monitoring
- [Camera Management](operations/camera-management.md) — Multi-camera worker pool, thread isolation, reconnection policies, and credential masking.
- [Camera Dashboard & APIs](operations/camera-dashboard.md) — REST endpoints, live annotated snapshots, and interactive frame inspection.
- [Alerts & External Notifications](operations/alerts.md) — Alert deduplication, cooldown timers, Webhooks, and SMTP email dispatches.
- [Incident Management](operations/incident-management.md) — Incident lifecycle state machine (`OPEN` $\rightarrow$ `ACK` $\rightarrow$ `RESOLVED`), SLAs, and audit trails.
- [Evidence Management](operations/evidence-management.md) — Tamper-evident SHA-256 image snapshots, storage quotas, and traversal defenses.
- [System Monitoring](operations/monitoring.md) — Prometheus metrics (`/metrics`), Kubernetes liveness/readiness probes, and logging.

## Deployment & Setup
- [Installation Guide](deployment/installation.md) — System prerequisites, virtual environments, dependency installation, and first run.
- [Configuration Reference](deployment/configuration.md) — Configuration hierarchy, environment profiles, and policy specifications.
- [Production Deployment](deployment/production-deployment.md) — Systemd service setup, Nginx reverse proxy, and maintenance crons.
- [Troubleshooting](deployment/troubleshooting.md) — Diagnosing webcam permissions, RTSP drops, SQLite locks, and CUDA fallback.

## Security & Access Control
- [Authentication](security/authentication.md) — Cryptographic PBKDF2-HMAC-SHA256 password hashing and JWT access tokens.
- [Role-Based Access Control](security/authorization.md) — RBAC tiers (`ADMIN`, `OPERATOR`, `VIEWER`), route guards, and audit logs.
- [Security Model](security/security-model.md) — Threat model, credential protection, input sanitization, and path traversal defense.

## Testing & Quality Assurance
- [Testing Strategy](testing/testing-strategy.md) — Multi-layered testing pyramid, automated test suites, and execution instructions.
- [Integration Testing](testing/integration-testing.md) — Comprehensive 39-scenario end-to-end integration test report.
- [Performance & Benchmarks](testing/performance.md) — Latency budgets, CPU/GPU throughput, and memory stability measurements.
- [Known Issues & Defect Log](testing/known-issues.md) — Documented defect resolutions and active operating constraints.

## Datasets & Methodology
- [Dataset Strategy](datasets/dataset-strategy.md) — Positive object detection philosophy and absence label normalization.
- [Dataset Sources](datasets/sources.md) — Ingested datasets, class distribution tables, and zero-leakage split verification.

## Engineering Reports
- [Production Readiness](reports/production-readiness.md) — Factual readiness scorecard across all subsystems and operational capabilities.
- [Known Limitations](reports/known-limitations.md) — Physical optical limits, environmental factors, and concurrency thresholds.
