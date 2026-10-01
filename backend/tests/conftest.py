"""
conftest.py — SafeSync backend test configuration
Adds backend/ to sys.path so tests can import app modules directly.
"""
import sys
import os

# Add backend/ to path for all tests
_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# Add project root to path
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
