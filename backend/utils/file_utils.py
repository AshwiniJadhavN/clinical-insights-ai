"""
File validation and path-handling utilities.
Called by DocumentService before any bytes are written to disk.
"""

import re
import uuid
from pathlib import Path

from backend.config import Settings


def validate_upload(filename: str, size_bytes: int, settings: Settings) -> None:
    suffix = Path(filename).suffix.lower()
    if suffix not in settings.allowed_extensions:
        allowed = ", ".join(settings.allowed_extensions)
        raise ValueError(f"File type '{suffix}' is not allowed. Accepted types: {allowed}")
    if size_bytes == 0:
        raise ValueError("Uploaded file appears to be empty.")
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if size_bytes > max_bytes:
        mb = size_bytes / (1024 * 1024)
        raise ValueError(
            f"File is too large ({mb:.1f} MB). Maximum allowed size is {settings.max_file_size_mb} MB."
        )


def sanitize_filename(original: str) -> str:
    name = Path(original).name
    name = re.sub(r"[^\w\-.]", "_", name)
    return name if name else "document"


def make_upload_path(original_filename: str, upload_dir: str) -> tuple[str, Path]:
    doc_id = str(uuid.uuid4())
    suffix = Path(original_filename).suffix.lower()
    disk_name = f"{doc_id}{suffix}"
    return doc_id, Path(upload_dir) / disk_name


def ensure_directory(path: str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
