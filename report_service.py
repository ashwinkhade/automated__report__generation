"""
Report Service.

Orchestrates the full pipeline:
ETL → Analytics → LLM narrative → Export (HTML / PDF / DOCX) → persist to DB.
"""
from __future__ import annotations
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.models.report import Report
from backend.models.dataset import Dataset
from .etl_service import ETLService
from .analytics_service import AnalyticsService
from .llm_service import llm_service
from .export_service import ExportService

logger = logging.getLogger(__name__)


class ReportService:
    """High-level orchestration for report generation."""

    @classmethod
    def generate(cls, db: Session, report: Report, dataset: Dataset) -> Report:
        """Run pipeline end-to-end and update the Report row in place."""
        report.status = "processing"
        db.commit()

        try:
            # 1. ETL
            df, etl_meta = ETLService.run_pipeline(dataset.file_path)

            # 2. Analytics
            analytics = AnalyticsService.analyze(df, etl_meta["column_types"])

            # 3. LLM narrative
            narrative = llm_service.generate_report_narrative(analytics)

            # 4. Export
            os.makedirs(settings.REPORT_DIR, exist_ok=True)
            base = f"report_{report.id}_{int(datetime.now().timestamp())}"
            html_path = os.path.join(settings.REPORT_DIR, f"{base}.html")
            pdf_path = os.path.join(settings.REPORT_DIR, f"{base}.pdf")
            docx_path = os.path.join(settings.REPORT_DIR, f"{base}.docx")

            exporter = ExportService()
            exporter.to_html(html_path, report.title, narrative, analytics)
            try:
                exporter.to_pdf(pdf_path, report.title, narrative, analytics)
            except Exception as e:
                logger.warning("PDF export failed: %s", e)
                pdf_path = None
            try:
                exporter.to_docx(docx_path, report.title, narrative, analytics)
            except Exception as e:
                logger.warning("DOCX export failed: %s", e)
                docx_path = None

            # 5. Persist
            report.summary = narrative["summary"]
            report.insights = narrative["insights"]
            report.recommendations = narrative["recommendations"]
            report.kpis = analytics["kpis"]
            report.charts = analytics["charts"]
            report.raw_analytics = {
                "summary_stats": analytics.get("summary_stats", {}),
                "meta": analytics.get("meta", {}),
                "etl_meta": {
                    "original_rows": etl_meta["original_rows"],
                    "cleaned_rows": etl_meta["cleaned_rows"],
                    "duplicates_removed": etl_meta["duplicates_removed"],
                },
            }
            report.html_path = html_path
            report.pdf_path = pdf_path
            report.docx_path = docx_path
            report.status = "completed"
            report.completed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(report)
            return report

        except Exception as e:
            logger.exception("Report generation failed")
            report.status = "failed"
            report.error_message = str(e)[:1000]
            db.commit()
            db.refresh(report)
            return report
