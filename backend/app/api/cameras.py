"""Camera management endpoints."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.worker_manager import worker_manager
from app.auth.auth import require_role

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
async def add_camera(
    body: AddCameraRequest,
    _user: dict = Depends(require_role("ADMIN")),
) -> dict:
    """Register an RTSP camera (admin only)."""
    if worker_manager.get_camera(body.camera_id):
        raise HTTPException(status_code=409, detail=f"Camera '{body.camera_id}' already exists")
    meta = worker_manager.register_camera(
        camera_id=body.camera_id,
        name=body.name,
        source=body.rtsp_url,
        source_type="rtsp",
    )
    from app.db.mongo import mongo_connection
    db = mongo_connection.db
    if db is not None:
        try:
            await db["cameras"].update_one(
                {"camera_id": body.camera_id},
                {"$set": {
                    "camera_id": body.camera_id,
                    "name": body.name,
                    "rtsp_url": body.rtsp_url,
                    "status": "OFFLINE",
                    "enabled": True,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }},
                upsert=True,
            )
        except Exception:
            pass
    return meta


@router.get("/{camera_id}/config")
async def get_camera_config(camera_id: str) -> dict:
    """Get camera zone/line/threshold configuration."""
    if not worker_manager.get_camera(camera_id):
        raise HTTPException(status_code=404, detail=f"Camera '{camera_id}' not found")

    from app.db.mongo import mongo_connection
    db = mongo_connection.db
    if db is not None:
        doc = await db["camera_configurations"].find_one(
            {"camera_id": camera_id}, {"_id": 0}
        )
        if doc:
            return doc

    return {
        "camera_id": camera_id,
        "zones": {},
        "lines": {
            "A": [[0.0, 0.35], [1.0, 0.35]],
            "B": [[0.0, 0.65], [1.0, 0.65]],
        },
        "direction_map": {"loading": "A->B", "unloading": "B->A"},
        "thresholds": {
            "activity_start_sec": 10,
            "session_idle_end_sec": 300,
            "min_confidence": 0.4,
        },
    }


@router.put("/{camera_id}/config")
async def update_camera_config(
    camera_id: str,
    config: UpdateConfigRequest,
    _user: dict = Depends(require_role("ADMIN", "SUPERVISOR")),
) -> dict:
    """Update camera zone/line/threshold configuration."""
    if not worker_manager.get_camera(camera_id):
        raise HTTPException(status_code=404, detail=f"Camera '{camera_id}' not found")

    from app.db.mongo import mongo_connection
    db = mongo_connection.db
    if db is not None:
        update_doc = {
            "camera_id": camera_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if config.zones:
            update_doc["zones"] = config.zones
        if config.lines:
            update_doc["lines"] = config.lines
        if config.direction_map:
            update_doc["direction_map"] = config.direction_map
        if config.thresholds:
            update_doc["thresholds"] = config.thresholds

        await db["camera_configurations"].update_one(
            {"camera_id": camera_id},
            {"$set": update_doc, "$inc": {"version": 1}},
            upsert=True,
        )
        return {"updated": True, "camera_id": camera_id}

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
