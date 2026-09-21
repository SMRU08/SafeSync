"""
base.py — RAKSHYA VISION Phase 10 Step 8
Abstract Base Class, Data Models, and Status Enums for External Alert Providers.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ProviderStatus(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    ERROR = "ERROR"


class AlertNotificationPayload(BaseModel):
    """Normalized payload dispatched to external alert channels."""
    incident_id: str
    alert_id: str
    camera_id: str
    zone_id: str
    event_type: str
    severity: str
    title: str
    message: str
    timestamp: str
    affected_workers_count: int = 0
    evidence_reference: Optional[str] = None
    system_version: str = "RAKSHYA VISION 2.0 (Phase 10)"


class BaseAlertProvider(ABC):
    """
    Abstract interface for external alert notification channels (Webhook, Email, SMS).
    Guarantees fault isolation and honest status reporting without fake delivery receipts.
    """

    def __init__(self, name: str):
        self.name = name
        self.status: ProviderStatus = ProviderStatus.NOT_CONFIGURED
        self.last_error: Optional[str] = None
        self.total_dispatched: int = 0
        self.total_failed: int = 0

    @abstractmethod
    def send_alert(self, payload: AlertNotificationPayload) -> bool:
        """
        Sends an alert notification.
        Returns True on confirmed delivery, False on failure.
        MUST NOT raise unhandled exceptions.
        """
        pass

    def get_status(self) -> Dict[str, Any]:
        """Returns the current operational status of the provider."""
        return {
            "name": self.name,
            "status": self.status.value,
            "last_error": self.last_error,
            "total_dispatched": self.total_dispatched,
            "total_failed": self.total_failed,
        }
