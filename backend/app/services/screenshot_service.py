"""
Screenshot upload and file management service.
Handles validation, saving, and cleanup of uploaded screenshot files.
"""

import os
import uuid
import aiofiles
from pathlib import Path
from typing import Optional
from fastapi import UploadFile

from app.config import settings
from app.utils.validators import validate_image_content_type, validate_image_extension, sanitize_filename


UPLOAD_DIR = Path("uploads")


async def ensure_upload_dir() -> Path:
    """Ensure the upload directory exists."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR


async def validate_screenshot(file: UploadFile) -> tuple[bool, str]:
    """
    Validate a single uploaded screenshot.
    Returns (is_valid, error_message).
    """
    if not file.filename:
        return False, "File has no filename."

    # Check extension
    if not validate_image_extension(file.filename):
        return False, f"Unsupported image format: {file.filename}. Allowed: PNG, JPG, JPEG, WEBP."

    # Check content type
    if file.content_type and not validate_image_content_type(file.content_type):
        return False, f"Unsupported content type: {file.content_type}."

    # Check file size (read first chunk to estimate)
    content = await file.read()
    await file.seek(0)  # Reset for later use

    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        return False, f"File {file.filename} exceeds maximum size of {settings.MAX_FILE_SIZE_MB}MB."

    if len(content) == 0:
        return False, f"File {file.filename} is empty."

    return True, ""


async def validate_screenshots(files: list[UploadFile]) -> tuple[bool, str]:
    """
    Validate a batch of uploaded screenshots.
    Returns (is_valid, error_message).
    """
    if len(files) < settings.MIN_SCREENSHOTS:
        return False, f"At least {settings.MIN_SCREENSHOTS} screenshots are required for cross-page consistency analysis."

    if len(files) > settings.MAX_SCREENSHOTS:
        return False, f"Maximum {settings.MAX_SCREENSHOTS} screenshots allowed."

    for file in files:
        is_valid, error = await validate_screenshot(file)
        if not is_valid:
            return False, error

    return True, ""


async def save_screenshots(
    files: list[UploadFile],
    analysis_id: str,
) -> list[dict[str, str]]:
    """
    Save uploaded screenshots to disk.
    Returns list of {filename, filepath, original_name} dicts.
    """
    upload_dir = await ensure_upload_dir()
    analysis_dir = upload_dir / analysis_id
    analysis_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []

    for file in files:
        original_name = file.filename or "unknown.png"
        safe_name = sanitize_filename(original_name)
        unique_name = f"{uuid.uuid4().hex[:8]}_{safe_name}"
        filepath = analysis_dir / unique_name

        content = await file.read()
        async with aiofiles.open(filepath, "wb") as f:
            await f.write(content)

        saved_files.append({
            "filename": unique_name,
            "filepath": str(filepath),
            "original_name": original_name,
            "page_name": Path(original_name).stem,  # Use filename without extension as page name
        })

    return saved_files


async def cleanup_screenshots(analysis_id: str) -> None:
    """Remove uploaded screenshots for an analysis."""
    analysis_dir = UPLOAD_DIR / analysis_id
    if analysis_dir.exists():
        import shutil
        shutil.rmtree(analysis_dir, ignore_errors=True)


def get_page_name_from_filename(filename: str) -> str:
    """Extract a human-readable page name from a filename."""
    stem = Path(filename).stem
    # Remove common prefixes/suffixes
    stem = stem.replace("screenshot_", "").replace("_screenshot", "")
    stem = stem.replace("-", " ").replace("_", " ")
    return stem.strip().title() or "Unknown Page"
