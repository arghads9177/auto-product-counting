"""Metrics endpoints."""
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/camera/{camera_id}")
async def get_camera_metrics(camera_id: str):
    """Get per-camera metrics."""
    return {"camera_id": camera_id, "metrics": {}}


@router.get("/plant")
async def get_plant_metrics():
    """Get plant-level metrics."""
    return {"plant_metrics": {}}
