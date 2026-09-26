"""
registry.py — SafeSync Phase 10 Step 8
Central Provider Registry managing external alert notifications concurrently
with complete fault isolation and honest status aggregation.
"""

import logging
from typing import Dict, List, Any
import concurrent.futures

from app.config import settings
from app.services.alert_providers.base import (
    BaseAlertProvider,
    AlertNotificationPayload,
    ProviderStatus,
)
from app.services.alert_providers.webhook_provider import WebhookProvider
from app.services.alert_providers.email_provider import EmailProvider
from app.services.alert_providers.sms_provider import SmsProvider

logger = logging.getLogger("provider_registry")


class ProviderRegistry:
    """
    Singleton registry tracking all configured external notification channels.
    """
    _instance: "ProviderRegistry" = None

    def __init__(self):
        self.providers: Dict[str, BaseAlertProvider] = {}
        self._init_providers()

    @classmethod
    def get_instance(cls) -> "ProviderRegistry":
        if cls._instance is None:
            cls._instance = ProviderRegistry()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        cls._instance = None

    def _init_providers(self):
        # 1. Webhook Provider
        self.providers["webhook"] = WebhookProvider(
            url=settings.WEBHOOK_URL,
            secret=settings.WEBHOOK_SECRET,
            enabled=settings.ALERT_WEBHOOK_ENABLED,
        )

        # 2. Email Provider
        self.providers["email"] = EmailProvider(
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_USERNAME,
            password=settings.EMAIL_PASSWORD,
            from_address=settings.EMAIL_FROM_ADDRESS,
            recipients=settings.EMAIL_RECIPIENTS,
            enabled=settings.ALERT_EMAIL_ENABLED,
        )

        # 3. SMS Provider
        self.providers["sms"] = SmsProvider(
            api_key=settings.SMS_API_KEY,
            api_secret=settings.SMS_API_SECRET,
            enabled=settings.ALERT_SMS_ENABLED,
        )

    def dispatch_alert(self, payload: AlertNotificationPayload) -> Dict[str, bool]:
        """
        Dispatches an alert concurrently across all configured channels.
        Guarantees failures in one provider never affect other providers or the main process.
        """
        results: Dict[str, bool] = {}

        def _send(p_name: str, p_inst: BaseAlertProvider):
            try:
                ok = p_inst.send_alert(payload)
                status_str = "success" if ok else "failed"
                try:
                    from app.services.metrics import MetricsCollector
                    MetricsCollector.get_instance().increment_counter(
                        "safesync_alert_dispatches_total",
                        labels={"provider": p_name, "status": status_str}
                    )
                except Exception:
                    pass
                return p_name, ok
            except Exception as e:
                logger.error("Unexpected error in provider %s: %s", p_name, e)
                try:
                    from app.services.metrics import MetricsCollector
                    MetricsCollector.get_instance().increment_counter(
                        "safesync_alert_dispatches_total",
                        labels={"provider": p_name, "status": "error"}
                    )
                except Exception:
                    pass
                return p_name, False

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(_send, name, prov)
                for name, prov in self.providers.items()
                if prov.status == ProviderStatus.ENABLED
            ]
            for f in concurrent.futures.as_completed(futures):
                name, success = f.result()
                results[name] = success

        return results

    def get_all_statuses(self) -> List[Dict[str, Any]]:
        """Returns status dictionary for each registered alert provider."""
        return [prov.get_status() for prov in self.providers.values()]
