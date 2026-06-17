"""Metrics endpoints."""
from fastapi import APIRouter, Query

from app.core.worker_manager import worker_manager

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/camera/{camera_id}")
async def get_camera_metrics(camera_id: str):
    """Get per-camera metrics."""
    from app.main import metrics_service
    if metrics_service is not None:
        return await metrics_service.get_camera_metrics(camera_id)
    counts = worker_manager.get_counts(camera_id)
    return {
        "camera_id": camera_id,
        "today_loading": counts["loading"],
        "today_unloading": counts["unloading"],
        "today_total": counts["loading"] + counts["unloading"],
    }


@router.get("/plant")
async def get_plant_metrics():
    """Get plant-level metrics."""
    from app.main import metrics_service
    if metrics_service is not None:
        return await metrics_service.get_plant_metrics()
    return worker_manager.get_summary()
