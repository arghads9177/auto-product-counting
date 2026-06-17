"""Count metrics endpoints."""
from fastapi import APIRouter

from app.core.worker_manager import worker_manager

router = APIRouter(prefix="/api", tags=["counts"])


@router.get("/counts/summary")
async def get_counts_summary():
    """Live plant-level count summary from all running camera workers."""
    return worker_manager.get_summary()
