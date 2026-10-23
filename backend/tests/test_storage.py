"""Tests for Storage service (magic bytes, size limits, file sanitization)."""

import pytest
from app.services.storage import (
    MAX_FILE_SIZE_BYTES,
    detect_mime_from_magic_bytes,
    generate_presigned_download_url,
    sanitize_filename,
    upload_document_bytes,
)


def test_magic_byte_detection():
    pdf_bytes = b"%PDF-1.5 test document"
    jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00"
    exe_bytes = b"MZ\x90\x00\x03\x00\x00\x00"

    assert detect_mime_from_magic_bytes(pdf_bytes) == "application/pdf"
    assert detect_mime_from_magic_bytes(jpeg_bytes) == "image/jpeg"
    assert detect_mime_from_magic_bytes(png_bytes) == "image/png"
    assert detect_mime_from_magic_bytes(exe_bytes) is None


def test_sanitize_filename():
    assert sanitize_filename("../../../etc/passwd") == "passwd"
    assert sanitize_filename("my report (1).pdf") == "my_report__1_.pdf"


def test_upload_validations():
    # Disallowed MIME
    with pytest.raises(ValueError) as exc:
        upload_document_bytes(b"bad content", "evil.sh", institution_id=1)
    assert "Disallowed or invalid file type" in str(exc.value)

    # Empty file
    with pytest.raises(ValueError) as exc:
        upload_document_bytes(b"", "empty.pdf", institution_id=1)
    assert "empty file" in str(exc.value)

    # Size cap
    oversized = b"%PDF-" + b"0" * (MAX_FILE_SIZE_BYTES + 10)
    with pytest.raises(ValueError) as exc:
        upload_document_bytes(oversized, "big.pdf", institution_id=1)
    assert "exceeds maximum limit" in str(exc.value)

    # Valid upload (saves to fallback or S3)
    valid_pdf = b"%PDF-1.4 sample content"
    key, mime, size, sha = upload_document_bytes(valid_pdf, "sample.pdf", institution_id=1)
    assert "institutions/1/" in key
    assert mime == "application/pdf"
    assert size == len(valid_pdf)
    assert len(sha) == 64

    # Presigned URL generation
    url = generate_presigned_download_url(key)
    assert len(url) > 0
