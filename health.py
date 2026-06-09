"""Health check route."""
from fastapi import APIRouter
from backend.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
        "llm_enabled": bool(settings.OPENAI_API_KEY),
        "s3_enabled": bool(settings.AWS_S3_BUCKET),
    }
