"""Annotated MJPEG streaming endpoint."""
import asyncio

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.worker_manager import worker_manager

router = APIRouter(prefix="/stream", tags=["streaming"])

_BOUNDARY = b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
_BOUNDARY_END = b"\r\n"


@router.get("/{camera_id}.mjpeg")
async def get_mjpeg_stream(camera_id: str):
    """Stream annotated MJPEG for a camera (bboxes + track IDs)."""
    fq = worker_manager.get_frame_queue(camera_id)
    if fq is None:
        raise HTTPException(status_code=404, detail=f"Camera '{camera_id}' not found")

    async def generate():
        while True:
            try:
                jpeg: bytes = fq.get_nowait()
            except Exception:
                await asyncio.sleep(0.033)  # ~30 fps poll cadence
                continue
            yield _BOUNDARY + jpeg + _BOUNDARY_END

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
