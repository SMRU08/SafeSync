# Configuration Management

RAKSHYA VISION implements a multi-tier configuration architecture combining declarative YAML specification files with runtime environment variable overrides.

---

## 1. Configuration Hierarchy

The system loads configuration according to strict priority rules:

```
┌────────────────────────────────────────────────────────┐
│ 1. Operating System Environment Variables (Highest)   │
└──────────────────────────┬─────────────────────────────┘
                           │ overrides
                           ▼
┌────────────────────────────────────────────────────────┐
│ 2. Local .env File                                     │
└──────────────────────────┬─────────────────────────────┘
                           │ overrides
                           ▼
┌────────────────────────────────────────────────────────┐
│ 3. Environment YAML (production.yaml / development.yaml│
└──────────────────────────┬─────────────────────────────┘
                           │ overrides
                           ▼
┌────────────────────────────────────────────────────────┐
│ 4. Built-in Pydantic v2 Code Defaults (Lowest)         │
└────────────────────────────────────────────────────────┘
```

---

## 2. Configuration Profiles

The active profile is selected via the `ENVIRONMENT` variable:

```bash
# Development (default)
export ENVIRONMENT=development

# Production
export ENVIRONMENT=production
```

### 2.1 Production Hardening Rules
When running with `ENVIRONMENT=production`:
1. **Secret Key Enforcement:** The application will **refuse to start** if `SECRET_KEY` or `JWT_SECRET_KEY` is missing or set to insecure placeholders (e.g. `changeme`, `secret`, `123456`).
2. **CORS Restrictions:** Wildcard CORS (`allow_origins: ["*"]`) is strictly disallowed in production mode; explicit origin domains must be specified.
3. **Debug Mode Disabled:** API debug endpoints and verbose interactive error traces are deactivated.

---

## 3. Configuration Files Reference

All primary configuration files reside in `configs/`:

| File | Purpose | Key Parameters |
|---|---|---|
| `production.yaml` | Production environment defaults | Host/port, database paths, CORS whitelist, log level. |
| `development.yaml` | Local developer defaults | Reload flags, relaxed CORS, verbose logging. |
| `cameras.yaml` | Camera definitions & zones | Camera IDs, RTSP URIs, reconnection backoff policies. |
| `detection.yaml` | AI inference parameters | Confidence thresholds, NMS IoU, input resolution (384). |
| `risk_policy.yaml` | Risk factor weights | Base event severities, persistence rates, zone multipliers. |
| `alert_policy.yaml` | Alert deduplication rules | Cooldown durations (60s), escalation timeouts (120s). |

---

## 4. Environment Variables Reference

| Variable | Type | Default | Description |
|---|---|---|---|
| `ENVIRONMENT` | string | `development` | Profile: `development` or `production` |
| `SECRET_KEY` | string | *required in prod* | Secret key for session security & HMAC hashing |
| `JWT_SECRET_KEY` | string | *required in prod* | Secret key for signing JWT authentication tokens |
| `DATABASE_URL` | string | `sqlite:///./rakshya_vision.db` | SQLAlchemy database connection string |
| `HOST` | string | `0.0.0.0` | Bind host address |
| `PORT` | int | `8000` | Bind port number |
| `CORS_ORIGINS` | string | `http://localhost:5173` | Comma-separated list of allowed web origins |
| `WEBHOOK_URL` | string | *(optional)* | Destination HTTP endpoint for external safety alerts |
| `WEBHOOK_SECRET` | string | *(optional)* | Secret used for HMAC-SHA256 signature verification |
| `EMAIL_HOST` | string | *(optional)* | SMTP host for email alerts |
| `MAX_EVIDENCE_STORAGE_GB`| float | `10.0` | Maximum disk capacity allocated for incident snapshots |
