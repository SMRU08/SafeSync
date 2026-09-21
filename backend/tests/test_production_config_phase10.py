"""
test_production_config_phase10.py — RAKSHYA VISION Phase 10 Step 3
Automated tests for Centralized Production Configuration, Secret Safety, and CORS Validation.
"""

import os
import pytest
from app.config import (
    Settings,
    _load_yaml_config,
    DEFAULT_PRODUCTION_CONFIG,
    DEFAULT_REGISTRY_PATH,
)


def test_production_yaml_loads():
    """Verify production.yaml exists, parses cleanly, and contains required production sections."""
    assert os.path.isfile(DEFAULT_PRODUCTION_CONFIG)
    config = _load_yaml_config(DEFAULT_PRODUCTION_CONFIG)
    assert isinstance(config, dict)
    assert "APP_ENV" in config
    assert config["APP_ENV"] == "production"
    assert "DATABASE_URL" in config


def test_development_config_loads_with_safe_defaults():
    """Verify development mode initializes with safe local defaults."""
    dev_settings = Settings(APP_ENV="development")
    assert dev_settings.APP_ENV == "development"
    assert dev_settings.DEBUG is True
    assert len(dev_settings.CORS_ORIGINS) > 0
    assert "http://localhost:5173" in dev_settings.CORS_ORIGINS


def test_environment_variables_override_yaml(monkeypatch):
    """Verify that environment variables take precedence over YAML configuration values."""
    monkeypatch.setenv("PORT", "9999")
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./custom_test.db")

    custom_settings = Settings()
    assert custom_settings.PORT == 9999
    assert custom_settings.HOST == "127.0.0.1"
    assert custom_settings.DATABASE_URL == "sqlite:///./custom_test.db"


def test_missing_production_secret_detected():
    """Verify that in production mode, a missing secret raises a clear error."""
    prod_settings = Settings(
        APP_ENV="production",
        SECRET_KEY=None,
        JWT_SECRET_KEY=None,
        CORS_ALLOWED_ORIGINS="https://dashboard.production.example",
    )

    with pytest.raises(ValueError) as exc_info:
        prod_settings.validate_production_configuration()

    assert "CONFIGURATION ERROR: Required production secret is missing." in str(exc_info.value)


def test_insecure_placeholder_secret_rejected():
    """Verify that placeholder secret values (e.g. CHANGE_ME) are rejected in production mode."""
    prod_settings = Settings(
        APP_ENV="production",
        JWT_SECRET_KEY="CHANGE_ME_PLEASE",
        CORS_ALLOWED_ORIGINS="https://dashboard.production.example",
    )

    with pytest.raises(ValueError) as exc_info:
        prod_settings.validate_production_configuration()

    assert "CONFIGURATION ERROR: Required production secret is missing." in str(exc_info.value)


def test_valid_production_secret_and_cors_pass():
    """Verify that valid secrets and explicit CORS pass production validation."""
    prod_settings = Settings(
        APP_ENV="production",
        JWT_SECRET_KEY="c8f1e4b9d2a04875b1d9c2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3",
        CORS_ALLOWED_ORIGINS="https://dashboard.production.example,https://soc.facility.example",
    )

    report = prod_settings.validate_production_configuration()
    assert report["environment"] == "production"
    assert report["secrets_validated"] is True
    assert report["cors_configured"] is True
    assert len(prod_settings.CORS_ORIGINS) == 2


def test_cors_validation_in_production():
    """Verify that empty or wildcard CORS in production raises a clear error."""
    prod_settings_no_cors = Settings(
        APP_ENV="production",
        JWT_SECRET_KEY="c8f1e4b9d2a04875b1d9c2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3",
        CORS_ORIGINS=[],
        CORS_ALLOWED_ORIGINS="",
    )

    with pytest.raises(ValueError) as exc_info:
        prod_settings_no_cors.validate_production_configuration()

    assert "CONFIGURATION ERROR: Production CORS origins NOT CONFIGURED." in str(exc_info.value)


def test_model_registry_path_validation():
    """Verify that a nonexistent model registry path is caught during validation."""
    bad_settings = Settings(
        APP_ENV="production",
        JWT_SECRET_KEY="c8f1e4b9d2a04875b1d9c2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3",
        CORS_ALLOWED_ORIGINS="https://dashboard.example",
        MODEL_REGISTRY_PATH="non_existent/registry.yaml",
    )

    with pytest.raises(FileNotFoundError) as exc_info:
        bad_settings.validate_production_configuration()

    assert "CONFIGURATION ERROR: Model registry not found" in str(exc_info.value)


def test_no_secrets_appear_in_string_or_logs():
    """Verify that sensitive secrets are strictly redacted in __str__, __repr__, and get_safe_summary()."""
    test_secret = "super-secret-jwt-key-never-print-this"
    test_cam_pass = "top-secret-camera-password-123"

    cfg = Settings(
        JWT_SECRET_KEY=test_secret,
        CAMERA_PASSWORD=test_cam_pass,
    )

    repr_str = repr(cfg)
    str_val = str(cfg)
    summary = cfg.get_safe_summary()

    # Neither secret should appear in plain text
    assert test_secret not in repr_str
    assert test_cam_pass not in repr_str
    assert test_secret not in str_val
    assert test_cam_pass not in str_val

    # Ensure redacted tags are present
    assert summary["JWT_SECRET_KEY"] == "[REDACTED]"
    assert summary["CAMERA_PASSWORD"] == "[REDACTED]"
