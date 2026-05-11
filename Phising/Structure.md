Rất tốt 👍
Bạn đang chọn hướng đúng:

> 🌐 Web-based tool (dashboard)
> +
> 🧠 SOC-focused analytics & incident logic

Tức là bạn không làm “web đẹp để demo”,
mà làm **một mini SOC phishing simulation platform**.

Mình sẽ thiết kế lại **structure chi tiết – production mindset – nhưng vẫn làm được một mình**.

---

# 🎯 MỤC TIÊU HỆ THỐNG

Một nền tảng cho phép:

* Tạo và quản lý nhiều phishing campaign
* Quản lý danh sách user mục tiêu
* Gửi email mô phỏng
* Track click (IP + user-agent + timestamp)
* Phân tích campaign-level
* Phân loại isolated vs widespread
* Sinh báo cáo incident
* Hiển thị dashboard

---

# 🏗️ KIẾN TRÚC TỔNG THỂ

```
                ┌────────────────────┐
                │   Admin Dashboard  │
                └──────────┬─────────┘
                           ↓
                ┌────────────────────┐
                │  Campaign Manager  │
                └──────────┬─────────┘
                           ↓
        ┌──────────────────────────────┐
        │  Email Sender + Link Builder │
        └──────────┬───────────────────┘
                   ↓
        ┌──────────────────────────────┐
        │      Tracking Endpoint       │
        └──────────┬───────────────────┘
                   ↓
        ┌──────────────────────────────┐
        │     Database (SQLite)        │
        └──────────┬───────────────────┘
                   ↓
        ┌──────────────────────────────┐
        │ Analytics + Incident Engine  │
        └──────────────────────────────┘
```

---

# 📁 PROJECT STRUCTURE (CHI TIẾT – CHUẨN TOOL)

```
phishing_simulator/
│
├── app.py                     # Entry point (Flask app)
├── config.py                  # Config (DB path, SMTP, app settings)
├── requirements.txt
│
├── database/
│   ├── db.py                  # DB connection & init
│   ├── models.py              # Table schemas
│
├── modules/
│   ├── campaign/
│   │   ├── manager.py         # Create/update campaign
│   │   ├── targets.py         # Add/remove users
│   │
│   ├── email/
│   │   ├── sender.py          # SMTP send logic
│   │   ├── templates.py       # Email template builder
│   │
│   ├── tracking/
│   │   ├── tracker.py         # Click tracking logic
│   │
│   ├── analytics/
│   │   ├── metrics.py         # Click rate, totals
│   │   ├── classification.py  # Isolated vs Widespread logic
│   │   ├── severity.py        # Severity scoring engine
│   │
│   ├── reporting/
│   │   ├── incident_report.py # Auto-generate report
│
├── routes/
│   ├── dashboard_routes.py
│   ├── campaign_routes.py
│   ├── tracking_routes.py
│
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── create_campaign.html
│   ├── campaign_detail.html
│   ├── report_view.html
│
├── static/
│   ├── css/
│   ├── js/
│
├── logs/
│   └── app.log
│
└── data/
    └── phishing.db
```

---

# 🗄️ DATABASE STRUCTURE (SOC-READY)

## 1️⃣ campaigns

| field      | type     | purpose                 |
| ---------- | -------- | ----------------------- |
| id         | INTEGER  | campaign id             |
| name       | TEXT     | campaign name           |
| created_at | DATETIME | timestamp               |
| status     | TEXT     | draft / active / closed |
| severity   | TEXT     | auto-calculated         |

---

## 2️⃣ users

| field      | type    |
| ---------- | ------- |
| id         | INTEGER |
| email      | TEXT    |
| department | TEXT    |

---

## 3️⃣ campaign_targets

| field       | type    |
| ----------- | ------- |
| campaign_id | INTEGER |
| user_id     | INTEGER |

---

## 4️⃣ events

| field       | type                  |
| ----------- | --------------------- |
| id          | INTEGER               |
| campaign_id | INTEGER               |
| user_id     | INTEGER               |
| event_type  | TEXT (sent / clicked) |
| ip          | TEXT                  |
| user_agent  | TEXT                  |
| timestamp   | DATETIME              |

---

## 5️⃣ incident_reports (Optional Advanced)

| field       | type     |
| ----------- | -------- |
| campaign_id | INTEGER  |
| summary     | TEXT     |
| severity    | TEXT     |
| created_at  | DATETIME |

---

# 🪜 DEVELOPMENT PHASES (WEB + SOC HYBRID)

---

# 🔵 PHASE 1 – CORE WEB TOOL (Foundation)

### STEP 1 – Setup Flask + SQLite

* app.py
* db initialization
* test insert campaign

---

### STEP 2 – Campaign Creation UI

Route:

```
/campaign/create
```

Save to DB.

---

### STEP 3 – Add Target Users

* Upload CSV
* Insert into campaign_targets

---

### STEP 4 – Email Sending Engine

* Generate tracking link:

```
/track?cid=1&uid=5
```

* Insert event_type = sent

---

### STEP 5 – Tracking Endpoint

Route:

```
/track
```

When clicked:

* Insert event_type = clicked
* Save IP
* Save user_agent

---

# 🔵 PHASE 2 – SOC Analytics Layer

Đây là phần nâng cấp.

---

## STEP 6 – Metrics Engine

Tính:

* total_targeted
* total_clicked
* click_rate
* unique_clicked_users

---

## STEP 7 – Classification Engine

Logic:

```
if click_rate == 0:
    result = "No Incident"

elif unique_clicked_users == 1:
    result = "Isolated User Error"

else:
    result = "Widespread Awareness Issue"
```

---

## STEP 8 – Severity Engine

Ví dụ:

```
if click_rate > 70%:
    severity = "High"
elif click_rate > 30%:
    severity = "Medium"
else:
    severity = "Low"
```

---

# 🔵 PHASE 3 – Reporting & Dashboard

---

## STEP 9 – Dashboard

Hiển thị:

* Active campaigns
* Click rate %
* Severity badge
* Top risky users

---

## STEP 10 – Auto Incident Report Generator

Sinh report dạng:

```
Campaign Summary
Impact
Severity
Root Cause
Recommendations
```

---

# 🧠 SOC INTELLIGENCE LAYER (ĐIỂM ĂN TIỀN)

Bạn có thể thêm:

* Phân tích theo department
* Phân tích theo user-agent
* Phát hiện repeated clickers
* Campaign comparison

---

# 🎓 KHI HOÀN THÀNH TOOL NÀY BẠN SẼ CÓ:

✔ Full-stack mini security platform
✔ Database design
✔ Web backend
✔ Analytics logic
✔ Incident classification
✔ Reporting automation
✔ SOC workflow simulation

---

# 📌 QUAN TRỌNG

Bạn không nên code tất cả cùng lúc.

Trình tự đúng:

1. DB
2. Campaign creation
3. Tracking
4. Analytics
5. Reporting
6. UI polish

---

# 🚀 BƯỚC TIẾP THEO

Giờ bạn đang ở ngã rẽ quan trọng.

Bạn muốn mình:

1️⃣ Thiết kế chi tiết PHASE 1 (tuần 1 làm gì từng ngày)
2️⃣ Vẽ luồng dữ liệu cụ thể từ click → analytics
3️⃣ Thiết kế logic SOC analytics sâu hơn (Tier 2 mindset)

Chọn 1 hướng, mình đi cực chi tiết cho bạn.
