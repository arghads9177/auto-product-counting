import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import cameras, sessions, counts, metrics, logs, reports, auth, uploads, streams
from app.core.worker_manager import worker_manager
from app.db.mongo import mongo_connection
from app.realtime.socketio_server import sio, sio_app
from app.services.event_bus import EventBus
from app.services.session_service import SessionService
from app.services.metrics_service import MetricsService

event_bus: EventBus | None = None
session_service: SessionService | None = None
metrics_service: MetricsService | None = None


def get_event_bus() -> EventBus:
    assert event_bus is not None
    return event_bus


def get_session_service() -> SessionService:
    assert session_service is not None
    return session_service


def get_metrics_service() -> MetricsService:
    assert metrics_service is not None
    return metrics_service


async def _drain_event_queue() -> None:
    """Drain worker multiprocessing queue → EventBus + in-memory tracking."""
    q = worker_manager.event_queue
    while True:
        try:
            while not q.empty():
                event = q.get_nowait()
                kind = event.get("type", "unknown")
                cam = event.get("camera_id", "?")

                if kind == "throughput":
                    cnt = f"  L={event.get('loading',0)} U={event.get('unloading',0)}"
                    print(
                        f"[{cam}] throughput: "
                        f"capture={event['capture_fps']} fps  "
                        f"consume={event['consume_fps']} fps  "
                        f"drop={event['drop_rate']:.1%}"
                        f"{cnt}"
                    )
                elif kind == "camera_status":
                    status = event.get("status")
                    worker_manager.update_status(cam, status)
                    src_fps = event.get("source_fps", "")
                    suffix = f" @ {src_fps} fps" if src_fps else ""
                    print(f"[{cam}] status → {status}{suffix}")
                elif kind == "activity_event":
                    worker_manager.on_activity_event(event)
                    ak = event.get("kind", "?")
                    payload = event.get("payload", {})
                    sid = event.get("session_id", "?")
                    if ak == "session_start":
                        print(
                            f"[{cam}] SESSION START: {payload.get('session_type')}  "
                            f"id={sid}"
                        )
                    elif ak == "session_end":
                        print(
                            f"[{cam}] SESSION END: {payload.get('session_type')}  "
                            f"id={sid}  count={payload.get('count', 0)}"
                        )
                    else:
                        print(f"[{cam}] activity: {ak}  session={sid}")
                elif kind == "count_event":
                    worker_manager.on_count_event(event)
                    sid = event.get("session_id") or "no-session"
                    print(
                        f"[{cam}] count: {event['direction']}  "
                        f"track={event['track_id']}  session={sid}"
                    )
                else:
                    print(f"[event] {event}")

                if event_bus is not None:
                    try:
                        await event_bus.process_event(event)
                    except Exception as exc:
                        print(f"[event_bus] error: {exc}")
        except Exception:
            pass
        await asyncio.sleep(0.1)


async def _summary_tick() -> None:
    """Periodically broadcast a summary_tick to all Socket.IO clients."""
    while True:
        await asyncio.sleep(1.5)
        try:
            summary = worker_manager.get_summary()
            summary["cameras"] = [
                {
                    "camera_id": c["camera_id"],
                    "name": c.get("name", ""),
                    "status": c.get("status", "OFFLINE"),
                    "running": c.get("running", False),
                }
                for c in worker_manager.list_cameras()
            ]
            summary["active_sessions_detail"] = worker_manager.get_active_sessions()
            await sio.emit("summary_tick", summary)
        except Exception:
            pass


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global event_bus, session_service, metrics_service

    Path(settings.UPLOADS_DIR).mkdir(parents=True, exist_ok=True)

    try:
        await mongo_connection.connect()
    except Exception as exc:
        print(f"WARNING: MongoDB connection failed: {exc}")
        print("Running in degraded mode — events will NOT be persisted")

    db = mongo_connection.db

    if db is not None:
        session_service = SessionService(db)
        metrics_service = MetricsService(db)
        event_bus = EventBus(db, sio)
        event_bus.set_session_service(session_service)
        event_bus.set_metrics_service(metrics_service)
        from app.auth.auth import seed_admin_user
        await seed_admin_user()
    else:
        event_bus = None
        session_service = None
        metrics_service = None

    drain_task = asyncio.create_task(_drain_event_queue())
    tick_task = asyncio.create_task(_summary_tick())

    print("Application startup — uploads dir:", settings.UPLOADS_DIR)
    try:
        yield
    finally:
        drain_task.cancel()
        tick_task.cancel()
        worker_manager.stop_all()
        await mongo_connection.disconnect()
        print("Application shutdown — all workers stopped")


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cameras.router)
app.include_router(sessions.router)
app.include_router(counts.router)
app.include_router(metrics.router)
app.include_router(logs.router)
app.include_router(reports.router)
app.include_router(auth.router)
app.include_router(uploads.router)
app.include_router(streams.router)

app.mount("/ws", sio_app)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/api/health")
async def api_health() -> dict:
    cameras_status = {
        c["camera_id"]: c["status"]
        for c in worker_manager.list_cameras()
    }
    db_status = "connected" if mongo_connection.db is not None else "disconnected"
    return {
        "status": "ok",
        "components": {
            "api": "healthy",
            "cameras": cameras_status,
            "database": db_status,
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
