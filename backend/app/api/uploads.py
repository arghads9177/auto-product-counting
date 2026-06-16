"""File upload endpoints — registers an .mp4 as a camera source."""
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.config import settings
from app.core.worker_manager import worker_manager

router = APIRouter(prefix="/api", tags=["uploads"])

_ALLOWED_SUFFIXES = {".mp4", ".avi", ".mov", ".mkv"}


@router.post("/uploads")
async def upload_video(file: UploadFile = File(...)) -> dict:
    """Upload a video file and register it as a camera source.

    Returns a *camera_id* that can be passed to ``POST /api/cameras/{id}/start``.
    """
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: {sorted(_ALLOWED_SUFFIXES)}",
        )

    uploads_dir = Path(settings.UPLOADS_DIR)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    source_id = uuid.uuid4().hex[:8]
    dest = uploads_dir / f"{source_id}{suffix}"
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    camera_id = f"UP_{source_id.upper()}"
    name = Path(file.filename or camera_id).stem
    worker_manager.register_camera(
        camera_id=camera_id,
        name=name,
        source=str(dest.resolve()),
        source_type="file",
    )

    return {
        "camera_id": camera_id,
        "source_id": source_id,
        "filename": file.filename,
        "path": str(dest),
    }
