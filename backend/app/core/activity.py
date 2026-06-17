"""Activity/Session FSM for loading/unloading detection.

State machine per camera:

    IDLE
      └─(truck present AND worker/movement detected
         for ≥ activity_start_sec)─▶ ACTIVE(LOADING|UNLOADING)
    ACTIVE
      ├─ counting products via dual-line logic
      └─(no new counts for ≥ session_idle_end_sec)─▶ COMPLETED → IDLE
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

COCO_TRUCK_IDS = {5, 7}   # bus, truck
COCO_PERSON_ID = 0


@dataclass
class SessionInfo:
    session_id: str
    camera_id: str
    session_type: str          # LOADING or UNLOADING
    start_time: str            # ISO-8601 UTC
    count: int = 0


@dataclass
class FSMConfig:
    activity_start_sec: float = 10.0
    session_idle_end_sec: float = 300.0


class ActivityFSM:
    """Per-camera finite state machine for activity detection.

    Call update() once per detection cycle (every detect_every_n frames).
    It returns a list of event dicts to be pushed onto the event_queue.
    """

    def __init__(self, camera_id: str, config: FSMConfig | None = None):
        self.camera_id = camera_id
        self.cfg = config or FSMConfig()

        self.state: str = "IDLE"           # IDLE | ACTIVE | COMPLETED
        self.session: SessionInfo | None = None

        # Accumulator: how long have we seen "activity" conditions continuously
        self._activity_onset: float | None = None
        # Timestamp of last count event during ACTIVE state
        self._last_count_time: float | None = None

    def update(
        self,
        class_ids,
        new_count_events: list[dict],
        now: float | None = None,
    ) -> list[dict]:
        """Advance the FSM. Returns event dicts for the event_queue.

        Args:
            class_ids: numpy array of COCO class IDs from current detections.
            new_count_events: count event dicts produced by DualLineCounter
                              this cycle (may be empty).
            now: monotonic time (defaults to time.monotonic()).
        """
        now = time.monotonic() if now is None else now
        events: list[dict] = []

        if self.state == "IDLE":
            events.extend(self._idle_step(class_ids, new_count_events, now))
        elif self.state == "ACTIVE":
            events.extend(self._active_step(class_ids, new_count_events, now))

        return events

    # ------------------------------------------------------------------
    # IDLE state
    # ------------------------------------------------------------------

    def _idle_step(self, class_ids, new_count_events, now: float) -> list[dict]:
        truck_present = _has_class(class_ids, COCO_TRUCK_IDS)
        person_present = _has_class(class_ids, {COCO_PERSON_ID})
        has_movement = len(new_count_events) > 0

        activity_detected = truck_present and (person_present or has_movement)

        if activity_detected:
            if self._activity_onset is None:
                self._activity_onset = now
            elapsed = now - self._activity_onset
            if elapsed >= self.cfg.activity_start_sec:
                return self._start_session(new_count_events, now)
        else:
            self._activity_onset = None

        return []

    def _start_session(self, new_count_events, now: float) -> list[dict]:
        direction = _dominant_direction(new_count_events)
        session_type = direction if direction else "LOADING"

        sid = _make_session_id(session_type)
        ts = datetime.now(timezone.utc).isoformat()

        self.session = SessionInfo(
            session_id=sid,
            camera_id=self.camera_id,
            session_type=session_type,
            start_time=ts,
            count=len(new_count_events),
        )
        self.state = "ACTIVE"
        self._last_count_time = now
        self._activity_onset = None

        return [{
            "type": "activity_event",
            "camera_id": self.camera_id,
            "session_id": sid,
            "kind": "session_start",
            "payload": {
                "session_type": session_type,
                "start_time": ts,
            },
        }]

    # ------------------------------------------------------------------
    # ACTIVE state
    # ------------------------------------------------------------------

    def _active_step(self, class_ids, new_count_events, now: float) -> list[dict]:
        assert self.session is not None
        events: list[dict] = []

        if new_count_events:
            self._last_count_time = now
            self.session.count += len(new_count_events)
            if self.session.session_type == "LOADING":
                loading = sum(1 for e in new_count_events if e["direction"] == "LOADING")
                unloading = len(new_count_events) - loading
            else:
                unloading = sum(1 for e in new_count_events if e["direction"] == "UNLOADING")
                loading = len(new_count_events) - unloading

            # If we see significant opposite-direction movement, re-classify
            opposite = "UNLOADING" if self.session.session_type == "LOADING" else "LOADING"
            opp_count = sum(1 for e in new_count_events if e["direction"] == opposite)
            if opp_count > 0 and self.session.count <= opp_count * 2:
                new_dir = _dominant_direction(new_count_events)
                if new_dir and new_dir != self.session.session_type:
                    self.session.session_type = new_dir

        idle_duration = now - (self._last_count_time or now)
        if idle_duration >= self.cfg.session_idle_end_sec:
            events.extend(self._complete_session())

        return events

    def _complete_session(self) -> list[dict]:
        assert self.session is not None
        ts = datetime.now(timezone.utc).isoformat()
        event = {
            "type": "activity_event",
            "camera_id": self.camera_id,
            "session_id": self.session.session_id,
            "kind": "session_end",
            "payload": {
                "session_type": self.session.session_type,
                "start_time": self.session.start_time,
                "end_time": ts,
                "count": self.session.count,
            },
        }
        self.session = None
        self.state = "IDLE"
        self._last_count_time = None
        self._activity_onset = None
        return [event]

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @property
    def current_session_id(self) -> str | None:
        return self.session.session_id if self.session else None

    @property
    def current_session_type(self) -> str | None:
        return self.session.session_type if self.session else None

    def force_complete(self) -> list[dict]:
        """Force-complete the current session (e.g. on camera stop)."""
        if self.state == "ACTIVE" and self.session:
            return self._complete_session()
        return []


def _has_class(class_ids, target_ids: set[int]) -> bool:
    if class_ids is None or len(class_ids) == 0:
        return False
    return any(int(cid) in target_ids for cid in class_ids)


def _dominant_direction(count_events: list[dict]) -> str | None:
    if not count_events:
        return None
    loading = sum(1 for e in count_events if e.get("direction") == "LOADING")
    unloading = len(count_events) - loading
    if loading >= unloading:
        return "LOADING"
    return "UNLOADING"


def _make_session_id(session_type: str) -> str:
    prefix = session_type[:4].upper()
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    short_uuid = uuid.uuid4().hex[:6].upper()
    return f"{prefix}_{date_part}_{short_uuid}"
