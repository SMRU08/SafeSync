# RAKSHYA VISION — Phase 10 Step 7: Authentication & Role-Based Access Control (RBAC)

## 1. Overview & Objective
In **Phase 10 Step 7**, RAKSHYA VISION transitions from open access to an enterprise-grade **Authentication and Role-Based Access Control (RBAC)** security architecture.

In industrial facility operations, unauthorized individuals must never be permitted to stop safety monitoring cameras, dismiss critical fire/smoke alarms, or provision system credentials. Step 7 establishes strong cryptographic guarantees, strict user tiering, and an immutable audit trail.

---

## 2. Cryptographic Security Standards

1. **Password Hashing:**
   - **Algorithm:** PBKDF2-HMAC-SHA256
   - **Iterations:** 600,000 (exceeding OWASP recommendations)
   - **Salting:** Cryptographically secure 16-byte random salt per user (`os.urandom(16)`)
   - **Verification:** Constant-time hash verification (`hmac.compare_digest`) to prevent timing side-channel attacks.
   - **Storage Format:** `pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>`
2. **JWT Access Tokens:**
   - Standard PyJWT signed tokens with HMAC-SHA256 (`HS256`).
   - Sourced strictly from configuration environment variables (`JWT_SECRET_KEY` / `SECRET_KEY`).
   - Token payload encapsulates `sub` (username), `role`, `iat` (issued at), and `exp` (expiration).
   - Configurable expiration window (`ACCESS_TOKEN_EXPIRE_MINUTES`, default 480 minutes / 8 hours).

---

## 3. Role-Based Access Control (RBAC) Tiers

Three distinct operational tiers are enforced:

| Role | Permissions |
| :--- | :--- |
| **`ADMIN`** | Full access: User provisioning, role assignment, security audit log review, camera start/stop/register, and incident resolution/dismissal. |
| **`OPERATOR`** | Operations access: Camera feed inspection, camera worker start/stop, live WebSocket streaming, and incident acknowledgement & resolution. |
| **`VIEWER`** | Read-only access: Monitoring dashboards, read-only camera lists, live telemetry, and incident review. Cannot modify cameras or alerts. |

---

## 4. Protected Endpoints & Audit Logging

### Protected Routes:
- `POST /api/cameras/{id}/start`: Requires `ADMIN` or `OPERATOR`.
- `POST /api/cameras/{id}/stop`: Requires `ADMIN` or `OPERATOR`.
- `POST /api/cameras`: Requires `ADMIN`.
- `POST /api/alerts/{id}/acknowledge`: Requires `ADMIN` or `OPERATOR`.
- `POST /api/alerts/{id}/resolve`: Requires `ADMIN` or `OPERATOR`.
- `POST /api/alerts/{id}/dismiss`: Requires `ADMIN` or `OPERATOR`.
- `POST /api/auth/users`: Requires `ADMIN`.
- `GET /api/auth/audit-logs`: Requires `ADMIN`.
- `WebSocket /ws/alerts?token=...`: Requires valid token when `AUTH_ENABLED=True`.

### Immutable Audit Trail (`audit_logs` Table):
Records all security-sensitive actions:
- `LOGIN_SUCCESS`, `LOGIN_FAILED`, `LOGIN_BLOCKED`
- `USER_CREATED`
- Camera worker starts/stops
- Incident acknowledgement/resolution

---

## 5. Development Mode Safe Fallback
When running in local development mode (`AUTH_ENABLED=False`), a default `dev_admin` profile is provided automatically to ensure existing automated test suites, CLI tools, and developers can work seamlessly without authentication friction.
