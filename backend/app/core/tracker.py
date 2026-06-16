"""ByteTrack tracker wrapper using supervision."""


class ByteTracker:
    """Wrapper for ByteTrack via supervision."""

    def __init__(self):
        self.tracker = None

    def update(self, detections):
        """Update tracker with detections."""
        pass

    def reset(self):
        """Reset tracker state."""
        pass
