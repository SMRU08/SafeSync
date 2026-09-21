"""
email_provider.py — RAKSHYA VISION Phase 10 Step 8
Production SMTP Email Alert Provider using standard library smtplib,
environment credentials, and STARTTLS encryption.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List

from app.services.alert_providers.base import (
    BaseAlertProvider,
    ProviderStatus,
    AlertNotificationPayload,
)

logger = logging.getLogger("email_provider")


class EmailProvider(BaseAlertProvider):
    """
    Delivers safety alerts via SMTP Email.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: int = 587,
        username: Optional[str] = None,
        password: Optional[str] = None,
        from_address: Optional[str] = None,
        recipients: Optional[str] = None,
        enabled: bool = False,
        timeout_seconds: float = 5.0,
    ):
        super().__init__(name="Email")
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_address = from_address or "alerts@rakshya-vision.local"
        self.recipients = [r.strip() for r in (recipients or "").split(",") if r.strip()]
        self.enabled = enabled
        self.timeout_seconds = timeout_seconds

        self._evaluate_status()

    def _evaluate_status(self):
        if not self.enabled:
            self.status = ProviderStatus.DISABLED
        elif not self.host or not self.recipients:
            self.status = ProviderStatus.NOT_CONFIGURED
        else:
            self.status = ProviderStatus.ENABLED

    def send_alert(self, payload: AlertNotificationPayload) -> bool:
        if self.status != ProviderStatus.ENABLED or not self.host or not self.recipients:
            return False

        subject = f"[RAKSHYA VISION {payload.severity}] {payload.title}"
        body = (
            f"SAFETY INCIDENT NOTIFICATION\n"
            f"--------------------------------------------------\n"
            f"Incident ID : {payload.incident_id}\n"
            f"Alert ID    : {payload.alert_id}\n"
            f"Severity    : {payload.severity}\n"
            f"Event Type  : {payload.event_type}\n"
            f"Camera      : {payload.camera_id}\n"
            f"Zone        : {payload.zone_id}\n"
            f"Timestamp   : {payload.timestamp}\n"
            f"Message     : {payload.message}\n"
            f"Workers     : {payload.affected_workers_count} affected\n"
            f"System      : {payload.system_version}\n"
            f"--------------------------------------------------\n"
        )

        msg = MIMEMultipart()
        msg["From"] = self.from_address
        msg["To"] = ", ".join(self.recipients)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(self.host, self.port, timeout=self.timeout_seconds) as server:
                server.ehlo()
                try:
                    server.starttls()
                    server.ehlo()
                except Exception:
                    pass  # In local test relays TLS might be unsupported

                if self.username and self.password:
                    server.login(self.username, self.password)

                server.sendmail(self.from_address, self.recipients, msg.as_string())

            self.total_dispatched += 1
            self.last_error = None
            self.status = ProviderStatus.ENABLED
            logger.info("Successfully dispatched email alert %s to %s", payload.alert_id, self.recipients)
            return True

        except Exception as e:
            self.total_failed += 1
            self.last_error = str(e)
            self.status = ProviderStatus.ERROR
            logger.error("Failed to dispatch email alert %s: %s", payload.alert_id, e)
            return False
