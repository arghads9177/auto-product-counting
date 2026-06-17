"""System/AI logs and activity event timeline endpoints."""
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(prefix="/api", tags=["logs"])


@router.get("/logs")
async def get_logs(
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = None,
    severity: Optional[str] = None,
    camera_id: Optional[str] = None,
):
    """Get system and AI logs with filtering."""
    from app.db.mongo import mongo_connection
    db = mongo_connection.db
    if db is None:
        return {"logs": []}

    query = {}
    if category:
        query["category"] = category.upper()
    if severity:
        query["severity"] = severity.upper()
    if camera_id:
        query["camera_id"] = camera_id

    cursor = (
        db["system_logs"]
        .find(query, {"_id": 0})
        .sort("timestamp", -1)
        .limit(limit)
    )
    rows = await cursor.to_list(length=limit)
    return {"logs": rows}


@router.get("/events/timeline")
async def get_event_timeline(
    limit: int = Query(50, ge=1, le=500),
    camera_id: Optional[str] = None,
    session_id: Optional[str] = None,
):
    """Live event feed — activity events (session start/end, FSM transitions)."""
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
        db["activity_events"]
        .find(query, {"_id": 0})
        .sort("timestamp", -1)
        .limit(limit)
    )
    events = await cursor.to_list(length=limit)
    return {"events": events}
