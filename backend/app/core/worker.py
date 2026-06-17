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
    """Process entry point — detect, track, count, annotate, stream."""
    import supervision as sv
    from app.config import settings
    from app.core.frame_reader import FrameReader
    from app.core.detector import YOLODetector, COCO_TARGET_CLASSES
    from app.core.tracker import ByteTracker
    from app.core.counter import DualLineCounter
    from app.core.zones import DEFAULT_LINE_A, DEFAULT_LINE_B
    from app.core.activity import ActivityFSM, FSMConfig

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

    # Grab one frame to get pixel dimensions before creating line zones.
    frame_w = settings.MJPEG_FRAME_WIDTH
    frame_h = 480
    for _ in range(50):  # wait up to ~0.25 s
        ok, seed_frame = reader.read()
        if ok:
            frame_h, frame_w = seed_frame.shape[:2]
            break
        time.sleep(0.005)

    # Build sv.LineZone instances from default normalized config.
    # Phase 5 will replace these with values loaded from camera_configurations.
    lz_a = DEFAULT_LINE_A.to_sv_line_zone(frame_w, frame_h)
    lz_b = DEFAULT_LINE_B.to_sv_line_zone(frame_w, frame_h)
    counter = DualLineCounter(lz_a, lz_b)

    fsm = ActivityFSM(camera_id, FSMConfig(
        activity_start_sec=10.0,
        session_idle_end_sec=300.0,
    ))

    box_annotator = sv.BoxAnnotator()
    label_annotator = sv.LabelAnnotator()
    line_annotator = sv.LineZoneAnnotator(thickness=2)

    detect_every = settings.DETECT_EVERY_N_FRAMES
    mjpeg_quality = settings.MJPEG_QUALITY

    frame_idx = 0
    stats_interval = 100
    last_detections: sv.Detections = sv.Detections.empty()
    consecutive_failures = 0
    max_failures_before_reconnect = 150  # ~0.75s at 5ms sleep

    while not stop_event.is_set():
        ok, frame = reader.read()
        if not ok:
            consecutive_failures += 1
            if consecutive_failures >= max_failures_before_reconnect:
                event_queue.put({
                    "type": "camera_status",
                    "camera_id": camera_id,
                    "status": "BUFFERING",
                })
                reader.release()
                for attempt in range(5):
                    if stop_event.is_set():
                        break
                    time.sleep(2.0)
                    if reader.open():
                        event_queue.put({
                            "type": "camera_status",
                            "camera_id": camera_id,
                            "status": "ONLINE",
                        })
                        consecutive_failures = 0
                        break
                else:
                    event_queue.put({
                        "type": "camera_status",
                        "camera_id": camera_id,
                        "status": "ERROR",
                        "message": "Reconnection failed after 5 attempts",
                    })
                    break
            else:
                time.sleep(0.005)
            continue

        consecutive_failures = 0

        frame_idx += 1

        if frame_idx % detect_every == 0:
            raw = detector.detect(frame)
            last_detections = tracker.update(raw)

            new_events = counter.update(last_detections)

            # Feed FSM with current detections and count events
            fsm_events = fsm.update(
                class_ids=last_detections.class_id,
                new_count_events=new_events,
            )

            for ev in fsm_events:
                event_queue.put(ev)
                if ev.get("kind") == "session_end":
                    counter.reset()

            session_id = fsm.current_session_id

            for ev in new_events:
                event_queue.put({
                    "type": "count_event",
                    "camera_id": camera_id,
                    "track_id": ev["track_id"],
                    "direction": ev["direction"],
                    "timestamp": ev["timestamp"],
                    "session_id": session_id,
                })

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

        # Draw counting lines with live in/out counts.
        line_annotator.annotate(annotated, line_counter=lz_a)
        line_annotator.annotate(annotated, line_counter=lz_b)

        ok_enc, buf = cv2.imencode(
            ".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, mjpeg_quality]
        )
        if ok_enc:
            _push_frame(frame_queue, buf.tobytes())

        if frame_idx % stats_interval == 0:
            s = reader.stats
            counts = counter.get_counts()
            event_queue.put({
                "type": "throughput",
                "camera_id": camera_id,
                "frames_read": s.frames_read,
                "frames_dropped": s.frames_dropped,
                "capture_fps": round(s.capture_fps, 2),
                "consume_fps": round(s.consume_fps, 2),
                "drop_rate": round(s.drop_rate, 3),
                "loading": counts["loading"],
                "unloading": counts["unloading"],
            })

    for ev in fsm.force_complete():
        event_queue.put(ev)

    reader.release()
    detector.unload()
    event_queue.put({
        "type": "camera_status",
        "camera_id": camera_id,
        "status": "OFFLINE",
    })
