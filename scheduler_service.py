"""
Scheduler Service.

Uses APScheduler to run weekly report generation for every user that has at
least one dataset uploaded. The scheduler starts when the FastAPI app starts.
"""
from __future__ import annotations
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from backend.core.database import SessionLocal
from backend.models.user import User
from backend.models.dataset import Dataset
from backend.models.report import Report
from .report_service import ReportService

logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


def _generate_weekly_reports():
    db: Session = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active.is_(True)).all()
        for user in users:
            dataset = (
                db.query(Dataset)
                .filter(Dataset.owner_id == user.id)
                .order_by(Dataset.created_at.desc())
                .first()
            )
            if not dataset:
                continue
            report = Report(
                owner_id=user.id,
                dataset_id=dataset.id,
                title="Scheduled Weekly Report",
                status="pending",
            )
            db.add(report)
            db.commit()
            db.refresh(report)
            ReportService.generate(db, report, dataset)
            logger.info("Generated scheduled report %s for user %s", report.id, user.id)
    finally:
        db.close()


def start_scheduler():
    """Idempotent scheduler startup."""
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler(timezone="UTC")
    # Every Monday at 06:00 UTC
    _scheduler.add_job(
        _generate_weekly_reports,
        CronTrigger(day_of_week="mon", hour=6, minute=0),
        id="weekly_reports",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduler started.")


def shutdown_scheduler():
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
