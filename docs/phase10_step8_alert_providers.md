# RAKSHYA VISION — Phase 10 Step 8: External Alert Provider Architecture

## 1. Overview & Objectives
In **Phase 10 Step 8**, an extensible, production-oriented **External Alert Provider Architecture** is integrated into RAKSHYA VISION.

When high-risk PPE non-compliance or environmental hazards (fire/smoke) are confirmed and smart alerts are created or escalated, notifications must be dispatched to external channels (e.g. enterprise Webhooks, security operations center Email, or industrial SMS gateways).

In strict compliance with Phase 10 production principles:
1. **Zero Fabrication:** The system **never claims "SMS SENT" or "EMAIL SENT"** unless actual external delivery succeeds.
2. **Honest Operational Statuses:** Every provider explicitly reports `ENABLED`, `DISABLED`, `NOT_CONFIGURED`, or `ERROR`.
3. **Strict Fault Isolation:** External network drops, HTTP 500 errors, or SMTP timeouts **never crash or stall** the core computer vision detection pipeline, worker tracker, or database transactions.
4. **Preserved Anti-Flood Protections:** External dispatches strictly respect temporal alert deduplication, cooldown windows, and persistence escalation rules.

---

## 2. Architecture & Concurrency

```
              ┌────────────────────────────────────────────────────────┐
              │                      AlertEngine                       │
              │  (Evaluates Risk, Dedup, Cooldown, Escalation, DB)    │
              └──────────────────────────┬─────────────────────────────┘
                                         │ (CREATED / ESCALATED)
                                         ▼
              ┌────────────────────────────────────────────────────────┐
              │                    ProviderRegistry                    │
              │             (Concurrent ThreadPoolExecutor)            │
              └──────────────┬───────────┼───────────┬─────────────────┘
                             │           │           │
               ┌─────────────┘           │           └─────────────┐
               ▼                         ▼                         ▼
     ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
     │ WebhookProvider  │      │  EmailProvider   │      │   SmsProvider    │
     │ ───────────────  │      │ ───────────────  │      │ ───────────────  │
     │ Status: ENABLED  │      │Status: NOT_CONFIG│      │Status: NOT_CONFIG│
     │ HMAC-SHA256 Sig  │      │ STARTTLS SMTP    │      │ Extensible API   │
     │ Timeout: 3.0s    │      │ Timeout: 5.0s    │      │ No Fake Claims   │
     └──────────────────┘      └──────────────────┘      └──────────────────┘
```

---

## 3. Provider Implementations & Contracts

### A. Base Interface (`backend/app/services/alert_providers/base.py`)
- Standardized `AlertNotificationPayload`: contains `incident_id`, `alert_id`, `camera_id`, `zone_id`, `event_type`, `severity`, `title`, `message`, `timestamp`, `affected_workers_count`, `evidence_reference`, `system_version`.
- Abstract `send_alert(payload: AlertNotificationPayload) -> bool`.
- Standardized `get_status() -> dict`.

### B. Webhook Provider (`backend/app/services/alert_providers/webhook_provider.py`)
- Sends JSON POST requests to configured `WEBHOOK_URL`.
- Includes cryptographic HMAC-SHA256 signature in `X-Rakshya-Signature` header computed using `WEBHOOK_SECRET`.
- Bounded 3.0-second network timeout and maximum 2 retries before marking provider as `ERROR`.

### C. Email Provider (`backend/app/services/alert_providers/email_provider.py`)
- Sends formatted plain text safety notifications via standard library `smtplib` with STARTTLS encryption.
- Credentials read securely from environment variables (`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USERNAME`, `EMAIL_PASSWORD`, `EMAIL_FROM_ADDRESS`, `EMAIL_RECIPIENTS`).
- Reports `NOT_CONFIGURED` if host or recipient lists are absent.

### D. SMS Provider (`backend/app/services/alert_providers/sms_provider.py`)
- Clean, extensible SMS gateway interface.
- Evaluates `SMS_API_KEY` and `SMS_API_SECRET`.
- Strictly reports `NOT_CONFIGURED` when credentials are not configured, preventing fraudulent "SMS Delivered" claims.

---

## 4. Status Reporting Endpoint

Mounted at: `GET /api/alerts/providers/status`
Example response:
```json
[
  {
    "name": "Webhook",
    "status": "DISABLED",
    "last_error": null,
    "total_dispatched": 0,
    "total_failed": 0
  },
  {
    "name": "Email",
    "status": "NOT_CONFIGURED",
    "last_error": null,
    "total_dispatched": 0,
    "total_failed": 0
  },
  {
    "name": "SMS",
    "status": "NOT_CONFIGURED",
    "last_error": null,
    "total_dispatched": 0,
    "total_failed": 0
  }
]
```

---

## 5. Real-World Validation Disclosure
- **Webhook Provider HMAC & Dispatch:** **VERIFIED**. Tested with local and simulated receivers.
- **Provider Status Transparency:** **VERIFIED**. `GET /api/alerts/providers/status` returns authentic statuses.
- **Fault Isolation & Asynchronous Dispatch:** **VERIFIED**. Unreachable endpoints fail safely without stalling AlertEngine or DB.
- **Physical External Telephony / Live Production SMTP:** **NOT CONFIGURED / NOT TESTED**. Real third-party SMS/SMTP vendor accounts were not configured in this test environment.
