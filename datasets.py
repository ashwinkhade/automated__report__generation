"""Dataset upload + listing routes."""
import os
import uuid
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from backend.core.config import settings
from backend.core.database import get_db
from backend.api.deps import get_current_user
from backend.models.user import User
from backend.models.dataset import Dataset
from backend.schemas.dataset import DatasetOut, DatasetPreview
from backend.services.etl_service import ETLService
from backend.services.storage_service import storage_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/datasets", tags=["datasets"])

ALLOWED_EXT = {".csv", ".xls", ".xlsx"}


@router.post("/upload", response_model=DatasetOut, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail=f"Unsupported file type {ext}. Allowed: {ALLOWED_EXT}")

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large.")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(settings.UPLOAD_DIR, safe_name)
    with open(dest, "wb") as f:
        f.write(content)

    # Quickly read the dataset to extract metadata
    try:
        df, meta = ETLService.run_pipeline(dest)
    except Exception as e:
        logger.exception("Upload parse failed: %s", e)
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")

    s3_key = None
    if storage_service.s3_enabled:
        s3_key = f"datasets/{current.id}/{safe_name}"
        storage_service.upload_to_s3(dest, s3_key)

    ds = Dataset(
        owner_id=current.id,
        name=file.filename or safe_name,
        file_path=dest,
        s3_key=s3_key,
        file_type=ext.lstrip("."),
        size_bytes=len(content),
        row_count=int(len(df)),
        column_count=int(df.shape[1]),
        columns_meta=meta["columns_meta"],
    )
    db.add(ds)
    db.commit()
    db.refresh(ds)
    return ds


@router.get("", response_model=List[DatasetOut])
def list_datasets(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return (
        db.query(Dataset)
        .filter(Dataset.owner_id == current.id)
        .order_by(Dataset.created_at.desc())
        .all()
    )


@router.get("/{dataset_id}/preview", response_model=DatasetPreview)
def preview_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    ds = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id, Dataset.owner_id == current.id)
        .first()
    )
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    df = ETLService.load_file(ds.file_path)
    df = ETLService.clean_column_names(df)
    head = df.head(20)
    return DatasetPreview(
        columns=list(head.columns),
        rows=head.astype(object).where(head.notna(), None).values.tolist(),
        total_rows=int(len(df)),
    )


@router.delete("/{dataset_id}", status_code=204)
def delete_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    ds = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id, Dataset.owner_id == current.id)
        .first()
    )
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    try:
        if ds.file_path and os.path.exists(ds.file_path):
            os.remove(ds.file_path)
    except Exception:
        pass
    db.delete(ds)
    db.commit()
