"""Per-camera worker process (Phase 1: ingestion + throughput measurement)."""
import multiprocessing
import time
from multiprocessing.synchronize import Event as MpEvent
from typing import Optional


class CameraWorker:
    """Manages a single per-camera OS process."""

    def __init__(
        self,
        camera_id: str,
        source: str,
        event_queue: multiprocessing.Queue,
    ) -> None:
        self.camera_id = camera_id
        self.source = source
        self.event_queue = event_queue
        self._stop_event: MpEvent = multiprocessing.Event()
        self.process: Optional[multiprocessing.Process] = None

    def start(self) -> None:
        self.process = multiprocessing.Process(
            target=_worker_run,
            args=(self.camera_id, self.source, self.event_queue, self._stop_event),
            daemon=True,
            name=f"cam-{self.camera_id}",
        )
        self.process.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self.process is not None:
            self.process.join(timeout=5.0)
            if self.process.is_alive():
                self.process.terminate()
                self.process.join(timeout=2.0)


def _worker_run(
    camera_id: str,
    source: str,
    event_queue: multiprocessing.Queue,
    stop_event: MpEvent,
) -> None:
    """Process entry point — runs in a forked child.

    Phase 1 scope: open the source, read frames with drop-to-latest, and
    periodically emit throughput stats.  Detection/tracking/counting will
    be layered on top in Phases 2–4.
    """
    # Import here so the child process re-resolves after fork on all platforms.
    from app.core.frame_reader import FrameReader

    reader = FrameReader(source, target_width=640)
    if not reader.open():
        event_queue.put({
            "type": "camera_status",
            "camera_id": camera_id,
            "status": "ERROR",
            "message": f"Failed to open source: {source}",
        })
        return

    event_queue.put({
        "type": "camera_status",
        "camera_id": camera_id,
        "status": "ONLINE",
        "source_fps": reader.source_fps(),
    })

    frame_idx = 0
    stats_interval = 100  # emit throughput every N consumed frames

    while not stop_event.is_set():
        ok, _ = reader.read()
        if not ok:
            time.sleep(0.005)
            continue

        frame_idx += 1

        # Phases 2–4 will insert: detect → track → count → annotate
        # For now we just consume and measure.

        if frame_idx % stats_interval == 0:
            s = reader.stats
            event_queue.put({
                "type": "throughput",
                "camera_id": camera_id,
                "frames_read": s.frames_read,
                "frames_dropped": s.frames_dropped,
                "capture_fps": round(s.capture_fps, 2),
                "consume_fps": round(s.consume_fps, 2),
                "drop_rate": round(s.drop_rate, 3),
            })

    reader.release()
    event_queue.put({
        "type": "camera_status",
        "camera_id": camera_id,
        "status": "OFFLINE",
    })
