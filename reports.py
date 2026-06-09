"""Report generation, listing, download, and chatbot routes."""
import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.api.deps import get_current_user
from backend.models.user import User
from backend.models.dataset import Dataset
from backend.models.report import Report
from backend.schemas.report import (
    ReportCreate, ReportOut, ReportListItem, ChatQuery, ChatResponse,
)
from backend.services.report_service import ReportService
from backend.services.llm_service import llm_service
from backend.services.email_service import email_service

router = APIRouter(prefix="/reports", tags=["reports"])


def _generate_async(report_id: int, dataset_id: int, user_email: str):
    """Background task entry point."""
    from backend.core.database import SessionLocal
    db = SessionLocal()
    try:
        report = db.query(Report).get(report_id)
        dataset = db.query(Dataset).get(dataset_id)
        if not report or not dataset:
            return
        ReportService.generate(db, report, dataset)
        if report.status == "completed" and user_email:
            email_service.send(
                to=user_email,
                subject=f"Your report '{report.title}' is ready",
                body_html=f"<p>Your AI-generated report <b>{report.title}</b> is ready. "
                          f"Log in to view it in the dashboard.</p>",
                attachments=[p for p in [report.pdf_path] if p and os.path.exists(p)],
            )
    finally:
        db.close()


@router.post("", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def create_report(
    payload: ReportCreate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    ds = (
        db.query(Dataset)
        .filter(Dataset.id == payload.dataset_id, Dataset.owner_id == current.id)
        .first()
    )
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    report = Report(
        owner_id=current.id,
        dataset_id=ds.id,
        title=payload.title or "Weekly Business Analytics Report",
        status="pending",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    background.add_task(_generate_async, report.id, ds.id, current.email)
    return report


@router.get("", response_model=List[ReportListItem])
def list_reports(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return (
        db.query(Report)
        .filter(Report.owner_id == current.id)
        .order_by(Report.created_at.desc())
        .all()
    )


@router.get("/{report_id}", response_model=ReportOut)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    report = (
        db.query(Report)
        .filter(Report.id == report_id, Report.owner_id == current.id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report


@router.delete("/{report_id}", status_code=204)
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    report = (
        db.query(Report)
        .filter(Report.id == report_id, Report.owner_id == current.id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    for p in (report.html_path, report.pdf_path, report.docx_path):
        try:
            if p and os.path.exists(p):
                os.remove(p)
        except Exception:
            pass
    db.delete(report)
    db.commit()


@router.get("/{report_id}/download/{fmt}")
def download_report(
    report_id: int,
    fmt: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    if fmt not in ("html", "pdf", "docx"):
        raise HTTPException(status_code=400, detail="Format must be html, pdf, or docx.")
    report = (
        db.query(Report)
        .filter(Report.id == report_id, Report.owner_id == current.id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    path = getattr(report, f"{fmt}_path")
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"{fmt.upper()} not available for this report.")
    media_types = {
        "html": "text/html",
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    filename = f"{report.title.replace(' ', '_')}.{fmt}"
    return FileResponse(path, media_type=media_types[fmt], filename=filename)


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatQuery,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """AI chatbot grounded in a specific report's data."""
    context = {}
    if payload.report_id:
        report = (
            db.query(Report)
            .filter(Report.id == payload.report_id, Report.owner_id == current.id)
            .first()
        )
        if not report:
            raise HTTPException(status_code=404, detail="Report not found.")
        context = {
            "title": report.title,
            "summary": report.summary,
            "kpis": report.kpis,
            "insights": report.insights,
            "recommendations": report.recommendations,
        }
    answer = llm_service.answer_question(payload.question, context)
    return ChatResponse(answer=answer)
