# Production Deployment Guide

This guide details best practices for deploying SafeSync in enterprise and industrial edge environments.

---

## 1. Production Architecture

In production, SafeSync typically runs on an industrial edge server (e.g. Advantech, Dell Edge, or custom x86/ARM rack units) located on the same local area network as the facility's CCTV and IP cameras:

```
[ IP Cameras / CCTV ]
         │ (RTSP over LAN)
         ▼
┌────────────────────────────────────────────────────────┐
│               Industrial Edge Server                   │
│                                                        │
│  ┌──────────────────┐          ┌────────────────────┐  │
│  │ Nginx (Reverse   │          │ Static UI Assets   │  │
│  │ Proxy / SSL)     ├─────────►│ (dist/ HTML/JS/CSS)│  │
│  └─────────┬────────┘          └────────────────────┘  │
│            │ HTTP / WS                                 │
│            ▼                                           │
│  ┌──────────────────┐          ┌────────────────────┐  │
│  │ FastAPI Backend  │          │ SQLite WAL DB      │  │
│  │ (Uvicorn Service)├─────────►│ & Evidence Store   │  │
│  └──────────────────┘          └────────────────────┘  │
└────────────────────────────────────────────────────────┘
         │ (HTTPS / WSS over Intranet)
         ▼
[ Security Operations Center / Browser Clients ]
```

---

## 2. Process Supervision with Systemd

Create a dedicated systemd service for the backend API:
`/etc/systemd/system/safesync-backend.service`

```ini
[Unit]
Description=SafeSync AI Safety Backend Service
After=network.target

[Service]
Type=simple
User=safetyapp
Group=safetyapp
WorkingDirectory=/opt/safesync/backend
Environment="PATH=/opt/safesync/backend/.venv/bin"
EnvironmentFile=/opt/safesync/.env
ExecStart=/opt/safesync/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 --log-config /opt/safesync/configs/logging.yaml
Restart=always
RestartSec=5
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

> [!NOTE]
> Single worker mode (`--workers 1`) is strongly recommended when using in-memory `EventBroadcaster` and multi-threaded `CameraManager` to maintain unified in-memory tracking states across all cameras.

---

## 3. Reverse Proxy Configuration (Nginx)

Nginx handles HTTPS termination, serves static frontend assets, and proxies WebSocket connections:
`/etc/nginx/sites-available/safesync.conf`

```nginx
server {
    listen 80;
    server_name safety.internal.plant;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name safety.internal.plant;

    ssl_certificate /etc/ssl/certs/safesync.crt;
    ssl_certificate_key /etc/ssl/private/safesync.key;
    ssl_protocols TLSv1.2 TLSv1.3;

    # Static Frontend Assets
    root /opt/safesync/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend REST API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket Real-Time Channel
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
```

---

## 4. Maintenance Automation

Add daily maintenance to the server's crontab (`crontab -e`):

```bash
# Prune resolved incidents older than 30 days and evidence exceeding quota daily at 02:00
0 2 * * * /opt/safesync/backend/.venv/bin/python /opt/safesync/scripts/cleanup_retention.py --retention-days 30 --mode prune >> /var/log/safesync-retention.log 2>&1
```
