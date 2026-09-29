"""
test_model_registry_phase10.py — SafeSync Phase 10 Step 2
Automated tests for Model Registry, lifecycle states, and SHA-256 Checksum Enforcement.
"""

import os
import tempfile
import pytest
import yaml

from app.ai.detection.model_loader import (
    ModelLoader,
    load_model_registry,
    get_model_entry_from_registry,
    DEFAULT_REGISTRY_PATH,
    CANONICAL_CLASSES,
)


def test_registry_file_structure_and_statuses():
    """Verify registry loads cleanly and contains production, candidate, and archived models."""
    registry = load_model_registry(DEFAULT_REGISTRY_PATH)
    assert "active_production_model" in registry
    assert "models" in registry

    models = registry["models"]
    assert "ppe_fire_smoke_v2" in models or "ppe_fire_smoke_v3" in models
    active_m = models.get(registry.get("active_production_model", "ppe_fire_smoke_v3"))
    assert active_m["status"] == "production"

    # Test candidate and archived entries exist
    statuses = {m["status"] for m in models.values()}
    assert "production" in statuses
    assert "candidate" in statuses
    assert "archived" in statuses

    # Test retrieval helper
    prod_entry = get_model_entry_from_registry("production", DEFAULT_REGISTRY_PATH)
    assert prod_entry["model_name"] in ("ppe_fire_smoke_v2", "ppe_fire_smoke_v3")

    cand_entry = get_model_entry_from_registry("candidate", DEFAULT_REGISTRY_PATH)
    assert cand_entry["status"] == "candidate"

    arch_entry = get_model_entry_from_registry("archived", DEFAULT_REGISTRY_PATH)
    assert arch_entry["status"] == "archived"


def test_valid_checksum_model_loads():
    """Verify that a model with a valid SHA-256 checksum loads successfully."""
    loader = ModelLoader(registry_path=DEFAULT_REGISTRY_PATH)
    model = loader.load_model(target_status="production")
    assert model is not None
    assert loader.is_loaded() is True
    assert loader.classes == CANONICAL_CLASSES


def test_invalid_checksum_model_rejected():
    """Verify that an invalid SHA-256 checksum stops model loading and raises clear error."""
    loader = ModelLoader(registry_path=DEFAULT_REGISTRY_PATH)
    fake_sha = "0000000000000000000000000000000000000000000000000000000000000000"

    with pytest.raises(ValueError) as exc_info:
        loader.load_model(
            target_status="production",
            expected_sha=fake_sha,
        )

    err_msg = str(exc_info.value)
    assert "MODEL CHECKSUM VERIFICATION FAILED" in err_msg
    assert fake_sha in err_msg


def test_missing_model_file_error():
    """Verify that a nonexistent model file raises FileNotFoundError with clear description."""
    loader = ModelLoader(registry_path=DEFAULT_REGISTRY_PATH)
    non_existent = "models/detection/non_existent_weights.pt"

    with pytest.raises(FileNotFoundError) as exc_info:
        loader.resolve_model_path(override_path=non_existent)

    assert "Detection model weights file not found" in str(exc_info.value)


def test_missing_registry_file_error():
    """Verify that a missing registry path raises FileNotFoundError."""
    missing_path = "models/registry/non_existent_registry.yaml"

    with pytest.raises(FileNotFoundError) as exc_info:
        load_model_registry(missing_path)

    assert "Model registry not found" in str(exc_info.value)


def test_malformed_registry_file_error():
    """Verify that a malformed registry file raises ValueError with clear description."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tf:
        tf.write("this is not: valid: yaml: [unbalanced")
        temp_path = tf.name

    try:
        with pytest.raises(ValueError) as exc_info:
            load_model_registry(temp_path)
        assert "Malformed model registry" in str(exc_info.value)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_registry_missing_models_key_error():
    """Verify that a registry missing the 'models' mapping raises ValueError."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tf:
        yaml.dump({"active_production_model": "test"}, tf)
        temp_path = tf.name

    try:
        with pytest.raises(ValueError) as exc_info:
            load_model_registry(temp_path)
        assert "Missing 'models' mapping" in str(exc_info.value)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
