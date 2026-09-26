# Authentication Architecture

SafeSync implements an enterprise-grade authentication subsystem to prevent unauthorized access to safety operations, camera controls, and incident management functions.

---

## 1. Password Hashing Standards

User credentials stored in the `users` table adhere to cryptographic best practices:

- **Algorithm:** PBKDF2-HMAC-SHA256
- **Work Factor:** 600,000 iterations (exceeding OWASP recommendations)
- **Salting:** Cryptographically secure 16-byte random salt per user generated via `os.urandom(16)`
- **Verification:** Constant-time hash comparison (`hmac.compare_digest`) preventing timing side-channel attacks
- **Storage Format:**
  `pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>`

```python
# Verification flow excerpt
def verify_password(plain_password: str, hashed_password: str) -> bool:
    parts = hashed_password.split("$")
    if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
        return False
    iterations, salt_hex, expected_hash_hex = int(parts[1]), parts[2], parts[3]
    salt = bytes.fromhex(salt_hex)
    computed = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(computed.hex(), expected_hash_hex)
```

---

## 2. JWT Access Tokens

Sessions are managed using signed JSON Web Tokens (JWT):

- **Algorithm:** HMAC-SHA256 (`HS256`)
- **Key Source:** `JWT_SECRET_KEY` environment variable
- **Validity Window:** 480 minutes (8 hours) by default, configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`
- **Token Claims:**
  - `sub`: Username / user identifier
  - `role`: Assigned RBAC role (`ADMIN`, `OPERATOR`, `VIEWER`)
  - `iat`: Timestamp of issuance
  - `exp`: Expiration timestamp

---

## 3. Authentication Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/login` | Validates credentials via OAuth2 Password Bearer flow; returns JWT access token. |
| `GET` | `/api/auth/me` | Returns profile and active role of authenticated user. |
| `POST` | `/api/auth/users` | Provisions a new user account (Requires `ADMIN` role). |
| `GET` | `/api/auth/audit-logs` | Retrieves security event audit trail (Requires `ADMIN` role). |

---

## 4. Development Mode Fallback

To support local rapid testing and automated test execution without hardcoded credentials, the authentication requirement is governed by:

```bash
AUTH_ENABLED=True   # Enforces JWT on all protected endpoints (default in production)
AUTH_ENABLED=False  # Treats requests as pre-authenticated 'dev_admin' (development only)
```

When `AUTH_ENABLED=True`, missing or invalid tokens return `HTTP 401 Unauthorized`.
