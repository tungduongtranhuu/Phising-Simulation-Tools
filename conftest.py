"""Ensure the repo root is importable so `import phishguard` works in tests
without requiring an editable install."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
