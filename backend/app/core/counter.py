"""Dual-line crossing counter with per-track deduplication."""
from __future__ import annotations

from datetime import datetime, timezone

import supervision as sv


class DualLineCounter:
    """Counts loading (A→B) and unloading (B→A) product movements.

    Both sv.LineZone instances are owned externally and passed in so that
    the caller can annotate them on video frames with LineZoneAnnotator.

    Algorithm:
    - For every tracked detection frame, trigger() both line zones.
    - Record per-track ordered crossing history: which line (A or B) the
      track crossed on each trigger call.
    - When a track has crossed A before B → LOADING; B before A → UNLOADING.
    - A track is counted at most once per session (dedup via _counted set).
    - Phase 5 will persist count_events to MongoDB; here we only accumulate
      in-memory counters and return structured event dicts to the caller.
    """

    def __init__(self, line_a: sv.LineZone, line_b: sv.LineZone) -> None:
        self.line_a = line_a
        self.line_b = line_b
        # tracker_id → ordered list of line names crossed ('A' or 'B')
        self._crossings: dict[int, list[str]] = {}
        # tracker_ids already counted this session
        self._counted: set[int] = set()
        self._loading = 0
        self._unloading = 0

    def update(self, detections: sv.Detections) -> list[dict]:
        """Trigger both lines and return any new count events.

        Returns a list of dicts (one per new count):
            {"track_id": int, "direction": "LOADING"|"UNLOADING", "timestamp": str}
        """
        if len(detections) == 0 or detections.tracker_id is None:
            return []

        in_a, out_a = self.line_a.trigger(detections)
        in_b, out_b = self.line_b.trigger(detections)

        events: list[dict] = []

        for i, tid_raw in enumerate(detections.tracker_id):
            if tid_raw is None:
                continue
            tid = int(tid_raw)

            hist = self._crossings.setdefault(tid, [])

            # Record line crossings (in or out counts equally as a "crossing").
            if in_a[i] or out_a[i]:
                hist.append("A")
            if in_b[i] or out_b[i]:
                hist.append("B")

            if tid in self._counted:
                continue

            direction = _classify_sequence(hist)
            if direction is None:
                continue

            self._counted.add(tid)
            if direction == "LOADING":
                self._loading += 1
            else:
                self._unloading += 1

            events.append({
                "track_id": tid,
                "direction": direction,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        return events

    def get_counts(self) -> dict[str, int]:
        return {"loading": self._loading, "unloading": self._unloading}

    def reset(self) -> None:
        """Reset all state at session boundaries."""
        self._crossings.clear()
        self._counted.clear()
        self._loading = 0
        self._unloading = 0


def _classify_sequence(hist: list[str]) -> str | None:
    """Return 'LOADING', 'UNLOADING', or None if sequence is incomplete."""
    first_a = next((i for i, l in enumerate(hist) if l == "A"), None)
    first_b = next((i for i, l in enumerate(hist) if l == "B"), None)

    if first_a is not None and first_b is not None:
        return "LOADING" if first_a < first_b else "UNLOADING"
    return None
