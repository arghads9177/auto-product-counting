"""Tests for Phase 6 — Realtime API (REST endpoints return live data)."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from mongomock_motor import AsyncMongoMockClient

from app.core.worker_manager import worker_manager


@pytest_asyncio.fixture(autouse=True)
async def patch_mongo(monkeypatch):
    """Patch mongo_connection to use an in-memory mock database."""
    from app.db import mongo as mongo_mod

    client = AsyncMongoMockClient()
    db = client["test_realtime"]
    monkeypatch.setattr(mongo_mod.mongo_connection, "db", db)
    monkeypatch.setattr(mongo_mod.mongo_connection, "client", client)

    import app.main as main_mod
    from app.services.session_service import SessionService
    from app.services.metrics_service import MetricsService
    from app.services.event_bus import EventBus

    svc = SessionService(db)
    met = MetricsService(db)
    bus = EventBus(db, sio=None)
    bus.set_session_service(svc)
    monkeypatch.setattr(main_mod, "session_service", svc)
    monkeypatch.setattr(main_mod, "metrics_service", met)
    monkeypatch.setattr(main_mod, "event_bus", bus)

    yield db

    for cid in list(worker_manager._cameras.keys()):
        worker_manager._cameras.pop(cid, None)
    worker_manager._counts.clear()
    worker_manager._sessions.clear()
    worker_manager._camera_sessions.clear()


@pytest_asyncio.fixture
async def client():
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestCountsSummary:
    @pytest.mark.asyncio
    async def test_summary_includes_active_sessions(self, client):
        worker_manager.register_camera("CAM01", "Test Cam", "fake.mp4", "file")
        worker_manager._sessions["S1"] = {
            "session_id": "S1",
            "camera_id": "CAM01",
            "session_type": "LOADING",
            "start_time": "2026-06-17T10:00:00Z",
            "count": 5,
        }
        r = await client.get("/api/counts/summary")
        assert r.status_code == 200
        body = r.json()
        assert body["active_sessions"] == 1
        assert len(body["active_sessions_detail"]) == 1

    @pytest.mark.asyncio
    async def test_camera_counts(self, client):
        worker_manager.register_camera("CAM01", "Test Cam", "fake.mp4", "file")
        worker_manager.on_count_event({"camera_id": "CAM01", "direction": "LOADING"})
        r = await client.get("/api/counts/camera/CAM01")
        assert r.status_code == 200
        assert r.json()["loading"] == 1


class TestCountEvents:
    @pytest.mark.asyncio
    async def test_query_events(self, client, patch_mongo):
        db = patch_mongo
        await db["count_events"].insert_one({
            "event_id": "e1",
            "camera_id": "CAM01",
            "session_id": "S1",
            "track_id": 42,
            "direction": "LOADING",
            "timestamp": "2026-06-17T10:00:00Z",
        })
        r = await client.get("/api/counts/events", params={"camera_id": "CAM01"})
        assert r.status_code == 200
        assert len(r.json()["events"]) == 1


class TestSessions:
    @pytest.mark.asyncio
    async def test_list_sessions_from_db(self, client, patch_mongo):
        db = patch_mongo
        await db["sessions"].insert_one({
            "session_id": "S1",
            "camera_id": "CAM01",
            "type": "LOADING",
            "status": "ACTIVE",
            "start_time": "2026-06-17T10:00:00Z",
            "count": 10,
        })
        r = await client.get("/api/sessions")
        assert r.status_code == 200
        assert len(r.json()["sessions"]) == 1

    @pytest.mark.asyncio
    async def test_session_detail_with_events(self, client, patch_mongo):
        db = patch_mongo
        await db["sessions"].insert_one({
            "session_id": "S1",
            "camera_id": "CAM01",
            "type": "LOADING",
            "status": "ACTIVE",
            "start_time": "2026-06-17T10:00:00Z",
            "count": 1,
        })
        await db["count_events"].insert_one({
            "event_id": "e1",
            "camera_id": "CAM01",
            "session_id": "S1",
            "track_id": 1,
            "direction": "LOADING",
            "timestamp": "2026-06-17T10:00:01Z",
        })
        await db["activity_events"].insert_one({
            "camera_id": "CAM01",
            "session_id": "S1",
            "kind": "session_start",
            "payload": {},
            "timestamp": "2026-06-17T10:00:00Z",
        })
        r = await client.get("/api/sessions/S1")
        assert r.status_code == 200
        body = r.json()
        assert len(body["count_events"]) == 1
        assert len(body["activity_events"]) == 1


class TestEventTimeline:
    @pytest.mark.asyncio
    async def test_timeline_returns_events(self, client, patch_mongo):
        db = patch_mongo
        await db["activity_events"].insert_many([
            {"camera_id": "CAM01", "session_id": "S1", "kind": "session_start",
             "payload": {}, "timestamp": "2026-06-17T10:00:00Z"},
            {"camera_id": "CAM01", "session_id": "S1", "kind": "session_end",
             "payload": {}, "timestamp": "2026-06-17T10:30:00Z"},
        ])
        r = await client.get("/api/events/timeline")
        assert r.status_code == 200
        assert len(r.json()["events"]) == 2

    @pytest.mark.asyncio
    async def test_timeline_filters_by_camera(self, client, patch_mongo):
        db = patch_mongo
        await db["activity_events"].insert_many([
            {"camera_id": "CAM01", "session_id": "S1", "kind": "x",
             "payload": {}, "timestamp": "2026-06-17T10:00:00Z"},
            {"camera_id": "CAM02", "session_id": "S2", "kind": "x",
             "payload": {}, "timestamp": "2026-06-17T10:05:00Z"},
        ])
        r = await client.get("/api/events/timeline", params={"camera_id": "CAM01"})
        assert r.status_code == 200
        assert len(r.json()["events"]) == 1


class TestLogs:
    @pytest.mark.asyncio
    async def test_logs_endpoint(self, client, patch_mongo):
        db = patch_mongo
        await db["system_logs"].insert_one({
            "category": "SYSTEM",
            "type": "startup",
            "severity": "INFO",
            "message": "test",
            "timestamp": "2026-06-17T10:00:00Z",
        })
        r = await client.get("/api/logs", params={"severity": "INFO"})
        assert r.status_code == 200
        assert len(r.json()["logs"]) == 1


class TestMetrics:
    @pytest.mark.asyncio
    async def test_camera_metrics_from_db(self, client, patch_mongo):
        db = patch_mongo
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).isoformat()
        worker_manager.register_camera("CAM01", "Test", "x", "file")
        await db["count_events"].insert_many([
            {"camera_id": "CAM01", "direction": "LOADING", "timestamp": ts,
             "session_id": "S1", "track_id": 1},
            {"camera_id": "CAM01", "direction": "UNLOADING", "timestamp": ts,
             "session_id": "S1", "track_id": 2},
        ])
        r = await client.get("/api/metrics/camera/CAM01")
        assert r.status_code == 200
        body = r.json()
        assert body["today_loading"] == 1
        assert body["today_unloading"] == 1
