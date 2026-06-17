"""Tests for Phase 5 — persistence services (SessionService, MetricsService, EventBus)."""
import pytest
import pytest_asyncio
from mongomock_motor import AsyncMongoMockClient

from app.services.session_service import SessionService
from app.services.metrics_service import MetricsService
from app.services.event_bus import EventBus


@pytest_asyncio.fixture
async def db():
    client = AsyncMongoMockClient()
    return client["test_db"]


@pytest_asyncio.fixture
async def session_svc(db):
    return SessionService(db)


@pytest_asyncio.fixture
async def metrics_svc(db):
    return MetricsService(db)


@pytest_asyncio.fixture
async def bus(db, session_svc):
    eb = EventBus(db, sio=None)
    eb.set_session_service(session_svc)
    return eb


# ── SessionService ──────────────────────────────────────────────────

class TestSessionService:
    @pytest.mark.asyncio
    async def test_create_and_get(self, session_svc):
        doc = await session_svc.create_session(
            session_id="LOAD_20260617_ABC123",
            camera_id="CAM01",
            session_type="LOADING",
            start_time="2026-06-17T10:00:00Z",
        )
        assert doc["session_id"] == "LOAD_20260617_ABC123"
        assert doc["status"] == "ACTIVE"

        fetched = await session_svc.get_session("LOAD_20260617_ABC123")
        assert fetched is not None
        assert fetched["camera_id"] == "CAM01"

    @pytest.mark.asyncio
    async def test_complete_session(self, session_svc):
        await session_svc.create_session(
            session_id="S1", camera_id="CAM01",
            session_type="LOADING", start_time="2026-06-17T10:00:00Z",
        )
        await session_svc.complete_session(
            session_id="S1",
            end_time="2026-06-17T11:00:00Z",
            final_count=42,
        )
        doc = await session_svc.get_session("S1")
        assert doc["status"] == "COMPLETED"
        assert doc["count"] == 42
        assert doc["end_time"] == "2026-06-17T11:00:00Z"

    @pytest.mark.asyncio
    async def test_list_sessions_filters(self, session_svc):
        await session_svc.create_session("S1", "CAM01", "LOADING", "2026-06-17T09:00:00Z")
        await session_svc.create_session("S2", "CAM02", "UNLOADING", "2026-06-17T10:00:00Z")
        await session_svc.complete_session("S1", "2026-06-17T09:30:00Z", 10)

        active = await session_svc.list_sessions(status="ACTIVE")
        assert len(active) == 1
        assert active[0]["session_id"] == "S2"

        cam01 = await session_svc.list_sessions(camera_id="CAM01")
        assert len(cam01) == 1

    @pytest.mark.asyncio
    async def test_increment_count(self, session_svc):
        await session_svc.create_session("S1", "CAM01", "LOADING", "2026-06-17T10:00:00Z")
        await session_svc.increment_count("S1")
        await session_svc.increment_count("S1")
        doc = await session_svc.get_session("S1")
        assert doc["count"] == 2

    @pytest.mark.asyncio
    async def test_get_active_sessions(self, session_svc):
        await session_svc.create_session("S1", "CAM01", "LOADING", "2026-06-17T10:00:00Z")
        await session_svc.create_session("S2", "CAM01", "UNLOADING", "2026-06-17T11:00:00Z")
        active = await session_svc.get_active_sessions("CAM01")
        assert len(active) == 2


# ── EventBus ────────────────────────────────────────────────────────

class TestEventBus:
    @pytest.mark.asyncio
    async def test_count_event_persisted(self, bus, db):
        await bus.process_event({
            "type": "count_event",
            "camera_id": "CAM01",
            "session_id": "S1",
            "track_id": 42,
            "direction": "LOADING",
            "timestamp": "2026-06-17T10:05:00Z",
        })
        docs = await db["count_events"].find({}).to_list(length=10)
        assert len(docs) == 1
        assert docs[0]["track_id"] == 42

    @pytest.mark.asyncio
    async def test_activity_session_start_creates_session(self, bus, db):
        await bus.process_event({
            "type": "activity_event",
            "camera_id": "CAM01",
            "session_id": "LOAD_20260617_XYZ",
            "kind": "session_start",
            "payload": {
                "session_type": "LOADING",
                "start_time": "2026-06-17T10:00:00Z",
            },
        })
        doc = await db["sessions"].find_one({"session_id": "LOAD_20260617_XYZ"})
        assert doc is not None
        assert doc["status"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_activity_session_end_completes_session(self, bus, db):
        await bus.process_event({
            "type": "activity_event",
            "camera_id": "CAM01",
            "session_id": "S1",
            "kind": "session_start",
            "payload": {"session_type": "LOADING", "start_time": "2026-06-17T10:00:00Z"},
        })
        await bus.process_event({
            "type": "activity_event",
            "camera_id": "CAM01",
            "session_id": "S1",
            "kind": "session_end",
            "payload": {
                "session_type": "LOADING",
                "start_time": "2026-06-17T10:00:00Z",
                "end_time": "2026-06-17T10:30:00Z",
                "count": 25,
            },
        })
        doc = await db["sessions"].find_one({"session_id": "S1"})
        assert doc["status"] == "COMPLETED"
        assert doc["count"] == 25

    @pytest.mark.asyncio
    async def test_camera_status_persisted(self, bus, db):
        await db["cameras"].insert_one({"camera_id": "CAM01", "status": "OFFLINE"})
        await bus.process_event({
            "type": "camera_status",
            "camera_id": "CAM01",
            "status": "ONLINE",
        })
        doc = await db["cameras"].find_one({"camera_id": "CAM01"})
        assert doc["status"] == "ONLINE"

    @pytest.mark.asyncio
    async def test_log_persisted(self, bus, db):
        await bus.log(
            category="SYSTEM",
            log_type="startup",
            severity="INFO",
            message="test log message",
            camera_id="CAM01",
        )
        docs = await db["system_logs"].find({}).to_list(length=10)
        assert len(docs) == 1
        assert docs[0]["message"] == "test log message"


# ── MetricsService ──────────────────────────────────────────────────

class TestMetricsService:
    @pytest.mark.asyncio
    async def test_camera_metrics(self, metrics_svc, db):
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).isoformat()
        await db["count_events"].insert_many([
            {"camera_id": "CAM01", "direction": "LOADING", "timestamp": ts, "session_id": "S1", "track_id": 1},
            {"camera_id": "CAM01", "direction": "LOADING", "timestamp": ts, "session_id": "S1", "track_id": 2},
            {"camera_id": "CAM01", "direction": "UNLOADING", "timestamp": ts, "session_id": "S1", "track_id": 3},
        ])
        result = await metrics_svc.get_camera_metrics("CAM01")
        assert result["today_loading"] == 2
        assert result["today_unloading"] == 1
        assert result["today_total"] == 3

    @pytest.mark.asyncio
    async def test_plant_metrics(self, metrics_svc, db):
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).isoformat()
        await db["count_events"].insert_many([
            {"camera_id": "CAM01", "direction": "LOADING", "timestamp": ts, "session_id": "S1", "track_id": 1},
            {"camera_id": "CAM02", "direction": "UNLOADING", "timestamp": ts, "session_id": "S2", "track_id": 2},
        ])
        result = await metrics_svc.get_plant_metrics()
        assert result["today_total"] == 2
        assert result["today_loading"] == 1
        assert result["today_unloading"] == 1
        assert len(result["hourly_trend"]) == 1
