"""Zone and line geometry management."""


class Zone:
    """Zone geometry in normalized coordinates."""

    def __init__(self, name: str, points: list):
        self.name = name
        self.points = points

    def contains_point(self, point):
        """Check if point is in zone."""
        pass


class Line:
    """Line for counting crossings."""

    def __init__(self, name: str, point1: tuple, point2: tuple):
        self.name = name
        self.point1 = point1
        self.point2 = point2

    def crosses(self, p1, p2):
        """Check if line is crossed."""
        pass
