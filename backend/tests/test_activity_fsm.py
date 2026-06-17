"""Tests for the Activity FSM (Phase 4)."""
import numpy as np
import pytest

from app.core.activity import ActivityFSM, FSMConfig


def _make_class_ids(*ids):
    return np.array(ids, dtype=int) if ids else np.array([], dtype=int)


def _make_count_event(direction="LOADING"):
    return {"track_id": 1, "direction": direction, "timestamp": "2026-01-01T00:00:00Z"}


@pytest.fixture
def fsm():
    return ActivityFSM("CAM01", FSMConfig(activity_start_sec=2.0, session_idle_end_sec=5.0))


class TestIdleToActive:
    def test_no_truck_stays_idle(self, fsm):
        events = fsm.update(_make_class_ids(0), [], now=0)
        assert fsm.state == "IDLE"
        assert events == []

    def test_truck_alone_stays_idle(self, fsm):
        events = fsm.update(_make_class_ids(7), [], now=0)
        assert fsm.state == "IDLE"

    def test_truck_plus_person_starts_accumulation(self, fsm):
        fsm.update(_make_class_ids(7, 0), [], now=0)
        assert fsm.state == "IDLE"
        assert fsm._activity_onset == 0

    def test_transitions_after_activity_start_sec(self, fsm):
        fsm.update(_make_class_ids(7, 0), [], now=0)
        assert fsm.state == "IDLE"

        events = fsm.update(_make_class_ids(7, 0), [], now=1.0)
        assert fsm.state == "IDLE"

        events = fsm.update(
            _make_class_ids(7, 0),
            [_make_count_event("LOADING")],
            now=2.5,
        )
        assert fsm.state == "ACTIVE"
        assert len(events) == 1
        assert events[0]["kind"] == "session_start"
        assert events[0]["payload"]["session_type"] == "LOADING"

    def test_activity_resets_if_conditions_lost(self, fsm):
        fsm.update(_make_class_ids(7, 0), [], now=0)
        assert fsm._activity_onset == 0

        fsm.update(_make_class_ids(0), [], now=1.0)
        assert fsm._activity_onset is None

    def test_bus_counts_as_truck(self, fsm):
        fsm.update(_make_class_ids(5, 0), [], now=0)
        assert fsm._activity_onset == 0


class TestActiveState:
    def _activate(self, fsm, now=0):
        fsm.update(_make_class_ids(7, 0), [], now=now)
        return fsm.update(
            _make_class_ids(7, 0),
            [_make_count_event("LOADING")],
            now=now + 2.5,
        )

    def test_session_id_assigned(self, fsm):
        self._activate(fsm)
        assert fsm.current_session_id is not None
        assert fsm.current_session_type == "LOADING"

    def test_counts_accumulate(self, fsm):
        self._activate(fsm)
        fsm.update(_make_class_ids(7, 0), [_make_count_event()], now=4)
        assert fsm.session.count == 2

    def test_completes_after_idle_timeout(self, fsm):
        self._activate(fsm, now=0)
        # Session started at t=2.5. At t=6 that's only 3.5s idle — still active.
        events = fsm.update(_make_class_ids(7), [], now=6)
        assert fsm.state == "ACTIVE"

        # At t=8 that's 5.5s idle → should complete (threshold is 5s).
        events = fsm.update(_make_class_ids(), [], now=8)
        assert fsm.state == "IDLE"
        assert len(events) == 1
        assert events[0]["kind"] == "session_end"
        assert events[0]["payload"]["count"] >= 1

    def test_activity_resets_idle_timer(self, fsm):
        self._activate(fsm, now=0)
        # Count at t=4 resets idle timer
        fsm.update(_make_class_ids(7, 0), [_make_count_event()], now=4)
        # t=8 is only 4s after last count, still under 5s threshold
        events = fsm.update(_make_class_ids(), [], now=8)
        assert fsm.state == "ACTIVE"
        # t=10 is 6s since last count → should complete
        events = fsm.update(_make_class_ids(), [], now=10)
        assert fsm.state == "IDLE"


class TestForceComplete:
    def test_force_complete_active(self, fsm):
        fsm.update(_make_class_ids(7, 0), [], now=0)
        fsm.update(_make_class_ids(7, 0), [_make_count_event()], now=2.5)
        assert fsm.state == "ACTIVE"

        events = fsm.force_complete()
        assert fsm.state == "IDLE"
        assert len(events) == 1
        assert events[0]["kind"] == "session_end"

    def test_force_complete_idle_is_noop(self, fsm):
        events = fsm.force_complete()
        assert events == []


class TestSessionDirection:
    def test_unloading_direction(self, fsm):
        fsm.update(_make_class_ids(7, 0), [], now=0)
        events = fsm.update(
            _make_class_ids(7, 0),
            [_make_count_event("UNLOADING")],
            now=2.5,
        )
        assert fsm.state == "ACTIVE"
        assert events[0]["payload"]["session_type"] == "UNLOADING"
