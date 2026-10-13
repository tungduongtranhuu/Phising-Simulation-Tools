"""Parse a .eml file into a structured, analysis-friendly object.

Static only: attachments are read into memory for hashing/typing but never
written to disk or executed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from pathlib import Path


@dataclass
class Attachment:
    filename: str
    content_type: str
    size: int
    payload: bytes = field(repr=False, default=b"")


@dataclass
class ParsedEmail:
    path: str
    raw: bytes = field(repr=False, default=b"")
    msg: EmailMessage | None = field(repr=False, default=None)
    headers: dict[str, str] = field(default_factory=dict)
    text: str = ""
    html: str = ""
    attachments: list[Attachment] = field(default_factory=list)

    def header(self, name: str, default: str = "") -> str:
        return self.headers.get(name.lower(), default)

    def all_headers(self, name: str) -> list[str]:
        if self.msg is None:
            return []
        return [str(v) for v in self.msg.get_all(name, [])]


def parse_file(path: str | Path) -> ParsedEmail:
    path = Path(path)
    raw = path.read_bytes()
    msg = BytesParser(policy=policy.default).parsebytes(raw)

    parsed = ParsedEmail(path=str(path), raw=raw, msg=msg)
    parsed.headers = {k.lower(): str(v) for k, v in msg.items()}

    for part in msg.walk():
        if part.is_multipart():
            continue
        ctype = part.get_content_type()
        disp = (part.get_content_disposition() or "").lower()
        filename = part.get_filename()

        if disp == "attachment" or filename:
            payload = part.get_payload(decode=True) or b""
            parsed.attachments.append(
                Attachment(
                    filename=filename or "unnamed",
                    content_type=ctype,
                    size=len(payload),
                    payload=payload,
                )
            )
        elif ctype == "text/plain" and not parsed.text:
            parsed.text = _safe_body(part)
        elif ctype == "text/html" and not parsed.html:
            parsed.html = _safe_body(part)

    return parsed


def _safe_body(part) -> str:
    try:
        content = part.get_content()
        return content if isinstance(content, str) else str(content)
    except Exception:
        payload = part.get_payload(decode=True) or b""
        return payload.decode("utf-8", "replace")
