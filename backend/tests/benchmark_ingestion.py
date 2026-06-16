#!/usr/bin/env python3
"""CPU throughput benchmark for Phase 1 frame ingestion.

Usage (from backend/ dir):
    uv run python tests/benchmark_ingestion.py <source> [target_width] [duration_sec]

Examples:
    uv run python tests/benchmark_ingestion.py samples/clip.mp4
    uv run python tests/benchmark_ingestion.py rtsp://localhost:8554/cam01 640 30
    uv run python tests/benchmark_ingestion.py samples/clip.mp4 320 10
"""

import sys
import time

# Allow running from repo root or backend/
sys.path.insert(0, ".")

from app.core.frame_reader import FrameReader


def benchmark(source: str, target_width: int = 640, duration_sec: float = 15.0) -> None:
    print(f"\n{'='*60}")
    print(f"  Source       : {source}")
    print(f"  Target width : {target_width}px")
    print(f"  Duration     : {duration_sec}s")
    print(f"{'='*60}\n")

    reader = FrameReader(source, target_width=target_width)
    if not reader.open():
        print(f"ERROR: Cannot open source: {source}", file=sys.stderr)
        sys.exit(1)

    native_fps = reader.source_fps()
    print(f"Source FPS (reported): {native_fps:.1f}")
    print("Reading frames...\n")

    consumed = 0
    prev_report = time.monotonic()
    prev_consumed = 0
    deadline = time.monotonic() + duration_sec

    try:
        while time.monotonic() < deadline:
            ok, _ = reader.read()
            if ok:
                consumed += 1
            else:
                time.sleep(0.002)

            now = time.monotonic()
            if now - prev_report >= 5.0:
                interval_fps = (consumed - prev_consumed) / (now - prev_report)
                s = reader.stats
                print(
                    f"  t={now - reader.stats.start_time:5.1f}s | "
                    f"consume={interval_fps:5.1f} fps | "
                    f"capture={s.capture_fps:5.1f} fps | "
                    f"drop={s.drop_rate:.1%} | "
                    f"total_consumed={consumed}"
                )
                prev_report = now
                prev_consumed = consumed
    finally:
        reader.release()

    s = reader.stats
    elapsed = s.elapsed_sec
    print(f"\n{'='*60}")
    print(f"  RESULTS")
    print(f"{'='*60}")
    print(f"  Elapsed           : {elapsed:.2f}s")
    print(f"  Frames captured   : {s.frames_captured}")
    print(f"  Frames consumed   : {s.frames_read}")
    print(f"  Frames dropped    : {s.frames_dropped}")
    print(f"  Capture FPS       : {s.capture_fps:.2f}")
    print(f"  Consume FPS       : {s.consume_fps:.2f}")
    print(f"  Drop rate         : {s.drop_rate:.1%}")
    print(f"{'='*60}\n")

    if s.capture_fps < 10:
        print("WARNING: Capture FPS < 10. Source may be slow or unreachable.")
    if s.drop_rate > 0.5:
        print("WARNING: Drop rate > 50%. Consumer is too slow — increase DETECT_EVERY_N_FRAMES.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    _source = sys.argv[1]
    _width = int(sys.argv[2]) if len(sys.argv) > 2 else 640
    _duration = float(sys.argv[3]) if len(sys.argv) > 3 else 15.0

    benchmark(_source, target_width=_width, duration_sec=_duration)
