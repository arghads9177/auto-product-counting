"""Count metrics endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["counts"])


@router.get("/counts/summary")
async def get_counts_summary():
    """Get summary count tiles."""
    return {
        "today_total": 0,
        "active_sessions": 0,
        "online_cameras": 0,
        "loading_count": 0,
        "unloading_count": 0,
    }
