"""SafeSync backend root package."""
import os
import sys

# Ensure backend directory is on sys.path for top-level 'app' module resolution
_backend_dir = os.path.dirname(os.path.abspath(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
