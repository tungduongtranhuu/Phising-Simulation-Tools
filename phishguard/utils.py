"""Shared helpers: IOC defanging, registered-domain extraction, Levenshtein."""

from __future__ import annotations

import re

try:
    import tldextract

    # Use the bundled snapshot so we never hit the network just to parse a name.
    _extractor = tldextract.TLDExtract(suffix_list_urls=())
except Exception:  # pragma: no cover
    _extractor = None


def registered_domain(host_or_email: str) -> str:
    """Return the registrable domain (eTLD+1) for a host or email address."""
    if not host_or_email:
        return ""
    host = host_or_email.strip().strip(".").lower()
    if "@" in host:
        host = host.rsplit("@", 1)[-1]
    # strip scheme / path / port if a URL slipped in
    host = re.sub(r"^[a-z]+://", "", host).split("/")[0].split(":")[0]
    if _extractor is not None:
        ext = _extractor(host)
        if ext.domain and ext.suffix:
            return f"{ext.domain}.{ext.suffix}"
        return ext.domain or host
    # Fallback: last two labels.
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def defang(value: str) -> str:
    """Neutralise an IOC so it cannot be clicked: hxxp, [.], [@], [:]."""
    if not value:
        return value
    out = value
    out = re.sub(r"https?", lambda m: m.group(0).replace("t", "x"), out, flags=re.IGNORECASE)
    out = out.replace("://", "[://]")
    out = out.replace(".", "[.]")
    out = out.replace("@", "[@]")
    return out


def defang_ip(ip: str) -> str:
    return ip.replace(".", "[.]") if ip else ip


_LEV_CACHE: dict[tuple[str, str], int] = {}


def levenshtein(a: str, b: str) -> int:
    """Classic edit distance (iterative, O(len(a)*len(b)))."""
    key = (a, b)
    if key in _LEV_CACHE:
        return _LEV_CACHE[key]
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    _LEV_CACHE[key] = prev[-1]
    return prev[-1]


_ADDR_RE = re.compile(r"<([^>]+)>")


def split_address(raw: str) -> tuple[str, str]:
    """Split a header value like '"Name" <a@b.com>' into (display_name, email)."""
    if not raw:
        return "", ""
    m = _ADDR_RE.search(raw)
    if m:
        email = m.group(1).strip()
        name = raw[: m.start()].strip().strip('"').strip()
        return name, email.lower()
    raw = raw.strip()
    if "@" in raw:
        return "", raw.strip("<>").strip().lower()
    return raw.strip('"'), ""
