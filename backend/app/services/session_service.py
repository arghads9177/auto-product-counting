"""Session management service — MongoDB-backed."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase


class SessionService:
    """Manages loading/unloading sessions in MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db["sessions"]

    async def create_session(
        self,
        session_id: str,
        camera_id: str,
        session_type: str,
        start_time: str,
    ) -> dict:
        doc = {
            "session_id": session_id,
            "camera_id": camera_id,
            "type": session_type,
            "status": "ACTIVE",
            "start_time": start_time,
            "end_time": None,
            "count": 0,
            "created_by_rule": "activity_fsm",
        }
        await self.col.insert_one(doc)
        doc.pop("_id", None)
        return doc

    async def complete_session(
        self,
        session_id: str,
        end_time: str,
        final_count: int,
    ) -> None:
        await self.col.update_one(
            {"session_id": session_id},
            {"$set": {
                "status": "COMPLETED",
                "end_time": end_time,
                "count": final_count,
            }},
        )

    async def increment_count(self, session_id: str, amount: int = 1) -> None:
        await self.col.update_one(
            {"session_id": session_id},
            {"$inc": {"count": amount}},
        )

    async def get_active_sessions(self, camera_id: str | None = None) -> list[dict]:
        query: dict[str, Any] = {"status": "ACTIVE"}
        if camera_id:
            query["camera_id"] = camera_id
        cursor = self.col.find(query, {"_id": 0})
        return await cursor.to_list(length=100)

    async def list_sessions(
        self,
        status: str | None = None,
        camera_id: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        query: dict[str, Any] = {}
        if status:
            query["status"] = status.upper()
        if camera_id:
            query["camera_id"] = camera_id
        cursor = (
            self.col.find(query, {"_id": 0})
            .sort("start_time", -1)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def get_session(self, session_id: str) -> dict | None:
        doc = await self.col.find_one({"session_id": session_id}, {"_id": 0})
        return doc
