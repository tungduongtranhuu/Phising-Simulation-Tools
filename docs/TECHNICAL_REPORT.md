# PhishGuard — Technical Report

**Version:** 0.1.0
**Type:** Defensive (blue-team) CLI tool — static phishing-email analysis and DNS security audit
**Language / stack:** Python 3.11+, Typer, Rich, dnspython, BeautifulSoup, Jinja2
**Lines of code:** ~2,300 (package only), 14 unit tests

---

## Table of contents

1. [Executive summary](#1-executive-summary)
2. [Design principles](#2-design-principles)
3. [System architecture & data flow](#3-system-architecture--data-flow)
4. [Project layout](#4-project-layout)
5. [Core infrastructure](#5-core-infrastructure)
6. [Module A — DNS security audit](#6-module-a--dns-security-audit)
7. [Module B — Email analysis](#7-module-b--email-analysis)
8. [Threat-intelligence enrichment](#8-threat-intelligence-enrichment)
9. [Scoring engine & verdicts](#9-scoring-engine--verdicts)
10. [MITRE ATT&CK mapping](#10-mitre-attck-mapping)
11. [Output layer](#11-output-layer)
12. [SIEM integration (Wazuh)](#12-siem-integration-wazuh)
13. [CLI](#13-cli)
14. [Testing strategy](#14-testing-strategy)
15. [Security & ethics](#15-security--ethics)
16. [Known limitations & roadmap](#16-known-limitations--roadmap)
17. [Appendix — finding ID reference](#17-appendix--finding-id-reference)

---

## 1. Executive summary

PhishGuard answers two operational questions that a SOC analyst (L1) and a mail
administrator face daily:

| Module | Input | Question it answers | Real user |
|---|---|---|---|
| **A — DNS audit** | a domain (`example.com`) | Is this domain configured to resist email spoofing and DNS attacks? | security team / admin |
| **B — Email analysis** | a `.eml` file | Is this email phishing? What are the IOCs? | SOC L1 triaging a reported mail |

Both modules converge on a **single scoring engine** that produces a verdict, a
numeric risk score, and a mapping to **MITRE ATT&CK**. Results are rendered to
the terminal (Rich), JSON, and an HTML report (Jinja2), and can be shipped to a
**Wazuh** SIEM as newline-delimited JSON for alerting and dashboards.

The tool is **entirely static and defensive**: it never sends email, never opens
a URL, and never executes an attachment. Module B reuses Module A to cross-check
the sender domain's DNS posture (a domain with no DMARC is trivially spoofable).

---

## 2. Design principles

Four principles drove every implementation decision.

### 2.1 Static & defensive by construction
No code path performs a network request *to a URL found in an email*, writes an
attachment to disk, or executes any payload. Attachments are read into memory,
hashed, and type-sniffed — nothing more. This is a hard safety boundary, not a
configuration option.

### 2.2 Graceful degradation
The tool splits dependencies into **core** (always required) and **optional**
(`dkimpy`, `python-whois`, `python-magic`, `oletools`). Every optional feature is
wrapped so that a missing library or a failing network call **skips that check**
rather than crashing the run. Example pattern used throughout:

```python
try:
    import whois as _whois
except ImportError:
    _whois = None          # feature later guarded by `if _whois is None: return []`
```

This matters because `python-magic` needs `libmagic`, `oletools` is heavy, and
WHOIS/TI calls need keys and connectivity — none of which can be assumed on an
analyst's laptop. An `--offline` flag disables **all** outbound traffic.

### 2.3 Configuration over code
Scoring weights, keyword lists, impersonated brands, and risky TLDs live in
`config/*.yaml`. An analyst tunes detections without touching Python. The loader
([config.py](../phishguard/config.py)) caches each file with `lru_cache` and
falls back to embedded defaults if a file is missing or PyYAML is absent.

### 2.4 Explainability
Every detection is a `Finding` object carrying an **ID**, a **severity**, the
**points** it contributed to the score, a human-readable **detail**, and a
**remediation recommendation**. The score is never a black box — the HTML/JSON/
console outputs show exactly which findings produced which points.

---

## 3. System architecture & data flow

```
  example.com ─▶ ┌──────────────┐ ◀─ suspicious.eml
                 │  CLI (typer) │
                 └──────┬───────┘
         ┌──────────────┴───────────────┐
         ▼                              ▼
  Module A: DNS Audit           Module B: Email Analysis
  resolver ▸ spf/dmarc/dkim     parser ▸ headers ▸ sender
  dnssec ▸ records ▸ zone        urls ▸ attachments ▸ content
  transfer ▸ takeover ─────────▶ (B7 reuses Module A for the
         │                        sender domain)
         │                               │
         │                      Threat-intel enrichment
         │                      VirusTotal / AbuseIPDB / URLhaus
         │                      (+ SQLite cache, offline mode)
         └───────────┬──────────────────┘
                     ▼
        Scoring engine ▸ verdict ▸ MITRE mapping
                     │
   ┌──────────┬──────────┬───────────┬─────────────────┐
   ▼          ▼          ▼           ▼                 ▼
 Console    JSON       HTML       alerts.json ─▶ Wazuh agent ─▶ Dashboard
 (Rich)   (defanged) (Jinja2)      (NDJSON)       rules 100200+
```

**Flow for an email:** `cli.email_cmd` → `email_analysis.analyse_file` runs the
sub-analysers in order, each returning a `list[Finding]`; findings accumulate on
an `EmailReport`; IOCs are collected; optional enrichment adds more findings; the
email `scorer` sums weighted points and sets the verdict; an output renderer
serialises the report.

**Flow for a domain:** `cli.dns` → `dns_audit.audit` runs each check, each
appending to the shared `records` dict and returning findings; the DNS `scorer`
converts findings to penalties, derives the 0–100 score and A–F grade.

---

## 4. Project layout

```
phishguard/
├── config.py            # YAML loader + typed accessors
├── models.py            # Finding, IOCs, DnsReport, EmailReport (+ to_dict/siem_line)
├── utils.py             # registered_domain, defang, levenshtein, split_address
├── cli.py               # Typer app: `dns` and `email` commands
├── dns_audit/           # Module A
│   ├── resolver.py      # dnspython wrapper (timeouts + lru_cache)
│   ├── spf.py dmarc.py dkim.py dnssec.py records.py
│   ├── zone_transfer.py takeover.py
│   ├── scorer.py        # findings -> penalties -> score/grade
│   └── __init__.py      # audit() orchestrator
├── email_analysis/      # Module B
│   ├── parser.py headers.py sender.py urls.py attachments.py content.py
│   ├── scorer.py        # weighted sum -> verdict + MITRE
│   └── __init__.py      # analyse_file() orchestrator
├── intel/               # VirusTotal, AbuseIPDB, URLhaus + SQLite cache
└── output/              # console (Rich), json_out, html_report, siem
config/   scoring.yaml keywords.yaml brands.yaml risky_tlds.yaml
wazuh/    ossec_localfile.xml local_rules.xml
samples/  phishing/ legit/
tests/    test_spf/dmarc/headers/urls/scoring.py
```

---

## 5. Core infrastructure

### 5.1 `config.py` — configuration loader
- Resolves the repo root as `Path(__file__).parent.parent` so config is found
  regardless of the working directory.
- `_load_yaml(name)` returns `{}` on any failure (missing file, no PyYAML, parse
  error) — callers always get a dict.
- Typed accessors: `email_weights()`, `email_thresholds()`, `dns_scoring()`,
  `keywords()`, `brands()`, `risky_tlds()`. Each is `@lru_cache`'d, so the YAML
  is read once per process.

### 5.2 `models.py` — data model
Plain `dataclasses` (no pydantic dependency) chosen for zero-install portability
and trivial JSON export.

- **`Severity`** — `str, Enum` (`info`→`critical`), so it serialises as a string.
- **`Finding`** — `id, title, severity, points, detail, recommendation`.
- **`IOCs`** — `urls, ips, domains, hashes`.
- **`DnsReport` / `EmailReport`** — top-level results with `to_dict()` (full JSON)
  and `siem_line()` (compact event: no bulky records, subject truncated to 120
  chars — important so we never ship full email bodies to the SIEM).

### 5.3 `utils.py` — shared helpers
- **`registered_domain(host_or_email)`** — extracts the registrable domain
  (eTLD+1) using `tldextract` with the **bundled suffix snapshot**
  (`suffix_list_urls=()`) so parsing never triggers a network fetch. Handles
  emails, URLs, ports, and trailing dots. Falls back to "last two labels" if
  tldextract is unavailable. This single function underpins every
  domain-comparison check (From vs Reply-To, link text vs href, lookalike, etc.).
- **`defang(value)`** — neutralises IOCs so they can't be clicked:
  `http`→`hxxp`, `://`→`[://]`, `.`→`[.]`, `@`→`[@]`. Applied at the **output
  boundary** — the model stores raw values; renderers defang.
- **`levenshtein(a, b)`** — iterative edit distance (two-row DP, O(len·len)),
  memoised; used for typosquatting detection.
- **`split_address(raw)`** — parses `"PayPal Support" <a@b.xyz>` into
  `(display_name, email)` via regex; the basis of display-name-spoof detection.

**Design note:** keeping defang at the output layer (not the model) means SIEM
and internal comparisons use real values while every human-facing report is safe.

---

## 6. Module A — DNS security audit

`dns_audit.audit(domain, …)` normalises the domain to eTLD+1, then runs the
checks below. Each check appends raw lookups to a shared `records` dict (surfaced
in JSON) and returns `Finding`s. If `dnspython` is missing, the module returns a
single explanatory finding instead of crashing.

### 6.1 `resolver.py` — the DNS layer
A thin wrapper over `dns.resolver` with a 5-second timeout/lifetime and an
`lru_cache(maxsize=256)` on `(name, rdtype)`. TXT records are concatenated and
unquoted. **Every query returns `()` on any exception** — the whole module treats
"no answer" and "lookup failed" identically, which keeps call sites simple.

### 6.2 A2 — SPF ([spf.py](../phishguard/dns_audit/spf.py))
- Collects all `v=spf1` TXT records. **No record** → HIGH finding. **Multiple
  records** → HIGH (RFC 7208 allows exactly one).
- Extracts the `all` qualifier with regex `([~\-+?])all\b`:
  - `+all` → HIGH (passes the entire internet),
  - `?all` → MEDIUM (neutral), no `all` → MEDIUM.
- **Lookup budget:** `_count_lookups()` recursively counts the
  `include/a/mx/ptr/exists/redirect` mechanisms that cost DNS lookups, following
  `include`/`redirect` into nested records (depth-guarded, visited-set to avoid
  loops). `> 10` → MEDIUM, because an SPF record that exceeds the RFC limit
  **permerror**s and effectively fails for receivers.

### 6.3 A3 — DMARC ([dmarc.py](../phishguard/dns_audit/dmarc.py))
- `parse()` turns the record into a tag dict. Checks: **no record** → HIGH;
  **`p=none`** → HIGH (monitor-only, does not stop spoofing); **no `rua`** →
  MEDIUM (no visibility); **`pct<100`** → LOW. Each carries a ready-to-publish
  sample record as remediation.

### 6.4 A4 — DKIM ([dkim.py](../phishguard/dns_audit/dkim.py))
- DKIM selectors can't be enumerated from DNS, so we **probe a list of common
  selectors** (`default, google, selector1/2, k1/2, mail, dkim, s1/2, …`). When
  analysing an email, the **real selector** from the `DKIM-Signature s=` tag is
  passed in via `extra_selectors` for a precise check.
- `_rsa_bits()` estimates key size from the base64 `p=` blob: empty `p=` → revoked
  key (MEDIUM); `< 1024 bits` → weak key (MEDIUM).

### 6.5 A5 — DNSSEC ([dnssec.py](../phishguard/dns_audit/dnssec.py))
- DNSSEC is considered enabled only if **both** `DNSKEY` (at the zone) and `DS`
  (published at the parent/registrar) exist. Missing → MEDIUM.

### 6.6 A1/A6/A8/A9/A10 — records ([records.py](../phishguard/dns_audit/records.py))
- **A1 MX** — none present → INFO (the domain shouldn't send/receive mail).
- **A10 NS** — a single name server → LOW (resilience risk).
- **A6 CAA** — none → LOW (any CA may issue certs).
- **A8 MTA-STS** — requires the `_mta-sts` TXT **and** fetches
  `https://mta-sts.<domain>/.well-known/mta-sts.txt` (the only outbound HTTP in
  Module A, gated by `allow_network`) to read the policy `mode`. Missing → LOW;
  `mode: testing` → LOW (not enforced).
- **A9 TLS-RPT** — missing `_smtp._tls` TXT → LOW.

### 6.7 A7 — zone transfer ([zone_transfer.py](../phishguard/dns_audit/zone_transfer.py))
- Attempts an `AXFR` against **each** name server with `dns.query.xfr`. If any
  server returns the full zone → HIGH. **Ethics:** this is opt-outable
  (`--no-zone-transfer`) and the docstring warns it must only be run against
  domains you own/are authorised to test (or the learning target
  `zonetransfer.me`). AXFR is a read-only query, but an open transfer is a real
  misconfiguration worth reporting.

### 6.8 A11 — subdomain takeover ([takeover.py](../phishguard/dns_audit/takeover.py))
- Enumerates subdomains from **Certificate Transparency** via `crt.sh` (JSON API).
- For each subdomain with a `CNAME`, matches the target against a fingerprint
  table (GitHub Pages, Heroku, S3, CloudFront, Azure, Zendesk, Fastly, …, inspired
  by the community `can-i-take-over-xyz` project).
- A match is reported HIGH only if the CNAME target **no longer resolves**
  (`A`/`AAAA` empty) — a *dangling* CNAME that an attacker could claim. Resolving
  targets are ignored to suppress false positives.

### 6.9 DNS scoring ([scorer.py](../phishguard/dns_audit/scorer.py))
Starts at **100** and subtracts penalties. The scorer maps each finding to a
penalty key via `_penalty_key()` (keyed on finding ID + title keywords), writes
the penalty back onto `finding.points` (negative, for explainability), and
derives the grade:

```
score = 100 − Σ penalties      (clamped to [0,100])
A ≥ 90 · B ≥ 75 · C ≥ 60 · D ≥ 40 · F < 40
```

Penalty table (`config/scoring.yaml`): no SPF −25, `+all` −30, no DMARC −25,
`p=none` −15, open AXFR −30, takeover −25, no DNSSEC −10, no DKIM −10,
no CAA/MTA-STS/TLS-RPT −3 each. Informational DMARC sub-findings (missing `rua`,
low `pct`) deliberately carry **no** penalty — they're advisory.

---

## 7. Module B — Email analysis

`email_analysis.analyse_file(path, …)` orchestrates six sub-analysers, collects
IOCs, optionally enriches, then scores.

### 7.1 `parser.py` — safe .eml parsing
- Uses the stdlib `BytesParser(policy=policy.default)` — the modern email API that
  correctly decodes MIME, headers, and encodings.
- `msg.walk()` separates the first `text/plain` body, the first `text/html` body,
  and all attachments. Attachment payloads are decoded **into memory** as `bytes`
  (`ParsedEmail`/`Attachment` dataclasses) — never written to disk.
- `all_headers(name)` preserves repeated headers (critical for the multi-line
  `Received` chain and multiple `Authentication-Results`).

### 7.2 `headers.py` — authentication & routing (B1, B3–B6)
- **B1 auth results** — regex-extracts `spf= / dkim= / dmarc=` verdicts from
  `Authentication-Results` (and `ARC-Authentication-Results`). `fail` on DMARC →
  HIGH; other negative verdicts → MEDIUM. These are the upstream mail server's
  own SPF/DKIM/DMARC evaluation.
- **B3 From vs Reply-To vs Return-Path** — compares registrable domains. Reply-To
  mismatch → MEDIUM (replies silently go elsewhere — a BEC hallmark); Return-Path
  mismatch → LOW (legitimate ESPs also do this, so it's weighted low).
- **B5 originating IP** — walks `Received` headers **bottom-up** (oldest first)
  and returns the first **public** IP, skipping RFC 1918 / loopback / link-local
  ranges. This is the true sender's IP, later enriched via AbuseIPDB.
- **B6 Message-ID** — flags when the Message-ID host domain ≠ From domain (LOW;
  a weak corroborating signal).

### 7.3 `sender.py` — sender-domain analysis (B4, B8–B10)
- **B4 display-name spoofing** — if the display name contains a brand word
  (`brands.yaml`) but the sender domain is **not** one of that brand's legitimate
  domains → HIGH. Catches `"PayPal Support" <svc@paypa1-secure.xyz>`.
- **B9 typosquatting** — Levenshtein distance between the domain's core label and
  each brand's core label; `0 < distance ≤ max_distance (2)` → HIGH. Exact
  legitimate domains short-circuit to avoid false positives.
- **B10 punycode/homoglyph** — presence of `xn--` → HIGH (IDN homoglyph risk).
- **B8 domain age** — WHOIS creation date; `< 30 days` (configurable) → HIGH.
  Newly-registered domains are one of the strongest phishing predictors. Guarded
  by `allow_network` and the optional `python-whois`.

### 7.4 `urls.py` — URL analysis (B11–B17), never fetched
- **B11 extraction** — URLs from plain text (regex) and, via BeautifulSoup, from
  HTML `<a href>` and `<form action>`. De-duplicated, order preserved.
- **B12 link-text vs destination** — compares the registrable domain of the
  anchor's visible text against its real `href`; mismatch → HIGH. This is the
  single most reliable credential-phishing indicator.
- **B13 shorteners** (bit.ly, t.co, …) → MEDIUM; **B14 raw-IP URLs** → MEDIUM;
  **B15 risky TLDs** (`.zip .top .xyz .click …`) → MEDIUM; **B16 login keywords**
  in the path (`login, verify, webscr, …`) → LOW; **B17** `<form>` or
  `<input type=password>` in the body → MEDIUM. Each category is flagged **once**
  to avoid score inflation from many similar URLs.
- All lists are config-driven (`risky_tlds.yaml`). **No URL is ever requested.**

### 7.5 `attachments.py` — attachment inspection (B18–B23)
- **B18 hashing** — SHA256 of every attachment (fed to VirusTotal — hash only).
- **B19 real type** — `python-magic` sniffs the true MIME; an executable MIME
  under a non-exe extension → HIGH (extension spoofing).
- **B20 dangerous extensions** (`.exe .scr .js .vbs .hta .iso .lnk .html …`) → HIGH.
- **B21 double extension** — regex `…\.(pdf|docx?|…)\.(exe|scr|js|…)$` catches
  `facture.pdf.exe` → HIGH.
- **B22 Office macros** — `oletools` (`VBA_Parser`) detects macros; **auto-run**
  (`AutoOpen`, `Document_Open`, …) or **suspicious calls** (`Shell`,
  `URLDownloadToFile`, `CreateObject`, `powershell`) → HIGH; a plain macro →
  MEDIUM.
- **B23 password-protected archives** — reads the ZIP central directory
  (`flag_bits & 0x1`) **without extracting**; if the body text also mentions a
  password → MEDIUM (classic AV-evasion technique).

### 7.6 `content.py` — social-engineering language (B24–B26)
- Case-insensitive substring match of the subject+body against three keyword
  groups in `keywords.yaml` (FR+EN): **pressure/urgency** (B24), **financial
  lures** (B25), **generic greeting** (B26). Each group contributes a small,
  capped number of points — language alone never makes a verdict.

### 7.7 B7 — DNS cross-check (reuse of Module A)
`analyse_file` extracts the real DKIM selector(s) from the `DKIM-Signature`
headers and calls `dns_audit.audit(sender_domain, allow_network=False, …)`. If
the sender domain publishes **no DMARC**, it's trivially spoofable → MEDIUM. This
is the architectural link between the two modules.

### 7.8 Email scoring ([scorer.py](../phishguard/email_analysis/scorer.py))
Findings **add** points. `_weight_key()` maps each finding to a weight in
`config/scoring.yaml`; keyword groups (B24–B26) share a **cap** (default 15) so
wordy emails can't dominate the score:

```
score = Σ weighted findings  (keyword groups jointly capped at 15)
0–29  → clean
30–59 → suspicious   (needs analyst review)
≥60   → phishing
```

Representative weights: DMARC fail +25, lookalike/punycode +30, dangerous/double
attachment +30, auto-run macro +30, display-name spoof +20, link mismatch +20,
young domain +20, SPF fail +15, Reply-To mismatch +15, VirusTotal ≥3 engines +40,
AbuseIPDB >50 +15.

---

## 8. Threat-intelligence enrichment

`intel.build_enricher(offline)` returns an `enrich(iocs) -> list[Finding]`
callable, or **`None`** when enrichment is unavailable (offline, no `requests`,
or no API keys) — the orchestrator simply skips enrichment in that case.

- **`cache.py`** — a tiny SQLite cache (`.cache/intel.sqlite`) keyed by query,
  with a 24-hour TTL. This is what keeps usage inside free-tier API limits:
  repeated analyses of the same IOC hit the cache, not the API.
- **`virustotal.py`** — looks up file **hashes** only (never uploads files, which
  could leak sensitive data). `≥3` malicious engines → CRITICAL finding (+40).
- **`abuseipdb.py`** — reputation of the sender IP; `abuseConfidenceScore > 50` →
  HIGH (+15), with country/ISP context.
- **`urlhaus.py`** — abuse.ch malware-URL list (works without a key); a listed URL
  → CRITICAL.

Every network call is wrapped in `try/except` with a 10-second timeout and
returns `None` on failure, so one slow or broken API never stalls or aborts the
analysis.

---

## 9. Scoring engine & verdicts

Two scorers share the same philosophy — **explainable, config-driven,
finding-based** — but run in opposite directions:

| | DNS (Module A) | Email (Module B) |
|---|---|---|
| Direction | start 100, **subtract** | start 0, **add** |
| Output | score + **A–F grade** | score + **clean/suspicious/phishing** |
| Mapping | `_penalty_key()` | `_weight_key()` |
| Guardrail | penalties clamped to [0,100] | keyword groups capped |

Because thresholds and weights are external YAML, the tuning loop ("we get too
many false positives on newsletters") is a config edit + `pytest`, not a code
change. **Measuring the false-positive rate against legitimate mail is a
first-class goal** (see the evaluation table in the README) — it's the question
SOC interviewers ask most.

---

## 10. MITRE ATT&CK mapping

The email scorer maps finding IDs to techniques and reports the de-duplicated set:

| Finding(s) | Technique |
|---|---|
| B19–B22 (attachments, macros) | **T1566.001** Spearphishing Attachment |
| B12–B17 (malicious links/forms) | **T1566.002** Spearphishing Link |
| B8–B10 (new / typosquatted / IDN domain) | **T1583.001** Acquire Infrastructure: Domains |

These IDs also propagate into the Wazuh rules (`<mitre><id>T1566</id></mitre>`),
so the SIEM dashboard can pivot by technique.

---

## 11. Output layer

- **`console.py` (Rich)** — colour-coded panels and tables; verdict/grade colours
  (green/amber/red); a defanged IOC table; a batch-summary table with per-verdict
  counts. **Windows fix:** on import it reconfigures `stdout`/`stderr` to UTF-8,
  because the legacy console codepage (cp1252) cannot encode accented subjects or
  the `→` arrow and would otherwise raise `UnicodeEncodeError`.
- **`json_out.py`** — `to_dict()` + **defanging** of all URLs/IPs/domains before
  serialisation (`ensure_ascii=False` to preserve accents). This is the
  machine-readable, safe-to-share artifact.
- **`html_report.py` + `templates/report.html.j2`** — a self-contained Jinja2
  report (autoescaped, `defang` filters registered) with a coloured verdict
  banner, the findings table (with per-finding detail + recommendation), a
  defanged IOC table, and a **response-actions** checklist (block domain, purge
  mailboxes, reset credentials if clicked). Dark/light via `prefers-color-scheme`.
- **`siem.py`** — appends one **compact** JSON line (`report.siem_line()`) per
  result. Path resolution: `PHISHGUARD_SIEM_LOG` env → `/var/log/phishguard/
  alerts.json` on Linux → `logs/alerts.json` on Windows dev. Creates parent dirs
  as needed.

---

## 12. SIEM integration (Wazuh)

Two files in `wazuh/`:

- **`ossec_localfile.xml`** — add to the **agent** `ossec.conf`; tells Wazuh to
  read the NDJSON alert file as JSON.
- **`local_rules.xml`** — install on the **manager**. Rule `100200` decodes the
  JSON and matches `tool=phishguard`; children escalate by severity:
  `suspicious` → level 7, `phishing` → level 12 (both tagged `T1566`), and
  `module=dns grade=F` → level 10. Validate with `wazuh-logtest` before
  production.

**Correlation idea (the real SIEM value, great for interviews):** if PhishGuard
flags phishing containing domain *X*, and your IDS / DNS logs later show an
internal host querying *X*, raise a high-severity alert — **"a user may have
clicked the phishing link."** This turns isolated email analysis into
detection-and-response.

---

## 13. CLI

Built with **Typer** (`cli.py`). Two commands:

- **`phishguard dns <domain>`** — `--format console|json`, `-o` file,
  `--offline`, `--no-zone-transfer`, `--no-takeover`, `--html`, `--siem`.
- **`phishguard email <file|dir>`** — single file or a folder (`rglob *.eml`),
  `--format`, `-o`, `--html`, `--siem`, `--offline`, `--summary` (batch table).

Design choices: heavy modules are imported **lazily inside the command** so
`--help`/`--version` stay instant; batch mode catches per-file exceptions so one
malformed `.eml` doesn't abort the run; `.env` is auto-loaded via `python-dotenv`.
Entry points: `python -m phishguard` (`__main__.py`) and the `phishguard` console
script (`pyproject.toml`).

---

## 14. Testing strategy

14 unit tests (`pytest`), all **network-free** and deterministic:

- `test_spf.py` — the `all`-qualifier regex and `_count_lookups` (with
  `monkeypatch` stubbing nested record lookups).
- `test_dmarc.py` — tag parsing, including trailing-semicolon edge cases.
- `test_headers.py` — `split_address`, auth-result extraction, and the
  bottom-up public-IP selection from a synthetic `Received` chain.
- `test_urls.py` — link-text/href mismatch, raw-IP + risky-TLD detection, and a
  **negative test** (a clean GitHub URL yields no findings).
- `test_scoring.py` — end-to-end verdict (phishing), the keyword cap, the DNS
  penalty→grade math (`100−25−25 = 50 → D`), and lookalike detection **plus a
  false-positive guard** (`github.com` → no finding).

A root `conftest.py` puts the repo on `sys.path` so tests run without an install.
Threat-intel APIs are designed to be mocked (pure functions taking a cache
object); no test performs a live call. **Verified:** `14 passed`.

Functional verification on the bundled samples:

| Sample | Expected | Actual |
|---|---|---|
| `phishing/paypal_lookalike.eml` | phishing | **phishing, score 125** |
| `phishing/invoice_double_ext.eml` | phishing | **phishing, score 120** (B20+B21, SHA256) |
| `legit/example_newsletter.eml` | clean | **clean, score 0** (0 false positives) |

---

## 15. Security & ethics

- **Static only** — no link is fetched, no attachment executed; work inside a VM
  when handling live samples.
- **Hashes only to VirusTotal** — files are never uploaded (they may contain
  sensitive data).
- **All IOCs defanged** in every human-facing output.
- **Authorised targets only** for AXFR and subdomain enumeration (own/authorised
  domains, or the learning target `zonetransfer.me`); both are opt-outable.
- **No secrets in git** — `.env` is git-ignored (and the legacy project's `.env`
  was removed from tracking during the rebuild); real personal email under
  `samples/legit/` is git-ignored (only synthetic `example_*.eml` is committed).
- **Minimal SIEM payload** — `siem_line()` omits full bodies and truncates the
  subject, so analysis of sensitive mail doesn't leak into the SIEM.

---

## 16. Known limitations & roadmap

**Limitations**
- DKIM selector discovery is best-effort (common-selector probing) unless a real
  selector is supplied by an analysed email.
- Full DKIM signature re-verification (`dkimpy`) is optional; forwarded mail often
  legitimately breaks DKIM, so it's weighted, not decisive.
- `python-magic` needs `libmagic`; `oletools` is optional — without them, B19/B22
  are skipped.
- Typosquatting is limited to the curated `brands.yaml`; it won't catch
  impersonation of brands not in the list (a `dnstwist` backend is a natural
  upgrade).
- WHOIS/crt.sh/MTA-STS depend on network and public-service availability.

**Roadmap**
- IMAP ingestion of a phishing-report mailbox for automated triage.
- QR-code (quishing) detection in images via `pyzbar`.
- A small FastAPI web UI.
- IOC export to **STIX / MISP**.
- Detection rules as **Sigma** (portable across SIEMs).

---

## 17. Appendix — finding ID reference

**DNS (Module A)**

| ID | Check | Default severity |
|----|-------|------|
| A1 | MX present | info |
| A2 | SPF (missing / multiple / `+all` / `?all` / >10 lookups) | high/medium |
| A3 | DMARC (missing / `p=none` / no `rua` / `pct<100`) | high/medium/low |
| A4 | DKIM common selectors / weak key | medium |
| A5 | DNSSEC enabled | medium |
| A6 | CAA | low |
| A7 | Zone transfer (AXFR) open | high |
| A8 | MTA-STS | low |
| A9 | TLS-RPT | low |
| A10 | Name-server diversity | low |
| A11 | Subdomain takeover (dangling CNAME) | high |

**Email (Module B)**

| ID | Check | Default severity |
|----|-------|------|
| B1 | SPF/DKIM/DMARC auth results | high/medium |
| B3 | From vs Reply-To vs Return-Path | medium/low |
| B4 | Display-name brand spoof | high |
| B5 | Originating IP (Received chain) | — (IOC) |
| B6 | Message-ID domain mismatch | low |
| B7 | Sender domain has no DMARC (Module A reuse) | medium |
| B8 | Domain age < 30 days | high |
| B9 | Typosquatting (Levenshtein) | high |
| B10 | Punycode / homoglyph | high |
| B11 | URL extraction | — |
| B12 | Link text ≠ destination | high |
| B13 | URL shortener | medium |
| B14 | Raw-IP URL | medium |
| B15 | Risky TLD | medium |
| B16 | Login keyword in URL path | low |
| B17 | HTML form / password input | medium |
| B18 | Attachment SHA256 | — (IOC) |
| B19 | Real file type ≠ extension | high |
| B20 | Dangerous extension | high |
| B21 | Double extension | high |
| B22 | Office macro (auto-run / suspicious) | high/medium |
| B23 | Password-protected archive | medium |
| B24 | Pressure / urgency language | low |
| B25 | Financial lure | low |
| B26 | Generic greeting | info |
| VT | VirusTotal / URLhaus hit (enrichment) | critical |
| ABUSE | AbuseIPDB high score (enrichment) | high |

---

*Generated for the PhishGuard project. Defensive, static analysis only.*
