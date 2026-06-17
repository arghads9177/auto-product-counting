"""Phase 2 tests — detector and tracker unit tests (no real model or camera needed)."""
import numpy as np
import pytest
import supervision as sv


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------

def test_detector_requires_load():
    from app.core.detector import YOLODetector
    d = YOLODetector()
    with pytest.raises(RuntimeError, match="load\\(\\)"):
        d.detect(np.zeros((480, 640, 3), dtype=np.uint8))


def test_detector_unload_is_idempotent():
    from app.core.detector import YOLODetector
    d = YOLODetector()
    d.unload()  # model is already None — should not raise
    assert d.model is None


def test_coco_target_classes_contains_expected_ids():
    from app.core.detector import COCO_TARGET_CLASSES
    assert 0 in COCO_TARGET_CLASSES   # person
    assert 7 in COCO_TARGET_CLASSES   # truck
    assert 5 in COCO_TARGET_CLASSES   # bus


# ---------------------------------------------------------------------------
# Tracker
# ---------------------------------------------------------------------------

def test_tracker_instantiates():
    from app.core.tracker import ByteTracker
    bt = ByteTracker()
    assert bt.tracker is not None


def test_tracker_update_empty_detections():
    from app.core.tracker import ByteTracker
    bt = ByteTracker()
    result = bt.update(sv.Detections.empty())
    assert isinstance(result, sv.Detections)
    assert len(result) == 0


def test_tracker_reset_does_not_raise():
    from app.core.tracker import ByteTracker
    bt = ByteTracker()
    bt.reset()  # should not raise even on a fresh tracker


def test_tracker_assigns_ids_to_detections():
    """Tracker must assign stable integer tracker_ids."""
    from app.core.tracker import ByteTracker

    bt = ByteTracker()
    # Fake a single detection: one bounding box, class 7 (truck), conf 0.9
    det = sv.Detections(
        xyxy=np.array([[100, 100, 200, 200]], dtype=np.float32),
        confidence=np.array([0.9], dtype=np.float32),
        class_id=np.array([7], dtype=int),
    )
    tracked = bt.update(det)
    assert len(tracked) == 1
    assert tracked.tracker_id is not None
    assert tracked.tracker_id[0] is not None


# ---------------------------------------------------------------------------
# _push_frame helper
# ---------------------------------------------------------------------------

def test_push_frame_drops_stale():
    # Use threading.queue.Queue: same .empty()/.get_nowait()/.put_nowait() API
    # but synchronous (no background feeder thread), so the drop-to-latest
    # logic is deterministic in tests.
    import queue
    from app.core.worker import _push_frame

    q: queue.Queue = queue.Queue(maxsize=2)
    _push_frame(q, b"frame1")
    _push_frame(q, b"frame2")  # should drain frame1 then put frame2
    assert q.get_nowait() == b"frame2"
    assert q.empty()
