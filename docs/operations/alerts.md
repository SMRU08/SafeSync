# Alerts & External Notification Providers

RAKSHYA VISION couples intelligent local alert deduplication with an extensible external notification architecture to dispatch safety alerts to enterprise channels without overwhelming operators.

---

## 1. Alert Deduplication & Cooldown

When a worker remains non-compliant across hundreds of frames, sending hundreds of separate notifications would flood operators and silence legitimate alarms. The `AlertEngine` enforces multi-layer anti-flood protections:

```
Normalized Safety Event
          │
          ▼
┌────────────────────────────────────────────────────────┐
│               Deduplication Evaluation                 │
│  - Match existing OPEN Incident (Camera + Worker + Type)│
└─────────┬────────────────────────────────────┬─────────┘
          │ (New Incident)                     │ (Existing Ongoing Incident)
          ▼                                    ▼
┌──────────────────┐                 ┌───────────────────────────┐
│ Create Incident  │                 │ In Cooldown Window?       │
│ & Emit Alert     │                 │ (e.g. within 60 seconds)  │
└─────────┬────────┘                 └─────┬───────────────┬─────┘
          │                                │ (Yes)         │ (No - Expired)
          │                                ▼               ▼
          │                         Suppress Alert    Emit Escalated Alert
          ▼                                           & Reset Cooldown
┌────────────────────────────────────────────────────────┐
│         External Provider Dispatch (Async)             │
│   (Webhook, SMTP Email, Industrial SMS)                │
└────────────────────────────────────────────────────────┘
```

### 1.1 Cooldown Windows
Configured in `configs/alert_policy.yaml`:
- **Default Cooldown:** 60 seconds between repeat notifications for the same ongoing incident.
- **Persistence Escalation:** If a safety violation remains unaddressed for longer than 120 seconds, the incident severity automatically escalates from `MEDIUM` to `HIGH` or `HIGH` to `CRITICAL`, triggering an escalated alert override.

---

## 2. External Alert Provider Architecture

External dispatches are decoupled from the core vision pipeline via a background `ThreadPoolExecutor` managed by `ProviderRegistry`:

```
               ┌────────────────────────────────────────────────────────┐
               │                      AlertEngine                       │
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
      │ HMAC-SHA256 Sig  │      │ STARTTLS SMTP    │      │ Extensible API   │
      │ Timeout: 3.0s    │      │ Timeout: 5.0s    │      │ Zero Fake Claims │
      └──────────────────┘      └──────────────────┘      └──────────────────┘
```

### 2.1 Operational Guarantees
1. **Zero Fake Claims:** The system strictly reports `NOT_CONFIGURED` if recipient credentials or webhooks are missing. It never logs "SMS Sent" or "Email Sent" unless network delivery actually succeeds.
2. **Fault Isolation:** If an external webhook server is down (HTTP 500) or SMTP times out, the error is caught, logged, and marked `ERROR`. The computer vision pipeline, worker tracking, and database recording continue without disruption.

---

## 3. Supported Providers

### 3.1 Webhook Provider (`WebhookProvider`)
- Dispatches HTTP POST JSON requests to `WEBHOOK_URL`.
- Includes cryptographic HMAC-SHA256 signature in the `X-Rakshya-Signature` header computed using `WEBHOOK_SECRET`.
- Enforces a strict 3.0-second network timeout with up to 2 retries.

### 3.2 Email Provider (`EmailProvider`)
- Dispatches plain text safety notifications via standard library `smtplib` using STARTTLS encryption.
- Configured via environment variables: `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USERNAME`, `EMAIL_PASSWORD`, `EMAIL_FROM_ADDRESS`, `EMAIL_RECIPIENTS`.
- Enforces a 5.0-second connection timeout.

### 3.3 SMS / Gateway Provider (`SmsProvider`)
- Modular interface ready for industrial SMS gateways (Twilio, AWS SNS, GSM Modems).
- Reports `NOT_CONFIGURED` until active API keys are supplied.
