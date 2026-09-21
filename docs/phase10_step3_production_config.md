# RAKSHYA VISION — Phase 10 Step 3: Production Configuration & Secret Safety Report

**Document ID:** DOC-PHASE10-STEP3  
**System:** RAKSHYA VISION (AI Vision-Based Safety Monitoring System)  
**Date:** 2026-09-21  
**Status:** **STEP 3 VERIFIED & PASSING**  

---

## 1. Executive Summary

Phase 10 Step 3 establishes the centralized configuration and secret governance architecture for RAKSHYA VISION. It decouples operational runtime settings from source code, institutes strict configuration precedence, protects sensitive secrets from accidental leakage, and provides deterministic validation for production deployments.

---

## 2. Configuration Hierarchy & Precedence

The system evaluates configuration parameters using a three-tier hierarchy where runtime environment overrides static files:

```
┌─────────────────────────────────────────────────────────┐
│ 1. Environment Variables (os.environ, .env file)        │  <-- HIGHEST PRECEDENCE
└────────────────────────────┬────────────────────────────┘
                             │ Overrides
                             ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Production YAML Configuration (configs/production.yaml)│
└────────────────────────────┬────────────────────────────┘
                             │ Overrides
                             ▼
┌─────────────────────────────────────────────────────────┐
│ 3. Safe Application Defaults (backend/app/config.py)     │  <-- LOWEST PRECEDENCE
└─────────────────────────────────────────────────────────┘
```

---

## 3. Configuration Files & Environment Templates

### A. Centralized Production YAML
- **File:** [`configs/production.yaml`](file:///D:/Additional/PROJECT/RAKSHYA-VISION/configs/production.yaml)
- **Role:** Declares operational parameters (server, database, model registry, camera reconnect limits, tracking parameters, compliance thresholds, hazard timings, risk policy paths, retention days, upload size limits).
- **Security Rule:** Strictly **zero secrets** (no passwords, tokens, private RTSP credentials, or JWT signing keys).

### B. Environment Secret Template
- **File:** [`.env.example`](file:///D:/Additional/PROJECT/RAKSHYA-VISION/.env.example)
- **Role:** Template illustrating all environment variables with clear documentation and placeholder keys.
- **Git Protection:** Verified ignored in `.gitignore`:
  ```gitignore
  .env
  .env.*
  !.env.example
  .env.local
  .env.*.local
  ```

---

## 4. Secret Safety & Sanitization

1. **Memory & String Masking:**
   - Sensitive fields (`SECRET_KEY`, `JWT_SECRET_KEY`, `CAMERA_PASSWORD`, `EMAIL_PASSWORD`, `WEBHOOK_SECRET`, `SMS_API_SECRET`, `ADMIN_PASSWORD`) are automatically redacted when `Settings` is converted to a string or representation (`repr(settings)` and `str(settings)` return `"[REDACTED]"`).
2. **Missing Secret Detection:**
   - In `production` mode (`APP_ENV=production`), `validate_production_configuration()` enforces that a non-empty, non-placeholder secret key is provided.
   - If missing or set to insecure defaults (e.g. `CHANGE_ME...`), it halts with:
     ```
     CONFIGURATION ERROR: Required production secret is missing.
     ```
   - Secret values are **never printed in logs or exception messages**.

---

## 5. CORS Validation in Production

1. **Development Mode:**
   - Automatically permits local development origins: `http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:3000`.
2. **Production Mode:**
   - Wildcards (`*`) and empty lists are strictly rejected.
   - Must be explicitly populated via `CORS_ALLOWED_ORIGINS` (comma-separated URLs).
   - If missing or unconfigured, validation fails with:
     ```
     CONFIGURATION ERROR: Production CORS origins NOT CONFIGURED.
     ```

---

## 6. Administrator Setup Guide (Safe Example)

To deploy RAKSHYA VISION in a production environment:

1. **Copy the Environment Template:**
   ```bash
   cp .env.example .env
   chmod 600 .env
   ```

2. **Generate Strong Cryptographic Secrets:**
   ```bash
   python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
   ```

3. **Populate `.env` with Deployment Parameters:**
   ```ini
   APP_ENV=production
   DEBUG=false
   HOST=0.0.0.0
   PORT=8000

   JWT_SECRET_KEY=e83a29b47cf04618a510e1948db7c02f1a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d
   DATABASE_URL=sqlite:///./rakshya_vision.db
   CORS_ALLOWED_ORIGINS=https://soc.industrial-plant.com,https://monitoring.internal.lan

   EVIDENCE_STORAGE_DIR=outputs/evidence
   EVIDENCE_RETENTION_DAYS=30
   LOG_FILE_PATH=outputs/logs/rakshya_vision.log
   ```

4. **Validate Configuration Programmatically:**
   ```python
   from app.config import settings
   report = settings.validate_production_configuration()
   print("Configuration Validated:", report)
   ```

---

## 7. Automated Tests Executed

Automated unit tests in [`backend/tests/test_production_config_phase10.py`](file:///D:/Additional/PROJECT/RAKSHYA-VISION/backend/tests/test_production_config_phase10.py):

| Test Name | Verification Focus | Result |
|---|---|---|
| `test_production_yaml_loads` | Validates YAML syntax and core sections | **PASS** |
| `test_development_config_loads_with_safe_defaults` | Confirms development environment defaults | **PASS** |
| `test_environment_variables_override_yaml` | Validates environment variable precedence | **PASS** |
| `test_missing_production_secret_detected` | Ensures missing secrets fail cleanly | **PASS** |
| `test_insecure_placeholder_secret_rejected` | Ensures placeholder keys (`CHANGE_ME`) fail | **PASS** |
| `test_valid_production_secret_and_cors_pass` | Verifies compliant production setup passes | **PASS** |
| `test_cors_validation_in_production` | Rejects empty or wildcard CORS in production | **PASS** |
| `test_model_registry_path_validation` | Catches invalid model registry paths | **PASS** |
| `test_no_secrets_appear_in_string_or_logs` | Confirms redaction in strings and summaries | **PASS** |

### Test Suite Execution Summary
- **Pytest Suite:** **97 / 97 tests PASSED (100% passing in 12.18s)**
  - Baseline: 88 tests
  - Phase 10 Step 3 tests: 9 tests
- **Integration Test Suite:** **39 / 39 scenarios PASSED (100% passing)**
