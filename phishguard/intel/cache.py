"""Tiny SQLite-backed cache so we never exceed free-tier API limits."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from ..config import ROOT

_DEFAULT_TTL = 24 * 3600  # 1 day
_DB_PATH = ROOT / ".cache" / "intel.sqlite"


class Cache:
    def __init__(self, path: Path = _DB_PATH, ttl: int = _DEFAULT_TTL):
        self.ttl = ttl
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS cache "
            "(k TEXT PRIMARY KEY, v TEXT, ts REAL)"
        )
        self.conn.commit()

    def get(self, key: str):
        row = self.conn.execute("SELECT v, ts FROM cache WHERE k=?", (key,)).fetchone()
        if not row:
            return None
        value, ts = row
        if time.time() - ts > self.ttl:
            return None
        try:
            return json.loads(value)
        except Exception:
            return None

    def set(self, key: str, value) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO cache (k, v, ts) VALUES (?, ?, ?)",
            (key, json.dumps(value), time.time()),
        )
        self.conn.commit()

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass
