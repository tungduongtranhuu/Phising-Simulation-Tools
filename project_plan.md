# PhishGuard: Outil d'analyse de phishing et d'audit de sécurité DNS

> Tài liệu mô tả hệ thống (spec) để build project. Tên "PhishGuard" chỉ là tên tạm, bạn có thể đổi.

---

## 1. Mục tiêu

Xây dựng một công cụ dòng lệnh bằng Python có **2 module**:

| Module | Đầu vào | Câu hỏi trả lời | Người dùng thực tế |
|---|---|---|---|
| **A. Audit DNS** | Tên miền (`example.com`) | Domain này có được cấu hình an toàn để chống giả mạo email và tấn công DNS không? | Đội bảo mật / admin của tổ chức |
| **B. Phân tích email** | File `.eml` | Email này có phải phishing không? IOC (URL, IP, hash) là gì? | SOC analyst L1 khi người dùng báo email đáng ngờ |

Kết quả được xuất ra **terminal, JSON, báo cáo HTML** và **gửi sang SIEM Wazuh** để tạo alert.

Mục tiêu học tập (để ghi CV): hiểu SPF/DKIM/DMARC, DNSSEC, phân tích header email, trích xuất và làm giàu IOC (threat intelligence), chấm điểm rủi ro, tích hợp với SIEM, ánh xạ MITRE ATT&CK.

---

## 2. Phạm vi

**Làm:**
- Phân tích **tĩnh** email (không bao giờ mở link hay chạy file đính kèm)
- Audit DNS bằng truy vấn DNS công khai
- Tra cứu threat intelligence qua API miễn phí
- Tích hợp Wazuh qua file log JSON

**Không làm:**
- Gửi email phishing, chiến dịch mô phỏng (GoPhish): ngoài phạm vi
- Sandbox động (chạy malware): ngoài phạm vi
- Kết nối trực tiếp vào hộp thư (IMAP/Graph API): để dành cho bản mở rộng

---

## 3. Kiến trúc tổng quan

```
                        ┌──────────────────────────┐
   example.com  ──────► │   CLI (typer)            │ ◄────── suspicious.eml
                        └────────────┬─────────────┘
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
     ┌───────────────────────┐              ┌────────────────────────┐
     │  Module A: DNS Audit  │◄─────────────│  Module B: Email       │
     │  - SPF / DMARC / DKIM │  réutilise   │  - Parser .eml         │
     │  - DNSSEC / CAA / MX  │  pour le     │  - Headers / Auth      │
     │  - Zone transfer      │  domaine     │  - URLs / Pièces jointes│
     │  - MTA-STS / TLS-RPT  │  expéditeur  │  - Lookalike domains   │
     │  - Subdomain takeover │              │  - Contenu (mots-clés) │
     └──────────┬────────────┘              └───────────┬────────────┘
                │                                       ▼
                │                         ┌────────────────────────┐
                │                         │  Enrichissement TI     │
                │                         │  VirusTotal, AbuseIPDB │
                │                         │  URLhaus, WHOIS        │
                │                         └───────────┬────────────┘
                ▼                                     ▼
         ┌──────────────────────────────────────────────────┐
         │  Moteur de scoring  →  verdict + mapping MITRE    │
         └───────────────┬──────────────────────────────────┘
        ┌────────────────┼─────────────────┬────────────────────┐
        ▼                ▼                 ▼                    ▼
   Terminal (rich)   JSON report     HTML report (jinja2)   alerts.json ──► Agent Wazuh ──► Dashboard
```

---

## 4. Công nghệ và thư viện

| Nhóm | Công cụ | Dùng để làm gì |
|---|---|---|
| Ngôn ngữ | **Python 3.11+** | Toàn bộ project |
| CLI | `typer`, `rich` | Giao diện dòng lệnh, bảng màu trong terminal |
| DNS | `dnspython` | Truy vấn TXT, MX, CAA, DNSKEY, DS, NS, AXFR |
| SPF/DMARC | `checkdmarc` | Phân tích và kiểm tra cú pháp SPF/DMARC (có thể tự viết để hiểu sâu hơn) |
| DKIM | `dkimpy` | Xác minh chữ ký DKIM của email |
| Email | `email` (thư viện chuẩn, `policy=default`) | Đọc file `.eml`, header, phần MIME |
| HTML | `beautifulsoup4` | Lấy link trong phần HTML, so sánh chữ hiển thị và href thật |
| Domain | `tldextract`, `python-whois`, `dnstwist` | Tách domain gốc, tuổi domain, phát hiện domain giả mạo |
| File đính kèm | `hashlib`, `python-magic`, `oletools` | Hash SHA256, loại file thật, phát hiện macro Office |
| HTTP | `requests` | Gọi API threat intel, crt.sh, MTA-STS |
| Cấu hình | `pyyaml`, `python-dotenv` | Trọng số chấm điểm, API key |
| Báo cáo | `jinja2` | Báo cáo HTML |
| Mô hình dữ liệu | `pydantic` (hoặc `dataclasses`) | Cấu trúc kết quả rõ ràng, xuất JSON |
| Kiểm thử | `pytest` | Unit test |
| Chất lượng code | `ruff`, `black` | Lint và format |
| SIEM | **Wazuh** (manager + agent) | Thu thập alert JSON, rule tùy chỉnh, dashboard |
| Lab | VirusTotal, AbuseIPDB, URLhaus (abuse.ch) | API threat intel miễn phí (cần đăng ký key, có giới hạn số lượt, kiểm tra trên trang chính thức) |

---

## 5. Module A: Audit DNS

### 5.1 Các kiểm tra

| # | Kiểm tra | Cách làm | Dấu hiệu rủi ro | Mức độ |
|---|---|---|---|---|
| A1 | **MX** | Truy vấn `MX` | Không có MX nhưng vẫn gửi email | Info |
| A2 | **SPF** | TXT bắt đầu bằng `v=spf1` | Không có SPF; có nhiều bản ghi SPF; kết thúc `+all` hoặc `?all`; quá 10 lượt DNS lookup | Cao |
| A3 | **DMARC** | TXT tại `_dmarc.domain` | Không có DMARC; `p=none`; không có `rua`; `pct<100` | Cao |
| A4 | **DKIM** | TXT tại `<selector>._domainkey.domain` | Không tìm thấy selector phổ biến; khóa RSA < 1024 bit | Trung bình |
| A5 | **DNSSEC** | Có `DNSKEY` và `DS` tại zone cha | Không bật DNSSEC | Trung bình |
| A6 | **CAA** | Truy vấn `CAA` | Không giới hạn CA nào được cấp chứng chỉ | Thấp |
| A7 | **Zone transfer** | Thử `AXFR` trên từng name server | Name server cho phép tải toàn bộ zone | Cao |
| A8 | **MTA-STS** | TXT `_mta-sts.domain` + file `https://mta-sts.domain/.well-known/mta-sts.txt` | Không có, hoặc `mode: testing` | Thấp |
| A9 | **TLS-RPT** | TXT `_smtp._tls.domain` | Không có báo cáo TLS | Thấp |
| A10 | **Name servers** | Truy vấn `NS` | Chỉ có 1 NS, hoặc mọi NS cùng một mạng | Thấp |
| A11 | **Subdomain + takeover** | Lấy subdomain từ certificate transparency (crt.sh), kiểm tra CNAME trỏ đến dịch vụ không còn tồn tại (GitHub Pages, Heroku, S3, Azure...) | CNAME "treo" (dangling) | Cao |

**Lưu ý về DKIM:** không thể liệt kê tất cả selector DKIM của một domain. Hãy thử danh sách selector phổ biến: `default`, `google`, `selector1`, `selector2`, `k1`, `mail`, `dkim`, `s1`, `s2`. Nếu đang phân tích một email, lấy selector thật từ trường `s=` trong header `DKIM-Signature`.

**Lưu ý về subdomain takeover:** tham khảo dấu hiệu nhận biết từ repo cộng đồng `can-i-take-over-xyz` trên GitHub.

### 5.2 Chấm điểm DNS

Bắt đầu từ 100 điểm, trừ theo lỗi tìm được:

| Lỗi | Trừ điểm |
|---|---|
| Không có SPF | −25 |
| SPF `+all` | −30 |
| SPF `?all` hoặc quá 10 lookup | −10 |
| Không có DMARC | −25 |
| DMARC `p=none` | −15 |
| Zone transfer mở | −30 |
| Subdomain takeover khả nghi | −25 |
| Không có DNSSEC | −10 |
| Không có DKIM (selector phổ biến) | −10 |
| Không có CAA / MTA-STS / TLS-RPT | −3 mỗi mục |

Xếp hạng: **A** ≥ 90 · **B** ≥ 75 · **C** ≥ 60 · **D** ≥ 40 · **F** < 40.
Mỗi lỗi kèm **khuyến nghị sửa** (ví dụ bản ghi DMARC mẫu: `v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com`).

---

## 6. Module B: Phân tích email

### 6.1 Đọc file `.eml`

```python
from email import policy
from email.parser import BytesParser

with open(path, "rb") as f:
    msg = BytesParser(policy=policy.default).parse(f)
```

Duyệt `msg.walk()` để lấy phần text, HTML và file đính kèm.

### 6.2 Phân tích header

| # | Kiểm tra | Cách làm | Dấu hiệu |
|---|---|---|---|
| B1 | **Kết quả xác thực** | Đọc `Authentication-Results`: `spf=`, `dkim=`, `dmarc=` | `fail`, `softfail`, `none` |
| B2 | **Xác minh DKIM lại** | `dkim.verify(raw_bytes)` | Chữ ký không hợp lệ (lưu ý: email bị forward có thể làm hỏng DKIM) |
| B3 | **From / Reply-To / Return-Path** | So sánh domain gốc (dùng `tldextract`) | Ba domain khác nhau |
| B4 | **Giả mạo tên hiển thị** | `"PayPal Support" <abc@gmail-random.xyz>` | Tên thương hiệu nhưng domain lạ |
| B5 | **Chuỗi Received** | Tách các header `Received` (đọc từ dưới lên), lấy IP gửi đầu tiên | IP thuộc danh sách đen, quốc gia bất thường |
| B6 | **Message-ID** | Domain trong Message-ID | Không khớp với domain gửi |
| B7 | **Kiểm tra DNS domain gửi** | Gọi lại **Module A** (SPF/DMARC) | Domain không có DMARC: dễ bị giả mạo |

### 6.3 Phân tích domain người gửi

| # | Kiểm tra | Công cụ | Dấu hiệu |
|---|---|---|---|
| B8 | **Tuổi domain** | `python-whois` | Tạo dưới 30 ngày |
| B9 | **Domain giả mạo (typosquatting)** | `dnstwist` hoặc khoảng cách Levenshtein so với danh sách thương hiệu (`brands.yaml`) | `paypa1.com`, `micr0soft.com` |
| B10 | **Punycode / homoglyph** | Domain chứa `xn--` | `аpple.com` dùng chữ Cyrillic |

### 6.4 Phân tích URL

| # | Kiểm tra | Dấu hiệu |
|---|---|---|
| B11 | Trích xuất URL từ text và HTML (`<a href>`, `<form action>`) | |
| B12 | **Chữ hiển thị khác link thật** | `<a href="http://evil.xyz">https://bank.fr</a>` |
| B13 | **URL rút gọn** | bit.ly, tinyurl, t.co... |
| B14 | **IP thay vì domain** | `http://185.12.3.4/login` |
| B15 | **Đuôi domain rủi ro** | `.zip`, `.top`, `.xyz`, `.click`... (cấu hình được) |
| B16 | **Từ khóa đăng nhập** | `login`, `verify`, `secure`, `account`, `webscr` trong đường dẫn |
| B17 | **Form trong email HTML** | Có thẻ `<form>` hoặc `<input type="password">` |

**Không bao giờ truy cập URL.** Chỉ phân tích chuỗi và tra cứu qua API.

### 6.5 Phân tích file đính kèm

| # | Kiểm tra | Công cụ | Dấu hiệu |
|---|---|---|---|
| B18 | Hash MD5/SHA256 | `hashlib` | Dùng để tra VirusTotal |
| B19 | Loại file thật | `python-magic` | Đuôi `.pdf` nhưng thực chất là file thực thi |
| B20 | Đuôi nguy hiểm | Danh sách | `.exe`, `.scr`, `.js`, `.vbs`, `.hta`, `.iso`, `.img`, `.lnk`, `.html` |
| B21 | Đuôi kép | Regex | `facture.pdf.exe` |
| B22 | Macro Office | `oletools` (`olevba`) | Có macro, đặc biệt `AutoOpen`, `Shell`, `URLDownloadToFile` |
| B23 | File nén có mật khẩu | `zipfile` | Mật khẩu ghi trong nội dung email (kỹ thuật né antivirus) |

### 6.6 Phân tích nội dung

| # | Kiểm tra | Dấu hiệu |
|---|---|---|
| B24 | Từ ngữ tạo áp lực (FR + EN) | "urgent", "compte suspendu", "vérifiez immédiatement", "dernier avis", "action required" |
| B25 | Chủ đề tài chính | "virement", "facture impayée", "remboursement", "gift card" |
| B26 | Lời chào chung chung | "Cher client", "Dear user" |

Đặt danh sách từ khóa trong file `keywords.yaml` để dễ chỉnh sửa.

---

## 7. Làm giàu threat intelligence (enrichment)

| Nguồn | Tra cứu | Ghi chú |
|---|---|---|
| **VirusTotal** | Hash file, URL, domain | **Chỉ gửi hash**, không upload file (file có thể chứa dữ liệu nhạy cảm) |
| **AbuseIPDB** | IP gửi (từ Received) | Điểm `abuseConfidenceScore` |
| **URLhaus** (abuse.ch) | URL, hash | Danh sách URL phát tán malware |
| **WHOIS** | Tuổi domain | |

Yêu cầu kỹ thuật:
- API key lưu trong file `.env`, **không commit lên GitHub** (thêm vào `.gitignore`)
- **Cache** kết quả (file JSON hoặc SQLite) để không vượt giới hạn API miễn phí
- Có chế độ `--offline` để chạy khi không có mạng hoặc không có key
- Xử lý lỗi và timeout, không để cả chương trình dừng vì một API lỗi

---

## 8. Hệ thống chấm điểm email

Mỗi kiểm tra trả về một **finding** có trọng số. Trọng số lưu trong `config/scoring.yaml` để dễ tinh chỉnh.

| Finding | Điểm |
|---|---|
| DMARC fail | +25 |
| SPF fail / softfail | +15 |
| DKIM fail hoặc không có | +10 |
| Reply-To khác From | +15 |
| Tên hiển thị giả mạo thương hiệu | +20 |
| Domain tạo dưới 30 ngày | +20 |
| Domain giả mạo (typosquatting/punycode) | +30 |
| Link hiển thị khác link thật | +20 |
| URL dùng IP / URL rút gọn | +10 |
| File đính kèm đuôi nguy hiểm / đuôi kép | +30 |
| Macro Office tự chạy | +30 |
| VirusTotal: ≥ 3 engine phát hiện | +40 |
| IP gửi có điểm AbuseIPDB > 50 | +15 |
| Từ ngữ áp lực / tài chính | +5 mỗi nhóm (tối đa +15) |

**Kết luận:**
- **0–29:** `clean` (sạch)
- **30–59:** `suspicious` (đáng ngờ, cần analyst xem thêm)
- **≥ 60:** `phishing`

**Ánh xạ MITRE ATT&CK:**
- `T1566.001` Spearphishing Attachment (có file đính kèm nguy hiểm)
- `T1566.002` Spearphishing Link (có link độc hại)
- `T1583.001` Acquire Infrastructure: Domains (domain mới hoặc typosquatting)

**Quan trọng:** test với cả email **hợp lệ** (email thật của bạn xuất ra `.eml`) để đo **tỷ lệ false positive**. Đây là điểm người phỏng vấn SOC rất hay hỏi.

---

## 9. Đầu ra

### 9.1 CLI

```bash
# Audit DNS
phishguard dns example.com
phishguard dns example.com --format json -o report.json

# Phân tích email
phishguard email samples/suspicious.eml
phishguard email samples/suspicious.eml --html report.html --siem

# Phân tích hàng loạt
phishguard email samples/ --summary
```

### 9.2 Ví dụ kết quả JSON (email)

```json
{
  "tool": "phishguard",
  "module": "email",
  "timestamp": "2026-10-13T17:30:00+02:00",
  "file": "suspicious.eml",
  "subject": "Votre compte sera suspendu",
  "sender": "service@paypa1-secure.xyz",
  "sender_domain": "paypa1-secure.xyz",
  "sender_ip": "185.xx.xx.xx",
  "auth": { "spf": "fail", "dkim": "none", "dmarc": "fail" },
  "score": 95,
  "verdict": "phishing",
  "findings": [
    { "id": "B1", "title": "DMARC fail", "points": 25 },
    { "id": "B9", "title": "Lookalike domain of paypal.com", "points": 30 },
    { "id": "B12", "title": "Link text differs from href", "points": 20 }
  ],
  "iocs": {
    "urls": ["hxxp://paypa1-secure[.]xyz/login"],
    "ips": ["185.xx.xx.xx"],
    "hashes": []
  },
  "mitre": ["T1566.002", "T1583.001"]
}
```

IOC trong báo cáo phải được **"defang"** (`http` → `hxxp`, `.` → `[.]`) để không ai bấm nhầm.

### 9.3 Báo cáo HTML

Dùng `jinja2`. Gồm: kết luận và điểm (màu xanh/cam/đỏ), bảng findings, bảng IOC, header gốc, kết quả audit DNS của domain gửi, khuyến nghị hành động (chặn domain, xóa email khỏi các hộp thư, reset mật khẩu nếu người dùng đã bấm link...).

---

## 10. Tích hợp Wazuh (SIEM)

### 10.1 Ghi log

Khi chạy với `--siem`, công cụ ghi **mỗi kết quả là một dòng JSON** (dạng rút gọn, không chứa toàn bộ nội dung email) vào:

```
/var/log/phishguard/alerts.json
```

### 10.2 Cấu hình agent Wazuh (`ossec.conf` trên máy chạy công cụ)

```xml
<localfile>
  <log_format>json</log_format>
  <location>/var/log/phishguard/alerts.json</location>
</localfile>
```

### 10.3 Rule tùy chỉnh (`/var/ossec/etc/rules/local_rules.xml` trên manager)

```xml
<group name="phishguard,">

  <rule id="100200" level="3">
    <decoded_as>json</decoded_as>
    <field name="tool">phishguard</field>
    <description>PhishGuard: événement d'analyse</description>
  </rule>

  <rule id="100201" level="7">
    <if_sid>100200</if_sid>
    <field name="verdict">suspicious</field>
    <description>PhishGuard: email suspect de $(sender_domain)</description>
    <mitre><id>T1566</id></mitre>
  </rule>

  <rule id="100202" level="12">
    <if_sid>100200</if_sid>
    <field name="verdict">phishing</field>
    <description>PhishGuard: phishing détecté de $(sender_domain), score $(score)</description>
    <mitre><id>T1566</id></mitre>
  </rule>

  <rule id="100210" level="10">
    <if_sid>100200</if_sid>
    <field name="module">dns</field>
    <field name="grade">F</field>
    <description>PhishGuard: configuration DNS critique pour $(domain)</description>
  </rule>

</group>
```

Kiểm tra rule bằng công cụ `wazuh-logtest` trên manager trước khi dùng thật.

### 10.4 Ý tưởng tương quan (bonus, rất tốt để kể khi phỏng vấn)

Kết hợp với **IDS** của bạn: nếu PhishGuard phát hiện phishing chứa domain X, và sau đó IDS hoặc log DNS ghi nhận một máy trong mạng truy vấn domain X, thì tạo alert mức cao: **"Người dùng có thể đã bấm vào link phishing"**. Đây chính là giá trị cốt lõi của SIEM.

### 10.5 Dashboard

Tạo dashboard trong Wazuh: số email theo verdict, top domain gửi phishing, top kỹ thuật MITRE, điểm DNS của các domain đã audit.

---

## 11. Cấu trúc thư mục

```
phishguard/
├── README.md
├── pyproject.toml
├── .env.example              # VT_API_KEY=, ABUSEIPDB_API_KEY=, URLHAUS_KEY=
├── .gitignore
├── config/
│   ├── scoring.yaml          # trọng số
│   ├── keywords.yaml         # từ khóa FR/EN
│   ├── brands.yaml           # thương hiệu hay bị giả mạo
│   └── risky_tlds.yaml
├── phishguard/
│   ├── __init__.py
│   ├── cli.py                # typer
│   ├── models.py             # Finding, EmailReport, DnsReport (pydantic)
│   ├── dns_audit/
│   │   ├── spf.py
│   │   ├── dmarc.py
│   │   ├── dkim.py
│   │   ├── dnssec.py
│   │   ├── records.py        # MX, NS, CAA, MTA-STS, TLS-RPT
│   │   ├── zone_transfer.py
│   │   ├── takeover.py
│   │   └── scorer.py
│   ├── email_analysis/
│   │   ├── parser.py
│   │   ├── headers.py
│   │   ├── sender.py         # whois, lookalike, punycode
│   │   ├── urls.py
│   │   ├── attachments.py
│   │   ├── content.py
│   │   └── scorer.py
│   ├── intel/
│   │   ├── virustotal.py
│   │   ├── abuseipdb.py
│   │   ├── urlhaus.py
│   │   └── cache.py
│   └── output/
│       ├── console.py        # rich
│       ├── json_out.py
│       ├── html_report.py
│       ├── siem.py           # ghi alerts.json cho Wazuh
│       └── templates/report.html.j2
├── wazuh/
│   ├── ossec_localfile.xml
│   └── local_rules.xml
├── samples/                  # email test (KHÔNG commit email cá nhân thật)
│   ├── legit/
│   └── phishing/
├── tests/
│   ├── test_spf.py
│   ├── test_dmarc.py
│   ├── test_headers.py
│   ├── test_urls.py
│   └── test_scoring.py
└── docs/
    ├── architecture.png
    └── screenshots/
```

---

## 12. Lộ trình build (khớp tuần 4–6 của kế hoạch)

| Mốc | Nội dung | Kết quả kiểm chứng |
|---|---|---|
| **M1** (2–3 ngày) | Khung project, CLI, models, MX/SPF/DMARC | `phishguard dns gmail.com` in ra bảng kết quả |
| **M2** (3 ngày) | DKIM, DNSSEC, CAA, MTA-STS, zone transfer, chấm điểm DNS | Test trên `zonetransfer.me` (domain cố ý cấu hình lỗi để học) phát hiện AXFR mở |
| **M3** (3 ngày) | Parser `.eml`, header, From/Reply-To, Received | Phân tích đúng 10 email mẫu |
| **M4** (3 ngày) | URL, file đính kèm, nội dung, lookalike domain | Phát hiện link giả, đuôi kép, domain typosquatting |
| **M5** (2 ngày) | Threat intel + cache + chế độ offline | Kết quả có điểm VirusTotal/AbuseIPDB |
| **M6** (2 ngày) | Chấm điểm, JSON, HTML | Báo cáo HTML đẹp, đo false positive trên email hợp lệ |
| **M7** (2 ngày) | Wazuh: log JSON, rule, dashboard | Alert xuất hiện trên dashboard Wazuh |
| **M8** (1–2 ngày) | Test, README, ảnh chụp màn hình, video demo ngắn | Repo GitHub hoàn chỉnh |

Nếu thiếu thời gian: **ưu tiên Module B (email)** và Wazuh, giản lược Module A (chỉ SPF/DMARC/DKIM/zone transfer).

---

## 13. Dữ liệu test

- **Email phishing mẫu:** tìm trên GitHub với từ khóa `phishing_pot` hoặc `phishing email samples eml`
- **Email hợp lệ:** xuất vài email thật của bạn (newsletter, thông báo ngân hàng) sang `.eml` để đo false positive. **Không commit chúng lên GitHub**
- **DNS:** `zonetransfer.me` để test AXFR; domain lớn (google.com, gouv.fr) để xem cấu hình tốt trông như thế nào

---

## 14. Kiểm thử

- Unit test cho từng hàm phân tích (bản ghi SPF/DMARC mẫu dạng chuỗi, header mẫu)
- Mock các API threat intel trong test (không gọi API thật)
- Bảng đánh giá trong README:

| Bộ dữ liệu | Số email | Phát hiện đúng | False positive | False negative |
|---|---|---|---|---|
| Phishing | ... | ... | – | ... |
| Hợp lệ | ... | – | ... | – |

Có bảng này, project của bạn sẽ nổi bật hơn hẳn phần lớn project sinh viên.

---

## 15. An toàn và đạo đức

- Chỉ phân tích tĩnh, làm việc trong **máy ảo**
- Không bao giờ mở link hay file đính kèm từ email mẫu
- Chỉ gửi **hash** lên VirusTotal, không upload file
- Defang mọi IOC trong báo cáo
- Chỉ thử **zone transfer** và quét subdomain trên domain của bạn, domain được phép, hoặc domain dùng để học (`zonetransfer.me`)
- Không commit API key, email cá nhân, dữ liệu nhạy cảm

---

## 16. README trên GitHub nên có

1. Mô tả 2–3 câu: vấn đề và giải pháp
2. Sơ đồ kiến trúc
3. GIF hoặc ảnh chụp: terminal, báo cáo HTML, dashboard Wazuh
4. Cài đặt và cách dùng
5. Danh sách kiểm tra (bảng mục 5 và 6, viết gọn)
6. Bảng đánh giá (mục 14)
7. Giới hạn đã biết và hướng phát triển
8. Ánh xạ MITRE ATT&CK

Viết README bằng **tiếng Anh hoặc tiếng Pháp** vì nhà tuyển dụng sẽ đọc.

---

## 17. Ghi vào CV

> **PhishGuard – Outil d'analyse de phishing et d'audit DNS** (Python, Wazuh) · github.com/…
> - Analyse statique d'e-mails (.eml) : vérification SPF/DKIM/DMARC, incohérences From/Reply-To/Return-Path, traçage des en-têtes Received
> - Extraction et enrichissement d'IOC (URL, IP, hash) via VirusTotal, AbuseIPDB et URLhaus ; détection de typosquatting et de domaines récents
> - Score de risque, mapping MITRE ATT&CK (T1566) et rapport HTML ; taux de faux positifs mesuré sur un jeu d'e-mails légitimes
> - Audit DNS : SPF, DMARC, DKIM, DNSSEC, CAA, MTA-STS, transfert de zone, risque de subdomain takeover
> - Intégration SIEM : envoi des résultats à Wazuh, règles de détection personnalisées et dashboard

---

## 18. Mở rộng sau (nếu còn thời gian)

- Kết nối hộp thư qua IMAP để phân tích tự động hộp "signalement phishing"
- Phát hiện mã QR trong ảnh (quishing) bằng `pyzbar`
- Giao diện web nhỏ bằng FastAPI
- Xuất IOC sang định dạng STIX hoặc MISP
- Viết rule dưới dạng **Sigma** để dùng cho nhiều SIEM