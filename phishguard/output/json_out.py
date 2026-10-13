"""JSON serialisation. IOCs are defanged in the output."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from ..utils import defang, defang_ip


def _defang_report(d: dict) -> dict:
    d = copy.deepcopy(d)
    iocs = d.get("iocs")
    if isinstance(iocs, dict):
        iocs["urls"] = [defang(u) for u in iocs.get("urls", [])]
        iocs["ips"] = [defang_ip(i) for i in iocs.get("ips", [])]
        iocs["domains"] = [defang(x) for x in iocs.get("domains", [])]
    if d.get("sender_ip"):
        d["sender_ip"] = defang_ip(d["sender_ip"])
    return d


def to_json(report, *, defang_iocs: bool = True, indent: int = 2) -> str:
    data = report.to_dict()
    if defang_iocs:
        data = _defang_report(data)
    return json.dumps(data, indent=indent, ensure_ascii=False)


def write_json(report, path: str | Path, **kwargs) -> None:
    Path(path).write_text(to_json(report, **kwargs), encoding="utf-8")
