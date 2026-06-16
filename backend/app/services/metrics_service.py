"""Metrics aggregation service."""


class MetricsService:
    """Aggregates and computes metrics."""

    def __init__(self, db):
        self.db = db

    async def get_camera_metrics(self, camera_id):
        """Get metrics for a specific camera."""
        pass

    async def get_plant_metrics(self):
        """Get plant-wide metrics."""
        pass

    async def get_hourly_trend(self, camera_id, hours=24):
        """Get hourly trend data."""
        pass
