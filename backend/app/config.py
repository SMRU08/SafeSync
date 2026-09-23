"""
config.py — RAKSHYA VISION Phase 10 Step 3
Centralized, Typed Production Configuration System with Strict Secret Protection,
Environment Precedence, and CORS Validation.

Precedence:
  1. Environment Variables (os.environ / .env)
  2. Production Configuration (configs/production.yaml)
  3. Safe Application Defaults
"""

import os
import yaml
from typing import List, Optional, Any, Dict
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_PRODUCTION_CONFIG = os.path.join(ROOT, "configs", "production.yaml")
DEFAULT_REGISTRY_PATH = os.path.join(ROOT, "models", "registry", "model_registry.yaml")

DEVELOPMENT_CORS_DEFAULTS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

SENSITIVE_FIELD_NAMES = {
    "secret_key",
    "jwt_secret_key",
    "camera_password",
    "email_password",
    "webhook_secret",
    "sms_api_secret",
    "admin_password",
}

INSECURE_PLACEHOLDER_PREFIXES = (
    "change_me",
    "your_production",
    "placeholder",
    "default",
    "dev-secret",
    "rakshya-vision-dev",
)


def _load_raw_yaml_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Loads raw unflattened YAML configuration."""
    path = config_path or DEFAULT_PRODUCTION_CONFIG
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _load_yaml_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Loads and flattens YAML configuration into an uppercase dictionary."""
    path = config_path or DEFAULT_PRODUCTION_CONFIG
    if not os.path.isfile(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        return {}

    flattened = {}
    if "environment" in data:
        flattened["APP_ENV"] = data["environment"]

    server = data.get("server", {})
    if "host" in server:
        flattened["HOST"] = server["host"]
    if "port" in server:
        flattened["PORT"] = server["port"]
    if "cors_allowed_origins" in server:
        flattened["CORS_ORIGINS"] = server["cors_allowed_origins"]

    database = data.get("database", {})
    if "url" in database:
        flattened["DATABASE_URL"] = database["url"]

    model = data.get("model", {})
    if "registry_path" in model:
        flattened["MODEL_REGISTRY_PATH"] = model["registry_path"]

    camera = data.get("camera", {})
    if "config_file" in camera:
        flattened["CAMERA_CONFIG_PATH"] = camera["config_file"]

    retention = data.get("retention", {})
    if "evidence_days" in retention:
        flattened["EVIDENCE_RETENTION_DAYS"] = retention["evidence_days"]
    if "max_evidence_storage_gb" in retention:
        flattened["MAX_EVIDENCE_STORAGE_GB"] = float(retention["max_evidence_storage_gb"])

    logging_cfg = data.get("logging", {})
    if "log_file" in logging_cfg:
        flattened["LOG_FILE_PATH"] = logging_cfg["log_file"]
    if "level" in logging_cfg:
        flattened["LOG_LEVEL"] = logging_cfg["level"]
    if "max_bytes" in logging_cfg:
        flattened["LOG_MAX_BYTES"] = int(logging_cfg["max_bytes"])
    if "backup_count" in logging_cfg:
        flattened["LOG_BACKUP_COUNT"] = int(logging_cfg["backup_count"])

    return flattened


class Settings(BaseSettings):
    # Core Application Settings
    APP_NAME: str = "RAKSHYA VISION"
    APP_ENV: str = "development"  # 'development', 'test', 'production'
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite:///./rakshya_vision.db"

    # Paths
    MODEL_DIRECTORY: str = "../../models"
    DATASET_DIRECTORY: str = "../../datasets"
    MODEL_REGISTRY_PATH: str = "models/registry/model_registry.yaml"
    CAMERA_CONFIG_PATH: str = "configs/cameras.yaml"

    # Security & Secret Keys
    SECRET_KEY: Optional[str] = None
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    AUTH_ENABLED: bool = False

    # CORS Configuration
    CORS_ALLOWED_ORIGINS: Optional[str] = None
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: DEVELOPMENT_CORS_DEFAULTS.copy())

    # CCTV / Camera Credentials
    CAMERA_USERNAME: Optional[str] = None
    CAMERA_PASSWORD: Optional[str] = None

    # Alert Providers
    ALERT_WEBHOOK_ENABLED: bool = False
    WEBHOOK_URL: Optional[str] = None
    WEBHOOK_SECRET: Optional[str] = None

    ALERT_EMAIL_ENABLED: bool = False
    EMAIL_HOST: Optional[str] = None
    EMAIL_PORT: int = 587
    EMAIL_USERNAME: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    EMAIL_FROM_ADDRESS: Optional[str] = None
    EMAIL_RECIPIENTS: Optional[str] = None

    ALERT_SMS_ENABLED: bool = False
    SMS_API_KEY: Optional[str] = None
    SMS_API_SECRET: Optional[str] = None

    # Storage & Evidence Retention
    EVIDENCE_STORAGE_DIR: str = "outputs/evidence"
    EVIDENCE_RETENTION_DAYS: int = 30
    MAX_EVIDENCE_STORAGE_GB: float = 20.0
    LOG_FILE_PATH: str = "outputs/logs/rakshya_vision.log"
    LOG_LEVEL: str = "INFO"
    LOG_MAX_BYTES: int = 10485760
    LOG_BACKUP_COUNT: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def __init__(self, **values: Any):
        # 0. Raw YAML data access
        self._raw_yaml = _load_raw_yaml_config()

        # 1. Base YAML defaults
        yaml_defaults = _load_yaml_config()

        # 2. Environment variable overrides (os.environ takes precedence over YAML)
        for key in list(yaml_defaults.keys()):
            if key in os.environ:
                val = os.environ[key]
                # type cast basic ints if applicable
                if isinstance(yaml_defaults[key], int):
                    try:
                        val = int(val)
                    except ValueError:
                        pass
                yaml_defaults[key] = val

        # 3. Merged dictionary (explicit kwargs take highest precedence)
        merged = {**yaml_defaults, **values}
        super().__init__(**merged)

        # 4. Synchronize CORS_ALLOWED_ORIGINS env string into CORS_ORIGINS list
        if self.CORS_ALLOWED_ORIGINS is not None:
            origins = [o.strip() for o in self.CORS_ALLOWED_ORIGINS.split(",") if o.strip()]
            self.CORS_ORIGINS = origins
        elif "CORS_ORIGINS" in values:
            self.CORS_ORIGINS = list(values["CORS_ORIGINS"])
        elif yaml_defaults.get("CORS_ORIGINS"):
            self.CORS_ORIGINS = list(yaml_defaults["CORS_ORIGINS"])
        elif self.APP_ENV != "production":
            self.CORS_ORIGINS = DEVELOPMENT_CORS_DEFAULTS.copy()
        else:
            self.CORS_ORIGINS = []

        # Only include default development origins in non-production environments
        if self.APP_ENV != "production":
            for dev_origin in DEVELOPMENT_CORS_DEFAULTS:
                if dev_origin not in self.CORS_ORIGINS:
                    self.CORS_ORIGINS.append(dev_origin)

        # 5. Synchronize DEBUG flag with environment
        if self.APP_ENV == "production" and "DEBUG" not in values:
            self.DEBUG = False
        elif self.APP_ENV in ("development", "test") and "DEBUG" not in values:
            self.DEBUG = True

    @property
    def raw_config(self) -> Dict[str, Any]:
        """Provides access to the raw unflattened YAML configuration dictionary."""
        return getattr(self, "_raw_yaml", {})

    def validate_production_configuration(self) -> Dict[str, Any]:
        """
        Validates configuration strictly for production readiness.
        Raises ValueError or FileNotFoundError if requirements are unmet.
        Never exposes secret values.
        """
        report = {
            "environment": self.APP_ENV,
            "database_configured": bool(self.DATABASE_URL),
            "cors_configured": bool(self.CORS_ORIGINS),
            "secrets_validated": False,
            "model_registry_validated": False,
        }

        # 1. Secret Key Validation
        active_secret = self.JWT_SECRET_KEY or self.SECRET_KEY
        if not active_secret:
            raise ValueError("CONFIGURATION ERROR: Required production secret is missing.")

        active_secret_lower = active_secret.strip().lower()
        if len(active_secret) < 16 or any(active_secret_lower.startswith(prefix) for prefix in INSECURE_PLACEHOLDER_PREFIXES):
            raise ValueError("CONFIGURATION ERROR: Required production secret is missing.")

        report["secrets_validated"] = True

        # 2. CORS Validation
        if not self.CORS_ORIGINS or self.CORS_ORIGINS == ["*"] or "NOT CONFIGURED" in self.CORS_ORIGINS:
            raise ValueError("CONFIGURATION ERROR: Production CORS origins NOT CONFIGURED.")

        # 3. Database URL Validation
        if not self.DATABASE_URL or not self.DATABASE_URL.strip():
            raise ValueError("CONFIGURATION ERROR: Database URL is required.")

        # 4. Model Registry Path Validation
        reg_path = self.MODEL_REGISTRY_PATH
        if not os.path.isabs(reg_path):
            reg_path = os.path.normpath(os.path.join(ROOT, reg_path))
        if not os.path.isfile(reg_path):
            raise FileNotFoundError(f"CONFIGURATION ERROR: Model registry not found at: {reg_path}")

        report["model_registry_validated"] = True

        # 5. Retention Days Validation
        if self.EVIDENCE_RETENTION_DAYS <= 0:
            raise ValueError("CONFIGURATION ERROR: Evidence retention days must be greater than 0.")

        return report

    def get_safe_summary(self) -> Dict[str, Any]:
        """Returns a sanitized configuration summary with secrets strictly redacted."""
        summary = {}
        for key, val in self.model_dump().items():
            key_lower = key.lower()
            if any(s in key_lower for s in SENSITIVE_FIELD_NAMES):
                summary[key] = "[REDACTED]" if val else None
            else:
                summary[key] = val
        return summary

    def __repr__(self) -> str:
        safe_data = self.get_safe_summary()
        return f"Settings({safe_data})"

    def __str__(self) -> str:
        return self.__repr__()


settings = Settings()


def get_settings() -> Settings:
    """Returns the singleton Settings instance."""
    return settings


def setup_production_logging():
    """
    Configures structured logging with RotatingFileHandler and stdout formatting.
    Ensures safe, bounded log rotation according to production config.
    """
    import logging.handlers
    current_settings = get_settings()
    log_file_path = os.path.join(ROOT, current_settings.LOG_FILE_PATH)
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    root_logger = logging.getLogger()
    log_level = getattr(logging, current_settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    # Check if RotatingFileHandler already attached
    has_rotating_file = any(
        isinstance(h, logging.handlers.RotatingFileHandler) for h in root_logger.handlers
    )

    if not has_rotating_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=current_settings.LOG_MAX_BYTES,
            backupCount=current_settings.LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)
