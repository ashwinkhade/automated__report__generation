# Architecture

## High-level Diagram

```
                    ┌─────────────────────────────────────────────┐
                    │              USER (Browser)                 │
                    └────────────────────┬────────────────────────┘
                                         │ HTTPS
                                         ▼
                    ┌─────────────────────────────────────────────┐
                    │         React + Tailwind + Recharts          │
                    │   • Login / Register / Dashboard             │
                    │   • Upload CSV/XLSX, View Reports            │
                    │   • Interactive charts + AI chatbot          │
                    └────────────────────┬────────────────────────┘
                                         │ REST /api/v1/*
                                         ▼
                    ┌─────────────────────────────────────────────┐
                    │            FastAPI Backend                   │
                    │ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
                    │ │  Auth    │ │ Datasets │ │   Reports    │  │
                    │ │ (JWT)    │ │  Routes  │ │   Routes     │  │
                    │ └──────────┘ └────┬─────┘ └──────┬───────┘  │
                    │                   │              │           │
                    │         ┌─────────▼──────────────▼────────┐  │
                    │         │   Services Layer                 │  │
                    │         │  ETL → Analytics → LLM → Export  │  │
                    │         └─────────┬────────────────────────┘  │
                    │                   │                            │
                    │         ┌─────────▼────────┐                   │
                    │         │ APScheduler      │  (weekly cron)    │
                    │         └──────────────────┘                   │
                    └────────────┬────────────────┬─────────────────┘
                                 │                │
                       ┌─────────▼─────┐   ┌──────▼──────────┐
                       │ PostgreSQL    │   │  OpenAI API     │
                       │ users/data/   │   │  (LangChain)    │
                       │ reports       │   └─────────────────┘
                       └───────────────┘
                                 │
                       ┌─────────▼─────┐
                       │   AWS S3      │   (report files,
                       │               │    dataset backups)
                       └───────────────┘
```

## Request Flow: Generating a Report

1. User uploads `sales.csv` → backend stores file + parses metadata.
2. User clicks **Generate Report** → backend creates a `Report` row with `status=pending` and schedules a background task.
3. Background task pipeline:
   - **ETL** (`etl_service.py`): clean column names → detect types → impute NAs → dedupe.
   - **Analytics** (`analytics_service.py`): compute KPIs, build time-series + category aggregates → chart data.
   - **LLM** (`llm_service.py`): call OpenAI with KPI JSON → get `summary` + `insights` + `recommendations`.
   - **Export** (`export_service.py`): render Jinja2 HTML → WeasyPrint PDF → python-docx DOCX.
   - Update DB row to `status=completed`.
4. Frontend polls `GET /reports/{id}` every 3 s until `status=completed`, then renders charts.
5. User can chat with the report — `POST /reports/chat` re-uses the same LLM with report context.

## Scheduled Weekly Reports

`APScheduler` runs at `Mon 06:00 UTC`. For each active user with ≥1 dataset, it auto-generates a new report and emails it via SMTP (if configured).

## Resilience
- LLM service degrades gracefully — fallback templated narrative if `OPENAI_API_KEY` is missing.
- PDF export falls back to HTML bytes if WeasyPrint dependencies fail.
- Background failures store `error_message` so the UI can surface them.
