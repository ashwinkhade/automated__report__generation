# Project Report — Automated Report Generation System

## 1. Problem Statement
Analytics and BI teams spend significant time each week pulling data, building
dashboards, and writing executive summaries by hand. We automate this end-to-end:
**ingest → ETL → analytics → narrative → multi-format export**, with an AI
assistant grounded in the data.

## 2. Objectives
1. Accept arbitrary tabular business data (CSV / Excel).
2. Run a robust ETL pipeline that survives messy, real-world data.
3. Produce KPIs and chart-ready aggregates without hand-written SQL.
4. Use an LLM to write a 4-6 sentence executive summary, insights, and recommendations.
5. Export to PDF, DOCX, and HTML.
6. Provide a multi-user web app with secure auth, history, and an AI chatbot.

## 3. Methodology
- **Backend** — FastAPI with a service-oriented design. Pure-Python ETL using pandas.
- **LLM Layer** — OpenAI Chat Completions (JSON-mode) with prompt scaffolding. The
  prompt is grounded in the analytics dict so the model cannot invent numbers.
- **Frontend** — React (Vite) + Tailwind + Recharts. JWT auth via `localStorage`.
- **Storage** — PostgreSQL primary store; optional S3 for files; SMTP for emails.
- **Scheduling** — APScheduler in-process; cron-style for weekly batch reports.

## 4. Key Features
- ETL: column normalization, type inference, median/mode imputation, deduplication.
- Analytics: total revenue, WoW growth, top categories, daily trend, summary stats.
- LLM narrative + chatbot: degraded-mode fallback when no API key is set.
- Export: HTML (Jinja2), PDF (WeasyPrint), DOCX (python-docx).
- Auth: bcrypt + JWT, multi-tenant by `owner_id`.
- Real-time UI: report detail page polls every 3s while generating.

## 5. Testing
- pytest unit tests for ETL, analytics, and auth (`tests/backend/`).
- CI runs tests + frontend build on every push (`.github/workflows/ci.yml`).

## 6. Deployment Options
- **Local**: `docker compose up` — full stack in 3 minutes.
- **AWS EC2**: single VM with the same compose file.
- **AWS ECS Fargate + RDS + S3**: production-grade.
- **AWS Lambda + API Gateway**: serverless via Mangum.

## 7. Future Enhancements
- Streaming responses from the chatbot.
- Anomaly detection (z-score / Prophet) baked into analytics.
- Per-dataset custom prompts in the UI.
- SSO (Google / Okta) and role-based dashboards.
- Slack / Teams report delivery in addition to email.

## 8. Conclusion
The system delivers an end-to-end automated pipeline that any analyst can drive
through the browser. With ~3 minutes of setup, a team can replace manual weekly
reporting with AI-generated, multi-format, multi-user analytics reports.
