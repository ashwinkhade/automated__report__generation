"""Dataset database model — represents an uploaded data file."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.core.database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    s3_key = Column(String(500), nullable=True)
    file_type = Column(String(20))  # csv | xlsx
    size_bytes = Column(BigInteger, default=0)
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    columns_meta = Column(JSON, default=list)   # [{name, dtype, null_count}, ...]
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="datasets")
    reports = relationship("Report", back_populates="dataset", cascade="all, delete-orphan")
