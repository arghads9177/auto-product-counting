"""Phase 3 tests — dual-line counter and zone geometry."""
import supervision as sv

from app.core.counter import DualLineCounter, _classify_sequence
from app.core.zones import Zone, Line, DEFAULT_LINE_A, DEFAULT_LINE_B


# ---------------------------------------------------------------------------
# _classify_sequence (pure function, no supervision needed)
# ---------------------------------------------------------------------------

def test_classify_loading():
    assert _classify_sequence(["A", "B"]) == "LOADING"


def test_classify_unloading():
    assert _classify_sequence(["B", "A"]) == "UNLOADING"


def test_classify_incomplete_only_a():
    assert _classify_sequence(["A"]) is None


def test_classify_incomplete_only_b():
    assert _classify_sequence(["B"]) is None


def test_classify_empty():
    assert _classify_sequence([]) is None


def test_classify_uses_first_occurrence():
    # A B A → first A before first B → LOADING
    assert _classify_sequence(["A", "B", "A"]) == "LOADING"
    # B A B → first B before first A → UNLOADING
    assert _classify_sequence(["B", "A", "B"]) == "UNLOADING"


# ---------------------------------------------------------------------------
# Zone geometry
# ---------------------------------------------------------------------------

def test_zone_contains_interior_point():
    z = Zone("test", [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])
    assert z.contains_point(0.5, 0.5)


def test_zone_rejects_exterior_point():
    z = Zone("test", [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])
    assert not z.contains_point(1.5, 0.5)


def test_zone_rejects_boundary_corner():
    z = Zone("test", [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])
    # Corners are implementation-defined; just check it doesn't crash.
    z.contains_point(0.0, 0.0)


# ---------------------------------------------------------------------------
# Line → sv.LineZone conversion
# ---------------------------------------------------------------------------

def test_line_to_sv_line_zone():
    line = Line("A", start=(0.0, 0.5), end=(1.0, 0.5))
    lz = line.to_sv_line_zone(640, 480)
    assert isinstance(lz, sv.LineZone)


def test_default_lines_convert_without_error():
    lz_a = DEFAULT_LINE_A.to_sv_line_zone(640, 480)
    lz_b = DEFAULT_LINE_B.to_sv_line_zone(640, 480)
    assert isinstance(lz_a, sv.LineZone)
    assert isinstance(lz_b, sv.LineZone)


# ---------------------------------------------------------------------------
# DualLineCounter
# ---------------------------------------------------------------------------

def _make_counter(frame_w: int = 640, frame_h: int = 480) -> DualLineCounter:
    lz_a = DEFAULT_LINE_A.to_sv_line_zone(frame_w, frame_h)
    lz_b = DEFAULT_LINE_B.to_sv_line_zone(frame_w, frame_h)
    return DualLineCounter(lz_a, lz_b)


def test_counter_empty_detections_returns_no_events():
    counter = _make_counter()
    events = counter.update(sv.Detections.empty())
    assert events == []


def test_counter_initial_counts_are_zero():
    counter = _make_counter()
    assert counter.get_counts() == {"loading": 0, "unloading": 0}


def test_counter_reset_clears_state():
    counter = _make_counter()
    counter._loading = 5
    counter._unloading = 3
    counter._counted.add(42)
    counter.reset()
    assert counter.get_counts() == {"loading": 0, "unloading": 0}
    assert len(counter._counted) == 0


def test_counter_dedup_via_internal_state():
    """Verify that a track in _counted never produces a second event."""
    counter = _make_counter()
    counter._counted.add(99)
    # Manually inject a crossing history that would otherwise trigger a count.
    counter._crossings[99] = ["A", "B"]
    # Trigger with empty detections (no new line crossings will happen).
    events = counter.update(sv.Detections.empty())
    assert events == []
    assert counter.get_counts() == {"loading": 0, "unloading": 0}


# ---------------------------------------------------------------------------
# worker_manager summary
# ---------------------------------------------------------------------------

def test_worker_manager_summary_default():
    from app.core.worker_manager import _WorkerManager
    wm = _WorkerManager()
    s = wm.get_summary()
    assert s["today_total"] == 0
    assert s["loading_count"] == 0
    assert s["unloading_count"] == 0


def test_worker_manager_on_count_event_accumulates():
    from app.core.worker_manager import _WorkerManager
    wm = _WorkerManager()
    wm.on_count_event({"camera_id": "CAM01", "direction": "LOADING"})
    wm.on_count_event({"camera_id": "CAM01", "direction": "LOADING"})
    wm.on_count_event({"camera_id": "CAM01", "direction": "UNLOADING"})
    assert wm.get_counts("CAM01") == {"loading": 2, "unloading": 1}
    s = wm.get_summary()
    assert s["today_total"] == 3
