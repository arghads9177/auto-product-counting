"""Tests for Phase 10 — Hardening (max concurrent cameras, seed admin)."""
import pytest
import pytest_asyncio
from mongomock_motor import AsyncMongoMockClient

from app.core.worker_manager import _WorkerManager


class TestMaxConcurrentCameras:
    def test_max_cameras_enforced(self, monkeypatch):
        monkeypatch.setattr("app.config.settings.MAX_CONCURRENT_CAMERAS", 1)

        wm = _WorkerManager()
        wm.register_camera("CAM01", "Cam1", "fake1.mp4", "file")
        wm.register_camera("CAM02", "Cam2", "fake2.mp4", "file")

        # Can't actually start workers without video sources, but we can
        # test the concurrency check by mocking a running worker.
        class FakeProcess:
            def is_alive(self):
                return True

        class FakeWorker:
            process = FakeProcess()

        wm._workers["CAM01"] = FakeWorker()
        ok, msg = wm.start("CAM02")
        assert not ok
        assert "Max concurrent cameras" in msg


class TestSeedAdmin:
    @pytest.mark.asyncio
    async def test_seed_creates_admin(self, monkeypatch):
        client = AsyncMongoMockClient()
        db = client["test_seed"]

        from app.db import mongo as mongo_mod
        monkeypatch.setattr(mongo_mod.mongo_connection, "db", db)

        from app.auth.auth import seed_admin_user
        await seed_admin_user()

        user = await db["users"].find_one({"username": "admin"})
        assert user is not None
        assert user["role"] == "ADMIN"

    @pytest.mark.asyncio
    async def test_seed_idempotent(self, monkeypatch):
        client = AsyncMongoMockClient()
        db = client["test_seed2"]

        from app.db import mongo as mongo_mod
        monkeypatch.setattr(mongo_mod.mongo_connection, "db", db)

        from app.auth.auth import seed_admin_user
        await seed_admin_user()
        await seed_admin_user()  # should not raise

        count = await db["users"].count_documents({"username": "admin"})
        assert count == 1
