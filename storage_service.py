"""
Storage Service.

Local filesystem storage with optional AWS S3 mirroring.
If AWS credentials and bucket are configured, files are also uploaded to S3
so they're accessible from a Lambda / EC2 deployment.
"""
from __future__ import annotations
import os
import logging
from typing import Optional
from backend.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Local + S3 storage abstraction."""

    def __init__(self):
        self.s3_enabled = bool(
            settings.AWS_ACCESS_KEY_ID
            and settings.AWS_SECRET_ACCESS_KEY
            and settings.AWS_S3_BUCKET
        )
        self._s3 = None
        if self.s3_enabled:
            try:
                import boto3
                self._s3 = boto3.client(
                    "s3",
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION,
                )
            except Exception as e:
                logger.warning("Failed to initialize S3 client: %s", e)
                self.s3_enabled = False

    def save_local(self, content: bytes, dest_path: str) -> str:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(content)
        return dest_path

    def upload_to_s3(self, local_path: str, key: str) -> Optional[str]:
        if not self.s3_enabled or not self._s3:
            return None
        try:
            self._s3.upload_file(local_path, settings.AWS_S3_BUCKET, key)
            return f"s3://{settings.AWS_S3_BUCKET}/{key}"
        except Exception as e:
            logger.exception("S3 upload failed: %s", e)
            return None

    def presigned_url(self, key: str, expires: int = 3600) -> Optional[str]:
        if not self.s3_enabled or not self._s3:
            return None
        try:
            return self._s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.AWS_S3_BUCKET, "Key": key},
                ExpiresIn=expires,
            )
        except Exception as e:
            logger.exception("Presigned URL failed: %s", e)
            return None


storage_service = StorageService()
