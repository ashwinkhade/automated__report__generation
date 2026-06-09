# 📈 Automated Report Generation System

An end-to-end **AI-powered business analytics platform** that ingests CSV/Excel data, runs a full ETL pipeline, computes KPIs, uses an LLM to write executive insights and recommendations, and exports beautiful reports as **PDF / DOCX / HTML** — all served through a real-time React dashboard with multi-user authentication and an AI chatbot.

[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-blue?logo=githubactions)](.github/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11-blue?logo=python)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-18-61dafb?logo=react)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/fastapi-0.111-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-ready-2496ed?logo=docker)](docker-compose.yml)

---

## 📑 Table of Contents
- [Project Description](#-project-description)
- [Features](#-features)
- [Architecture](#-architecture-diagram)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Usage](#-usage)
- [Screenshots](#-screenshots)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Future Enhancements](#-future-enhancements)
- [License](#-license)

---

## 🧠 Project Description

Manual weekly business reporting is repetitive, error-prone, and slow. This project automates the **entire weekly reporting cycle**:

1. **Upload** raw business data (CSV / XLSX).
2. **ETL** — clean, type-cast, impute missing values, dedupe.
3. **Analytics** — total revenue, week-over-week growth, top categories, daily trends.
4. **LLM** — OpenAI + LangChain produce an executive summary, key insights, and actionable recommendations.
5. **Export** — PDF (WeasyPrint), DOCX (python-docx), HTML (Jinja2).
6. **Schedule** — APScheduler re-generates reports every Monday at 06:00 UTC.
7. **Chat** — ask the AI assistant questions grounded in your report's data.

---

## ✨ Features

- 🔐 **JWT Authentication** (multi-user, bcrypt-hashed passwords)
- 📤 **Upload** CSV / XLS / XLSX (up to 50 MB) with automatic schema detection
- 🛠️ **ETL Pipeline** — column normalization, type inference, NA imputation, deduplication
- 📊 **Analytics Engine** — revenue trends, KPIs, top-N categories, customer volume
- 🤖 **LLM-powered narrative** — executive summaries, insights, recommendations (OpenAI + LangChain)
- 📈 **Real-time React dashboard** with Recharts (line / bar / pie / area)
- 📄 **Multi-format export** — PDF, DOCX, HTML
- 🗂️ **Report history** with status tracking (pending → processing → completed)
- 🕒 **Scheduled weekly generation** via APScheduler
- 💬 **AI chatbot** for ad-hoc questions about a report's data
- ✉️ **Email delivery** of completed reports (SMTP, optional)
- ☁️ **AWS-ready** — S3 storage, Lambda handler, ECS/EC2 deployment guides
- 🐳 **Docker Compose** — one command to launch everything
- ✅ **CI/CD** — GitHub Actions runs tests + builds Docker images

---

## 🏛 Architecture Diagram

```
┌──────────────┐     HTTPS      ┌──────────────────────────────────────┐
│   Browser    │ ─────────────▶ │ React + Tailwind + Recharts (Vite)   │
└──────────────┘                └────────────────┬─────────────────────┘
                                                 │ REST /api/v1
                                                 ▼
                              ┌──────────────────────────────────┐
                              │         FastAPI Backend          │
                              │  Auth ─ Datasets ─ Reports ─ Chat│
                              │                                  │
                              │  ETL → Analytics → LLM → Export  │
                              │              ▲                   │
                              │              │ APScheduler (cron)│
                              └────┬──────────┬─────────┬────────┘
                                   │          │         │
                          ┌────────▼──┐  ┌────▼────┐  ┌─▼────────┐
                          │PostgreSQL │  │ OpenAI  │  │  AWS S3  │
                          └───────────┘  └─────────┘  └──────────┘
```

Full diagram: [`docs/architecture.md`](docs/architecture.md)

---

## 🧰 Tech Stack

| Layer | Tools |
|-------|-------|
| **Frontend** | React 18, Vite, Tailwind CSS, Recharts, Axios, React Router, React Hot Toast |
| **Backend** | Python 3.11, FastAPI, Pydantic, SQLAlchemy, APScheduler |
| **AI / LLM** | OpenAI (gpt-4o-mini default), LangChain |
| **Data** | Pandas, NumPy, openpyxl |
| **Database** | PostgreSQL 16 (SQLite for dev/tests) |
| **Export** | Jinja2 (HTML), WeasyPrint (PDF), python-docx (DOCX) |
| **Auth** | OAuth2 password flow, JWT (python-jose), bcrypt (passlib) |
| **Cloud** | AWS S3, AWS Lambda (Mangum), AWS EC2 / ECS |
| **DevOps** | Docker, Docker Compose, GitHub Actions, Nginx |

---

## ⚙️ Installation

### Quickstart (Docker — recommended)

```bash
git clone https://github.com/<your-org>/automated-report-generation.git
cd automated-report-generation
cp .env.example .env       # edit and add OPENAI_API_KEY
docker compose up --build
```

- 🖥 Frontend: http://localhost
- 📚 API docs (Swagger): http://localhost:8000/docs

### Local dev (no Docker)

See [`docs/installation.md`](docs/installation.md) for Python + Node.js setup.

---

## 🚀 Usage

1. **Register** an account at `/register`.
2. Go to **Datasets** → **+ Upload File** and upload `data/sample_data.csv` (included).
3. Click **Generate** to start an AI report.
4. Open the report — view the **Executive Summary**, **KPI cards**, **interactive charts**, **insights**, and **recommendations**.
5. Use the **AI chatbot** at the bottom of the report to ask questions like:
   > _"Which region drove the most growth this week?"_
6. Download as **PDF / DOCX / HTML** via the buttons in the header.

### Generate fresh sample data
```bash
python scripts/generate_sample_data.py
```

---

## 🖼 Screenshots

The dashboard, datasets table, and AI report view are rendered with Tailwind + Recharts. Capture your own with Playwright (`docs/screenshots.md`) — or browse the prebuilt mockups in [`docs/img/`](docs/img/).

```
┌──────────────────────────────────────────────────────────┐
│ 📈 ReportGen AI       Dashboard                          │
│                                                          │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│   │Datasets │ │Reports  │ │Done     │ │Pending  │        │
│   │   3     │ │   8     │ │   7     │ │   1     │        │
│   └─────────┘ └─────────┘ └─────────┘ └─────────┘        │
│                                                          │
│   📈 Revenue Trend          📊 Top Products              │
│   [line chart]              [bar chart]                  │
└──────────────────────────────────────────────────────────┘
```

---

## 📚 API Documentation

Interactive docs are auto-generated at `/docs` (Swagger) and `/redoc`.
A reference cheatsheet lives in [`docs/api.md`](docs/api.md).

---

## 📁 Project Structure

```
automated-report-generation/
├── frontend/                  # React + Vite + Tailwind
│   ├── src/
│   │   ├── components/        # Layout, KpiCard, ChartRenderer, Chatbot
│   │   ├── pages/             # Login, Register, Dashboard, Datasets, Reports
│   │   ├── context/           # AuthContext
│   │   └── services/api.js
│   └── package.json
├── backend/                   # FastAPI
│   ├── api/                   # routes/ + deps
│   ├── services/              # ETL, Analytics, LLM, Export, Storage, Email, Scheduler
│   ├── models/                # SQLAlchemy models
│   ├── schemas/               # Pydantic schemas
│   ├── core/                  # config, database, security
│   ├── utils/                 # logger, lambda_handler
│   └── requirements.txt
├── data/sample_data.csv       # 1500-row e-commerce demo dataset
├── reports/                   # generated PDF / DOCX / HTML
├── docs/                      # architecture, API, AWS, schema, project report
├── docker/                    # Dockerfiles + nginx.conf
├── tests/backend/             # pytest
├── scripts/generate_sample_data.py
├── .github/workflows/ci.yml
├── docker-compose.yml
├── .env.example
├── LICENSE
└── README.md
```

---

## 🔭 Future Enhancements

- 🔍 Anomaly detection (Prophet / z-score) baked into analytics.
- 🔄 Streaming chatbot responses (Server-Sent Events).
- 👥 Role-based access (admin / analyst / viewer).
- 🌐 SSO (Google / Okta / Azure AD).
- 💬 Slack / Microsoft Teams report delivery.
- 📦 Per-dataset custom prompts & report templates.
- 📱 Mobile-first PWA.

---

## 📜 License

[MIT](LICENSE) © 2025 Automated Report Generation System Contributors
