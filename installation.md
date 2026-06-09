# Installation Guide

There are two supported paths: **Docker** (recommended) and **local dev**.

## Prerequisites
- Docker 24+ and Docker Compose v2, **or**
- Python 3.11+ and Node.js 20+
- PostgreSQL 15+ (only for local dev without Docker)

---

## 🐳 Docker (one-command setup)

```bash
git clone https://github.com/<your-org>/automated-report-generation.git
cd automated-report-generation
cp .env.example .env       # then edit and put your OPENAI_API_KEY etc.
docker compose up --build
```

Open:
- Frontend: http://localhost
- Backend Swagger: http://localhost:8000/docs

Stop & wipe DB:
```bash
docker compose down -v
```

---

## 🛠️ Local Development

### 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Start a Postgres locally (or use Docker just for the DB):
# docker run --name pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:16

cp ../.env.example ../.env  # edit
export $(grep -v '^#' ../.env | xargs)   # bash; on Windows use PowerShell

uvicorn backend.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

The Vite dev server proxies `/api/*` to `http://localhost:8000`.

### 3. Generate sample data (optional)

```bash
python scripts/generate_sample_data.py
# upload data/sample_data.csv via the UI
```

### 4. Run tests

```bash
pytest tests/backend -v
```
