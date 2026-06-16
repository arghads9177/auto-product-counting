"""JWT authentication and token management."""
from datetime import datetime, timedelta
from typing import Optional


class AuthService:
    """JWT authentication service."""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_token(self, username: str, expires_delta: Optional[timedelta] = None):
        """Create JWT token for user."""
        pass

    def verify_token(self, token: str):
        """Verify JWT token."""
        pass

    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt."""
        pass

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        pass
