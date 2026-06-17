"""Session monitoring endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.core.worker_manager import worker_manager

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("")
async def get_sessions(
    status: Optional[str] = None,
    camera_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
):
    """Get active or historical sessions."""
    from app.main import session_service
    if session_service is not None:
        rows = await session_service.list_sessions(
            status=status, camera_id=camera_id, limit=limit,
        )
        return {"sessions": rows}

    sessions = worker_manager.get_active_sessions()
    if status and status.upper() != "ACTIVE":
        sessions = []
    if camera_id:
        sessions = [s for s in sessions if s.get("camera_id") == camera_id]
    return {"sessions": sessions}


@router.get("/{session_id}")
async def get_session_details(session_id: str):
    """Get detailed information for a session including count events."""
    from app.main import session_service
    from app.db.mongo import mongo_connection

    if session_service is not None:
        doc = await session_service.get_session(session_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="Session not found")

        db = mongo_connection.db
        count_events = []
        activity_events = []
        if db is not None:
            cursor = (
                db["count_events"]
                .find({"session_id": session_id}, {"_id": 0})
                .sort("timestamp", 1)
            )
            count_events = await cursor.to_list(length=5000)

            cursor = (
                db["activity_events"]
                .find({"session_id": session_id}, {"_id": 0})
                .sort("timestamp", 1)
            )
            activity_events = await cursor.to_list(length=500)

        doc["count_events"] = count_events
        doc["activity_events"] = activity_events
        return doc

    return {"session_id": session_id, "events": []}
