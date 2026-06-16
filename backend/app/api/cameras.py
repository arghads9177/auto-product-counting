"""Camera management endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.worker_manager import worker_manager

router = APIRouter(prefix="/api/cameras", tags=["cameras"])


class AddCameraRequest(BaseModel):
    camera_id: str
    name: str
    rtsp_url: str


class UpdateConfigRequest(BaseModel):
    zones: dict = {}
    lines: dict = {}
    direction_map: dict = {}
    thresholds: dict = {}


@router.get("")
async def list_cameras() -> dict:
    """List all registered cameras with live status."""
    return {"cameras": worker_manager.list_cameras()}


@router.post("")
async def add_camera(body: AddCameraRequest) -> dict:
    """Register an RTSP camera (admin only)."""
    if worker_manager.get_camera(body.camera_id):
        raise HTTPException(status_code=409, detail=f"Camera '{body.camera_id}' already exists")
    meta = worker_manager.register_camera(
        camera_id=body.camera_id,
        name=body.name,
        source=body.rtsp_url,
        source_type="rtsp",
    )
    return meta


@router.get("/{camera_id}/config")
async def get_camera_config(camera_id: str) -> dict:
    """Get camera zone/line/threshold configuration."""
    if not worker_manager.get_camera(camera_id):
        raise HTTPException(status_code=404, detail=f"Camera '{camera_id}' not found")
    # Phase 5 will return real config from MongoDB; stub for now.
    return {"camera_id": camera_id, "zones": {}, "lines": {}, "thresholds": {}}


@router.put("/{camera_id}/config")
async def update_camera_config(camera_id: str, config: UpdateConfigRequest) -> dict:
    """Update camera zone/line/threshold configuration."""
    if not worker_manager.get_camera(camera_id):
        raise HTTPException(status_code=404, detail=f"Camera '{camera_id}' not found")
    # Phase 5 will persist this to MongoDB.
    return {"updated": True, "camera_id": camera_id}


@router.post("/{camera_id}/start")
async def start_camera_worker(camera_id: str) -> dict:
    """Start the frame-ingestion worker for a camera."""
    ok, message = worker_manager.start(camera_id)
    if not ok:
        raise HTTPException(status_code=400, detail=message)
    return {"status": "started", "camera_id": camera_id}


@router.post("/{camera_id}/stop")
async def stop_camera_worker(camera_id: str) -> dict:
    """Stop the worker for a camera."""
    ok, message = worker_manager.stop(camera_id)
    if not ok:
        raise HTTPException(status_code=400, detail=message)
    return {"status": "stopped", "camera_id": camera_id}
