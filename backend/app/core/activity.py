"""Activity/Session FSM for loading/unloading detection."""


class ActivityFSM:
    """Finite state machine for activity detection."""

    def __init__(self):
        self.state = "IDLE"
        self.start_time = None

    def update(self, trucks_present, activity_detected):
        """Update FSM based on activity."""
        pass

    def get_session_type(self):
        """Get current session type (LOADING/UNLOADING)."""
        return None
