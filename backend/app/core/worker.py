"""Per-camera worker process."""
import multiprocessing
import time
from multiprocessing.synchronize import Event as MpEvent
from typing import Optional

import cv2


class CameraWorker:
    """Manages a single per-camera OS process."""

    def __init__(
        self,
        camera_id: str,
        source: str,
        event_queue: multiprocessing.Queue,
        frame_queue: multiprocessing.Queue,
    ) -> None:
        self.camera_id = camera_id
        self.source = source
        self.event_queue = event_queue
        self.frame_queue = frame_queue
        self._stop_event: MpEvent = multiprocessing.Event()
        self.process: Optional[multiprocessing.Process] = None

    def start(self) -> None:
        self.process = multiprocessing.Process(
            target=_worker_run,
            args=(
                self.camera_id,
                self.source,
                self.event_queue,
                self.frame_queue,
                self._stop_event,
            ),
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


def _push_frame(frame_queue: multiprocessing.Queue, jpeg_bytes: bytes) -> None:
    """Drop stale frames so the queue never holds more than one waiting frame."""
    while not frame_queue.empty():
        try:
            frame_queue.get_nowait()
        except Exception:
            break
    try:
        frame_queue.put_nowait(jpeg_bytes)
    except Exception:
        pass


def _worker_run(
    camera_id: str,
    source: str,
    event_queue: multiprocessing.Queue,
    frame_queue: multiprocessing.Queue,
    stop_event: MpEvent,
) -> None:
    """Process entry point — detect, track, annotate, stream."""
    # Child-process imports to avoid re-importing in the parent after fork.
    import supervision as sv
    from app.config import settings
    from app.core.frame_reader import FrameReader
    from app.core.detector import YOLODetector, COCO_TARGET_CLASSES
    from app.core.tracker import ByteTracker

    reader = FrameReader(source, target_width=settings.MJPEG_FRAME_WIDTH)
    if not reader.open():
        event_queue.put({
            "type": "camera_status",
            "camera_id": camera_id,
            "status": "ERROR",
            "message": f"Failed to open source: {source}",
        })
        return

    source_fps = reader.source_fps() or 25.0
    event_queue.put({
        "type": "camera_status",
        "camera_id": camera_id,
        "status": "ONLINE",
        "source_fps": source_fps,
    })

    detector = YOLODetector(confidence=settings.MIN_CONFIDENCE)
    detector.load()

    tracker = ByteTracker(frame_rate=source_fps)

    box_annotator = sv.BoxAnnotator()
    label_annotator = sv.LabelAnnotator()

    detect_every = settings.DETECT_EVERY_N_FRAMES
    mjpeg_quality = settings.MJPEG_QUALITY

    frame_idx = 0
    stats_interval = 100
    last_detections: sv.Detections = sv.Detections.empty()

    while not stop_event.is_set():
        ok, frame = reader.read()
        if not ok:
            time.sleep(0.005)
            continue

        frame_idx += 1

        if frame_idx % detect_every == 0:
            raw = detector.detect(frame)
            last_detections = tracker.update(raw)

        annotated = frame.copy()
        if len(last_detections) > 0:
            labels = [
                f"#{tid} {COCO_TARGET_CLASSES.get(int(cid), 'obj')}"
                if tid is not None
                else COCO_TARGET_CLASSES.get(int(cid), "obj")
                for tid, cid in zip(last_detections.tracker_id, last_detections.class_id)
            ]
            annotated = box_annotator.annotate(annotated, last_detections)
            annotated = label_annotator.annotate(annotated, last_detections, labels=labels)

        ok_enc, buf = cv2.imencode(
            ".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, mjpeg_quality]
        )
        if ok_enc:
            _push_frame(frame_queue, buf.tobytes())

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
    detector.unload()
    event_queue.put({
        "type": "camera_status",
        "camera_id": camera_id,
        "status": "OFFLINE",
    })
