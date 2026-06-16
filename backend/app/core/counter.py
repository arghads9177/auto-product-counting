"""Dual-line counting logic."""


class DualLineCounter:
    """Dual-line crossing counter with dedup."""

    def __init__(self, line_a, line_b):
        self.line_a = line_a
        self.line_b = line_b
        self.tracks_seen = {}

    def count_crossing(self, track_id, position):
        """Count a crossing if valid."""
        pass

    def get_counts(self):
        """Get loading and unloading counts."""
        return {"loading": 0, "unloading": 0}
