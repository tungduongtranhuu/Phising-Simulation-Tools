"""Load YAML configuration (scoring weights, keywords, brands, risky TLDs).

Configuration lives in the top-level ``config/`` directory so analysts can tune
weights and word lists without touching code. Sensible defaults are embedded so
the tool still runs if a file is missing.
"""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

# Repo root is the parent of the `phishguard` package directory.
ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"


def _load_yaml(name: str) -> dict[str, Any]:
    path = CONFIG_DIR / name
    if yaml is None or not path.is_file():
        return {}
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        return data or {}
    except Exception:
        return {}


@functools.lru_cache(maxsize=None)
def scoring() -> dict[str, Any]:
    return _load_yaml("scoring.yaml")


@functools.lru_cache(maxsize=None)
def keywords() -> dict[str, list[str]]:
    return _load_yaml("keywords.yaml")


@functools.lru_cache(maxsize=None)
def brands() -> dict[str, Any]:
    return _load_yaml("brands.yaml")


@functools.lru_cache(maxsize=None)
def risky_tlds() -> dict[str, Any]:
    return _load_yaml("risky_tlds.yaml")


def email_weights() -> dict[str, int]:
    return scoring().get("email", {}).get("findings", {})


def email_thresholds() -> dict[str, int]:
    return scoring().get("email", {}).get("verdict_thresholds", {"suspicious": 30, "phishing": 60})


def dns_scoring() -> dict[str, Any]:
    return scoring().get("dns", {})
