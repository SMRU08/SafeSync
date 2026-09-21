"""
schemas.py — RAKSHYA VISION Phase 10 Step 5
Camera models, lifecycle states, and operational metrics schemas.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CameraState(str, Enum):
    DISABLED = "DISABLED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    RECONNECTING = "RECONNECTING"
    DEGRADED = "DEGRADED"
    DISCONNECTED = "DISCONNECTED"
    ERROR = "ERROR"


class CameraSourceType(str, Enum):
    RTSP = "rtsp"
    USB = "usb"
    FILE = "file"
    SYNTHETIC = "synthetic"


class ReconnectPolicy(BaseModel):
    max_retries: int = Field(default=5, ge=0, description="Maximum consecutive reconnection retries")
    initial_delay_seconds: float = Field(default=1.0, ge=0.01, description="Initial retry delay in seconds")
    max_delay_seconds: float = Field(default=30.0, ge=0.01, description="Upper bound for exponential backoff")


class CameraConfigModel(BaseModel):
    id: str = Field(..., description="Unique camera identifier, e.g. camera_01")
    name: str = Field(..., description="Human readable camera name")
    zone_id: str = Field(default="UNKNOWN", description="Associated facility zone identifier")
    source: str = Field(..., description="Camera source URL, device index, or file path")
    source_type: CameraSourceType = Field(default=CameraSourceType.USB)
    enabled: bool = Field(default=True)
    fps_target: int = Field(default=30, ge=1, le=120)
    resolution: Optional[str] = Field(default="1280x720")
    timeout_seconds: float = Field(default=5.0, ge=0.5)
    reconnect_policy: ReconnectPolicy = Field(default_factory=ReconnectPolicy)


class CameraMetrics(BaseModel):
    fps: float = Field(default=0.0, description="Actual processed frames per second")
    frame_count: int = Field(default=0, description="Total frames captured successfully")
    dropped_frames: int = Field(default=0, description="Frames dropped due to buffer overrun or read failure")
    reconnect_count: int = Field(default=0, description="Total reconnect attempts performed")
    last_successful_frame_timestamp: Optional[float] = Field(default=None)
    last_error: Optional[str] = Field(default=None)
    uptime_seconds: float = Field(default=0.0)


class CameraStatus(BaseModel):
    camera_id: str
    name: str
    zone_id: str
    source_type: str
    enabled: bool
    state: CameraState
    metrics: CameraMetrics
    safe_source: str = Field(..., description="Sanitized source with passwords and credentials masked")
