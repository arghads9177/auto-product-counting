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

    # ------------------------------------------------------------------
    # Worker lifecycle
    # ------------------------------------------------------------------

    def start(self, camera_id: str) -> tuple[bool, str]:
        """Start a worker for *camera_id*. Returns (success, message)."""
        if camera_id not in self._cameras:
            return False, f"Camera '{camera_id}' not registered"
        if self.is_running(camera_id):
            return False, f"Worker for '{camera_id}' already running"

        source = self._cameras[camera_id]["source"]
        worker = CameraWorker(camera_id, source, self._queue)
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
