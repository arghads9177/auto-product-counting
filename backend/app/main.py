import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import cameras, sessions, counts, metrics, logs, reports, auth, uploads, streams
from app.core.worker_manager import worker_manager


async def _drain_event_queue() -> None:
    """Log throughput and status events from worker processes."""
    q = worker_manager.event_queue
    while True:
        try:
            while not q.empty():
                event = q.get_nowait()
                kind = event.get("type", "unknown")
                cam = event.get("camera_id", "?")
                if kind == "throughput":
                    counts = f"  L={event.get('loading',0)} U={event.get('unloading',0)}"
                    print(
                        f"[{cam}] throughput: "
                        f"capture={event['capture_fps']} fps  "
                        f"consume={event['consume_fps']} fps  "
                        f"drop={event['drop_rate']:.1%}"
                        f"{counts}"
                    )
                elif kind == "camera_status":
                    status = event.get("status")
                    worker_manager.update_status(cam, status)
                    src_fps = event.get("source_fps", "")
                    suffix = f" @ {src_fps} fps" if src_fps else ""
                    print(f"[{cam}] status → {status}{suffix}")
                elif kind == "count_event":
                    worker_manager.on_count_event(event)
                    print(
                        f"[{cam}] count: {event['direction']}  "
                        f"track={event['track_id']}"
                    )
                else:
                    print(f"[event] {event}")
        except Exception:
            pass
        await asyncio.sleep(0.5)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Path(settings.UPLOADS_DIR).mkdir(parents=True, exist_ok=True)
    drain_task = asyncio.create_task(_drain_event_queue())
    print("Application startup — uploads dir:", settings.UPLOADS_DIR)
    try:
        yield
    finally:
        drain_task.cancel()
        worker_manager.stop_all()
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


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/api/health")
async def api_health() -> dict:
    cameras_status = {
        c["camera_id"]: c["status"]
        for c in worker_manager.list_cameras()
    }
    return {
        "status": "ok",
        "components": {
            "api": "healthy",
            "cameras": cameras_status,
            "database": "unchecked",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
