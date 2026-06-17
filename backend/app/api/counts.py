"""Count metrics endpoints."""
from fastapi import APIRouter, Query
from typing import Optional

from app.core.worker_manager import worker_manager

router = APIRouter(prefix="/api", tags=["counts"])


@router.get("/counts/summary")
async def get_counts_summary():
    """Live plant-level count summary — in-memory for speed, enriched with active sessions."""
    summary = worker_manager.get_summary()
    summary["active_sessions_detail"] = worker_manager.get_active_sessions()
    return summary


@router.get("/counts/camera/{camera_id}")
async def get_camera_counts(camera_id: str):
    """Per-camera count totals and active session info."""
    counts = worker_manager.get_counts(camera_id)
    session = worker_manager.get_camera_session(camera_id)
    return {
        "camera_id": camera_id,
        "loading": counts["loading"],
        "unloading": counts["unloading"],
        "total": counts["loading"] + counts["unloading"],
        "active_session": session,
    }


@router.get("/counts/events")
async def get_count_events(
    camera_id: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
):
    """Query persisted count events from MongoDB."""
    from app.db.mongo import mongo_connection
    db = mongo_connection.db
    if db is None:
        return {"events": []}

    query = {}
    if camera_id:
        query["camera_id"] = camera_id
    if session_id:
        query["session_id"] = session_id

    cursor = (
        db["count_events"]
        .find(query, {"_id": 0})
        .sort("timestamp", -1)
        .limit(limit)
    )
    events = await cursor.to_list(length=limit)
    return {"events": events}
