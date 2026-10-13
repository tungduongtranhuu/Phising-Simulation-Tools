"""URL extraction and analysis (B11-B17). Never fetches a URL."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from ..config import risky_tlds as risky_cfg
from ..models import Finding, Severity
from ..utils import registered_domain

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover
    BeautifulSoup = None  # type: ignore[assignment]

_URL_RE = re.compile(r"\bhttps?://[^\s\"'<>)\]}]+", re.IGNORECASE)
_IPV4_RE = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")


def _cfg() -> dict:
    c = risky_cfg()
    return {
        "risky": set(c.get("risky_tlds", [])),
        "shorteners": set(c.get("shorteners", [])),
        "login": [k.lower() for k in c.get("login_keywords", [])],
    }


def extract(text: str, html: str) -> tuple[list[str], list[tuple[str, str]]]:
    """Return (all_urls, mismatches) where mismatch = (visible_text, real_href)."""
    urls: list[str] = []
    mismatches: list[tuple[str, str]] = []

    urls += _URL_RE.findall(text or "")

    if html and BeautifulSoup is not None:
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.lower().startswith("http"):
                urls.append(href)
                shown = a.get_text(strip=True)
                shown_urls = _URL_RE.findall(shown)
                if shown_urls and registered_domain(shown_urls[0]) != registered_domain(href):
                    mismatches.append((shown, href))
        for form in soup.find_all("form", action=True):
            action = form["action"].strip()
            if action.lower().startswith("http"):
                urls.append(action)
    elif html:
        urls += _URL_RE.findall(html)

    # de-duplicate, keep order
    seen: set[str] = set()
    deduped = [u for u in urls if not (u in seen or seen.add(u))]
    return deduped, mismatches


def analyse(text: str, html: str) -> tuple[list[Finding], list[str]]:
    cfg = _cfg()
    findings: list[Finding] = []
    urls, mismatches = extract(text, html)

    # B12 — displayed text differs from real href
    for shown, href in mismatches:
        findings.append(
            Finding(
                "B12", "Link text differs from destination", Severity.HIGH,
                detail=f'Shows "{shown}" but links to {href}.',
                recommendation="Hidden destination — hallmark of credential phishing.",
            )
        )

    flagged_ip = flagged_short = flagged_tld = flagged_login = False
    for url in urls:
        p = urlparse(url)
        host = p.hostname or ""
        reg = registered_domain(host)

        if _IPV4_RE.match(host) and not flagged_ip:
            findings.append(
                Finding(
                    "B14", "URL uses a raw IP address", Severity.MEDIUM, detail=url,
                    recommendation="Legit services rarely link to bare IPs.",
                )
            )
            flagged_ip = True

        if reg in cfg["shorteners"] and not flagged_short:
            findings.append(
                Finding(
                    "B13", "URL shortener hides destination", Severity.MEDIUM, detail=url,
                    recommendation="Expand via a safe service before trusting.",
                )
            )
            flagged_short = True

        tld = reg.rsplit(".", 1)[-1] if "." in reg else ""
        if tld in cfg["risky"] and not flagged_tld:
            findings.append(
                Finding(
                    "B15", f"Risky TLD .{tld}", Severity.MEDIUM, detail=url,
                    recommendation="Frequently abused TLD; scrutinise.",
                )
            )
            flagged_tld = True

        path_q = (p.path + "?" + (p.query or "")).lower()
        if any(k in path_q for k in cfg["login"]) and not flagged_login:
            findings.append(
                Finding(
                    "B16", "Login/credential keyword in URL", Severity.LOW, detail=url,
                    recommendation="Possible credential-harvest page.",
                )
            )
            flagged_login = True

    # B17 — forms / password inputs in HTML
    if html and BeautifulSoup is not None:
        soup = BeautifulSoup(html, "html.parser")
        if soup.find("input", attrs={"type": "password"}) or soup.find("form"):
            findings.append(
                Finding(
                    "B17", "HTML contains a form / password field", Severity.MEDIUM,
                    detail="Email body embeds a <form> or password <input>.",
                    recommendation="Legit senders do not collect credentials inside email bodies.",
                )
            )
    return findings, urls
