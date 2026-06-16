"""Drop-to-latest frame reader for RTSP and file sources."""
import threading
import time
from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np


@dataclass
class FrameStats:
    frames_captured: int = 0
    frames_read: int = 0
    frames_dropped: int = 0
    start_time: float = field(default_factory=time.monotonic)

    @property
    def elapsed_sec(self) -> float:
        return time.monotonic() - self.start_time

    @property
    def capture_fps(self) -> float:
        e = self.elapsed_sec
        return self.frames_captured / e if e > 0 else 0.0

    @property
    def consume_fps(self) -> float:
        e = self.elapsed_sec
        return self.frames_read / e if e > 0 else 0.0

    @property
    def drop_rate(self) -> float:
        total = self.frames_captured
        return self.frames_dropped / total if total > 0 else 0.0


class FrameReader:
    """OpenCV VideoCapture wrapper with a background capture thread.

    A background thread continuously grabs frames from the source.  The
    calling thread always gets the most recent frame; older ones that were
    not consumed in time are silently dropped.  This bounds dashboard
    latency regardless of how fast the source produces frames vs. how fast
    the pipeline can process them.

    Usage::

        reader = FrameReader("rtsp://localhost:8554/cam01")
        if not reader.open():
            raise RuntimeError("Cannot open source")
        try:
            while True:
                ok, frame = reader.read()
                if ok:
                    process(frame)
        finally:
            reader.release()
    """

    def __init__(self, source: str, target_width: int = 640):
        self.source = source
        self.target_width = target_width
        self._cap: Optional[cv2.VideoCapture] = None
        self._latest: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.stats = FrameStats()

    def open(self) -> bool:
        """Open the source and start the background capture thread.

        Returns True on success.  Sets CAP_PROP_BUFFERSIZE = 1 to reduce
        the kernel-level buffer to a single frame, giving the capture thread
        as fresh a frame as possible on each read.
        """
        self._cap = cv2.VideoCapture(self.source)
        if not self._cap.isOpened():
            return False
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.stats = FrameStats()
        self._running = True
        self._thread = threading.Thread(
            target=self._capture_loop,
            daemon=True,
            name=f"capture:{self.source}",
        )
        self._thread.start()
        return True

    def read(self) -> tuple[bool, Optional[np.ndarray]]:
        """Return the most recently captured frame, or (False, None) if none yet."""
        with self._lock:
            if self._latest is None:
                return False, None
            frame = self._latest
            self._latest = None
            self.stats.frames_read += 1
        return True, frame

    def source_fps(self) -> float:
        """Native FPS reported by the source (0.0 if unknown)."""
        if self._cap is not None:
            fps = self._cap.get(cv2.CAP_PROP_FPS)
            return fps if fps and fps > 0 else 0.0
        return 0.0

    def release(self) -> None:
        """Stop the capture thread and release VideoCapture."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def _capture_loop(self) -> None:
        while self._running:
            if self._cap is None:
                break
            ret, frame = self._cap.read()
            if not ret:
                time.sleep(0.01)
                continue
            resized = self._resize(frame)
            with self._lock:
                if self._latest is not None:
                    self.stats.frames_dropped += 1
                self._latest = resized
                self.stats.frames_captured += 1

    def _resize(self, frame: np.ndarray) -> np.ndarray:
        if self.target_width <= 0:
            return frame
        h, w = frame.shape[:2]
        if w == self.target_width:
            return frame
        scale = self.target_width / w
        new_h = int(h * scale)
        return cv2.resize(frame, (self.target_width, new_h), interpolation=cv2.INTER_LINEAR)
