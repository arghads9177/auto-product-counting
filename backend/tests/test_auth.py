"""Tests for Phase 8 — Auth/Roles (JWT + role guards)."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from mongomock_motor import AsyncMongoMockClient

from app.auth.auth import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        h = hash_password("secret")
        assert verify_password("secret", h)

    def test_wrong_password_rejected(self):
        h = hash_password("secret")
        assert not verify_password("wrong", h)


class TestJWT:
    def test_create_and_decode(self):
        token = create_access_token("alice", "ADMIN")
        payload = decode_token(token)
        assert payload["sub"] == "alice"
        assert payload["role"] == "ADMIN"

    def test_invalid_token_raises(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_token("garbage.token.here")
        assert exc_info.value.status_code == 401


@pytest_asyncio.fixture(autouse=True)
async def patch_mongo(monkeypatch):
    from app.db import mongo as mongo_mod
    client = AsyncMongoMockClient()
    db = client["test_auth"]
    monkeypatch.setattr(mongo_mod.mongo_connection, "db", db)
    monkeypatch.setattr(mongo_mod.mongo_connection, "client", client)

    import app.main as main_mod
    from app.services.session_service import SessionService
    from app.services.metrics_service import MetricsService
    from app.services.event_bus import EventBus

    monkeypatch.setattr(main_mod, "session_service", SessionService(db))
    monkeypatch.setattr(main_mod, "metrics_service", MetricsService(db))
    monkeypatch.setattr(main_mod, "event_bus", EventBus(db, sio=None))

    yield db


@pytest_asyncio.fixture
async def client():
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _auth_header(username="admin", role="ADMIN"):
    token = create_access_token(username, role)
    return {"Authorization": f"Bearer {token}"}


class TestLoginEndpoint:
    @pytest.mark.asyncio
    async def test_login_success(self, client, patch_mongo):
        db = patch_mongo
        await db["users"].insert_one({
            "username": "admin",
            "password_hash": hash_password("admin"),
            "role": "ADMIN",
        })
        r = await client.post("/api/auth/login", json={
            "username": "admin", "password": "admin",
        })
        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body
        assert body["role"] == "ADMIN"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, patch_mongo):
        db = patch_mongo
        await db["users"].insert_one({
            "username": "admin",
            "password_hash": hash_password("admin"),
            "role": "ADMIN",
        })
        r = await client.post("/api/auth/login", json={
            "username": "admin", "password": "wrong",
        })
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_login_unknown_user(self, client):
        r = await client.post("/api/auth/login", json={
            "username": "nobody", "password": "x",
        })
        assert r.status_code == 401


class TestRegisterEndpoint:
    @pytest.mark.asyncio
    async def test_register_as_admin(self, client):
        r = await client.post(
            "/api/auth/register",
            json={"username": "bob", "password": "pass", "role": "OPERATOR"},
            headers=_auth_header("admin", "ADMIN"),
        )
        assert r.status_code == 200
        assert r.json()["username"] == "bob"

    @pytest.mark.asyncio
    async def test_register_denied_for_operator(self, client):
        r = await client.post(
            "/api/auth/register",
            json={"username": "bob", "password": "pass"},
            headers=_auth_header("op", "OPERATOR"),
        )
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_register_no_auth(self, client):
        r = await client.post(
            "/api/auth/register",
            json={"username": "bob", "password": "pass"},
        )
        assert r.status_code == 401


class TestMeEndpoint:
    @pytest.mark.asyncio
    async def test_me(self, client):
        r = await client.get("/api/auth/me", headers=_auth_header("alice", "SUPERVISOR"))
        assert r.status_code == 200
        assert r.json()["username"] == "alice"
        assert r.json()["role"] == "SUPERVISOR"


class TestRoleGuards:
    @pytest.mark.asyncio
    async def test_add_camera_requires_admin(self, client):
        r = await client.post(
            "/api/cameras",
            json={"camera_id": "CAM01", "name": "Test", "rtsp_url": "rtsp://x"},
            headers=_auth_header("op", "OPERATOR"),
        )
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_add_camera_allowed_for_admin(self, client):
        r = await client.post(
            "/api/cameras",
            json={"camera_id": "CAM01", "name": "Test", "rtsp_url": "rtsp://x"},
            headers=_auth_header("admin", "ADMIN"),
        )
        assert r.status_code == 200
