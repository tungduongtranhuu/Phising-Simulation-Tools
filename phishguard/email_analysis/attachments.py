"""Attachment analysis (B18-B23). Files are hashed/typed in memory, never run."""

from __future__ import annotations

import hashlib
import io
import re
import zipfile

from ..config import risky_tlds as risky_cfg
from ..models import Finding, Severity
from .parser import Attachment

try:
    import magic  # python-magic
except Exception:  # pragma: no cover
    magic = None

try:
    from oletools.olevba import VBA_Parser
except Exception:  # pragma: no cover
    VBA_Parser = None

_DOUBLE_EXT_RE = re.compile(
    r"\.(pdf|docx?|xlsx?|jpe?g|png|txt|zip)\.(exe|scr|js|vbs|bat|cmd|com|pif|lnk|hta)$",
    re.IGNORECASE,
)
_AUTORUN_MACROS = ("autoopen", "auto_open", "document_open", "workbook_open", "autoexec")
_SUSPECT_MACRO_CALLS = ("shell", "urldownloadtofile", "createobject", "wscript", "powershell")


def _dangerous_exts() -> set[str]:
    return set(risky_cfg().get("dangerous_extensions", []))


def analyse(attachments: list[Attachment], body_text: str) -> tuple[list[Finding], list[str]]:
    findings: list[Finding] = []
    hashes: list[str] = []
    dangerous = _dangerous_exts()

    for att in attachments:
        name = att.filename
        payload = att.payload
        sha256 = hashlib.sha256(payload).hexdigest() if payload else ""
        if sha256:
            hashes.append(sha256)

        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""

        # B20 — dangerous extension
        if ext in dangerous:
            findings.append(
                Finding(
                    "B20", f"Dangerous attachment extension: {name}", Severity.HIGH,
                    detail=f"sha256={sha256}",
                    recommendation="Do not open; detonate in an isolated sandbox if needed.",
                )
            )

        # B21 — double extension
        if _DOUBLE_EXT_RE.search(name):
            findings.append(
                Finding(
                    "B21", f"Double extension disguises executable: {name}", Severity.HIGH,
                    detail=f"sha256={sha256}",
                    recommendation="Strong malware indicator; quarantine.",
                )
            )

        # B19 — real type vs claimed extension
        if magic is not None and payload:
            try:
                mime = magic.from_buffer(payload, mime=True)
            except Exception:
                mime = ""
            if mime:
                exe_like = mime in (
                    "application/x-dosexec", "application/x-msdownload",
                    "application/x-executable", "application/x-mach-binary",
                )
                if exe_like and ext not in ("exe", "dll", "scr", "com"):
                    findings.append(
                        Finding(
                            "B19", f"File type mismatch: {name} is actually {mime}", Severity.HIGH,
                            detail=f"Claimed .{ext} but magic says {mime}. sha256={sha256}",
                            recommendation="Extension spoofing; treat as malicious.",
                        )
                    )

        # B22 — Office macros
        if VBA_Parser is not None and ext in ("doc", "docm", "xls", "xlsm", "ppt", "pptm", "dotm"):
            findings += _scan_macros(name, payload, sha256)

        # B23 — password-protected archive with password in the email body
        if ext == "zip" and payload:
            findings += _scan_zip(name, payload, body_text)

    return findings, hashes


def _scan_macros(name: str, payload: bytes, sha256: str) -> list[Finding]:
    findings: list[Finding] = []
    try:
        vp = VBA_Parser(name, data=payload)
        if not vp.detect_vba_macros():
            return findings
        code = ""
        for _, _, _, vba_code in vp.extract_macros():
            code += (vba_code or "").lower()
        autorun = [m for m in _AUTORUN_MACROS if m in code]
        suspect = [c for c in _SUSPECT_MACRO_CALLS if c in code]
        if autorun or suspect:
            findings.append(
                Finding(
                    "B22", f"Auto-executing Office macro in {name}", Severity.HIGH,
                    detail=f"autorun={autorun} calls={suspect} sha256={sha256}",
                    recommendation="Macro malware; block and alert the user.",
                )
            )
        else:
            findings.append(
                Finding(
                    "B22", f"Office macro present in {name}", Severity.MEDIUM,
                    detail=f"sha256={sha256}",
                    recommendation="Review the macro in a sandbox.",
                )
            )
    except Exception:
        pass
    return findings


def _scan_zip(name: str, payload: bytes, body_text: str) -> list[Finding]:
    try:
        zf = zipfile.ZipFile(io.BytesIO(payload))
    except Exception:
        return []
    encrypted = any(info.flag_bits & 0x1 for info in zf.infolist())
    if not encrypted:
        return []
    pwd_hint = bool(re.search(r"\b(password|mot de passe|mdp)\b", (body_text or ""), re.IGNORECASE))
    detail = f"{name} is a password-protected archive"
    if pwd_hint:
        detail += "; password appears in the email body (AV-evasion technique)"
    return [
        Finding(
            "B23", "Password-protected archive", Severity.MEDIUM, detail=detail,
            recommendation="Encrypted archives bypass mail AV; inspect carefully.",
        )
    ]
