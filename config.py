"""
Application configuration management.
Loads environment variables and provides typed settings for the entire app.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Automated Report Generation System"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = "change-this-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/reportgen"

    # OpenAI / LLM
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.3

    # AWS
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET: Optional[str] = None

    # Email (SMTP)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@reportgen.local"

    # Storage
    UPLOAD_DIR: str = "./data/uploads"
    REPORT_DIR: str = "./reports"
    MAX_UPLOAD_SIZE_MB: int = 50

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Redis (for Celery / caching)
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
