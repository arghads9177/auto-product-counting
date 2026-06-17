"""Registry of active CameraWorker processes and in-memory camera metadata."""
import multiprocessing
from typing import Optional
from datetime import datetime, timezone

from app.core.worker import CameraWorker


class _WorkerManager:
    """Singleton that owns the shared event queue and all per-camera workers.

    Camera metadata lives here in Phase 1; Phase 5 will add MongoDB persistence
    while keeping this registry as the authoritative runtime state.
    """

    def __init__(self) -> None:
        self._cameras: dict[str, dict] = {}   # camera_id → metadata dict
        self._workers: dict[str, CameraWorker] = {}
        self._queue: multiprocessing.Queue = multiprocessing.Queue()
        # Per-camera MJPEG frame queues (maxsize=2 for drop-to-latest semantics)
        self._frame_queues: dict[str, multiprocessing.Queue] = {}
        # In-memory count totals per camera; Phase 5 adds MongoDB persistence
        self._counts: dict[str, dict[str, int]] = {}  # camera_id → {loading, unloading}
        # Active sessions: session_id → session info dict
        self._sessions: dict[str, dict] = {}
        # camera_id → active session_id (at most one per camera)
        self._camera_sessions: dict[str, str] = {}

    @property
    def event_queue(self) -> multiprocessing.Queue:
        return self._queue

    # ------------------------------------------------------------------
    # Camera metadata
    # ------------------------------------------------------------------

    def register_camera(
        self,
        camera_id: str,
        name: str,
        source: str,
        source_type: str = "rtsp",
    ) -> dict:
        """Register or update camera metadata. Returns the metadata dict."""
        entry = {
            "camera_id": camera_id,
            "name": name,
            "source": source,
            "source_type": source_type,  # "rtsp" | "file"
            "status": "OFFLINE",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._cameras[camera_id] = entry
        return entry

    def get_camera(self, camera_id: str) -> Optional[dict]:
        return self._cameras.get(camera_id)

    def list_cameras(self) -> list[dict]:
        cameras = []
        for cid, meta in self._cameras.items():
            row = dict(meta)
            row["running"] = self.is_running(cid)
            cameras.append(row)
        return cameras

    def update_status(self, camera_id: str, status: str) -> None:
        if camera_id in self._cameras:
            self._cameras[camera_id]["status"] = status

    def on_count_event(self, event: dict) -> None:
        """Accumulate a count_event emitted by a worker process."""
        cid = event.get("camera_id")
        if not cid:
            return
        bucket = self._counts.setdefault(cid, {"loading": 0, "unloading": 0})
        direction = event.get("direction", "")
        if direction == "LOADING":
            bucket["loading"] += 1
        elif direction == "UNLOADING":
            bucket["unloading"] += 1

        sid = event.get("session_id")
        if sid and sid in self._sessions:
            self._sessions[sid]["count"] += 1

    def get_counts(self, camera_id: str) -> dict[str, int]:
        return dict(self._counts.get(camera_id, {"loading": 0, "unloading": 0}))

    def on_activity_event(self, event: dict) -> None:
        """Handle session_start / session_end from the Activity FSM."""
        kind = event.get("kind")
        camera_id = event.get("camera_id")
        session_id = event.get("session_id")
        payload = event.get("payload", {})

        if kind == "session_start":
            info = {
                "session_id": session_id,
                "camera_id": camera_id,
                "session_type": payload.get("session_type"),
                "start_time": payload.get("start_time"),
                "count": 0,
            }
            self._sessions[session_id] = info
            self._camera_sessions[camera_id] = session_id
        elif kind == "session_end":
            self._sessions.pop(session_id, None)
            if self._camera_sessions.get(camera_id) == session_id:
                self._camera_sessions.pop(camera_id, None)

    def get_active_sessions(self) -> list[dict]:
        return list(self._sessions.values())

    def get_camera_session(self, camera_id: str) -> dict | None:
        sid = self._camera_sessions.get(camera_id)
        return self._sessions.get(sid) if sid else None

    def get_summary(self) -> dict:
        """Return plant-level totals across all cameras."""
        total_loading = sum(v["loading"] for v in self._counts.values())
        total_unloading = sum(v["unloading"] for v in self._counts.values())
        online = sum(
            1 for c in self._cameras.values() if c.get("status") == "ONLINE"
        )
        return {
            "online_cameras": online,
            "total_cameras": len(self._cameras),
            "today_total": total_loading + total_unloading,
            "loading_count": total_loading,
            "unloading_count": total_unloading,
            "active_sessions": len(self._sessions),
        }

    # ------------------------------------------------------------------
    # Worker lifecycle
    # ------------------------------------------------------------------

    def get_frame_queue(self, camera_id: str) -> Optional[multiprocessing.Queue]:
        """Return the MJPEG frame queue for *camera_id*, or None if unknown."""
        return self._frame_queues.get(camera_id)

    def start(self, camera_id: str) -> tuple[bool, str]:
        """Start a worker for *camera_id*. Returns (success, message)."""
        if camera_id not in self._cameras:
            return False, f"Camera '{camera_id}' not registered"
        if self.is_running(camera_id):
            return False, f"Worker for '{camera_id}' already running"

        from app.config import settings
        running_count = sum(1 for w in self._workers.values() if w.process and w.process.is_alive())
        if running_count >= settings.MAX_CONCURRENT_CAMERAS:
            return False, f"Max concurrent cameras ({settings.MAX_CONCURRENT_CAMERAS}) reached"

        source = self._cameras[camera_id]["source"]
        fq = self._frame_queues.setdefault(camera_id, multiprocessing.Queue(maxsize=2))
        worker = CameraWorker(camera_id, source, self._queue, fq)
        worker.start()
        self._workers[camera_id] = worker
        self.update_status(camera_id, "ONLINE")
        return True, "started"

    def stop(self, camera_id: str) -> tuple[bool, str]:
        """Stop the worker for *camera_id*. Returns (success, message)."""
        worker = self._workers.pop(camera_id, None)
        if worker is None:
            return False, f"No running worker for '{camera_id}'"
        worker.stop()
        self.update_status(camera_id, "OFFLINE")
        return True, "stopped"

    def stop_all(self) -> None:
        """Gracefully stop all running workers (called on app shutdown)."""
        for worker in list(self._workers.values()):
            worker.stop()
        self._workers.clear()

    def is_running(self, camera_id: str) -> bool:
        worker = self._workers.get(camera_id)
        return worker is not None and worker.process is not None and worker.process.is_alive()


worker_manager = _WorkerManager()
