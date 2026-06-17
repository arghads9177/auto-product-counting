"""Metrics aggregation service — MongoDB-backed."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase


class MetricsService:
    """Aggregates and computes metrics from count_events and sessions."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db

    async def get_camera_metrics(self, camera_id: str) -> dict:
        col = self.db["count_events"]
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

        pipeline = [
            {"$match": {"camera_id": camera_id, "timestamp": {"$gte": today_start}}},
            {"$group": {
                "_id": "$direction",
                "count": {"$sum": 1},
            }},
        ]
        results = {r["_id"]: r["count"] async for r in col.aggregate(pipeline)}

        active_session = await self.db["sessions"].find_one(
            {"camera_id": camera_id, "status": "ACTIVE"},
            {"_id": 0},
        )
        total_sessions = await self.db["sessions"].count_documents(
            {"camera_id": camera_id}
        )

        return {
            "camera_id": camera_id,
            "today_loading": results.get("LOADING", 0),
            "today_unloading": results.get("UNLOADING", 0),
            "today_total": sum(results.values()),
            "total_sessions": total_sessions,
            "active_session": active_session,
        }

    async def get_plant_metrics(self) -> dict:
        col = self.db["count_events"]
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

        pipeline = [
            {"$match": {"timestamp": {"$gte": today_start}}},
            {"$group": {
                "_id": "$direction",
                "count": {"$sum": 1},
            }},
        ]
        results = {r["_id"]: r["count"] async for r in col.aggregate(pipeline)}

        active_sessions = await self.db["sessions"].count_documents({"status": "ACTIVE"})
        completed_today = await self.db["sessions"].count_documents({
            "status": "COMPLETED",
            "end_time": {"$gte": today_start},
        })

        hourly = await self._hourly_trend(today_start)

        return {
            "today_loading": results.get("LOADING", 0),
            "today_unloading": results.get("UNLOADING", 0),
            "today_total": sum(results.values()),
            "active_sessions": active_sessions,
            "completed_sessions_today": completed_today,
            "hourly_trend": hourly,
        }

    async def get_hourly_trend(self, camera_id: str, hours: int = 24) -> list[dict]:
        since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        return await self._hourly_trend(since, camera_id)

    async def _hourly_trend(
        self,
        since: str,
        camera_id: str | None = None,
    ) -> list[dict]:
        query: dict[str, Any] = {"timestamp": {"$gte": since}}
        if camera_id:
            query["camera_id"] = camera_id

        cursor = self.db["count_events"].find(
            query, {"timestamp": 1, "direction": 1, "_id": 0}
        )
        hours_map: dict[int, dict] = {}
        async for doc in cursor:
            ts = doc.get("timestamp", "")
            try:
                hour = datetime.fromisoformat(ts).hour
            except (ValueError, TypeError):
                continue
            d = doc.get("direction")
            bucket = hours_map.setdefault(hour, {"hour": hour, "loading": 0, "unloading": 0})
            if d == "LOADING":
                bucket["loading"] += 1
            elif d == "UNLOADING":
                bucket["unloading"] += 1

        return sorted(hours_map.values(), key=lambda x: x["hour"])
