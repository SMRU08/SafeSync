"""
webhook_provider.py — SafeSync Phase 10 Step 8
Production Webhook Alert Provider with HMAC-SHA256 Signatures,
bounded timeout (3.0s), and bounded retries.
"""

import hmac
import hashlib
import json
import logging
from typing import Optional
import urllib.request
import urllib.error

from app.services.alert_providers.base import (
    BaseAlertProvider,
    ProviderStatus,
    AlertNotificationPayload,
)

logger = logging.getLogger("webhook_provider")


class WebhookProvider(BaseAlertProvider):
    """
    Delivers safety alerts via HTTP/HTTPS POST webhooks with optional HMAC signature.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        secret: Optional[str] = None,
        enabled: bool = False,
        timeout_seconds: float = 3.0,
        max_retries: int = 2,
    ):
        super().__init__(name="Webhook")
        self.url = url
        self.secret = secret
        self.enabled = enabled
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

        self._evaluate_status()

    def _evaluate_status(self):
        if not self.enabled:
            self.status = ProviderStatus.DISABLED
        elif not self.url or not self.url.strip():
            self.status = ProviderStatus.NOT_CONFIGURED
        else:
            self.status = ProviderStatus.ENABLED

    def _generate_signature(self, payload_bytes: bytes) -> Optional[str]:
        if not self.secret:
            return None
        return hmac.new(
            self.secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()

    def send_alert(self, payload: AlertNotificationPayload) -> bool:
        if self.status != ProviderStatus.ENABLED or not self.url:
            return False

        payload_json = json.dumps(payload.model_dump()).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "SafeSync-ALERT-SYSTEM/2.0",
        }

        signature = self._generate_signature(payload_json)
        if signature:
            headers["X-SafeSync-Signature"] = signature

        req = urllib.request.Request(self.url, data=payload_json, headers=headers, method="POST")

        attempts = 0
        last_exc: Optional[Exception] = None

        while attempts <= self.max_retries:
            attempts += 1
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                    if 200 <= response.status < 300:
                        self.total_dispatched += 1
                        self.last_error = None
                        self.status = ProviderStatus.ENABLED
                        logger.info("Successfully delivered webhook alert %s to %s", payload.alert_id, self.url)
                        return True
                    else:
                        raise urllib.error.HTTPError(
                            self.url, response.status, f"HTTP {response.status}", response.headers, None
                        )
            except Exception as e:
                last_exc = e
                logger.warning(
                    "Webhook delivery attempt %d/%d failed for %s: %s",
                    attempts,
                    self.max_retries + 1,
                    self.url,
                    e,
                )

        # Reached max retries
        self.total_failed += 1
        self.last_error = str(last_exc)
        self.status = ProviderStatus.ERROR
        logger.error("Webhook alert delivery permanently failed after %d attempts: %s", attempts, last_exc)
        return False
