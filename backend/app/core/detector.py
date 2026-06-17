"""YOLOv11 detector wrapper."""
import numpy as np
import supervision as sv

# COCO class IDs relevant to this application
COCO_TARGET_CLASSES: dict[int, str] = {
    0: "person",
    2: "car",
    5: "bus",
    7: "truck",
}

_TARGET_IDS = list(COCO_TARGET_CLASSES.keys())


class YOLODetector:
    """YOLOv11n wrapper for CPU inference."""

    def __init__(self, model_name: str = "yolo11n.pt", confidence: float = 0.4):
        self.model_name = model_name
        self.confidence = confidence
        self.model = None

    def load(self) -> None:
        """Load YOLO model weights (downloads on first call)."""
        from ultralytics import YOLO
        self.model = YOLO(self.model_name)

    def detect(self, frame: np.ndarray) -> sv.Detections:
        """Run inference and return detections filtered to target COCO classes."""
        if self.model is None:
            raise RuntimeError("Model not loaded — call load() first")
        results = self.model(frame, conf=self.confidence, verbose=False)[0]
        detections = sv.Detections.from_ultralytics(results)
        if len(detections) == 0:
            return detections
        mask = np.isin(detections.class_id, _TARGET_IDS)
        return detections[mask]

    def unload(self) -> None:
        """Release model from memory."""
        self.model = None
