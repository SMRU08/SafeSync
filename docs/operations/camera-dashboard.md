# Camera Dashboard & REST API

The Camera Dashboard provides security operations personnel and engineers with interactive control, live visual monitoring, and health telemetry across all registered cameras.

---

## 1. Camera REST API Reference

All endpoints are mounted under `/api/cameras`:

| Method | Path | Description | Access Level |
|---|---|---|---|
| `GET` | `/api/cameras` | Lists all registered cameras with live operational metrics. | Public / Viewer |
| `GET` | `/api/cameras/{id}` | Returns detailed status for a specific camera worker. | Public / Viewer |
| `POST` | `/api/cameras/{id}/start` | Starts the camera capture worker thread. | Operator / Admin |
| `POST` | `/api/cameras/{id}/stop` | Stops the camera worker and releases hardware resources. | Operator / Admin |
| `POST` | `/api/cameras` | Dynamically registers or updates a camera configuration. | Admin |
| `GET` | `/api/cameras/{id}/snapshot` | Returns the latest frame as an image stream (`image/jpeg`). | Public / Viewer |

---

## 2. Snapshot Retrieval API

The snapshot endpoint allows live visual inspection directly from web browsers or dashboard tiles:

```http
GET /api/cameras/camera_01/snapshot?annotated=true HTTP/1.1
Host: localhost:8000
```

### Query Parameters
- `annotated` (boolean, default: `true`):
  - `true`: Returns the frame overlaid with real-time YOLO bounding boxes, ByteTrack IDs, and anatomical PPE checklist status badges.
  - `false`: Returns the raw, unannotated optical sensor frame.

### Response Headers
- `Content-Type: image/jpeg`
- `X-Frame-Timestamp: 1726938600.123`
- `X-Inference-Latency-Ms: 38.5`

---

## 3. Operations Center UI Integration

The React 18 SOC Dashboard includes a dedicated **Live Cameras** view:

1. **Multi-Camera Grid:**
   Displays responsive video tiles for all configured cameras with live snapshot auto-refresh (1.0–2.0 second intervals).
2. **Telemetry Overlay:**
   Each camera card displays real-time telemetry:
   - Operational state badge (`CONNECTED`, `RECONNECTING`, `DISABLED`).
   - Frame rate counter (FPS) and dropped frames tally.
   - Inference latency in milliseconds.
   - Active worker count and hazard flags.
3. **Interactive Frame Tester:**
   Allows operators to manually upload single image frames to test AI model detections, anatomical PPE associations, and tracking responses against test patterns without modifying camera configurations.
