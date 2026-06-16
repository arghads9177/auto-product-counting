"""Video streaming endpoints."""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/stream", tags=["streaming"])


@router.get("/{camera_id}.mjpeg")
async def get_mjpeg_stream(camera_id: str):
    """Stream annotated MJPEG for a camera."""
    async def generate():
        # Placeholder - will be implemented in phase 2
        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"

    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")
