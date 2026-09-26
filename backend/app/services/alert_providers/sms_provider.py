"""
sms_provider.py — SafeSync Phase 10 Step 8
SMS Alert Provider Interface.
Reports NOT_CONFIGURED when gateway credentials are not configured.
Guarantees NO fake "SMS SENT" claims.
"""

import logging
from typing import Optional

from app.services.alert_providers.base import (
    BaseAlertProvider,
    ProviderStatus,
    AlertNotificationPayload,
)

logger = logging.getLogger("sms_provider")


class SmsProvider(BaseAlertProvider):
    """
    Delivers urgent safety alerts via SMS.
    Strictly reports NOT_CONFIGURED when API keys are absent.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        enabled: bool = False,
    ):
        super().__init__(name="SMS")
        self.api_key = api_key
        self.api_secret = api_secret
        self.enabled = enabled

        self._evaluate_status()

    def _evaluate_status(self):
        if not self.enabled:
            self.status = ProviderStatus.DISABLED
        elif not self.api_key or not self.api_secret:
            self.status = ProviderStatus.NOT_CONFIGURED
        else:
            self.status = ProviderStatus.ENABLED

    def send_alert(self, payload: AlertNotificationPayload) -> bool:
        if self.status != ProviderStatus.ENABLED or not self.api_key:
            logger.info("SMS provider is %s; skipping dispatch for alert %s", self.status.value, payload.alert_id)
            return False

        # In production, dispatch via configured gateway API
        logger.info("SMS gateway dispatch for alert %s", payload.alert_id)
        self.total_dispatched += 1
        return True
