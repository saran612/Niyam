"""MinIO / S3 Document Storage and Security Service.

Enforces:
- Magic bytes MIME type validation (disallows executables, scripts, html)
- File size caps (default max 10MB)
- Sanitized file paths (prevent path traversal)
- Presigned GET/PUT URLs
"""

import hashlib
import os
import re
import uuid

import boto3
from app.core.config import settings
from botocore.client import Config

ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def detect_mime_from_magic_bytes(content: bytes) -> str | None:
    """Detect file type strictly from file header magic bytes."""
    if content.startswith(b"%PDF-"):
        return "application/pdf"
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    return None


def sanitize_filename(filename: str) -> str:
    """Strip dangerous path traversal characters and symbols."""
    base = os.path.basename(filename)
    clean = re.sub(r"[^a-zA-Z0-9_.-]", "_", base)
    return clean


def upload_document_bytes(
    content: bytes,
    original_filename: str,
    institution_id: int,
) -> tuple[str, str, int, str]:
    """Validates and stores document bytes.

    Returns (s3_key, mime_type, file_size, sha256_hash).
    Raises ValueError on validation failure.
    """
    file_size = len(content)
    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File size {file_size} exceeds maximum limit of {MAX_FILE_SIZE_BYTES} bytes")
    if file_size == 0:
        raise ValueError("Cannot upload empty file")

    detected_mime = detect_mime_from_magic_bytes(content)
    if not detected_mime or detected_mime not in ALLOWED_MIME_TYPES:
        raise ValueError("Disallowed or invalid file type. Only PDF and JPG/PNG are permitted.")

    sha256 = hashlib.sha256(content).hexdigest()
    clean_name = sanitize_filename(original_filename)
    unique_prefix = uuid.uuid4().hex[:12]
    s3_key = f"institutions/{institution_id}/{unique_prefix}_{clean_name}"

    # Try storing to S3 / Mock S3, fallback to local storage dir if offline
    try:
        s3 = get_s3_client()
        # Ensure bucket exists
        try:
            s3.head_bucket(Bucket=settings.S3_BUCKET)
        except Exception:
            s3.create_bucket(Bucket=settings.S3_BUCKET)
        s3.put_object(
            Bucket=settings.S3_BUCKET,
            Key=s3_key,
            Body=content,
            ContentType=detected_mime,
        )
    except Exception:
        # Local storage fallback
        local_path = os.path.join(settings.STORAGE_DIR, s3_key)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(content)

    return s3_key, detected_mime, file_size, sha256


def generate_presigned_download_url(s3_key: str, expires_seconds: int = 3600) -> str:
    """Generate presigned download URL."""
    try:
        s3 = get_s3_client()
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET, "Key": s3_key},
            ExpiresIn=expires_seconds,
        )
        return str(url)
    except Exception:
        # Local mock URL
        return f"/api/documents/download-direct?key={s3_key}"
