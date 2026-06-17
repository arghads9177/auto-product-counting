"""Event bus — persists events to MongoDB and broadcasts via Socket.IO."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase


class EventBus:
    """Fan-out: worker events → MongoDB persistence + Socket.IO broadcast."""

    def __init__(self, db: AsyncIOMotorDatabase, sio=None) -> None:
        self.db = db
        self.sio = sio
        self._session_service = None
        self._metrics_service = None

    def set_session_service(self, svc) -> None:
        self._session_service = svc

    def set_metrics_service(self, svc) -> None:
        self._metrics_service = svc

    async def process_event(self, event: dict) -> None:
        kind = event.get("type")
        if kind == "count_event":
            await self._handle_count_event(event)
        elif kind == "activity_event":
            await self._handle_activity_event(event)
        elif kind == "camera_status":
            await self._handle_camera_status(event)
        elif kind == "throughput":
            await self._broadcast("throughput", event)

    async def _handle_count_event(self, event: dict) -> None:
        doc = {
            "event_id": uuid.uuid4().hex,
            "camera_id": event.get("camera_id"),
            "session_id": event.get("session_id"),
            "track_id": event.get("track_id"),
            "direction": event.get("direction"),
            "timestamp": event.get("timestamp"),
        }
        try:
            await self.db["count_events"].insert_one(doc)
        except Exception:
            pass

        if doc["session_id"] and self._session_service:
            try:
                await self._session_service.increment_count(doc["session_id"])
            except Exception:
                pass

        await self._broadcast("count_event", {
            k: v for k, v in doc.items() if k != "_id"
        })

    async def _handle_activity_event(self, event: dict) -> None:
        ak = event.get("kind")
        payload = event.get("payload", {})
        session_id = event.get("session_id")
        camera_id = event.get("camera_id")

        doc = {
            "camera_id": camera_id,
            "session_id": session_id,
            "kind": ak,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            await self.db["activity_events"].insert_one(doc)
        except Exception:
            pass

        if ak == "session_start" and self._session_service:
            try:
                await self._session_service.create_session(
                    session_id=session_id,
                    camera_id=camera_id,
                    session_type=payload.get("session_type", "LOADING"),
                    start_time=payload.get("start_time", doc["timestamp"]),
                )
            except Exception:
                pass
            await self._broadcast("session_update", {
                "session_id": session_id,
                "camera_id": camera_id,
                "status": "ACTIVE",
                "type": payload.get("session_type"),
                "start_time": payload.get("start_time"),
            })

        elif ak == "session_end" and self._session_service:
            try:
                await self._session_service.complete_session(
                    session_id=session_id,
                    end_time=payload.get("end_time", doc["timestamp"]),
                    final_count=payload.get("count", 0),
                )
            except Exception:
                pass
            await self._broadcast("session_update", {
                "session_id": session_id,
                "camera_id": camera_id,
                "status": "COMPLETED",
                "type": payload.get("session_type"),
                "end_time": payload.get("end_time"),
                "count": payload.get("count", 0),
            })

        await self._broadcast("activity_event", {
            k: v for k, v in doc.items() if k != "_id"
        })

    async def _handle_camera_status(self, event: dict) -> None:
        camera_id = event.get("camera_id")
        status = event.get("status")
        try:
            await self.db["cameras"].update_one(
                {"camera_id": camera_id},
                {"$set": {"status": status}},
            )
        except Exception:
            pass
        await self._broadcast("camera_status", {
            "camera_id": camera_id,
            "status": status,
        })

    async def log(
        self,
        category: str,
        log_type: str,
        severity: str,
        message: str,
        camera_id: str | None = None,
        session_id: str | None = None,
    ) -> None:
        doc = {
            "category": category,
            "type": log_type,
            "severity": severity,
            "camera_id": camera_id,
            "session_id": session_id,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            await self.db["system_logs"].insert_one(doc)
        except Exception:
            pass

    async def _broadcast(self, event_name: str, data: dict) -> None:
        if self.sio is None:
            return
        try:
            await self.sio.emit(event_name, data)
        except Exception:
            pass
        camera_id = data.get("camera_id")
        if camera_id:
            try:
                await self.sio.emit(event_name, data, room=f"cam:{camera_id}")
            except Exception:
                pass
