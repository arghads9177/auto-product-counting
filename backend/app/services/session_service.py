"""Session management service."""


class SessionService:
    """Manages loading/unloading sessions."""

    def __init__(self, db):
        self.db = db

    async def create_session(self, camera_id, session_type):
        """Create a new session."""
        pass

    async def complete_session(self, session_id):
        """Complete an active session."""
        pass

    async def get_active_sessions(self, camera_id):
        """Get active sessions for a camera."""
        pass
