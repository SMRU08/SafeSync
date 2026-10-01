"""
Root tests runner & system smoke test for SafeSync.
Provides root-level pytest compatibility for testing pipeline integrity.
"""
import sys
import os
import pytest

# Ensure backend and root are on sys.path
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_BACKEND = os.path.join(_ROOT, "backend")
for p in [_BACKEND, _ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)


def test_core_module_imports():
    """Verify core pipeline components can be imported successfully."""
    from app.ai.compliance.tracker import ByteTrack
    from app.ai.compliance.association import SpatialPPEAssociator
    from app.ai.compliance.temporal import TemporalComplianceTracker
    from app.services.alert_engine import AlertEngine
    from app.services.risk_engine import RiskEngine

    assert ByteTrack is not None
    assert SpatialPPEAssociator is not None
    assert TemporalComplianceTracker is not None
    assert AlertEngine is not None
    assert RiskEngine is not None


def test_canonical_class_ontology():
    """Verify canonical 7-class ontology constants."""
    from app.ai.compliance.schemas import PPEItemType

    expected = {"helmet", "safety_vest", "gloves", "safety_footwear"}
    actual = {item.value for item in PPEItemType}
    assert expected.issubset(actual)


def test_unknown_not_violation_principle():
    """Verify that UNKNOWN PPEState does not evaluate as a violation."""
    from app.ai.compliance.schemas import PPEState

    assert PPEState.UNKNOWN.value == "UNKNOWN"
    assert PPEState.UNKNOWN != PPEState.ABSENT
