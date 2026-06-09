"""
FastAPI application entry point.

Wires routes, CORS, startup/shutdown hooks (DB init, scheduler).
Run locally:
    uvicorn backend.main:app --reload --port 8000
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from backend.core.config import settings
from backend.core.database import init_db
from backend.api.routes import auth, datasets, reports, health
from backend.services.scheduler_service import start_scheduler, shutdown_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.REPORT_DIR, exist_ok=True)
    try:
        start_scheduler()
    except Exception as e:
        logging.warning("Scheduler failed to start: %s", e)
    yield
    shutdown_scheduler()


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered automated report generation with ETL, analytics, and LLM insights.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health.router, prefix=settings.API_V1_PREFIX)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(datasets.router, prefix=settings.API_V1_PREFIX)
app.include_router(reports.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
    }
