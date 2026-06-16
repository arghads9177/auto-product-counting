"""Session monitoring endpoints."""
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("")
async def get_sessions(status: Optional[str] = None, camera_id: Optional[str] = None):
    """Get active or historical sessions."""
    return {"sessions": []}


@router.get("/{session_id}")
async def get_session_details(session_id: str):
    """Get detailed information for a session."""
    return {"session_id": session_id, "events": []}
