"""Write one compact JSON line per result for the Wazuh agent to ingest."""

from __future__ import annotations

import json
import os
from pathlib import Path

_DEFAULT_LINUX = "/var/log/phishguard/alerts.json"


def _default_path() -> Path:
    env = os.getenv("PHISHGUARD_SIEM_LOG")
    if env:
        return Path(env)
    linux = Path(_DEFAULT_LINUX)
    if linux.parent.exists() or os.name != "nt":
        return linux
    # On Windows (dev), fall back to a repo-local log directory.
    from ..config import ROOT
    return ROOT / "logs" / "alerts.json"


def emit(report, path: str | Path | None = None) -> Path:
    """Append the report's compact SIEM line as NDJSON. Returns the path used."""
    target = Path(path) if path else _default_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(report.siem_line(), ensure_ascii=False)
    with target.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    return target
