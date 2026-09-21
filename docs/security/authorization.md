# Role-Based Access Control (RBAC)

RAKSHYA VISION enforces strict Role-Based Access Control (RBAC) to ensure that users only possess the permissions necessary for their operational duties.

---

## 1. Operational User Roles

Three standardized roles govern access to the system:

```
┌──────────────────┐
│     ADMIN        │ Full administrative access (Users, Camera Registration, Audits)
└────────┬─────────┘
         │ inherits
         ▼
┌──────────────────┐
│    OPERATOR      │ Safety Operations (Acknowledge/Resolve Incidents, Start/Stop Feeds)
└────────┬─────────┘
         │ inherits
         ▼
┌──────────────────┐
│     VIEWER       │ Read-only inspection (Monitoring Dashboards, Telemetry, Video Grids)
└──────────────────┘
```

---

## 2. Permission Matrix

| Operation / Endpoint | Required Role | VIEWER | OPERATOR | ADMIN |
|---|---|:---:|:---:|:---:|
| View Live Cameras & Metrics (`GET /api/cameras`) | `VIEWER` | Yes | Yes | Yes |
| View Safety Incidents (`GET /api/incidents`) | `VIEWER` | Yes | Yes | Yes |
| View System Health & Observability (`/health/*`) | Public / `VIEWER` | Yes | Yes | Yes |
| Start/Stop Camera Workers (`POST /api/cameras/{id}/start`) | `OPERATOR` | No | Yes | Yes |
| Acknowledge Incident (`POST /api/alerts/{id}/acknowledge`) | `OPERATOR` | No | Yes | Yes |
| Resolve Incident (`POST /api/alerts/{id}/resolve`) | `OPERATOR` | No | Yes | Yes |
| Dismiss Incident (`POST /api/alerts/{id}/dismiss`) | `OPERATOR` | No | Yes | Yes |
| Register New Camera (`POST /api/cameras`) | `ADMIN` | No | No | Yes |
| User Provisioning (`POST /api/auth/users`) | `ADMIN` | No | No | Yes |
| Inspect Security Audit Logs (`GET /api/auth/audit-logs`) | `ADMIN` | No | No | Yes |

---

## 3. Route Protection Enforcement

FastAPI route handlers enforce permissions declaratively using dependency injection:

```python
from app.api.auth import require_role
from app.models.auth import UserRole

@router.post("/cameras/{camera_id}/start")
def start_camera(
    camera_id: str,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR]))
):
    # Only ADMIN or OPERATOR can execute this block
    ...
```

If an authenticated user with role `VIEWER` attempts to start a camera or dismiss an alert, FastAPI immediately returns:
`HTTP 403 Forbidden: "Insufficient permissions for this operation."`

---

## 4. Security Audit Logging

All privileged and security-sensitive actions are recorded permanently in the `audit_logs` table:

```json
{
  "id": 482,
  "action": "CAMERA_STOP",
  "username": "safety_officer_1",
  "target": "camera_02",
  "client_ip": "192.168.1.145",
  "timestamp": "2026-09-21T18:42:10.000Z"
}
```

Logged events include:
- Authentication attempts: `LOGIN_SUCCESS`, `LOGIN_FAILED`, `LOGIN_BLOCKED`
- User management: `USER_CREATED`, `USER_DISABLED`
- Device control: `CAMERA_STARTED`, `CAMERA_STOPPED`, `CAMERA_REGISTERED`
- Incident actions: `INCIDENT_ACKNOWLEDGED`, `INCIDENT_RESOLVED`, `INCIDENT_DISMISSED`
