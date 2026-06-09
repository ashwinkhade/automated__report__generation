"""Report database model — represents a generated analytics report."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.core.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    title = Column(String(255), nullable=False)
    status = Column(String(20), default="pending")  # pending | processing | completed | failed
    summary = Column(Text)
    insights = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    kpis = Column(JSON, default=dict)
    charts = Column(JSON, default=list)      # list of {title, type, data}
    raw_analytics = Column(JSON, default=dict)
    html_path = Column(String(500))
    pdf_path = Column(String(500))
    docx_path = Column(String(500))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    owner = relationship("User", back_populates="reports")
    dataset = relationship("Dataset", back_populates="reports")
