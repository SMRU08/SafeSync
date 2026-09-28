"""
schemas.py — SafeSync Phase 10 Step 5
Camera models, lifecycle states, and operational metrics schemas.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator


class CameraState(str, Enum):
    CONFIGURED = "CONFIGURED"
    DISABLED = "DISABLED"
    CONNECTING = "CONNECTING"
    ONLINE = "ONLINE"
    CONNECTED = "CONNECTED"
    STREAMING = "STREAMING"
    RECONNECTING = "RECONNECTING"
    DEGRADED = "DEGRADED"
    DISCONNECTED = "DISCONNECTED"
    OFFLINE = "OFFLINE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class CameraSourceType(str, Enum):
    RTSP = "rtsp"
    USB = "usb"
    FILE = "file"
    SYNTHETIC = "synthetic"
    HTTP = "http"
    NETWORK = "network"
    ANDROID = "android"


class ReconnectPolicy(BaseModel):
    max_retries: int = Field(default=5, ge=0, description="Maximum consecutive reconnection retries")
    initial_delay_seconds: float = Field(default=1.0, ge=0.01, description="Initial retry delay in seconds")
    max_delay_seconds: float = Field(default=30.0, ge=0.01, description="Upper bound for exponential backoff")


class CameraConfigModel(BaseModel):
    id: str = Field(..., description="Unique camera identifier, e.g. camera_01")
    name: str = Field(..., description="Human readable camera name")
    location: Optional[str] = Field(default="", description="Physical installation location")
    zone_id: str = Field(default="UNKNOWN", description="Associated facility zone identifier")
    source: str = Field(..., description="Camera source URL, device index, or file path")
    source_type: CameraSourceType = Field(default=CameraSourceType.USB)
    enabled: bool = Field(default=True)
    fps_target: int = Field(default=30, ge=1, le=120)
    resolution: Optional[str] = Field(default="1280x720")
    timeout_seconds: float = Field(default=5.0, ge=0.5)
    speaker_enabled: bool = Field(default=True, description="Speaker audio alert status (ON/OFF)")
    reconnect_policy: ReconnectPolicy = Field(default_factory=ReconnectPolicy)


class CameraMetrics(BaseModel):
    fps: float = Field(default=0.0, description="Actual processed frames per second")
    frame_count: int = Field(default=0, description="Total frames captured successfully")
    dropped_frames: int = Field(default=0, description="Frames dropped due to buffer overrun or read failure")
    reconnect_count: int = Field(default=0, description="Total reconnect attempts performed")
    last_successful_frame_timestamp: Optional[float] = Field(default=None)
    last_error: Optional[str] = Field(default=None)
    uptime_seconds: float = Field(default=0.0)
    inference_latency_ms: float = Field(default=0.0, description="Latest AI inference latency in milliseconds")
    active_workers: int = Field(default=0, description="Current number of tracked workers in frame")
    active_violations: int = Field(default=0, description="Current number of workers in violation state")
    active_hazards: int = Field(default=0, description="Current number of confirmed environmental hazards")
    capture_fps: float = Field(default=0.0, description="Camera capture loop frames per second")
    stream_latency_ms: float = Field(default=0.0, description="Latency from capture to stream delivery in ms")
    dropped_ai_frames: int = Field(default=0, description="Frames skipped for AI inference to maintain real-time display")
    frame_queue_depth: int = Field(default=0, description="Pending frame buffer depth (strictly bounded at 0 or 1)")
    latest_frame_id: int = Field(default=0, description="Monotonically increasing captured frame counter")


class CameraStatus(BaseModel):
    camera_id: str
    name: str
    location: Optional[str] = Field(default="")
    zone_id: str
    source_type: str
    enabled: bool
    speaker_enabled: bool = Field(default=True, description="Camera speaker audio alert status (ON/OFF)")
    state: CameraState
    status: str = Field(default="offline", description="online, streaming, offline, connecting, error, degraded")
    connection_status: str = Field(default="offline")
    is_streaming: bool = Field(default=False, description="True only when valid frames are actively flowing")
    last_frame_age_ms: Optional[int] = Field(default=None, description="Age of newest frame in milliseconds")
    frame_id: int = Field(default=0, description="Latest captured frame monotonic sequence number")
    last_frame_timestamp: Optional[float] = Field(default=None)
    stream_url: str = Field(default="")
    fps: float = Field(default=0.0)
    resolution: Optional[str] = Field(default="1280x720")
    last_seen: Optional[str] = Field(default=None)
    metrics: CameraMetrics
    safe_source: str = Field(..., description="Sanitized source with passwords and credentials masked")
    ai_analysis: Optional[Dict[str, Any]] = Field(default=None)


class CameraSpeakerToggleRequest(BaseModel):
    enabled: bool = Field(default=True, description="Camera speaker audio alert status (ON/OFF)")

    @model_validator(mode="before")
    @classmethod
    def parse_input(cls, data: Any) -> Any:
        if isinstance(data, str):
            try:
                import json
                parsed = json.loads(data)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
        return data
