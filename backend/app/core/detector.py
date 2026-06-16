"""YOLOv11 detector wrapper."""


class YOLODetector:
    """Wrapper for YOLOv11n detector."""

    def __init__(self, model_name: str = "yolov11n"):
        self.model_name = model_name
        self.model = None

    def load(self):
        """Load YOLOv11 model."""
        pass

    def detect(self, frame):
        """Run inference on frame."""
        pass

    def unload(self):
        """Unload model from memory."""
        pass
