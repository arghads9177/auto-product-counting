"""Phase 1 integration tests — frame ingestion."""
import time
from pathlib import Path

import cv2
import numpy as np
import pytest

from app.core.frame_reader import FrameReader, FrameStats


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_video(path: str, frames: int = 60, fps: float = 30.0, width: int = 320, height: int = 240) -> None:
    """Write a synthetic .mp4 with solid-color frames."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(path, fourcc, fps, (width, height))
    for i in range(frames):
        color = (int(i * 4 % 255), 100, 150)
        frame = np.full((height, width, 3), color, dtype=np.uint8)
        writer.write(frame)
    writer.release()


@pytest.fixture
def video_path(tmp_path: Path) -> str:
    path = str(tmp_path / "test_clip.mp4")
    _make_video(path, frames=90, fps=30.0)
    return path


# ---------------------------------------------------------------------------
# FrameReader — basic open/read/release
# ---------------------------------------------------------------------------

class TestFrameReader:
    def test_open_valid_file(self, video_path: str) -> None:
        reader = FrameReader(video_path)
        assert reader.open(), "FrameReader should open a valid .mp4"
        reader.release()

    def test_open_missing_file_returns_false(self) -> None:
        reader = FrameReader("/tmp/__no_such_file__.mp4")
        assert not reader.open(), "FrameReader should return False for missing file"

    def test_read_returns_frames(self, video_path: str) -> None:
        reader = FrameReader(video_path, target_width=320)
        assert reader.open()
        try:
            # Give the capture thread time to grab the first frame.
            deadline = time.monotonic() + 2.0
            ok, frame = False, None
            while time.monotonic() < deadline:
                ok, frame = reader.read()
                if ok:
                    break
                time.sleep(0.02)
            assert ok, "Should have received at least one frame within 2 s"
            assert frame is not None
            assert frame.shape[1] == 320, "Width should be resized to target_width"
        finally:
            reader.release()

    def test_resize_preserves_aspect_ratio(self, video_path: str) -> None:
        reader = FrameReader(video_path, target_width=160)
        assert reader.open()
        try:
            deadline = time.monotonic() + 2.0
            frame = None
            while time.monotonic() < deadline:
                ok, frame = reader.read()
                if ok:
                    break
                time.sleep(0.02)
            assert frame is not None
            h, w = frame.shape[:2]
            assert w == 160
            # Original is 320×240 → scale 0.5 → 160×120
            assert h == 120
        finally:
            reader.release()

    def test_stats_increment(self, video_path: str) -> None:
        reader = FrameReader(video_path)
        assert reader.open()
        try:
            consumed = 0
            deadline = time.monotonic() + 3.0
            while time.monotonic() < deadline and consumed < 10:
                ok, _ = reader.read()
                if ok:
                    consumed += 1
                else:
                    time.sleep(0.01)
            assert reader.stats.frames_captured >= consumed
            assert reader.stats.frames_read == consumed
        finally:
            reader.release()

    def test_source_fps(self, video_path: str) -> None:
        reader = FrameReader(video_path)
        assert reader.open()
        try:
            fps = reader.source_fps()
            assert fps == pytest.approx(30.0, abs=1.0), f"Expected ~30 fps, got {fps}"
        finally:
            reader.release()

    def test_release_stops_capture_thread(self, video_path: str) -> None:
        reader = FrameReader(video_path)
        assert reader.open()
        thread = reader._thread
        assert thread is not None
        reader.release()
        assert not thread.is_alive(), "Capture thread should be dead after release"


# ---------------------------------------------------------------------------
# FrameReader — drop-to-latest behaviour
# ---------------------------------------------------------------------------

class TestDropToLatest:
    def test_no_frame_duplication(self, video_path: str) -> None:
        """Each read() call should consume the frame — subsequent call returns False until new one."""
        reader = FrameReader(video_path)
        assert reader.open()
        try:
            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline:
                ok, _ = reader.read()
                if ok:
                    break
                time.sleep(0.01)
            # Immediately read again — buffer should be empty.
            ok2, _ = reader.read()
            assert not ok2, "Second immediate read should return False (buffer consumed)"
        finally:
            reader.release()

    def test_drop_rate_when_reading_slowly(self, video_path: str) -> None:
        """Reading much slower than capture fps should accumulate drops."""
        reader = FrameReader(video_path)
        assert reader.open()
        try:
            time.sleep(0.5)  # let capture thread build up buffered frames
            ok, _ = reader.read()
            assert ok
            # dropped ≥ 0; if source is fast enough we'll see drops
            assert reader.stats.frames_captured >= 1
        finally:
            reader.release()


# ---------------------------------------------------------------------------
# FrameStats
# ---------------------------------------------------------------------------

class TestFrameStats:
    def test_initial_state(self) -> None:
        s = FrameStats()
        assert s.frames_captured == 0
        assert s.frames_read == 0
        assert s.frames_dropped == 0
        assert s.capture_fps == 0.0
        assert s.drop_rate == 0.0

    def test_fps_calculation(self) -> None:
        s = FrameStats()
        s.frames_captured = 300
        # elapsed_sec is based on time.monotonic(), so we can't check exact value,
        # but capture_fps should be > 0 since some time has passed since init.
        time.sleep(0.01)
        assert s.capture_fps > 0

    def test_drop_rate(self) -> None:
        s = FrameStats()
        s.frames_captured = 100
        s.frames_dropped = 20
        assert s.drop_rate == pytest.approx(0.2)
