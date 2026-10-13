"""Data models for findings and reports (stdlib dataclasses, JSON-serialisable)."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Finding:
    """A single detection. ``points`` adds to the email risk score; for DNS
    findings ``points`` is the penalty subtracted from 100."""

    id: str
    title: str
    severity: Severity = Severity.INFO
    points: int = 0
    detail: str = ""
    recommendation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "severity": self.severity.value,
            "points": self.points,
            "detail": self.detail,
            "recommendation": self.recommendation,
        }


@dataclass
class IOCs:
    urls: list[str] = field(default_factory=list)
    ips: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    hashes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


@dataclass
class DnsReport:
    tool: str = "phishguard"
    module: str = "dns"
    timestamp: str = field(default_factory=_now)
    domain: str = ""
    score: int = 100
    grade: str = "A"
    findings: list[Finding] = field(default_factory=list)
    records: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "module": self.module,
            "timestamp": self.timestamp,
            "domain": self.domain,
            "score": self.score,
            "grade": self.grade,
            "findings": [f.to_dict() for f in self.findings],
            "records": self.records,
        }

    def siem_line(self) -> dict[str, Any]:
        """Compact event for Wazuh (no bulky raw records)."""
        return {
            "tool": self.tool,
            "module": self.module,
            "timestamp": self.timestamp,
            "domain": self.domain,
            "score": self.score,
            "grade": self.grade,
            "finding_count": len(self.findings),
        }


@dataclass
class EmailReport:
    tool: str = "phishguard"
    module: str = "email"
    timestamp: str = field(default_factory=_now)
    file: str = ""
    subject: str = ""
    sender: str = ""
    sender_domain: str = ""
    sender_ip: str = ""
    auth: dict[str, str] = field(default_factory=lambda: {"spf": "", "dkim": "", "dmarc": ""})
    score: int = 0
    verdict: str = "clean"
    findings: list[Finding] = field(default_factory=list)
    iocs: IOCs = field(default_factory=IOCs)
    mitre: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "module": self.module,
            "timestamp": self.timestamp,
            "file": self.file,
            "subject": self.subject,
            "sender": self.sender,
            "sender_domain": self.sender_domain,
            "sender_ip": self.sender_ip,
            "auth": self.auth,
            "score": self.score,
            "verdict": self.verdict,
            "findings": [f.to_dict() for f in self.findings],
            "iocs": self.iocs.to_dict(),
            "mitre": self.mitre,
        }

    def siem_line(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "module": self.module,
            "timestamp": self.timestamp,
            "file": self.file,
            "subject": self.subject[:120],
            "sender": self.sender,
            "sender_domain": self.sender_domain,
            "sender_ip": self.sender_ip,
            "auth": self.auth,
            "score": self.score,
            "verdict": self.verdict,
            "mitre": self.mitre,
            "finding_count": len(self.findings),
        }
