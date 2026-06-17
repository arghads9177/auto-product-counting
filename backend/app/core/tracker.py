"""ByteTrack tracker wrapper using supervision."""
import warnings

import supervision as sv


class ByteTracker:
    """ByteTrack wrapper (suppresses supervision deprecation warnings for v0.29)."""

    def __init__(
        self,
        track_activation_threshold: float = 0.25,
        lost_track_buffer: int = 30,
        minimum_matching_threshold: float = 0.8,
        frame_rate: float = 25.0,
    ):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            self.tracker = sv.ByteTrack(
                track_activation_threshold=track_activation_threshold,
                lost_track_buffer=lost_track_buffer,
                minimum_matching_threshold=minimum_matching_threshold,
                frame_rate=frame_rate,
            )

    def update(self, detections: sv.Detections) -> sv.Detections:
        """Update tracker and return detections with stable tracker_id assigned."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            return self.tracker.update_with_detections(detections)

    def reset(self) -> None:
        """Reset tracker state — call between counting sessions."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            self.tracker.reset()
