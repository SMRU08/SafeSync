"""
websocket.py — RAKSHYA VISION Phase 8
FastAPI WebSocket Router for Real-Time Safety Alerts & Live Event Broadcasting.
Bridges the Phase 7 EventBroadcaster singleton with connected frontend clients.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Set, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

try:
    from app.services.event_broadcaster import broadcaster
except ImportError:
    from backend.app.services.event_broadcaster import broadcaster

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


class WebSocketManager:
    """
    Manages active client WebSocket connections and dispatches events from EventBroadcaster.
    """

    def __init__(self):
        self._active_connections: Set[WebSocket] = set()
        self._client_queues: Dict[WebSocket, asyncio.Queue] = {}
        self._loop: asyncio.AbstractEventLoop | None = None
        self._listener_registered = False

    def _ensure_listener(self):
        if not self._listener_registered:
            broadcaster.subscribe(self._on_broadcaster_event)
            self._listener_registered = True
            logger.info("WebSocketManager registered as subscriber to EventBroadcaster.")

    def _on_broadcaster_event(self, event_name: str, payload: Dict[str, Any]):
        """
        Callback invoked by EventBroadcaster whenever a safety alert or incident event occurs.
        """
        message = {
            "type": "event",
            "event": event_name,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Thread-safe bounded enqueue to all client queues (drops oldest on full)
        def _safe_put(q: asyncio.Queue, msg: Any):
            if q.full():
                try:
                    q.get_nowait()
                except Exception:
                    pass
            try:
                q.put_nowait(msg)
            except Exception as err:
                logger.debug("Failed to enqueue message to websocket: %s", err)

        for ws, queue in list(self._client_queues.items()):
            if self._loop and self._loop.is_running():
                self._loop.call_soon_threadsafe(_safe_put, queue, message)
            else:
                _safe_put(queue, message)

    async def connect(self, websocket: WebSocket) -> asyncio.Queue:
        await websocket.accept()
        self._loop = asyncio.get_running_loop()
        self._ensure_listener()

        queue: asyncio.Queue = asyncio.Queue(maxsize=50)
        self._active_connections.add(websocket)
        self._client_queues[websocket] = queue

        logger.info(
            "WebSocket client connected. Active connections: %d",
            len(self._active_connections),
        )

        # Send initial welcome / handshake payload
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to RAKSHYA VISION Live Event Stream",
            "active_connections": len(self._active_connections),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return queue

    def disconnect(self, websocket: WebSocket):
        if websocket in self._active_connections:
            self._active_connections.remove(websocket)
        if websocket in self._client_queues:
            del self._client_queues[websocket]
        logger.info(
            "WebSocket client disconnected. Remaining connections: %d",
            len(self._active_connections),
        )

    @property
    def active_count(self) -> int:
        return len(self._active_connections)


manager = WebSocketManager()


@router.websocket("/ws/alerts")
@router.websocket("/ws/events")
async def websocket_alerts_endpoint(
    websocket: WebSocket,
    token: Optional[str] = None,
):
    """
    Live WebSocket channel streaming safety alerts, incident changes, and system notifications.
    Supports bi-directional heartbeat ping/pong.
    Requires valid token when AUTH_ENABLED=True.
    """
    from app.config import settings
    if settings.AUTH_ENABLED:
        if not token:
            await websocket.close(code=4001, reason="Authentication token required")
            return
        try:
            from app.security.auth import decode_access_token
            decode_access_token(token)
        except Exception:
            await websocket.close(code=4003, reason="Invalid or expired token")
            return

    queue = await manager.connect(websocket)

    async def send_loop():
        try:
            while True:
                msg = await queue.get()
                await websocket.send_json(msg)
                queue.task_done()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.debug("WebSocket send_loop ended: %s", e)

    send_task = asyncio.create_task(send_loop())

    try:
        while True:
            data = await websocket.receive_text()
            # Handle client heartbeat or ping
            try:
                parsed = json.loads(data)
                if parsed.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
            except (json.JSONDecodeError, TypeError):
                if data.strip().lower() == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
    except WebSocketDisconnect:
        logger.info("Client cleanly disconnected from WebSocket.")
    except Exception as exc:
        logger.warning("WebSocket connection exception: %s", exc)
    finally:
        send_task.cancel()
        manager.disconnect(websocket)
