"""Zone and line geometry in normalized 0..1 coordinates."""
from __future__ import annotations

from dataclasses import dataclass

import supervision as sv


@dataclass
class Zone:
    """Polygon zone in normalized (0..1) coordinates."""

    name: str
    points: list[list[float]]  # [[x,y], ...] normalized

    def contains_point(self, x: float, y: float) -> bool:
        """Ray-casting point-in-polygon test (normalized coords)."""
        pts = self.points
        n = len(pts)
        inside = False
        j = n - 1
        for i in range(n):
            xi, yi = pts[i]
            xj, yj = pts[j]
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        return inside


@dataclass
class Line:
    """Virtual counting line in normalized (0..1) coordinates.

    start/end are (x, y) pairs.  Use to_sv_line_zone() to get the
    pixel-space supervision LineZone required by the counter.
    """

    name: str
    start: tuple[float, float]
    end: tuple[float, float]

    def to_sv_line_zone(self, frame_w: int, frame_h: int) -> sv.LineZone:
        """Return a supervision LineZone in pixel coordinates."""
        x1, y1 = int(self.start[0] * frame_w), int(self.start[1] * frame_h)
        x2, y2 = int(self.end[0] * frame_w), int(self.end[1] * frame_h)
        return sv.LineZone(start=sv.Point(x1, y1), end=sv.Point(x2, y2))


# Default lines used when no camera_configuration exists in MongoDB yet.
# Line A at 35 % of frame height, Line B at 65 % — products moving top→bottom
# cross A first (loading); bottom→top cross B first (unloading).
DEFAULT_LINE_A = Line("A", start=(0.0, 0.35), end=(1.0, 0.35))
DEFAULT_LINE_B = Line("B", start=(0.0, 0.65), end=(1.0, 0.65))
